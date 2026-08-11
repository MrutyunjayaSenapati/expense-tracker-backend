import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.account import (
    AccountCreate,
    AccountListResponse,
    AccountResponse,
    AccountUpdate,
)
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get(
    "",
    response_model=AccountListResponse,
    summary="List all active accounts for user",
)
async def list_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    accounts = await service.list_accounts(current_user.id)
    return AccountListResponse(items=[AccountResponse.model_validate(a) for a in accounts])


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new financial account",
)
async def create_account(
    payload: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    account = await service.create_account(current_user.id, payload)
    return AccountResponse.model_validate(account)


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Get account by ID",
)
async def get_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    account = await service.get_account(current_user.id, account_id)
    return AccountResponse.model_validate(account)


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Update account metadata",
)
async def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    account = await service.update_account(current_user.id, account_id, payload)
    return AccountResponse.model_validate(account)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete/deactivate account",
)
async def delete_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AccountService(db)
    await service.delete_account(current_user.id, account_id)
