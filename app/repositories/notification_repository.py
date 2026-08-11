from typing import List, Optional, Tuple
import uuid
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: AsyncSession):
        super().__init__(Notification, db)

    async def get_by_user_and_id(
        self, user_id: uuid.UUID, notification_id: uuid.UUID
    ) -> Optional[Notification]:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        is_read: Optional[bool] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[Notification], int]:
        limit = min(max(1, limit), 100)
        offset = (max(1, page) - 1) * limit

        query = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)

        count_subquery = query.with_only_columns(func.count(Notification.id)).order_by(None)
        total_result = await self.db.execute(count_subquery)
        total = total_result.scalar_one()

        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def mark_read(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .values(is_read=True)
        )
        await self.db.flush()

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id)
            .values(is_read=True)
        )
        await self.db.flush()
