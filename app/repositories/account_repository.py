from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.account import Account
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    def __init__(self, db: AsyncSession):
        super().__init__(Account, db)

    async def get_by_user_and_id(self, user_id: uuid.UUID, account_id: uuid.UUID) -> Optional[Account]:
        result = await self.db.execute(
            select(Account).where(
                Account.id == account_id,
                Account.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def get_all_by_user(self, user_id: uuid.UUID, active_only: bool = True) -> List[Account]:
        query = select(Account).where(Account.user_id == user_id)
        if active_only:
            query = query.where(Account.is_active.is_(True))
        query = query.order_by(Account.created_at.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_balance(self, account_id: uuid.UUID, delta: Decimal) -> None:
        await self.db.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(balance=Account.balance + delta)
        )
        await self.db.flush()
