import logging
from typing import Any, Dict, List, Optional
import uuid
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.push_token_repository import PushTokenRepository

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class PushNotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PushTokenRepository(db)

    async def send_to_user(
        self,
        user_id: uuid.UUID,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        sound: str = "default",
        channel_id: Optional[str] = None,
    ) -> bool:
        """Send push notification to all active devices of a single user."""
        tokens = await self.repo.get_active_tokens_for_user(user_id)
        if not tokens:
            logger.info(f"No active push tokens found for user_id={user_id}")
            return False

        messages = []
        for t in tokens:
            msg: Dict[str, Any] = {
                "to": t.push_token,
                "title": title,
                "body": body,
                "sound": sound,
            }
            if data:
                msg["data"] = data
            if channel_id:
                msg["channelId"] = channel_id
            messages.append(msg)

        return await self._dispatch_to_expo(messages)

    async def send_to_users(
        self,
        user_ids: List[uuid.UUID],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        sound: str = "default",
    ) -> bool:
        """Send push notification to active devices of multiple users."""
        tokens = await self.repo.get_active_tokens_for_users(user_ids)
        if not tokens:
            return False

        messages = []
        for t in tokens:
            msg: Dict[str, Any] = {
                "to": t.push_token,
                "title": title,
                "body": body,
                "sound": sound,
            }
            if data:
                msg["data"] = data
            messages.append(msg)

        return await self._dispatch_to_expo(messages)

    async def broadcast_to_all(
        self,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        sound: str = "default",
    ) -> bool:
        """Broadcast push notification to ALL active registered devices."""
        tokens = await self.repo.get_all_active_tokens()
        if not tokens:
            logger.info("No active push tokens found for broadcast.")
            return False

        messages = []
        for t in tokens:
            msg: Dict[str, Any] = {
                "to": t.push_token,
                "title": title,
                "body": body,
                "sound": sound,
            }
            if data:
                msg["data"] = data
            messages.append(msg)

        return await self._dispatch_to_expo(messages)

    async def _dispatch_to_expo(self, messages: List[Dict[str, Any]]) -> bool:
        if not messages:
            return False

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(EXPO_PUSH_URL, json=messages, headers=headers)
                response_data = response.json()

                if response.status_code == 200 and "data" in response_data:
                    tickets = response_data["data"]
                    for idx, ticket in enumerate(tickets):
                        if ticket.get("status") == "error":
                            error_code = ticket.get("details", {}).get("error")
                            push_token = messages[idx].get("to")
                            if error_code == "DeviceNotRegistered" and push_token:
                                logger.warning(f"Push token {push_token} expired/unregistered. Deactivating...")
                                await self.repo.deactivate_token(push_token)
                                await self.db.commit()
                    return True
                else:
                    logger.error(f"Expo push dispatch failed: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Exception during Expo push notification dispatch: {str(e)}")
            return False
