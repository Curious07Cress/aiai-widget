"""
MLI Service

Integrates with the Dassault Systemes MLI (Machine Learning Interface) service
to check health status.
"""

import logging
import time
from typing import Optional, Dict, Any

import httpx

from ..config import get_settings
from ..models.health import ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)


class MLIService:
    """Service for checking MLI health status."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.mli_base_url
        self.timeout = self.settings.health_check_timeout

    async def check_health(self) -> ServiceHealth:
        """
        Check MLI service health.

        The MLI health check requires:
        1. Get auth token from /auth/token
        2. Call /health with Bearer token

        If we get a 302 redirect, the server is reachable but requires
        authentication via 3DPassport SSO.

        Returns:
            ServiceHealth with current status
        """
        start_time = time.time()

        try:
            # Step 1: Try to get auth token (or check reachability)
            token, auth_required = await self._get_auth_token()

            latency_ms = int((time.time() - start_time) * 1000)

            # If we got a redirect, server is reachable but requires auth
            if auth_required:
                return ServiceHealth(
                    status=ServiceStatus.OK,
                    latency_ms=latency_ms,
                    message="Reachable (requires auth)",
                    details={"auth_required": True},
                )

            if not token:
                return ServiceHealth(
                    status=ServiceStatus.DOWN,
                    message="Failed to obtain auth token",
                )

            # Step 2: Check health endpoint
            health_data = await self._call_health_endpoint(token)

            latency_ms = int((time.time() - start_time) * 1000)

            if health_data:
                return ServiceHealth(
                    status=ServiceStatus.OK,
                    latency_ms=latency_ms,
                    details=health_data,
                )
            else:
                return ServiceHealth(
                    status=ServiceStatus.DEGRADED,
                    latency_ms=latency_ms,
                    message="Health endpoint returned unexpected response",
                )

        except httpx.TimeoutException:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"MLI health check timed out after {latency_ms}ms")
            return ServiceHealth(
                status=ServiceStatus.DEGRADED,
                latency_ms=latency_ms,
                message="Health check timed out",
            )
        except httpx.ConnectError as e:
            logger.error(f"MLI connection error: {e}")
            return ServiceHealth(
                status=ServiceStatus.DOWN,
                message=f"Connection failed: {str(e)}",
            )
        except Exception as e:
            logger.error(f"MLI health check error: {e}")
            return ServiceHealth(
                status=ServiceStatus.UNKNOWN,
                message=f"Health check failed: {str(e)}",
            )

    async def _get_auth_token(self) -> tuple[Optional[str], bool]:
        """
        Get authentication token from MLI.

        Returns:
            Tuple of (token, auth_required):
            - token: Bearer token string or None if failed
            - auth_required: True if server returned 302 (requires SSO auth)
        """
        url = f"{self.base_url}/auth/token"
        logger.debug(f"Getting MLI auth token from {url}")

        try:
            # Don't follow redirects - 302 means requires SSO auth
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = await client.get(
                    url,
                    headers={"accept": "application/json"},
                )

                # Check for redirect (SSO auth required)
                if response.status_code in (301, 302, 303, 307, 308):
                    logger.debug("MLI requires SSO authentication (redirect)")
                    return None, True

                response.raise_for_status()
                data = response.json()

                # Token might be in different fields depending on API version
                token = (
                    data.get("access_token") or
                    data.get("token") or
                    data.get("data", {}).get("token")
                )

                if token:
                    logger.debug("Successfully obtained MLI auth token")
                    return token, False

                # If response is just the token string
                if isinstance(data, str):
                    return data, False

                logger.warning(f"Unexpected token response format: {data}")
                return None, False

        except Exception as e:
            logger.error(f"Failed to get MLI auth token: {e}")
            return None, False

    async def _call_health_endpoint(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Call the MLI health endpoint with authentication.

        Args:
            token: Bearer token

        Returns:
            Health response data or None if failed
        """
        url = f"{self.base_url}/health"
        logger.debug(f"Checking MLI health at {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={
                        "accept": "application/json",
                        "Authorization": f"Bearer {token}",
                    },
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"MLI health check HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"MLI health check error: {e}")
            return None

    async def get_models(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Get available models from MLI (for future use).

        Args:
            token: Optional pre-fetched token

        Returns:
            Dict with model information
        """
        if not token:
            token, auth_required = await self._get_auth_token()
            if auth_required:
                return {"error": "MLI requires SSO authentication"}

        if not token:
            return {"error": "Failed to obtain auth token"}

        url = f"{self.base_url}/models"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={
                        "accept": "application/json",
                        "Authorization": f"Bearer {token}",
                    },
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get MLI models: {e}")
            return {"error": str(e)}
