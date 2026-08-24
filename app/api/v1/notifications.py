import math
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
)
from app.schemas.push_token import (
    BroadcastNotificationRequest,
    PushTokenRegister,
    PushTokenResponse,
    PushTokenUnregister,
)
from app.repositories.push_token_repository import PushTokenRepository
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List in-app notifications",
)
async def list_notifications(
    is_read: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    items, total = await service.list_notifications(
        user_id=current_user.id, is_read=is_read, page=page, limit=limit
    )
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
    )


@router.post(
    "/push-token",
    response_model=PushTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Register or update Expo push token for current user",
)
async def register_push_token(
    payload: PushTokenRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = PushTokenRepository(db)
    token_obj = await repo.upsert_token(
        user_id=current_user.id,
        push_token=payload.push_token,
        device_type=payload.device_type or "android",
    )
    await db.commit()
    return PushTokenResponse.model_validate(token_obj)


@router.delete(
    "/push-token",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate Expo push token for current user",
)
async def unregister_push_token(
    payload: PushTokenUnregister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = PushTokenRepository(db)
    await repo.deactivate_token(push_token=payload.push_token)
    await db.commit()


@router.post(
    "/broadcast",
    status_code=status.HTTP_200_OK,
    summary="Broadcast push notification to ALL active users",
)
async def broadcast_push_notification(
    payload: BroadcastNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.push_notification_service import PushNotificationService
    push_service = PushNotificationService(db)
    success = await push_service.broadcast_to_all(
        title=payload.title,
        body=payload.body,
        data=payload.data,
    )
    return {"status": "ok", "sent": success}


@router.patch(
    "/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark all notifications as read",
)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    await service.mark_all_as_read(current_user.id)


@router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark single notification as read",
)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    await service.mark_as_read(current_user.id, notification_id)
