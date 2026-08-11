from datetime import datetime
from decimal import Decimal
import math
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List transactions with filters and search",
)
async def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[uuid.UUID] = None,
    account_id: Optional[uuid.UUID] = None,
    type: Optional[str] = Query(None, pattern="^(EXPENSE|INCOME)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None,
    sort: str = Query("transaction_date", pattern="^(transaction_date|amount|created_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    items, total = await service.list_transactions(
        user_id=current_user.id,
        page=page,
        limit=limit,
        category_id=category_id,
        account_id=account_id,
        txn_type=type,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        sort=sort,
        order=order,
    )
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in items],
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an expense or income transaction",
)
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    txn = await service.create_transaction(current_user.id, payload)
    return TransactionResponse.model_validate(txn)


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get single transaction details",
)
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    txn = await service.get_transaction(current_user.id, transaction_id)
    return TransactionResponse.model_validate(txn)


@router.patch(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update transaction details",
)
async def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    txn = await service.update_transaction(current_user.id, transaction_id, payload)
    return TransactionResponse.model_validate(txn)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete transaction and reverse balance impact",
)
async def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TransactionService(db)
    await service.delete_transaction(current_user.id, transaction_id)
