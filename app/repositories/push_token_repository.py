from typing import List, Optional
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.push_token import UserPushToken
from app.repositories.base import BaseRepository


class PushTokenRepository(BaseRepository[UserPushToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(UserPushToken, db)

    async def upsert_token(
        self, user_id: uuid.UUID, push_token: str, device_type: str = "android"
    ) -> UserPushToken:
        # Check if token already exists
        result = await self.db.execute(
            select(UserPushToken).where(UserPushToken.push_token == push_token)
        )
        existing = result.scalars().first()

        if existing:
            existing.user_id = user_id
            existing.device_type = device_type
            existing.is_active = True
            await self.db.flush()
            return existing

        token_obj = UserPushToken(
            user_id=user_id,
            push_token=push_token,
            device_type=device_type,
            is_active=True,
        )
        self.db.add(token_obj)
        await self.db.flush()
        return token_obj

    async def deactivate_token(self, push_token: str) -> None:
        await self.db.execute(
            update(UserPushToken)
            .where(UserPushToken.push_token == push_token)
            .values(is_active=False)
        )
        await self.db.flush()

    async def get_active_tokens_for_user(self, user_id: uuid.UUID) -> List[UserPushToken]:
        result = await self.db.execute(
            select(UserPushToken).where(
                UserPushToken.user_id == user_id,
                UserPushToken.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def get_active_tokens_for_users(self, user_ids: List[uuid.UUID]) -> List[UserPushToken]:
        if not user_ids:
            return []
        result = await self.db.execute(
            select(UserPushToken).where(
                UserPushToken.user_id.in_(user_ids),
                UserPushToken.is_active == True,
            )
        )
        return list(result.scalars().all())
