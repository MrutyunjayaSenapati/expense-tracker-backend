from datetime import date
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.budget import Budget, BudgetCategory
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self, db: AsyncSession):
        super().__init__(Budget, db)

    async def get_by_user_and_id(self, user_id: uuid.UUID, budget_id: uuid.UUID) -> Optional[Budget]:
        result = await self.db.execute(
            select(Budget)
            .options(
                selectinload(Budget.categories).selectinload(BudgetCategory.category)
            )
            .where(
                Budget.id == budget_id,
                Budget.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def get_all_by_user(self, user_id: uuid.UUID, active_only: bool = True) -> List[Budget]:
        query = (
            select(Budget)
            .options(
                selectinload(Budget.categories).selectinload(BudgetCategory.category)
            )
            .where(Budget.user_id == user_id)
        )
        if active_only:
            query = query.where(Budget.is_active.is_(True))
        query = query.order_by(Budget.start_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active_budget_for_date(self, user_id: uuid.UUID, target_date: date) -> Optional[Budget]:
        query = (
            select(Budget)
            .options(
                selectinload(Budget.categories).selectinload(BudgetCategory.category)
            )
            .where(
                Budget.user_id == user_id,
                Budget.is_active.is_(True),
                Budget.start_date <= target_date,
                Budget.end_date >= target_date,
            )
            .order_by(Budget.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().first()
