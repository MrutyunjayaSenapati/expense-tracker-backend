from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ResourceNotFoundError, ValidationAppError
from app.db.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.gamification_service import GamificationService


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.txn_repo = TransactionRepository(db)
        self.account_repo = AccountRepository(db)
        self.category_repo = CategoryRepository(db)
        self.gamification_service = GamificationService(db)

    async def list_transactions(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
        category_id: Optional[uuid.UUID] = None,
        account_id: Optional[uuid.UUID] = None,
        txn_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        search: Optional[str] = None,
        sort: str = "transaction_date",
        order: str = "desc",
    ) -> Tuple[List[Transaction], int]:
        return await self.txn_repo.list_filtered(
            user_id=user_id,
            page=page,
            limit=limit,
            category_id=category_id,
            account_id=account_id,
            txn_type=txn_type,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            search=search,
            sort=sort,
            order=order,
        )

    async def get_transaction(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
        txn = await self.txn_repo.get_by_user_and_id(user_id=user_id, transaction_id=transaction_id)
        if not txn:
            raise ResourceNotFoundError("Transaction not found", "TRANSACTION_NOT_FOUND")
        return txn

    async def create_transaction(self, user_id: uuid.UUID, payload: TransactionCreate) -> Transaction:
        # Validate account ownership
        account = await self.account_repo.get_by_user_and_id(user_id=user_id, account_id=payload.account_id)
        if not account or not account.is_active:
            raise ValidationAppError(
                message="Account not found or inactive",
                code="INVALID_ACCOUNT",
                fields={"account_id": "Specified account is invalid"},
            )

        # Validate category ownership
        category = await self.category_repo.get_by_user_and_id(user_id=user_id, category_id=payload.category_id)
        if not category or not category.is_active:
            raise ValidationAppError(
                message="Category not found or inactive",
                code="INVALID_CATEGORY",
                fields={"category_id": "Specified category is invalid"},
            )

        txn_date = payload.transaction_date or datetime.now(timezone.utc)

        # Create transaction model
        txn = Transaction(
            user_id=user_id,
            account_id=payload.account_id,
            category_id=payload.category_id,
            amount=payload.amount,
            type=payload.type,
            merchant=payload.merchant.strip() if payload.merchant else None,
            note=payload.note.strip() if payload.note else None,
            transaction_date=txn_date,
        )
        self.db.add(txn)
        await self.db.flush()

        # Update account balance atomically
        balance_delta = -payload.amount if payload.type == "EXPENSE" else payload.amount
        await self.account_repo.update_balance(payload.account_id, balance_delta)

        # Update streak and gamification
        await self.gamification_service.record_transaction_activity(user_id, txn_date.date())

        await self.db.commit()

        # Reload with joined account & category
        return await self.get_transaction(user_id, txn.id)

    async def update_transaction(
        self, user_id: uuid.UUID, transaction_id: uuid.UUID, payload: TransactionUpdate
    ) -> Transaction:
        txn = await self.get_transaction(user_id, transaction_id)

        old_amount = txn.amount
        old_type = txn.type
        old_account_id = txn.account_id

        # 1. Reverse old financial balance impact
        old_delta = old_amount if old_type == "EXPENSE" else -old_amount
        await self.account_repo.update_balance(old_account_id, old_delta)

        # 2. Check and validate new account if provided
        new_account_id = payload.account_id if payload.account_id is not None else old_account_id
        if payload.account_id is not None and payload.account_id != old_account_id:
            account = await self.account_repo.get_by_user_and_id(user_id, new_account_id)
            if not account or not account.is_active:
                raise ValidationAppError("New account is invalid", "INVALID_ACCOUNT")

        # 3. Check and validate new category if provided
        if payload.category_id is not None and payload.category_id != txn.category_id:
            category = await self.category_repo.get_by_user_and_id(user_id, payload.category_id)
            if not category or not category.is_active:
                raise ValidationAppError("New category is invalid", "INVALID_CATEGORY")
            txn.category_id = payload.category_id

        # 4. Apply changes
        new_amount = payload.amount if payload.amount is not None else old_amount
        new_type = payload.type if payload.type is not None else old_type

        txn.account_id = new_account_id
        txn.amount = new_amount
        txn.type = new_type

        if payload.merchant is not None:
            txn.merchant = payload.merchant.strip() if payload.merchant else None
        if payload.note is not None:
            txn.note = payload.note.strip() if payload.note else None
        if payload.transaction_date is not None:
            txn.transaction_date = payload.transaction_date

        # 5. Apply new financial balance impact
        new_delta = -new_amount if new_type == "EXPENSE" else new_amount
        await self.account_repo.update_balance(new_account_id, new_delta)

        await self.db.commit()
        return await self.get_transaction(user_id, txn.id)

    async def delete_transaction(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
        txn = await self.get_transaction(user_id, transaction_id)

        # Reverse balance impact
        delta = txn.amount if txn.type == "EXPENSE" else -txn.amount
        await self.account_repo.update_balance(txn.account_id, delta)

        await self.txn_repo.delete(txn)
        await self.db.commit()
