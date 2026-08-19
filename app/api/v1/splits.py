from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.split import (
    SplitBillCreate,
    SplitBillResponse,
    SplitSummaryResponse,
    SplitSettleRequest,
)
from app.services.split_service import SplitService

router = APIRouter(prefix="/splits", tags=["Split Expenses"])


@router.get(
    "",
    response_model=List[SplitBillResponse],
    summary="List all split bills involving the user",
)
async def list_splits(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(PENDING|SETTLED)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SplitService(db)
    items = await service.list_splits(current_user.id, status=status_filter)
    return [SplitBillResponse.model_validate(i) for i in items]


@router.get(
    "/summary",
    response_model=SplitSummaryResponse,
    summary="Get total owed and owing balances across all split bills",
)
async def get_splits_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SplitService(db)
    owed, owing, pending_count, settled_count = await service.get_summary(current_user.id)
    return SplitSummaryResponse(
        total_owed_to_you=owed,
        total_you_owe=owing,
        pending_bills_count=pending_count,
        settled_bills_count=settled_count,
    )


@router.post(
    "",
    response_model=SplitBillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new split bill",
)
async def create_split(
    payload: SplitBillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SplitService(db)
    item = await service.create_split(current_user.id, payload)
    return SplitBillResponse.model_validate(item)


@router.get(
    "/{bill_id}",
    response_model=SplitBillResponse,
    summary="Get split bill details by ID",
)
async def get_split(
    bill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SplitService(db)
    item = await service.get_split(current_user.id, bill_id)
    return SplitBillResponse.model_validate(item)


@router.patch(
    "/{bill_id}/participants/{participant_id}/settle",
    response_model=SplitBillResponse,
    summary="Mark a participant share as paid or unpaid",
)
async def settle_participant(
    bill_id: uuid.UUID,
    participant_id: uuid.UUID,
    payload: SplitSettleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SplitService(db)
    updated = await service.settle_participant(
        current_user.id, bill_id, participant_id, payload.is_paid
    )
    return SplitBillResponse.model_validate(updated)


@router.delete(
    "/{bill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a split bill",
)
async def delete_split(
    bill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SplitService(db)
    await service.delete_split(current_user.id, bill_id)
