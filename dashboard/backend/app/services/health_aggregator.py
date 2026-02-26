"""
Health Aggregator Service

Aggregates health checks from all monitored services into a unified response.
"""

import asyncio
import logging
import time
from typing import Dict, Optional

import httpx

from ..config import get_settings
from ..models.health import ServiceHealth, ServiceStatus, HealthCheckResponse
from .mli_service import MLIService
from .supervision import derive_supervision_url

logger = logging.getLogger(__name__)


class HealthAggregator:
    """Aggregates health status from all monitored services."""

    def __init__(self):
        self.settings = get_settings()
        self.mli_service = MLIService()
        self.timeout = self.settings.health_check_timeout

    async def check_all(self) -> HealthCheckResponse:
        """
        Check health of all monitored services concurrently.

        Returns:
            HealthCheckResponse with status of all services
        """
        logger.info("Starting health check for all services")

        # Run all health checks concurrently
        results = await asyncio.gather(
            self._check_aiai_api(),
            self._check_mli(),
            self._check_mcp_proxy(),
            self._check_jaeger(),
            return_exceptions=True,
        )

        services: Dict[str, ServiceHealth] = {}

        # Process results
        check_names = ["aiai_api", "mli", "mcp_proxy", "jaeger"]
        for name, result in zip(check_names, results):
            if isinstance(result, Exception):
                logger.error(f"Health check failed for {name}: {result}")
                services[name] = ServiceHealth(
                    status=ServiceStatus.UNKNOWN,
                    message=f"Health check error: {str(result)}",
                )
            else:
                services[name] = result

        # Build response and calculate overall status
        response = HealthCheckResponse(
            overall=ServiceStatus.UNKNOWN,
            services=services,
        )
        response.overall = response.calculate_overall()

        logger.info(f"Health check complete. Overall status: {response.overall}")
        return response

    async def _check_aiai_api(self) -> ServiceHealth:
        """Check AIAI API Server health."""
        url = f"{self.settings.aiai_base_url}/health"
        start_time = time.time()

        try:
            # Don't follow redirects - 302 means server is up but requires auth
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = await client.get(url)
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json() if response.content else {}

                    # Ensure serviceInstanceId is present
                    if "serviceInstanceId" not in data:
                        supervision_info = derive_supervision_url(self.settings.aiai_base_url)
                        if supervision_info:
                            data["serviceInstanceId"] = supervision_info.service_instance_id

                    return ServiceHealth(
                        status=ServiceStatus.OK,
                        latency_ms=latency_ms,
                        details=data,
                    )
                elif response.status_code in (301, 302, 303, 307, 308):
                    # Redirect means server is reachable but requires authentication
                    # This is expected for services behind 3DPassport SSO
                    # Derive serviceInstanceId from URL pattern
                    details = {"auth_required": True}
                    supervision_info = derive_supervision_url(self.settings.aiai_base_url)
                    if supervision_info:
                        details["serviceInstanceId"] = supervision_info.service_instance_id

                    return ServiceHealth(
                        status=ServiceStatus.OK,
                        latency_ms=latency_ms,
                        message="Reachable (requires auth)",
                        details=details,
                    )
                else:
                    return ServiceHealth(
                        status=ServiceStatus.DEGRADED,
                        latency_ms=latency_ms,
                        message=f"HTTP {response.status_code}",
                    )

        except httpx.TimeoutException:
            latency_ms = int((time.time() - start_time) * 1000)
            return ServiceHealth(
                status=ServiceStatus.DEGRADED,
                latency_ms=latency_ms,
                message="Request timed out",
            )
        except httpx.ConnectError:
            return ServiceHealth(
                status=ServiceStatus.DOWN,
                message="Connection refused",
            )
        except Exception as e:
            logger.error(f"AIAI API health check error: {e}")
            return ServiceHealth(
                status=ServiceStatus.UNKNOWN,
                message=str(e),
            )

    async def _check_mli(self) -> ServiceHealth:
        """Check MLI service health."""
        return await self.mli_service.check_health()

    async def _check_mcp_proxy(self) -> ServiceHealth:
        """Check MCP Proxy health."""
        if not self.settings.mcp_proxy_url:
            return ServiceHealth(
                status=ServiceStatus.UNKNOWN,
                message="MCP Proxy URL not configured",
            )

        url = f"{self.settings.mcp_proxy_url}/health"
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json() if response.content else {}

                    # Check tool availability if provided
                    tools = data.get("tools", {})
                    available = tools.get("available", 0)
                    total = tools.get("total", 0)

                    if total > 0 and available < total:
                        return ServiceHealth(
                            status=ServiceStatus.DEGRADED,
                            latency_ms=latency_ms,
                            message=f"{available}/{total} tools available",
                            details=data,
                        )

                    return ServiceHealth(
                        status=ServiceStatus.OK,
                        latency_ms=latency_ms,
                        details=data,
                    )
                else:
                    return ServiceHealth(
                        status=ServiceStatus.DEGRADED,
                        latency_ms=latency_ms,
                        message=f"HTTP {response.status_code}",
                    )

        except httpx.TimeoutException:
            latency_ms = int((time.time() - start_time) * 1000)
            return ServiceHealth(
                status=ServiceStatus.DEGRADED,
                latency_ms=latency_ms,
                message="Request timed out",
            )
        except httpx.ConnectError:
            return ServiceHealth(
                status=ServiceStatus.DOWN,
                message="Connection refused",
            )
        except Exception as e:
            logger.error(f"MCP Proxy health check error: {e}")
            return ServiceHealth(
                status=ServiceStatus.UNKNOWN,
                message=str(e),
            )

    async def _check_jaeger(self) -> ServiceHealth:
        """Check Jaeger availability (for trace queries)."""
        url = f"{self.settings.jaeger_base_url}/api/services"
        start_time = time.time()

        try:
            # Don't follow redirects - 302 means server is up but requires auth
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = await client.get(url)
                latency_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    services = data.get("data", [])
                    return ServiceHealth(
                        status=ServiceStatus.OK,
                        latency_ms=latency_ms,
                        details={"services_count": len(services)},
                    )
                elif response.status_code in (301, 302, 303, 307, 308):
                    # Redirect means server is reachable but requires authentication
                    return ServiceHealth(
                        status=ServiceStatus.OK,
                        latency_ms=latency_ms,
                        message="Reachable (requires auth)",
                        details={"auth_required": True},
                    )
                else:
                    return ServiceHealth(
                        status=ServiceStatus.DEGRADED,
                        latency_ms=latency_ms,
                        message=f"HTTP {response.status_code}",
                    )

        except httpx.TimeoutException:
            latency_ms = int((time.time() - start_time) * 1000)
            return ServiceHealth(
                status=ServiceStatus.DEGRADED,
                latency_ms=latency_ms,
                message="Request timed out",
            )
        except httpx.ConnectError:
            return ServiceHealth(
                status=ServiceStatus.DOWN,
                message="Connection refused",
            )
        except Exception as e:
            logger.error(f"Jaeger health check error: {e}")
            return ServiceHealth(
                status=ServiceStatus.UNKNOWN,
                message=str(e),
            )

    async def check_single(self, service_name: str) -> Optional[ServiceHealth]:
        """
        Check health of a single service.

        Args:
            service_name: Name of the service to check

        Returns:
            ServiceHealth or None if service not found
        """
        check_methods = {
            "aiai_api": self._check_aiai_api,
            "mli": self._check_mli,
            "mcp_proxy": self._check_mcp_proxy,
            "jaeger": self._check_jaeger,
        }

        method = check_methods.get(service_name)
        if not method:
            return None

        try:
            return await method()
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return ServiceHealth(
                status=ServiceStatus.UNKNOWN,
                message=str(e),
            )
