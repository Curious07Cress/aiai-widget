"""
Health Check API Router

Provides endpoints for checking service health status.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from ..models.health import HealthCheckResponse, ServiceHealth
from ..services.health_aggregator import HealthAggregator

router = APIRouter(prefix="/api/health", tags=["health"])

# Service instance
health_aggregator = HealthAggregator()


@router.get(
    "/all",
    response_model=HealthCheckResponse,
    summary="Check all services",
    description="Returns health status of all monitored services.",
)
async def check_all_health() -> HealthCheckResponse:
    """
    Check health of all monitored services.

    Returns aggregated health status including:
    - AIAI API Server
    - MLI Service
    - MCP Proxy
    - Jaeger (for trace availability)
    """
    return await health_aggregator.check_all()


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
