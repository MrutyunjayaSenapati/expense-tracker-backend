from datetime import date
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.recurring_transaction import RecurringTransaction
from app.repositories.base import BaseRepository


class RecurringTransactionRepository(BaseRepository[RecurringTransaction]):
    def __init__(self, db: AsyncSession):
        super().__init__(RecurringTransaction, db)

    async def get_by_user_and_id(
        self, user_id: uuid.UUID, recurring_id: uuid.UUID
    ) -> Optional[RecurringTransaction]:
        result = await self.db.execute(
            select(RecurringTransaction)
            .options(
                selectinload(RecurringTransaction.account),
                selectinload(RecurringTransaction.category),
            )
            .where(
                RecurringTransaction.id == recurring_id,
                RecurringTransaction.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def get_all_by_user(
        self, user_id: uuid.UUID, active_only: bool = True
    ) -> List[RecurringTransaction]:
        query = (
            select(RecurringTransaction)
            .options(
                selectinload(RecurringTransaction.account),
                selectinload(RecurringTransaction.category),
            )
            .where(RecurringTransaction.user_id == user_id)
        )
        if active_only:
            query = query.where(RecurringTransaction.is_active.is_(True))
        query = query.order_by(RecurringTransaction.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_due_transactions(self, target_date: date) -> List[RecurringTransaction]:
        query = (
            select(RecurringTransaction)
            .options(
                selectinload(RecurringTransaction.account),
                selectinload(RecurringTransaction.category),
            )
            .where(
                RecurringTransaction.is_active.is_(True),
                RecurringTransaction.next_occurrence <= target_date,
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
