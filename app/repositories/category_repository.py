from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: AsyncSession):
        super().__init__(Category, db)

    async def get_by_user_and_id(self, user_id: uuid.UUID, category_id: uuid.UUID) -> Optional[Category]:
        result = await self.db.execute(
            select(Category).where(
                Category.id == category_id,
                Category.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def get_all_by_user(
        self,
        user_id: uuid.UUID,
        category_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Category]:
        query = select(Category).where(Category.user_id == user_id)
        if category_type:
            query = query.where(Category.type == category_type.upper())
        if active_only:
            query = query.where(Category.is_active.is_(True))
        query = query.order_by(Category.name.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_bulk(self, categories: List[Category]) -> List[Category]:
        self.db.add_all(categories)
        await self.db.flush()
        return categories
