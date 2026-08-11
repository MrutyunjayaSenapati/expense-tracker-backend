from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)

    async def list_notifications(
        self,
        user_id: uuid.UUID,
        is_read: Optional[bool] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Notification], int]:
        return await self.repo.list_by_user(
            user_id=user_id, is_read=is_read, page=page, limit=limit
        )

    async def mark_as_read(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
        await self.repo.mark_read(user_id=user_id, notification_id=notification_id)
        await self.db.commit()

    async def mark_all_as_read(self, user_id: uuid.UUID) -> None:
        await self.repo.mark_all_read(user_id=user_id)
        await self.db.commit()
