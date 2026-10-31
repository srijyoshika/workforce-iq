"""
WorkforceIQ Database Connection Manager.
Manages SQLAlchemy 2.0 async engines, sessions, and live connectivity diagnostics.
Supports primary PostgreSQL engine with seamless local SQLite fallback for dev agility.
"""

import logging
import time
from typing import AsyncGenerator, Tuple, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from app.config import get_settings

logger = logging.getLogger("workforce_iq.database")

settings = get_settings()

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_active_dialect: str = "postgresql"


async def init_db_engine() -> Tuple[AsyncEngine, str]:
    """
    Initialize the database engine.
    Attempts primary PostgreSQL connection first.
    If PostgreSQL fails and DB_FALLBACK_SQLITE is enabled, initializes SQLite fallback.
    """
    global _engine, _session_factory, _active_dialect

    pg_url = settings.postgres_async_url

    # Attempt PostgreSQL engine initialization
    try:
        logger.info(f"Attempting connection to PostgreSQL at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}...")
        test_engine = create_async_engine(
            pg_url,
            echo=settings.DEBUG,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )
        # Verify connection with quick probe
        async with test_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        _engine = test_engine
        _active_dialect = "postgresql"
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info("Successfully connected to primary PostgreSQL database.")
        return _engine, "postgresql"

    except Exception as pg_err:
        logger.warning(
            f"Could not connect to PostgreSQL at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}: {pg_err}"
        )
        if not settings.DB_FALLBACK_SQLITE:
            logger.error("DB_FALLBACK_SQLITE is False. Halting startup on PostgreSQL failure.")
            raise pg_err

        logger.info("Engaging SQLite development fallback engine...")
        sqlite_url = settings.sqlite_async_url
        _engine = create_async_engine(
            sqlite_url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
        )
        _active_dialect = "sqlite"
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info(f"SQLite fallback engine active at {settings.SQLITE_DB_PATH}")
        return _engine, "sqlite"


def get_engine() -> AsyncEngine:
    """Return the active SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        raise RuntimeError("Database engine has not been initialized. Call init_db_engine() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the active SQLAlchemy session factory."""
    global _session_factory
    if _session_factory is None:
        raise RuntimeError("Database session factory has not been initialized.")
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for injecting transactional async DB sessions."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def ping_database() -> dict:
    """
    Execute a live diagnostic ping ('SELECT 1') against the configured database.
    Measures latency and returns structured connectivity health metadata.
    """
    global _engine, _active_dialect

    start_time = time.perf_counter()
    try:
        if _engine is None:
            await init_db_engine()

        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "connected": True,
            "status": "connected",
            "dialect": _active_dialect,
            "database_name": settings.POSTGRES_DB if _active_dialect == "postgresql" else "workforce_iq_dev.db",
            "host": settings.POSTGRES_HOST if _active_dialect == "postgresql" else "localhost",
            "port": settings.POSTGRES_PORT if _active_dialect == "postgresql" else None,
            "latency_ms": latency,
            "error_detail": None,
        }
    except Exception as exc:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "connected": False,
            "status": "disconnected",
            "dialect": _active_dialect or "postgresql",
            "database_name": settings.POSTGRES_DB,
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "latency_ms": latency,
            "error_detail": str(exc),
        }


async def close_db_engine() -> None:
    """Dispose of the database engine and connection pool during application shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Database engine connection pool disposed cleanly.")

