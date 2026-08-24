from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class PushTokenRegister(BaseModel):
    push_token: str = Field(..., min_length=1, max_length=255, description="Expo push token (ExponentPushToken[...])")
    device_type: Optional[str] = Field("android", max_length=20, description="Device OS (android, ios, web)")


class PushTokenUnregister(BaseModel):
    push_token: str = Field(..., min_length=1, max_length=255, description="Expo push token to deactivate")


class PushTokenResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    push_token: str
    device_type: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BroadcastNotificationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, example="🎉 50% Off Today Only!")
    body: str = Field(..., min_length=1, max_length=1000, example="Upgrade to Premium and get 50% discount.")
    data: Optional[dict] = Field(None, example={"screen": "/(tabs)/settings", "promo": "HALF50"})

