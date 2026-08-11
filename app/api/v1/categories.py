from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=CategoryListResponse,
    summary="List all categories for user",
)
async def list_categories(
    type: Optional[str] = Query(None, pattern="^(EXPENSE|INCOME)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    categories = await service.list_categories(current_user.id, category_type=type)
    return CategoryListResponse(items=[CategoryResponse.model_validate(c) for c in categories])


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom category",
)
async def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    category = await service.create_category(current_user.id, payload)
    return CategoryResponse.model_validate(category)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
)
async def get_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    category = await service.get_category(current_user.id, category_id)
    return CategoryResponse.model_validate(category)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category details",
)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    category = await service.update_category(current_user.id, category_id, payload)
    return CategoryResponse.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete/deactivate category",
)
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    await service.delete_category(current_user.id, category_id)
