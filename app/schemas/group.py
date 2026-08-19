import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GroupMemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email_or_phone: Optional[str] = Field(None, max_length=100)


class GroupMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    name: str
    email_or_phone: Optional[str] = None
    role: str
    joined_at: datetime


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    category: str = Field(default="HOME", max_length=50)  # HOME, TRIP, COUPLE, OTHER
    currency: str = Field(default="INR", max_length=10)
    members: Optional[List[GroupMemberCreate]] = []


class GroupJoinRequest(BaseModel):
    invite_code: str = Field(..., min_length=4, max_length=12)


class GroupExpenseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: Decimal = Field(..., gt=Decimal("0.00"), max_digits=14, decimal_places=2)
    paid_by_member_id: uuid.UUID
    split_member_ids: Optional[List[uuid.UUID]] = None  # None = split equally among all members
    date: Optional[datetime] = None
    note: Optional[str] = None


class GroupExpenseSplitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    member_id: uuid.UUID
    amount_owed: Decimal


class GroupExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    paid_by_user_id: Optional[uuid.UUID] = None
    payer_name: str
    title: str
    amount: Decimal
    date: datetime
    note: Optional[str] = None
    created_at: datetime
    splits: List[GroupExpenseSplitResponse] = []


class SimplifiedDebt(BaseModel):
    from_member_id: uuid.UUID
    from_member_name: str
    from_user_id: Optional[uuid.UUID] = None
    to_member_id: uuid.UUID
    to_member_name: str
    to_user_id: Optional[uuid.UUID] = None
    to_user_phone_or_upi: Optional[str] = None
    amount: Decimal


class MemberBalanceSummary(BaseModel):
    member_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    name: str
    paid_total: Decimal
    share_total: Decimal
    net_balance: Decimal  # Positive = gets back, Negative = owes


class GroupSettlementCreate(BaseModel):
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0.00"), max_digits=14, decimal_places=2)


class GroupSettlementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    amount: Decimal
    settled_at: datetime


class GroupDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str
    invite_code: str
    currency: str
    creator_id: uuid.UUID
    created_at: datetime
    members: List[GroupMemberResponse] = []
    expenses: List[GroupExpenseResponse] = []
    settlements: List[GroupSettlementResponse] = []
    balances: List[MemberBalanceSummary] = []
    simplified_debts: List[SimplifiedDebt] = []
    your_net_balance: Decimal = Decimal("0.00")


class GroupListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str
    invite_code: str
    currency: str
    creator_id: uuid.UUID
    member_count: int
    your_net_balance: Decimal
    created_at: datetime
