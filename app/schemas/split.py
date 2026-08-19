import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ParticipantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email_or_phone: Optional[str] = Field(None, max_length=100)
    amount_owed: Decimal = Field(..., gt=Decimal("0.00"), max_digits=14, decimal_places=2)


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    name: str
    phone_or_upi: Optional[str] = None
    amount_owed: Decimal
    is_paid: bool
    paid_at: Optional[datetime] = None


class UserMiniSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: Optional[str] = None


class SplitBillCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    total_amount: Decimal = Field(..., gt=Decimal("0.00"), max_digits=14, decimal_places=2)
    your_share: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), max_digits=14, decimal_places=2)
    paid_by: str = Field(default="YOU", pattern="^(YOU|FRIEND)$")
    payer_name: Optional[str] = Field(None, max_length=100)
    participants: List[ParticipantCreate] = Field(..., min_length=1)
    note: Optional[str] = None
    date: Optional[datetime] = None


class SplitBillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    total_amount: Decimal
    your_share: Decimal
    paid_by_user_id: uuid.UUID
    creator_id: uuid.UUID
    is_settled: bool
    note: Optional[str] = None
    date: datetime
    created_at: datetime
    updated_at: datetime
    paid_by: Optional[UserMiniSummary] = None
    creator: Optional[UserMiniSummary] = None
    participants: List[ParticipantResponse] = []


class SplitSummaryResponse(BaseModel):
    total_owed_to_you: Decimal
    total_you_owe: Decimal
    pending_bills_count: int
    settled_bills_count: int


class SplitSettleRequest(BaseModel):
    is_paid: bool = True
