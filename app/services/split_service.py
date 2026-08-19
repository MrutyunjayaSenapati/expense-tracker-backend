from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ResourceNotFoundError, ValidationAppError, AuthorizationError
from app.db.models.split import SplitBill, SplitParticipant
from app.repositories.split_repository import SplitRepository
from app.schemas.split import SplitBillCreate


class SplitService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SplitRepository(db)

    async def list_splits(
        self, user_id: uuid.UUID, status: Optional[str] = None
    ) -> List[SplitBill]:
        return await self.repo.get_all_for_user(user_id=user_id, status=status)

    async def get_split(self, user_id: uuid.UUID, bill_id: uuid.UUID) -> SplitBill:
        bill = await self.repo.get_by_id_with_details(bill_id)
        if not bill:
            raise ResourceNotFoundError("Split bill not found", "NOT_FOUND")

        # Check authorization (must be creator, payer, or participant)
        is_participant = any(p.user_id == user_id for p in bill.participants)
        if bill.creator_id != user_id and bill.paid_by_user_id != user_id and not is_participant:
            raise AuthorizationError("You do not have access to this split bill", "FORBIDDEN")

        return bill

    async def get_summary(self, user_id: uuid.UUID) -> Tuple[Decimal, Decimal, int, int]:
        return await self.repo.get_summary_for_user(user_id)

    async def create_split(self, user_id: uuid.UUID, payload: SplitBillCreate) -> SplitBill:
        # Determine payer
        paid_by_user_id = user_id
        if payload.paid_by == "FRIEND" and payload.payer_name:
            # Check if payer is a registered user
            matched_payer = await self.repo.find_user_by_identifier(payload.payer_name)
            if matched_payer:
                paid_by_user_id = matched_payer.id

        bill = SplitBill(
            creator_id=user_id,
            paid_by_user_id=paid_by_user_id,
            title=payload.title.strip(),
            total_amount=payload.total_amount,
            your_share=payload.your_share,
            date=payload.date or datetime.now(timezone.utc),
            is_settled=False,
            note=payload.note.strip() if payload.note else None,
        )
        self.db.add(bill)
        await self.db.flush()

        # Add participants and link matching registered users
        for p in payload.participants:
            matched_user = None
            if p.email_or_phone:
                matched_user = await self.repo.find_user_by_identifier(p.email_or_phone)
            if not matched_user:
                matched_user = await self.repo.find_user_by_identifier(p.name)

            participant = SplitParticipant(
                split_bill_id=bill.id,
                user_id=matched_user.id if matched_user else None,
                name=p.name.strip(),
                phone_or_upi=p.email_or_phone.strip() if p.email_or_phone else None,
                amount_owed=p.amount_owed,
                is_paid=False,
            )
            self.db.add(participant)

        await self.db.commit()
        return await self.get_split(user_id, bill.id)

    async def settle_participant(
        self, user_id: uuid.UUID, bill_id: uuid.UUID, participant_id: uuid.UUID, is_paid: bool
    ) -> SplitBill:
        bill = await self.get_split(user_id, bill_id)

        # Allow creator, payer, or the participant themselves to toggle status
        is_target_participant = any(
            p.id == participant_id and p.user_id == user_id for p in bill.participants
        )
        if bill.creator_id != user_id and bill.paid_by_user_id != user_id and not is_target_participant:
            raise AuthorizationError("Not allowed to update settlement for this participant", "FORBIDDEN")

        updated_bill = await self.repo.settle_participant(bill_id, participant_id, is_paid)
        if not updated_bill:
            raise ResourceNotFoundError("Participant or bill not found", "NOT_FOUND")

        return updated_bill

    async def delete_split(self, user_id: uuid.UUID, bill_id: uuid.UUID) -> None:
        bill = await self.get_split(user_id, bill_id)
        if bill.creator_id != user_id and bill.paid_by_user_id != user_id:
            raise AuthorizationError("Only the creator can delete this split bill", "FORBIDDEN")

        await self.db.delete(bill)
        await self.db.commit()
