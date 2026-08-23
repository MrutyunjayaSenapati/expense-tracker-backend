from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.constants import DEFAULT_EXPENSE_CATEGORIES, DEFAULT_INCOME_CATEGORIES, SYSTEM_ACHIEVEMENTS
from app.core.exceptions import AuthenticationError, ConflictError, ResourceNotFoundError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.db.models.category import Category
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.gamification_repository import GamificationRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
import httpx
from app.schemas.auth import (
    GoogleLoginRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.utils.datetime_utils import ensure_utc


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)
        self.category_repo = CategoryRepository(db)
        self.gamification_repo = GamificationRepository(db)

    async def register(self, payload: UserRegister) -> User:
        # Check duplicate
        existing = await self.user_repo.get_by_email(payload.email)
        if existing:
            raise ConflictError(
                message="User with this email already exists",
                code="USER_ALREADY_EXISTS",
            )

        # Create user
        user = User(
            name=payload.name.strip(),
            email=payload.email.strip().lower(),
            password_hash=get_password_hash(payload.password),
            is_active=True,
        )
        user = await self.user_repo.create(user)

        # Create default categories for user
        default_categories = []
        for cat in DEFAULT_EXPENSE_CATEGORIES:
            default_categories.append(
                Category(
                    user_id=user.id,
                    name=cat["name"],
                    type="EXPENSE",
                    icon=cat.get("icon"),
                    color=cat.get("color"),
                    is_active=True,
                )
            )
        for cat in DEFAULT_INCOME_CATEGORIES:
            default_categories.append(
                Category(
                    user_id=user.id,
                    name=cat["name"],
                    type="INCOME",
                    icon=cat.get("icon"),
                    color=cat.get("color"),
                    is_active=True,
                )
            )
        await self.category_repo.create_bulk(default_categories)

        # Seed global achievements if needed & init streak
        await self.gamification_repo.seed_system_achievements(SYSTEM_ACHIEVEMENTS)
        await self.gamification_repo.get_or_create_streak(user.id)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, payload: UserLogin) -> TokenResponse:
        user = await self.user_repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise AuthenticationError(
                message="Invalid email or password",
                code="AUTH_INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise AuthenticationError(
                message="Account has been deactivated",
                code="AUTH_INACTIVE_USER",
            )

        # Create access token
        access_token = create_access_token(subject=str(user.id))

        # Create and store refresh token
        raw_refresh_token = generate_refresh_token()
        hashed_refresh = hash_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=hashed_refresh,
            expires_at=expires_at,
        )
        await self.token_repo.create(refresh_token_record)
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    async def refresh_token(self, raw_refresh_token: str) -> RefreshTokenResponse:
        hashed_token = hash_token(raw_refresh_token)
        token_record = await self.token_repo.get_by_token_hash(hashed_token)

        if not token_record:
            raise AuthenticationError(
                message="Invalid refresh token",
                code="AUTH_INVALID_REFRESH_TOKEN",
            )

        if token_record.revoked_at is not None:
            raise AuthenticationError(
                message="Refresh token has been revoked",
                code="AUTH_REFRESH_TOKEN_REVOKED",
            )

        now = datetime.now(timezone.utc)
        expires_at = ensure_utc(token_record.expires_at)
        if expires_at <= now:
            raise AuthenticationError(
                message="Refresh token has expired",
                code="AUTH_REFRESH_TOKEN_EXPIRED",
            )

        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise AuthenticationError(
                message="User is inactive or not found",
                code="AUTH_INACTIVE_USER",
            )

        token_record.last_used_at = now
        await self.db.commit()

        access_token = create_access_token(subject=str(user.id))
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def google_login(self, payload: GoogleLoginRequest) -> TokenResponse:
        email = None
        name = None
        avatar_url = None
        google_id = None

        if not payload.id_token and not payload.access_token and not payload.code:
            raise AuthenticationError(
                message="Google token or authorization code is required",
                code="AUTH_GOOGLE_TOKEN_REQUIRED",
            )

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. If auth code is provided, exchange it for tokens
            id_token = payload.id_token
            access_token = payload.access_token

            if payload.code:
                try:
                    token_resp = await client.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "client_id": settings.GOOGLE_CLIENT_ID or "1034897317741-hacdelsguobptpkjmp3fujjk2k2guhfu.apps.googleusercontent.com",
                            "code": payload.code,
                            "grant_type": "authorization_code",
                            "redirect_uri": payload.redirect_uri or "https://expense-tracker-backend-9bdd.onrender.com/api/v1/auth/google/callback",
                        },
                    )
                    if token_resp.status_code == 200:
                        tdata = token_resp.json()
                        id_token = id_token or tdata.get("id_token")
                        access_token = access_token or tdata.get("access_token")
                    else:
                        print(f"⚠️ [Google Token Exchange Failed] Status: {token_resp.status_code}, Body: {token_resp.text}")
                except Exception as ex:
                    print(f"⚠️ [Google Token Exchange Exception]: {ex}")

            # 2. Try verifying with Google ID token
            if id_token:
                try:
                    resp = await client.get(
                        f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
                    )
                    if resp.status_code == 200:
                        info = resp.json()
                        email = info.get("email")
                        name = info.get("name") or info.get("given_name")
                        avatar_url = info.get("picture")
                        google_id = info.get("sub")
                except Exception:
                    pass

            # 3. Try verifying with Google Access token if needed
            if not email and access_token:
                try:
                    resp = await client.get(
                        "https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    if resp.status_code == 200:
                        info = resp.json()
                        email = info.get("email")
                        name = info.get("name") or info.get("given_name")
                        avatar_url = info.get("picture")
                        google_id = info.get("sub")
                except Exception:
                    pass

        if not email:
            raise AuthenticationError(
                message="Failed to verify Google credentials",
                code="AUTH_INVALID_GOOGLE_TOKEN",
            )

        email = email.strip().lower()
        if not name:
            name = email.split("@")[0].capitalize()

        # Find or create user
        user = await self.user_repo.get_by_email(email)
        if user:
            if not user.is_active:
                raise AuthenticationError(
                    message="Account has been deactivated",
                    code="AUTH_INACTIVE_USER",
                )
            # Update user profile with Google metadata if missing
            changed = False
            if google_id and not user.google_id:
                user.google_id = google_id
                changed = True
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
                changed = True
            if changed:
                await self.db.commit()
                await self.db.refresh(user)
        else:
            # Create new user for first time Google sign-in
            user = User(
                name=name.strip(),
                email=email,
                password_hash=None,
                avatar_url=avatar_url,
                auth_provider="google",
                google_id=google_id,
                is_active=True,
            )
            user = await self.user_repo.create(user)

            # Create default categories for user
            default_categories = []
            for cat in DEFAULT_EXPENSE_CATEGORIES:
                default_categories.append(
                    Category(
                        user_id=user.id,
                        name=cat["name"],
                        type="EXPENSE",
                        icon=cat.get("icon"),
                        color=cat.get("color"),
                        is_active=True,
                    )
                )
            for cat in DEFAULT_INCOME_CATEGORIES:
                default_categories.append(
                    Category(
                        user_id=user.id,
                        name=cat["name"],
                        type="INCOME",
                        icon=cat.get("icon"),
                        color=cat.get("color"),
                        is_active=True,
                    )
                )
            await self.category_repo.create_bulk(default_categories)

            # Seed global achievements if needed & init streak
            await self.gamification_repo.seed_system_achievements(SYSTEM_ACHIEVEMENTS)
            await self.gamification_repo.get_or_create_streak(user.id)

            await self.db.commit()
            await self.db.refresh(user)

        # Create access and refresh tokens
        access_token = create_access_token(subject=str(user.id))
        raw_refresh_token = generate_refresh_token()
        hashed_refresh = hash_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=hashed_refresh,
            expires_at=expires_at,
        )
        await self.token_repo.create(refresh_token_record)
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    async def logout(self, raw_refresh_token: str) -> None:
        if raw_refresh_token:
            hashed = hash_token(raw_refresh_token)
            await self.token_repo.revoke_token(hashed)
            await self.db.commit()

    async def delete_account(self, user_id: uuid.UUID) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User not found", "USER_NOT_FOUND")

        await self.token_repo.revoke_all_user_tokens(user_id)
        await self.user_repo.delete(user)
        await self.db.commit()
