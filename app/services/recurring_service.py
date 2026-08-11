from datetime import date, datetime, timedelta, timezone
from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ResourceNotFoundError, ValidationAppError
from app.db.models.notification import Notification
from app.db.models.recurring_transaction import RecurringTransaction
from app.db.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.recurring_repository import RecurringTransactionRepository
from app.schemas.recurring import RecurringTransactionCreate, RecurringTransactionUpdate


def _get_next_monthly_date(current_date: date) -> date:
    """Calculate the next month date safely handling varying month lengths."""
    year = current_date.year
    month = current_date.month + 1
    if month > 12:
        month = 1
        year += 1

    # Handle day overflow for shorter months
    day = current_date.day
    while day > 28:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1
    return date(year, month, day)


class RecurringTransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RecurringTransactionRepository(db)
        self.account_repo = AccountRepository(db)
        self.category_repo = CategoryRepository(db)

    async def list_recurring(self, user_id: uuid.UUID) -> List[RecurringTransaction]:
        return await self.repo.get_all_by_user(user_id=user_id, active_only=True)

    async def get_recurring(
        self, user_id: uuid.UUID, recurring_id: uuid.UUID
    ) -> RecurringTransaction:
        item = await self.repo.get_by_user_and_id(user_id=user_id, recurring_id=recurring_id)
        if not item or not item.is_active:
            raise ResourceNotFoundError("Recurring transaction not found", "NOT_FOUND")
        return item

    async def create_recurring(
        self, user_id: uuid.UUID, payload: RecurringTransactionCreate
    ) -> RecurringTransaction:
        account = await self.account_repo.get_by_user_and_id(user_id, payload.account_id)
        if not account or not account.is_active:
            raise ValidationAppError("Account not found or inactive", "INVALID_ACCOUNT")

        category = await self.category_repo.get_by_user_and_id(user_id, payload.category_id)
        if not category or not category.is_active:
            raise ValidationAppError("Category not found or inactive", "INVALID_CATEGORY")

        recurring = RecurringTransaction(
            user_id=user_id,
            account_id=payload.account_id,
            category_id=payload.category_id,
            type=payload.type,
            amount=payload.amount,
            merchant=payload.merchant.strip() if payload.merchant else None,
            note=payload.note.strip() if payload.note else None,
            frequency=payload.frequency,
            start_date=payload.start_date,
            end_date=payload.end_date,
            next_occurrence=payload.start_date,
            is_active=True,
        )
        self.db.add(recurring)
        await self.db.commit()
        return await self.get_recurring(user_id, recurring.id)

    async def update_recurring(
        self,
        user_id: uuid.UUID,
        recurring_id: uuid.UUID,
        payload: RecurringTransactionUpdate,
    ) -> RecurringTransaction:
        item = await self.get_recurring(user_id, recurring_id)

        if payload.account_id is not None:
            account = await self.account_repo.get_by_user_and_id(user_id, payload.account_id)
            if not account or not account.is_active:
                raise ValidationAppError("Account invalid", "INVALID_ACCOUNT")
            item.account_id = payload.account_id

        if payload.category_id is not None:
            category = await self.category_repo.get_by_user_and_id(user_id, payload.category_id)
            if not category or not category.is_active:
                raise ValidationAppError("Category invalid", "INVALID_CATEGORY")
            item.category_id = payload.category_id

        if payload.type is not None:
            item.type = payload.type
        if payload.amount is not None:
            item.amount = payload.amount
        if payload.merchant is not None:
            item.merchant = payload.merchant.strip() if payload.merchant else None
        if payload.note is not None:
            item.note = payload.note.strip() if payload.note else None
        if payload.frequency is not None:
            item.frequency = payload.frequency
        if payload.start_date is not None:
            item.start_date = payload.start_date
        if payload.end_date is not None:
            item.end_date = payload.end_date
        if payload.is_active is not None:
            item.is_active = payload.is_active

        await self.db.commit()
        return await self.get_recurring(user_id, item.id)

    async def delete_recurring(self, user_id: uuid.UUID, recurring_id: uuid.UUID) -> None:
        item = await self.get_recurring(user_id, recurring_id)
        item.is_active = False
        await self.db.commit()

    async def process_due_recurring_transactions(self, target_date: date) -> int:
        """Process all recurring transactions due up to target_date idempotently."""
        due_items = await self.repo.get_due_transactions(target_date)
        processed_count = 0

        for item in due_items:
            # 1. Create transaction record
            txn = Transaction(
                user_id=item.user_id,
                account_id=item.account_id,
                category_id=item.category_id,
                amount=item.amount,
                type=item.type,
                merchant=item.merchant,
                note=f"[Recurring] {item.note or ''}".strip(),
                transaction_date=datetime.now(timezone.utc),
            )
            self.db.add(txn)

            # 2. Update account balance
            delta = -item.amount if item.type == "EXPENSE" else item.amount
            await self.account_repo.update_balance(item.account_id, delta)

            # 3. Advance next_occurrence
            if item.frequency == "DAILY":
                next_date = item.next_occurrence + timedelta(days=1)
            else:  # MONTHLY
                next_date = _get_next_monthly_date(item.next_occurrence)

            item.next_occurrence = next_date

            # Check if expired
            if item.end_date and item.next_occurrence > item.end_date:
                item.is_active = False

            # 4. Notify user
            notif = Notification(
                user_id=item.user_id,
                type="RECURRING_TRANSACTION",
                title="Recurring Transaction Processed",
                message=f"Processed recurring {item.type.lower()} of ₹{item.amount:.2f}",
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(notif)
            processed_count += 1

        if processed_count > 0:
            await self.db.commit()

        return processed_count
