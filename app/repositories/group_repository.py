import uuid
from decimal import Decimal
from typing import List, Optional, Tuple, Dict
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.group import Group, GroupMember, GroupExpense, GroupExpenseSplit, GroupSettlement
from app.db.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.group import MemberBalanceSummary, SimplifiedDebt


class GroupRepository(BaseRepository[Group]):
    def __init__(self, db: AsyncSession):
        super().__init__(Group, db)

    async def find_user_by_identifier(self, identifier: str) -> Optional[User]:
        clean = identifier.strip().lower()
        result = await self.db.execute(
            select(User).where(
                or_(
                    func.lower(User.email) == clean,
                    User.name.ilike(f"%{clean}%"),
                )
            )
        )
        return result.scalars().first()

    async def get_by_invite_code(self, code: str) -> Optional[Group]:
        result = await self.db.execute(
            select(Group)
            .options(
                selectinload(Group.members).selectinload(GroupMember.user),
                selectinload(Group.expenses).selectinload(GroupExpense.splits),
                selectinload(Group.settlements),
            )
            .where(func.upper(Group.invite_code) == code.strip().upper())
        )
        return result.scalars().first()

    async def get_by_id_with_details(self, group_id: uuid.UUID) -> Optional[Group]:
        result = await self.db.execute(
            select(Group)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Group.members).selectinload(GroupMember.user),
                selectinload(Group.expenses).selectinload(GroupExpense.splits),
                selectinload(Group.settlements),
            )
            .where(Group.id == group_id)
        )
        return result.scalars().first()

    async def get_all_for_user(self, user_id: uuid.UUID) -> List[Group]:
        # Groups where user is creator OR member
        result = await self.db.execute(
            select(Group)
            .options(
                selectinload(Group.members).selectinload(GroupMember.user),
                selectinload(Group.expenses).selectinload(GroupExpense.splits),
                selectinload(Group.settlements),
            )
            .where(
                or_(
                    Group.creator_id == user_id,
                    Group.members.any(GroupMember.user_id == user_id),
                )
            )
            .order_by(Group.created_at.desc())
        )
        return list(result.scalars().all())

    def calculate_group_balances(
        self, group: Group
    ) -> Tuple[List[MemberBalanceSummary], List[SimplifiedDebt]]:
        """
        Calculates exact net balance for each member and runs the debt simplification algorithm.
        """
        # 1. Initialize tracking per member
        member_map: Dict[uuid.UUID, GroupMember] = {m.id: m for m in group.members}
        paid_totals: Dict[uuid.UUID, Decimal] = {m.id: Decimal("0.00") for m in group.members}
        share_totals: Dict[uuid.UUID, Decimal] = {m.id: Decimal("0.00") for m in group.members}

        # 2. Account for expenses
        for exp in group.expenses:
            # Find which member paid
            payer_member_id = None
            if exp.paid_by_user_id:
                for m in group.members:
                    if m.user_id == exp.paid_by_user_id:
                        payer_member_id = m.id
                        break
            if not payer_member_id:
                # Match by name
                for m in group.members:
                    if m.name.lower() == exp.payer_name.lower():
                        payer_member_id = m.id
                        break

            if payer_member_id and payer_member_id in paid_totals:
                paid_totals[payer_member_id] += exp.amount

            # Add each participant's share
            for split in exp.splits:
                if split.member_id in share_totals:
                    share_totals[split.member_id] += split.amount_owed

        # 3. Account for settlements
        for s in group.settlements:
            # from_user paid money to to_user
            from_member = next((m for m in group.members if m.user_id == s.from_user_id), None)
            to_member = next((m for m in group.members if m.user_id == s.to_user_id), None)

            if from_member:
                paid_totals[from_member.id] += s.amount
            if to_member:
                share_totals[to_member.id] += s.amount

        # 4. Compute Net Balances
        balance_summaries: List[MemberBalanceSummary] = []
        creditors: List[Dict] = []  # Owed money (positive)
        debtors: List[Dict] = []    # Owe money (negative)

        for m_id, member in member_map.items():
            paid = paid_totals[m_id]
            share = share_totals[m_id]
            net = paid - share

            summary = MemberBalanceSummary(
                member_id=m_id,
                user_id=member.user_id,
                name=member.name,
                paid_total=paid,
                share_total=share,
                net_balance=net,
            )
            balance_summaries.append(summary)

            if net > Decimal("0.01"):
                creditors.append({
                    "member": member,
                    "amount": net,
                })
            elif net < Decimal("-0.01"):
                debtors.append({
                    "member": member,
                    "amount": abs(net),
                })

        # 5. Greedy Debt Simplification Algorithm
        simplified_debts: List[SimplifiedDebt] = []
        creditors.sort(key=lambda x: x["amount"], reverse=True)
        debtors.sort(key=lambda x: x["amount"], reverse=True)

        c_idx = 0
        d_idx = 0

        while c_idx < len(creditors) and d_idx < len(debtors):
            creditor = creditors[c_idx]
            debtor = debtors[d_idx]

            settle_amt = min(creditor["amount"], debtor["amount"])
            if settle_amt > Decimal("0.01"):
                simplified_debts.append(
                    SimplifiedDebt(
                        from_member_id=debtor["member"].id,
                        from_member_name=debtor["member"].name,
                        from_user_id=debtor["member"].user_id,
                        to_member_id=creditor["member"].id,
                        to_member_name=creditor["member"].name,
                        to_user_id=creditor["member"].user_id,
                        to_user_phone_or_upi=creditor["member"].email_or_phone,
                        amount=settle_amt.quantize(Decimal("0.01")),
                    )
                )

            creditor["amount"] -= settle_amt
            debtor["amount"] -= settle_amt

            if creditor["amount"] < Decimal("0.01"):
                c_idx += 1
            if debtor["amount"] < Decimal("0.01"):
                d_idx += 1

        return balance_summaries, simplified_debts
