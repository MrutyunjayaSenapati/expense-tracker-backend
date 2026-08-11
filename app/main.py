from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.constants import SYSTEM_ACHIEVEMENTS
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.db.base import Base
from app.db.session import async_session_maker, engine
from app.repositories.gamification_repository import GamificationRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if running on SQLite / local dev
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed system achievements
    async with async_session_maker() as session:
        gamification_repo = GamificationRepository(session)
        await gamification_repo.seed_system_achievements(SYSTEM_ACHIEVEMENTS)
        await session.commit()

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


app.include_router(api_v1_router, prefix=settings.API_V1_STR)
