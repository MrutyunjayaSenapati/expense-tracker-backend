from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ResourceNotFoundError
from app.db.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.category_repo = CategoryRepository(db)

    async def list_categories(
        self, user_id: uuid.UUID, category_type: Optional[str] = None
    ) -> List[Category]:
        return await self.category_repo.get_all_by_user(
            user_id=user_id, category_type=category_type, active_only=True
        )

    async def get_category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> Category:
        category = await self.category_repo.get_by_user_and_id(
            user_id=user_id, category_id=category_id
        )
        if not category or not category.is_active:
            raise ResourceNotFoundError("Category not found", "CATEGORY_NOT_FOUND")
        return category

    async def create_category(self, user_id: uuid.UUID, payload: CategoryCreate) -> Category:
        category = Category(
            user_id=user_id,
            name=payload.name.strip(),
            type=payload.type,
            icon=payload.icon,
            color=payload.color,
            is_active=True,
        )
        category = await self.category_repo.create(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update_category(
        self, user_id: uuid.UUID, category_id: uuid.UUID, payload: CategoryUpdate
    ) -> Category:
        category = await self.get_category(user_id=user_id, category_id=category_id)

        if payload.name is not None:
            category.name = payload.name.strip()
        if payload.icon is not None:
            category.icon = payload.icon
        if payload.color is not None:
            category.color = payload.color

        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete_category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> None:
        category = await self.get_category(user_id=user_id, category_id=category_id)
        # Soft delete / deactivate to preserve historical transactions
        category.is_active = False
        await self.db.commit()
