from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ResourceNotFoundError, ValidationAppError, AuthorizationError, ConflictError
from app.db.models.group import Group, GroupMember, GroupExpense, GroupExpenseSplit, GroupSettlement
from app.repositories.group_repository import GroupRepository
from app.schemas.group import (
    GroupCreate,
    GroupDetailResponse,
    GroupListItemResponse,
    GroupExpenseCreate,
    GroupSettlementCreate,
    GroupMemberResponse,
    GroupExpenseResponse,
    GroupExpenseSplitResponse,
    GroupSettlementResponse,
)


class GroupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GroupRepository(db)

    async def create_group(self, user_id: uuid.UUID, user_name: str, payload: GroupCreate) -> GroupDetailResponse:
        group = Group(
            creator_id=user_id,
            name=payload.name.strip(),
            category=payload.category,
            currency=payload.currency,
        )
        self.db.add(group)
        await self.db.flush()

        # 1. Add creator as first member (ADMIN)
        creator_member = GroupMember(
            group_id=group.id,
            user_id=user_id,
            name=user_name,
            role="ADMIN",
        )
        self.db.add(creator_member)

        # 2. Add invited initial members
        if payload.members:
            for m in payload.members:
                matched_user = None
                if m.email_or_phone:
                    matched_user = await self.repo.find_user_by_identifier(m.email_or_phone)
                if not matched_user:
                    matched_user = await self.repo.find_user_by_identifier(m.name)

                member = GroupMember(
                    group_id=group.id,
                    user_id=matched_user.id if matched_user else None,
                    name=m.name.strip(),
                    email_or_phone=m.email_or_phone.strip() if m.email_or_phone else None,
                    role="MEMBER",
                )
                self.db.add(member)

        await self.db.commit()
        return await self.get_group_detail(user_id, group.id)

    async def list_groups_for_user(self, user_id: uuid.UUID) -> List[GroupListItemResponse]:
        groups = await self.repo.get_all_for_user(user_id)
        items: List[GroupListItemResponse] = []

        for g in groups:
            balances, _ = self.repo.calculate_group_balances(g)
            user_balance = next((b.net_balance for b in balances if b.user_id == user_id), Decimal("0.00"))

            items.append(
                GroupListItemResponse(
                    id=g.id,
                    name=g.name,
                    category=g.category,
                    invite_code=g.invite_code,
                    currency=g.currency,
                    creator_id=g.creator_id,
                    member_count=len(g.members),
                    your_net_balance=user_balance,
                    created_at=g.created_at,
                )
            )

        return items

    async def get_group_detail(self, user_id: uuid.UUID, group_id: uuid.UUID) -> GroupDetailResponse:
        group = await self.repo.get_by_id_with_details(group_id)
        if not group:
            raise ResourceNotFoundError("Group not found", "NOT_FOUND")

        # Must be creator or member
        is_member = any(m.user_id == user_id for m in group.members)
        if group.creator_id != user_id and not is_member:
            raise AuthorizationError("You are not a member of this group", "FORBIDDEN")

        balances, simplified_debts = self.repo.calculate_group_balances(group)
        your_net = next((b.net_balance for b in balances if b.user_id == user_id), Decimal("0.00"))

        return GroupDetailResponse(
            id=group.id,
            name=group.name,
            category=group.category,
            invite_code=group.invite_code,
            currency=group.currency,
            creator_id=group.creator_id,
            created_at=group.created_at,
            members=[GroupMemberResponse.model_validate(m) for m in group.members],
            expenses=[
                GroupExpenseResponse(
                    id=e.id,
                    group_id=e.group_id,
                    paid_by_user_id=e.paid_by_user_id,
                    payer_name=e.payer_name,
                    title=e.title,
                    amount=e.amount,
                    date=e.date,
                    note=e.note,
                    created_at=e.created_at,
                    splits=[GroupExpenseSplitResponse.model_validate(s) for s in e.splits],
                )
                for e in group.expenses
            ],
            settlements=[GroupSettlementResponse.model_validate(s) for s in group.settlements],
            balances=balances,
            simplified_debts=simplified_debts,
            your_net_balance=your_net,
        )

    async def join_group_by_code(self, user_id: uuid.UUID, user_name: str, user_email: str, code: str) -> GroupDetailResponse:
        group = await self.repo.get_by_invite_code(code)
        if not group:
            raise ResourceNotFoundError("Invalid group invite code", "INVALID_INVITE_CODE")

        # Check if already joined by user_id or email
        existing = next((m for m in group.members if m.user_id == user_id or (m.email_or_phone and m.email_or_phone.lower() == user_email.lower())), None)
        if existing:
            if not existing.user_id:
                existing.user_id = user_id
                await self.db.commit()
            return await self.get_group_detail(user_id, group.id)

        # Join as new member
        new_member = GroupMember(
            group_id=group.id,
            user_id=user_id,
            name=user_name,
            email_or_phone=user_email,
            role="MEMBER",
        )
        self.db.add(new_member)
        await self.db.commit()
        return await self.get_group_detail(user_id, group.id)

    async def add_group_expense(
        self, user_id: uuid.UUID, group_id: uuid.UUID, payload: GroupExpenseCreate
    ) -> GroupDetailResponse:
        group = await self.repo.get_by_id_with_details(group_id)
        if not group:
            raise ResourceNotFoundError("Group not found", "NOT_FOUND")

        # Find payer member
        payer_member = next((m for m in group.members if m.id == payload.paid_by_member_id), None)
        if not payer_member:
            raise ValidationAppError("Selected payer is not a member of this group", "INVALID_PAYER")

        # Determine participants involved in split
        split_members = group.members
        if payload.split_member_ids:
            split_members = [m for m in group.members if m.id in payload.split_member_ids]

        if not split_members:
            raise ValidationAppError("No participants selected for split", "INVALID_SPLIT")

        # Accurate penny division with remainder distribution
        total_cents = int(payload.amount * 100)
        split_count = len(split_members)
        base_cents = total_cents // split_count
        remainder_cents = total_cents % split_count

        splits_list = []
        for idx, m in enumerate(split_members):
            member_cents = base_cents + (1 if idx < remainder_cents else 0)
            member_amount = (Decimal(member_cents) / Decimal("100")).quantize(Decimal("0.01"))
            splits_list.append(
                GroupExpenseSplit(
                    member_id=m.id,
                    amount_owed=member_amount,
                )
            )

        expense = GroupExpense(
            group_id=group.id,
            paid_by_user_id=payer_member.user_id,
            payer_name=payer_member.name,
            title=payload.title.strip(),
            amount=payload.amount,
            date=payload.date or datetime.now(timezone.utc),
            note=payload.note.strip() if payload.note else None,
            splits=splits_list,
        )
        self.db.add(expense)
        target_group_id = group.id

        await self.db.commit()
        return await self.get_group_detail(user_id, target_group_id)

    async def record_settlement(
        self, user_id: uuid.UUID, group_id: uuid.UUID, payload: GroupSettlementCreate
    ) -> GroupDetailResponse:
        group = await self.repo.get_by_id_with_details(group_id)
        if not group:
            raise ResourceNotFoundError("Group not found", "NOT_FOUND")

        settlement = GroupSettlement(
            group_id=group.id,
            from_user_id=payload.from_user_id,
            to_user_id=payload.to_user_id,
            amount=payload.amount,
            settled_at=datetime.now(timezone.utc),
        )
        self.db.add(settlement)
        target_group_id = group.id

        await self.db.commit()
        return await self.get_group_detail(user_id, target_group_id)

    async def delete_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        group = await self.repo.get_by_id_with_details(group_id)
        if not group:
            raise ResourceNotFoundError("Group not found", "NOT_FOUND")
        if group.creator_id != user_id:
            raise AuthorizationError("Only the group creator can delete this group", "FORBIDDEN")

        await self.db.delete(group)
        await self.db.commit()
