from datetime import date
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.recurring import (
    RecurringTransactionCreate,
    RecurringTransactionListResponse,
    RecurringTransactionResponse,
    RecurringTransactionUpdate,
)
from app.services.recurring_service import RecurringTransactionService

router = APIRouter(prefix="/recurring-transactions", tags=["Recurring Transactions"])


@router.get(
    "",
    response_model=RecurringTransactionListResponse,
    summary="List all active recurring transactions",
)
async def list_recurring(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    items = await service.list_recurring(current_user.id)
    return RecurringTransactionListResponse(
        items=[RecurringTransactionResponse.model_validate(i) for i in items]
    )


@router.post(
    "",
    response_model=RecurringTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new recurring transaction schedule",
)
async def create_recurring(
    payload: RecurringTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    item = await service.create_recurring(current_user.id, payload)
    return RecurringTransactionResponse.model_validate(item)


@router.get(
    "/{recurring_id}",
    response_model=RecurringTransactionResponse,
    summary="Get recurring transaction by ID",
)
async def get_recurring(
    recurring_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    item = await service.get_recurring(current_user.id, recurring_id)
    return RecurringTransactionResponse.model_validate(item)


@router.patch(
    "/{recurring_id}",
    response_model=RecurringTransactionResponse,
    summary="Update recurring transaction",
)
async def update_recurring(
    recurring_id: uuid.UUID,
    payload: RecurringTransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    item = await service.update_recurring(current_user.id, recurring_id, payload)
    return RecurringTransactionResponse.model_validate(item)


@router.delete(
    "/{recurring_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete/deactivate recurring transaction",
)
async def delete_recurring(
    recurring_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    await service.delete_recurring(current_user.id, recurring_id)


@router.post(
    "/process",
    summary="Trigger processing of due recurring transactions",
)
async def process_recurring(
    target_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecurringTransactionService(db)
    processed = await service.process_due_recurring_transactions(target_date or date.today())
    return {"status": "success", "processed_count": processed}
