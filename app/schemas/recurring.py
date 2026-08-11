import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.transaction import AccountSummary, CategorySummary


class RecurringTransactionCreate(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID
    type: str = Field(..., pattern="^(EXPENSE|INCOME)$")
    amount: Decimal = Field(..., gt=Decimal("0.00"), max_digits=14, decimal_places=2)
    merchant: Optional[str] = Field(None, max_length=200)
    note: Optional[str] = None
    frequency: str = Field(..., pattern="^(DAILY|MONTHLY)$")
    start_date: date
    end_date: Optional[date] = None


class RecurringTransactionUpdate(BaseModel):
    account_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    type: Optional[str] = Field(None, pattern="^(EXPENSE|INCOME)$")
    amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"), max_digits=14, decimal_places=2)
    merchant: Optional[str] = Field(None, max_length=200)
    note: Optional[str] = None
    frequency: Optional[str] = Field(None, pattern="^(DAILY|MONTHLY)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class RecurringTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account: AccountSummary
    category: CategorySummary
    type: str
    amount: Decimal
    merchant: Optional[str] = None
    note: Optional[str] = None
    frequency: str
    start_date: date
    end_date: Optional[date] = None
    next_occurrence: date
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RecurringTransactionListResponse(BaseModel):
    items: List[RecurringTransactionResponse]
