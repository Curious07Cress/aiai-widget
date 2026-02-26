"""
3DPassport SSO Authentication Service

Provides authentication for AIAI server access via 3DPassport SSO.
"""

import logging
import os
from typing import Optional, Tuple
from urllib.parse import quote_plus

import httpx
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class PassportAuthService:
    """Handles 3DPassport SSO authentication for AIAI access."""

    def __init__(self, cache_ttl: int = 1800):
        """
        Initialize the auth service.

        Args:
            cache_ttl: Time-to-live for cached sessions in seconds (default 30 min)
        """
        # Cache authenticated clients by (username, aiai_url)
        self._session_cache: TTLCache = TTLCache(maxsize=10, ttl=cache_ttl)

    async def get_authenticated_client(
        self,
        aiai_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Tuple[httpx.AsyncClient, bool]:
        """
        Get an authenticated HTTP client for AIAI requests.

        Args:
            aiai_url: The AIAI server URL
            username: 3DPassport username (optional)
            password: 3DPassport password (optional)

        Returns:
            Tuple of (client, is_authenticated)
        """
        cache_key = (username or "anonymous", aiai_url)

        # Check cache for existing session
        if cache_key in self._session_cache:
            logger.debug(f"Using cached session for {username}")
            return self._session_cache[cache_key], True

        # If no credentials provided, return unauthenticated client
        if not username or not password:
            return httpx.AsyncClient(timeout=30, follow_redirects=False), False

        # Authenticate and cache
        try:
            client = await self._authenticate(aiai_url, username, password)
            self._session_cache[cache_key] = client
            return client, True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return httpx.AsyncClient(timeout=30, follow_redirects=False), False

    async def _authenticate(
        self,
        aiai_url: str,
        username: str,
        password: str,
    ) -> httpx.AsyncClient:
        """
        Authenticate with 3DPassport and return an authenticated client.

        Args:
            aiai_url: The AIAI server URL
            username: 3DPassport username
            password: 3DPassport password

        Returns:
            Authenticated httpx.AsyncClient
        """
        logger.info(f"Authenticating user {username} for {aiai_url}")

        # Create a client that preserves cookies
        client = httpx.AsyncClient(timeout=30, follow_redirects=False)

        try:
            # Step 1: Hit AIAI to get redirected to Passport
            response = await client.get(f"{aiai_url}/health")

            if response.status_code not in (301, 302, 303, 307, 308):
                # No redirect = no auth required or already authenticated
                logger.info("AIAI does not require authentication")
                return client

            # Extract Passport URL from redirect
            location = response.headers.get("location", "")
            if "/login?" not in location:
                raise Exception(f"Unexpected redirect: {location}")

            passport_url = location.split("/login?")[0]
            logger.debug(f"Passport URL: {passport_url}")

            # Step 2: Get login ticket
            auth_params_url = f"{passport_url}/login?action=get_auth_params"
            response = await client.get(
                auth_params_url,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()

            lt = response.json().get("lt")
            if not lt:
                raise Exception("Failed to get login ticket")

            logger.debug(f"Got login ticket: {lt[:20]}...")

            # Step 3: Login with credentials
            login_data = {
                "lt": lt,
                "username": username,
                "password": password,
                "rememberMe": "On",
            }

            response = await client.post(
                f"{passport_url}/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                follow_redirects=False,
            )

            if response.status_code != 302:
                raise Exception(f"Login failed with status {response.status_code}")

            # Check for CASTGC cookie (authentication success)
            castgc = None
            for cookie in client.cookies.jar:
                if cookie.name.startswith("CASTGC"):
                    castgc = cookie.value
                    break

            if not castgc:
                raise Exception("Login failed - no CASTGC cookie received")

            logger.debug("Got CASTGC cookie, getting service ticket...")

            # Step 4: Get service ticket for AIAI
            service_url = quote_plus(aiai_url)
            st_url = f"{passport_url}/login?service={service_url}&xrequestedwith=xmlhttprequest"

            response = await client.get(
                st_url,
                headers={"Accept": "application/json"},
                follow_redirects=False,
            )

            if response.status_code == 200:
                st_data = response.json()
                service_ticket = st_data.get("access_token")
                if service_ticket:
                    logger.debug(f"Got service ticket: {service_ticket[:20]}...")
            elif response.status_code == 401:
                raise Exception("Service ticket request unauthorized")
            else:
                logger.warning(f"Service ticket response: {response.status_code}")

            # Step 5: Access AIAI with the authenticated session
            response = await client.get(
                f"{aiai_url}/health",
                follow_redirects=True
            )

            if response.status_code == 200:
                logger.info(f"Successfully authenticated {username} for {aiai_url}")
                return client
            else:
                raise Exception(f"Failed to access AIAI after auth: {response.status_code}")

        except Exception as e:
            await client.aclose()
            raise Exception(f"Authentication failed: {e}")

    async def clear_session(self, username: str, aiai_url: str):
        """Clear cached session for a user."""
        cache_key = (username, aiai_url)
        if cache_key in self._session_cache:
            client = self._session_cache.pop(cache_key)
            await client.aclose()


# Global instance
_auth_service: Optional[PassportAuthService] = None


def get_auth_service() -> PassportAuthService:
    """Get the global auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = PassportAuthService()
    return _auth_service


async def get_authenticated_client(
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> httpx.AsyncClient:
    """
    Get an authenticated HTTP client for 3DPassport-protected services.

    This is a simplified wrapper around PassportAuthService for use with
    supervision and staging APIs.

    Args:
        base_url: Base URL for authentication (optional, uses env var if not provided)
        username: 3DPassport username (optional, uses env var if not provided)
        password: 3DPassport password (optional, uses env var if not provided)

    Returns:
        Authenticated httpx.AsyncClient

    Raises:
        ValueError: If credentials are not provided and not in environment

    Environment Variables:
        PASSPORT_USERNAME: 3DPassport username
        PASSPORT_PASSWORD: 3DPassport password
        AIAI_URL: Default base URL for authentication
    """
    # Get credentials from environment if not provided
    username = username or os.getenv("PASSPORT_USERNAME")
    password = password or os.getenv("PASSPORT_PASSWORD")
    base_url = base_url or os.getenv("AIAI_URL")

    # For now, return an unauthenticated client if credentials not provided
    # This allows the endpoints to work in development without SSO
    if not username or not password:
        logger.warning(
            "No 3DPassport credentials provided. "
            "Set PASSPORT_USERNAME and PASSPORT_PASSWORD environment variables for authenticated access."
        )
        return httpx.AsyncClient(timeout=30, follow_redirects=True)

    if not base_url:
        raise ValueError("base_url is required when credentials are provided")

    # Use the auth service to get authenticated client
    service = get_auth_service()
    client, is_authenticated = await service.get_authenticated_client(
        aiai_url=base_url,
        username=username,
        password=password,
    )

    if not is_authenticated:
        logger.warning(f"Authentication failed for user {username}")

    return client
