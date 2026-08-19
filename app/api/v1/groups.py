from typing import List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.group import (
    GroupCreate,
    GroupDetailResponse,
    GroupListItemResponse,
    GroupJoinRequest,
    GroupExpenseCreate,
    GroupSettlementCreate,
)
from app.services.group_service import GroupService

router = APIRouter(prefix="/groups", tags=["Shared Expense Groups"])


@router.get(
    "",
    response_model=List[GroupListItemResponse],
    summary="List all groups involving the current user",
)
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GroupService(db)
    return await service.list_groups_for_user(current_user.id)


@router.post(
    "",
    response_model=GroupDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shared expense group",
)
async def create_group(
    payload: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GroupService(db)
    return await service.create_group(current_user.id, current_user.name, payload)


@router.post(
    "/join",
    response_model=GroupDetailResponse,
    summary="Join an existing group using a 6-character invite code",
)
async def join_group(
    payload: GroupJoinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GroupService(db)
    return await service.join_group_by_code(
        current_user.id, current_user.name, current_user.email, payload.invite_code
    )


@router.get(
    "/{group_id}",
    response_model=GroupDetailResponse,
    summary="Get group dashboard with members, expenses, and simplified balances",
)
async def get_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GroupService(db)
    return await service.get_group_detail(current_user.id, group_id)


@router.post(
    "/{group_id}/expenses",
    response_model=GroupDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new multi-payer expense to the group",
)
async def add_group_expense(
    group_id: uuid.UUID,
    payload: GroupExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GroupService(db)
    return await service.add_group_expense(current_user.id, group_id, payload)


@router.post(
    "/{group_id}/settle",
    response_model=GroupDetailResponse,
    summary="Record a settlement payment between two group members",
)
async def record_settlement(
    group_id: uuid.UUID,
    payload: GroupSettlementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GroupService(db)
    return await service.record_settlement(current_user.id, group_id, payload)


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a group (creator only)",
)
async def delete_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = GroupService(db)
    await service.delete_group(current_user.id, group_id)
