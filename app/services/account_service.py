from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ResourceNotFoundError
from app.db.models.account import Account
from app.repositories.account_repository import AccountRepository
from app.schemas.account import AccountCreate, AccountUpdate


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)

    async def list_accounts(self, user_id: uuid.UUID) -> List[Account]:
        return await self.account_repo.get_all_by_user(user_id=user_id, active_only=True)

    async def get_account(self, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
        account = await self.account_repo.get_by_user_and_id(user_id=user_id, account_id=account_id)
        if not account or not account.is_active:
            raise ResourceNotFoundError("Account not found", "ACCOUNT_NOT_FOUND")
        return account

    async def create_account(self, user_id: uuid.UUID, payload: AccountCreate) -> Account:
        account = Account(
            user_id=user_id,
            name=payload.name.strip(),
            type=payload.type,
            balance=payload.starting_balance,
            currency="INR",
            is_active=True,
        )
        account = await self.account_repo.create(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def update_account(
        self, user_id: uuid.UUID, account_id: uuid.UUID, payload: AccountUpdate
    ) -> Account:
        account = await self.get_account(user_id=user_id, account_id=account_id)

        if payload.name is not None:
            account.name = payload.name.strip()
        if payload.type is not None:
            account.type = payload.type

        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def delete_account(self, user_id: uuid.UUID, account_id: uuid.UUID) -> None:
        account = await self.get_account(user_id=user_id, account_id=account_id)
        # Soft delete / deactivate to preserve historical transactions
        account.is_active = False
        await self.db.commit()
