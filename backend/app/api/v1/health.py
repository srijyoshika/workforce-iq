"""
Health Check and Diagnostics API Endpoints.
Routes strictly orchestrate HTTP handling and delegate all business/diagnostic logic to HealthService.
"""

from fastapi import APIRouter, status
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["System Health & Diagnostics"])


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Detailed System and Database Health",
    description="Returns live system operational status, database connectivity, latency, uptime, and host specs.",
)
async def get_system_health() -> HealthResponse:
    """Detailed health check endpoint used by frontend monitoring and status dashboards."""
    return await HealthService.get_system_health()


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Container and orchestrator liveness check confirming the HTTP worker is responsive.",
)
def get_liveness():
    """Liveness probe."""
    return HealthService.get_liveness()


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Readiness check validating that essential dependencies (like database) are operational.",
)
async def get_readiness():
    """Readiness probe."""
    return await HealthService.get_readiness()

