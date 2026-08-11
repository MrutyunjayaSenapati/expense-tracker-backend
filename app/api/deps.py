import uuid
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

security = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not auth or not auth.credentials:
        raise AuthenticationError("Missing or invalid authorization header", "AUTH_UNAUTHORIZED")

    payload = decode_token(auth.credentials)
    if not payload:
        raise AuthenticationError("Invalid or expired access token", "AUTH_INVALID_TOKEN")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Malformed token", "AUTH_INVALID_TOKEN")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Invalid user ID in token", "AUTH_INVALID_TOKEN")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise AuthenticationError("User account not found or inactive", "AUTH_INACTIVE_USER")

    return user
