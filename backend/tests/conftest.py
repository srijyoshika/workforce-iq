"""
Pytest Fixtures and Asynchronous Test Client Setup.
Uses HTTPX AsyncClient with ASGITransport for testing FastAPI endpoints,
and initializes test database schema for model integration testing.
"""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_application
from app.database import init_db_engine, close_db_engine, get_engine
import app.models
from app.models.base import Base


@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_test_database():
    """Ensure database engine and full schema tables are created for tests."""
    engine, dialect = await init_db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await close_db_engine()


@pytest_asyncio.fixture(scope="session")
async def app_instance(initialize_test_database):
    """Create and initialize the application instance for test session."""
    app = create_application()
    return app


@pytest_asyncio.fixture(scope="function")
async def client(app_instance):
    """Provide an HTTPX AsyncClient bound to the FastAPI application."""
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
