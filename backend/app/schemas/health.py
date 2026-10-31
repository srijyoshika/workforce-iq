"""
Pydantic Schemas for System and Database Health Monitoring.
"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class DatabaseHealthStatus(BaseModel):
    """Detailed database connectivity and dialect metadata."""
    connected: bool = Field(description="True if database responds to query")
    status: str = Field(description="connected | degraded | disconnected")
    dialect: str = Field(description="postgresql | sqlite")
    database_name: str = Field(description="Target database name")
    host: str = Field(description="Host address of database server")
    port: Optional[int] = Field(default=None, description="Port of database server")
    latency_ms: Optional[float] = Field(default=None, description="Roundtrip query latency in milliseconds")
    error_detail: Optional[str] = Field(default=None, description="Error message if disconnected")


class SystemInfo(BaseModel):
    """Host environment diagnostics."""
    platform: str = Field(description="Operating system and release")
    python_version: str = Field(description="Runtime Python version")
    cpu_count: int = Field(description="Available logical CPU cores")


class HealthResponse(BaseModel):
    """Complete enterprise health-check payload."""
    status: str = Field(description="Overall system health status: healthy | degraded | unhealthy")
    app_name: str = Field(description="Name of the application")
    version: str = Field(description="SemVer release version")
    environment: str = Field(description="Runtime environment")
    timestamp: datetime = Field(description="Current server UTC timestamp")
    uptime_seconds: float = Field(description="Server uptime in seconds")
    database: DatabaseHealthStatus = Field(description="Database connectivity health")
    system: SystemInfo = Field(description="Host system specifications")
    services: Dict[str, str] = Field(description="Status of individual subservices")

