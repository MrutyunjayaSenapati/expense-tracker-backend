import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AccountSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str


class TransactionBase(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0.00"), max_digits=14, decimal_places=2)
    type: str = Field(..., pattern="^(EXPENSE|INCOME)$")
    merchant: Optional[str] = Field(None, max_length=200)
    note: Optional[str] = None
    transaction_date: Optional[datetime] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    account_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    amount: Optional[Decimal] = Field(None, gt=Decimal("0.00"), max_digits=14, decimal_places=2)
    type: Optional[str] = Field(None, pattern="^(EXPENSE|INCOME)$")
    merchant: Optional[str] = Field(None, max_length=200)
    note: Optional[str] = None
    transaction_date: Optional[datetime] = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account: AccountSummary
    category: CategorySummary
    amount: Decimal
    type: str
    merchant: Optional[str] = None
    note: Optional[str] = None
    transaction_date: datetime
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    page: int
    limit: int
    total: int
    total_pages: int
