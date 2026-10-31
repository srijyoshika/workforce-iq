"""
Tests for System Health, Database Connectivity, and Infrastructure APIs.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Verify root API endpoint returns valid service metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "WorkforceIQ"
    assert data["status"] == "online"
    assert "/docs" in data["documentation"]
    assert "/health" in data["health"]


@pytest.mark.asyncio
async def test_health_endpoint_contract(client: AsyncClient):
    """Verify health endpoint complies with enterprise response contract."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    # Core metadata
    assert data["status"] in ["healthy", "degraded"]
    assert data["app_name"] == "WorkforceIQ"
    assert data["version"] == "1.0.0"
    assert data["environment"] == "development"
    assert "timestamp" in data
    assert isinstance(data["uptime_seconds"], (int, float))

    # Database diagnostics
    db = data["database"]
    assert "connected" in db
    assert isinstance(db["connected"], bool)
    assert db["status"] in ["connected", "disconnected"]
    assert db["dialect"] in ["postgresql", "sqlite"]
    assert isinstance(db["latency_ms"], (int, float))

    # System diagnostics
    system = data["system"]
    assert "platform" in system
    assert "python_version" in system
    assert system["cpu_count"] >= 1

    # Services
    assert "api" in data["services"]
    assert data["services"]["api"] == "operational"


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    """Verify container liveness probe."""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    """Verify readiness probe."""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database_connected" in data


@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient):
    """Verify CORS preflight handling for frontend origin."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }
    response = await client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "GET" in response.headers.get("access-control-allow-methods", "")

