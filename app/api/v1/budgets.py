import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.budget import (
    BudgetCreate,
    BudgetListResponse,
    BudgetResponse,
    BudgetUpdate,
)
from app.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get(
    "",
    response_model=BudgetListResponse,
    summary="List all budgets and their real-time spending progress",
)
async def list_budgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    budgets = await service.list_budgets(current_user.id)
    return BudgetListResponse(items=budgets)


@router.post(
    "",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new monthly budget",
)
async def create_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    return await service.create_budget(current_user.id, payload)


@router.get(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Get budget details and category allocations",
)
async def get_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    return await service.get_budget(current_user.id, budget_id)


@router.patch(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Update budget limit or dates",
)
async def update_budget(
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    return await service.update_budget(current_user.id, budget_id, payload)


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete budget",
)
async def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = BudgetService(db)
    await service.delete_budget(current_user.id, budget_id)
