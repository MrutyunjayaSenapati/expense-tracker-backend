import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.split import SplitBill, SplitParticipant
from app.db.models.user import User
from app.repositories.base import BaseRepository


class SplitRepository(BaseRepository[SplitBill]):
    def __init__(self, db: AsyncSession):
        super().__init__(SplitBill, db)

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

    async def get_by_id_with_details(self, bill_id: uuid.UUID) -> Optional[SplitBill]:
        result = await self.db.execute(
            select(SplitBill)
            .options(
                selectinload(SplitBill.creator),
                selectinload(SplitBill.paid_by),
                selectinload(SplitBill.participants).selectinload(SplitParticipant.user),
            )
            .where(SplitBill.id == bill_id)
        )
        return result.scalars().first()

    async def get_all_for_user(
        self, user_id: uuid.UUID, status: Optional[str] = None
    ) -> List[SplitBill]:
        # Bills where user is creator, payer, or one of the participants
        query = (
            select(SplitBill)
            .options(
                selectinload(SplitBill.creator),
                selectinload(SplitBill.paid_by),
                selectinload(SplitBill.participants).selectinload(SplitParticipant.user),
            )
            .where(
                or_(
                    SplitBill.creator_id == user_id,
                    SplitBill.paid_by_user_id == user_id,
                    SplitBill.participants.any(SplitParticipant.user_id == user_id),
                )
            )
        )

        if status == "PENDING":
            query = query.where(SplitBill.is_settled.is_(False))
        elif status == "SETTLED":
            query = query.where(SplitBill.is_settled.is_(True))

        query = query.order_by(SplitBill.date.desc(), SplitBill.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_summary_for_user(self, user_id: uuid.UUID) -> Tuple[Decimal, Decimal, int, int]:
        bills = await self.get_all_for_user(user_id)
        
        total_owed_to_you = Decimal("0.00")
        total_you_owe = Decimal("0.00")
        pending_count = 0
        settled_count = 0

        for bill in bills:
            if bill.is_settled:
                settled_count += 1
            else:
                pending_count += 1

            # If current user paid for the bill -> friends owe them
            if bill.paid_by_user_id == user_id:
                for p in bill.participants:
                    if not p.is_paid and p.user_id != user_id:
                        total_owed_to_you += p.amount_owed
            else:
                # If someone else paid and current user is a participant -> current user owes them
                for p in bill.participants:
                    if p.user_id == user_id and not p.is_paid:
                        total_you_owe += p.amount_owed

        return total_owed_to_you, total_you_owe, pending_count, settled_count

    async def settle_participant(
        self, bill_id: uuid.UUID, participant_id: uuid.UUID, is_paid: bool
    ) -> Optional[SplitBill]:
        bill = await self.get_by_id_with_details(bill_id)
        if not bill:
            return None

        for p in bill.participants:
            if p.id == participant_id:
                p.is_paid = is_paid
                p.paid_at = datetime.now(timezone.utc) if is_paid else None
                break

        # Check if all participants are settled
        all_settled = all(p.is_paid for p in bill.participants)
        bill.is_settled = all_settled

        await self.db.commit()
        await self.db.refresh(bill)
        return bill
