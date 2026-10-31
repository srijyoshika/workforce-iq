"""
Enterprise Health Check Service for WorkforceIQ.
Encapsulates business and diagnostic logic for system observability.
"""

from datetime import datetime, timezone
import os
import platform
import time
from app.config import get_settings
from app.database import ping_database
from app.schemas.health import HealthResponse, DatabaseHealthStatus, SystemInfo

# Global server start time recorded at import
_SERVER_START_TIME = time.time()


class HealthService:
    """Service providing comprehensive health, liveness, and readiness metrics."""

    @classmethod
    async def get_system_health(cls) -> HealthResponse:
        """
        Gathers live database status, uptime, system metrics, and service availability.
        Calculates overall operational state.
        """
        settings = get_settings()
        now = datetime.now(timezone.utc)
        uptime = round(time.time() - _SERVER_START_TIME, 2)

        # Probe database
        db_ping = await ping_database()
        db_status = DatabaseHealthStatus(
            connected=db_ping["connected"],
            status=db_ping["status"],
            dialect=db_ping["dialect"],
            database_name=db_ping["database_name"],
            host=db_ping["host"],
            port=db_ping["port"],
            latency_ms=db_ping["latency_ms"],
            error_detail=db_ping["error_detail"],
        )

        # Host system diagnostics
        system_info = SystemInfo(
            platform=f"{platform.system()} {platform.release()}",
            python_version=platform.python_version(),
            cpu_count=os.cpu_count() or 1,
        )

        # Overall health evaluation
        overall_status = "healthy" if db_status.connected else "degraded"

        return HealthResponse(
            status=overall_status,
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
            timestamp=now,
            uptime_seconds=uptime,
            database=db_status,
            system=system_info,
            services={
                "api": "operational",
                "database": "operational" if db_status.connected else "unavailable",
                "auth": "ready",
                "analytics_engine": "ready",
            },
        )

    @classmethod
    def get_liveness(cls) -> dict:
        """Basic Kubernetes/Container liveness probe."""
        return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}

    @classmethod
    async def get_readiness(cls) -> dict:
        """Readiness probe checking database availability."""
        db_ping = await ping_database()
        is_ready = db_ping["connected"]
        return {
            "status": "ready" if is_ready else "not_ready",
            "database_connected": is_ready,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

