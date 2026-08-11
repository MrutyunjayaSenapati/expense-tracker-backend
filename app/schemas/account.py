import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(CASH|BANK|UPI_WALLET|CREDIT_CARD|DEBIT_CARD|OTHER)$")


class AccountCreate(AccountBase):
    starting_balance: Decimal = Field(default=Decimal("0.00"), ge=Decimal("-1000000000.00"))


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, pattern="^(CASH|BANK|UPI_WALLET|CREDIT_CARD|DEBIT_CARD|OTHER)$")


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str
    balance: Decimal
    currency: str = "INR"
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AccountListResponse(BaseModel):
    items: List[AccountResponse]
