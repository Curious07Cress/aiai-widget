"""
Health Check API Router

Provides endpoints for checking service health status.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from ..models.health import HealthCheckResponse, ServiceHealth, ServiceStatus
from ..services.health_aggregator import HealthAggregator

router = APIRouter(prefix="/api/health", tags=["health"])

# Service instance
health_aggregator = HealthAggregator()


def _map_status_to_frontend(status) -> str:
    """Map backend status enum to frontend-expected strings."""
    mapping = {
        "ok": "healthy",
        "degraded": "degraded",
        "down": "unhealthy",
        "unknown": "unknown"
    }
    status_str = str(status).lower() if hasattr(status, 'value') else str(status).lower()
    return mapping.get(status_str, "unknown")


@router.get(
    "/all",
    summary="Check all services",
    description="Returns health status of all monitored services in frontend-compatible format.",
)
async def check_all_health():
    """
    Check health of all monitored services.

    Returns aggregated health status including:
    - AIAI API Server
    - MLI Service
    - MCP Proxy
    - Jaeger (for trace availability)

    Response format is transformed to match frontend expectations:
    - Keys: "aiai" instead of "aiai_api"
    - Fields: "response_time_ms" instead of "latency_ms"
    - Status: "healthy/unhealthy/degraded/unknown" instead of "ok/down/..."
    """
    result = await health_aggregator.check_all()

    # Get AIAI service or create unknown fallback
    aiai_service = result.services.get("aiai_api")
    if not aiai_service:
        aiai_service = ServiceHealth(status=ServiceStatus.UNKNOWN)

    # Transform to frontend-expected format
    return {
        "overall": _map_status_to_frontend(result.overall),
        "timestamp": result.timestamp.isoformat(),
        "services": {
            "aiai": {
                "status": _map_status_to_frontend(aiai_service.status),
                "response_time_ms": aiai_service.latency_ms,
                "endpoint": str(health_aggregator.settings.aiai_base_url),
                "last_check": aiai_service.last_checked.isoformat(),
                "details": aiai_service.details or {}
            }
        }
    }


@router.get(
    "/{service_name}",
    response_model=ServiceHealth,
    summary="Check single service",
    description="Returns health status of a specific service.",
)
async def check_service_health(service_name: str) -> ServiceHealth:
    """
    Check health of a specific service.

    Args:
        service_name: One of: aiai_api, mli, mcp_proxy, jaeger

    Returns:
        Health status for the specified service
    """
    result = await health_aggregator.check_single(service_name)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service: {service_name}. "
                   f"Valid services: aiai_api, mli, mcp_proxy, jaeger"
        )

    return result


@router.get(
    "/",
    summary="Backend health",
    description="Simple health check for the dashboard backend itself.",
)
async def backend_health():
    """Health check for the dashboard backend service."""
    return {"status": "ok", "service": "dashboard-backend"}
