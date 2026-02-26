"""
Health Check Data Models

Defines the structure for service health responses.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Status values for service health."""
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class ServiceHealth(BaseModel):
    """Health status for a single service."""
    status: ServiceStatus = Field(description="Current service status")
    latency_ms: Optional[int] = Field(None, description="Response latency in milliseconds")
    message: Optional[str] = Field(None, description="Additional status message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    last_checked: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Aggregated health check response for all services."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall: ServiceStatus = Field(description="Overall system status")
    services: Dict[str, ServiceHealth] = Field(
        description="Health status for each monitored service"
    )

    def calculate_overall(self) -> ServiceStatus:
        """Calculate overall status based on individual services."""
        statuses = [s.status for s in self.services.values()]

        if all(s == ServiceStatus.OK for s in statuses):
            return ServiceStatus.OK
        if any(s == ServiceStatus.DOWN for s in statuses):
            return ServiceStatus.DOWN
        if any(s == ServiceStatus.DEGRADED for s in statuses):
            return ServiceStatus.DEGRADED
        return ServiceStatus.UNKNOWN
