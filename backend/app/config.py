"""
WorkforceIQ Application Configuration Module.
Centralizes all environment variable management with strong typing via Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Union
import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CANONICAL_SQLITE_PATH = str((_PROJECT_ROOT / "workforce_iq_dev.db").resolve()).replace("\\", "/")


class Settings(BaseSettings):
    """Core enterprise configuration settings for WorkforceIQ backend."""

    # Application Metadata
    APP_NAME: str = Field(default="WorkforceIQ", description="Application Name")
    APP_VERSION: str = Field(default="1.0.0", description="SemVer version")
    ENVIRONMENT: str = Field(default="development", description="Runtime environment: development | staging | production")
    DEBUG: bool = Field(default=True, description="Debug mode flag")
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix")
    HOST: str = Field(default="127.0.0.1", description="Bind host")
    PORT: int = Field(default=8000, description="Bind port")

    # Security
    SECRET_KEY: str = Field(
        default="workforceiq-super-secret-development-key-change-in-production-2026",
        description="Application secret key for JWT/session management",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=480, description="Access token expiration in minutes (8h)")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="Allowed hosts list")

    # CORS Settings
    BACKEND_CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
        description="Allowed CORS origins",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # PostgreSQL Database Settings
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="postgres", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="workforce_iq", description="PostgreSQL database name")

    # Direct database URL override (optional)
    DATABASE_URL: Union[str, None] = Field(default=None, description="Explicit database URL override")

    # Development Fallback Option
    DB_FALLBACK_SQLITE: bool = Field(
        default=True,
        description="Allow fallback to SQLite if PostgreSQL is unavailable during local development",
    )
    SQLITE_DB_PATH: str = Field(default=_CANONICAL_SQLITE_PATH, description="Path for SQLite fallback DB")

    # Database Pool Settings
    DB_POOL_SIZE: int = Field(default=10, description="SQLAlchemy connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="SQLAlchemy connection pool max overflow")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Connection timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=1800, description="Connection recycle interval in seconds")

    @property
    def postgres_async_url(self) -> str:
        """Construct the asyncpg PostgreSQL connection URL."""
        if self.DATABASE_URL:
            # Ensure asyncpg driver is specified if postgresql is provided
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sqlite_async_url(self) -> str:
        """Construct the aiosqlite connection URL for dev fallback."""
        clean_path = self.SQLITE_DB_PATH.replace("\\", "/")
        if not clean_path.startswith("/"):
            return f"sqlite+aiosqlite:///{clean_path}"
        return f"sqlite+aiosqlite://{clean_path}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()

