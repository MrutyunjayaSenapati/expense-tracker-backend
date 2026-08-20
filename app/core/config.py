from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Expense Tracker API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./expense_tracker.db"

    # Security & Auth
    JWT_SECRET_KEY: str = "insecure_dev_secret_key_please_change_in_production_1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    GOOGLE_CLIENT_ID: str = "1034897317741-hacdelsguobptpkjmp3fujjk2k2guhfu.apps.googleusercontent.com"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:19006",
        "http://127.0.0.1:8000",
        "*",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
