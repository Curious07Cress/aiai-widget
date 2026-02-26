"""
AIAI API Proxy Router

Provides proxy endpoints for AIAI API calls that would otherwise
be blocked by CORS when called directly from the browser.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from ..config import get_settings
from ..services.passport_auth import get_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/aiai", tags=["aiai"])


async def _get_client(aiai_url: str) -> httpx.AsyncClient:
    """
    Get an HTTP client, authenticated if credentials are configured.

    Args:
        aiai_url: The AIAI server URL

    Returns:
        httpx.AsyncClient (may be authenticated)
    """
    settings = get_settings()

    if settings.passport_username and settings.passport_password:
        auth_service = get_auth_service()
        client, is_auth = await auth_service.get_authenticated_client(
            aiai_url=aiai_url,
            username=settings.passport_username,
            password=settings.passport_password,
        )
        if is_auth:
            logger.info(f"Using authenticated session for {settings.passport_username}")
        return client

    return httpx.AsyncClient(timeout=30, follow_redirects=False)


@router.get(
    "/assistants",
    summary="Get available assistants",
    description="Fetches the list of assistants from the AIAI API server.",
)
async def get_assistants(
    assistant_namespace: str = Query(
        default="",
        description="Filter assistants by namespace"
    ),
    aiai_url: Optional[str] = Query(
        default=None,
        description="Override AIAI server URL (for local development)"
    ),
) -> List[Dict[str, Any]]:
    """
    Fetch assistants from the AIAI API server.

    This endpoint proxies the request to avoid CORS issues when
    the browser tries to call the AIAI server directly.

    Note: AIAI uses POST for listing assistants (GET is deprecated).

    Args:
        assistant_namespace: Optional namespace filter
        aiai_url: Optional override for AIAI server URL

    Returns:
        List of assistant objects
    """
    settings = get_settings()
    base_url = aiai_url or settings.aiai_base_url
    url = f"{base_url}/api/v1/assistants"

    params = {
        "include_nocodecompanions": "false"
    }
    if assistant_namespace:
        params["assistant_namespace"] = assistant_namespace

    logger.info(f"Fetching assistants from {url} with params {params}")

    try:
        client = await _get_client(base_url)
        try:
            # AIAI uses POST for listing assistants (GET is deprecated)
            response = await client.post(
                url,
                params=params,
                json={},  # Empty body required by API
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

            # Handle SSO redirect
            if response.status_code in (301, 302, 303, 307, 308):
                logger.warning("AIAI requires SSO authentication")
                raise HTTPException(
                    status_code=503,
                    detail="AIAI server requires authentication. Configure DASHBOARD_PASSPORT_USERNAME and DASHBOARD_PASSPORT_PASSWORD in .env"
                )

            response.raise_for_status()
            data = response.json()
            logger.info(f"Received {len(data) if isinstance(data, list) else 'non-list'} assistants")

            # Return the assistants list
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "assistants" in data:
                return data["assistants"]
            elif isinstance(data, dict) and "data" in data:
                return data["data"]
            else:
                return [data] if data else []
        finally:
            # Don't close authenticated clients (they're cached)
            if not (settings.passport_username and settings.passport_password):
                await client.aclose()

    except httpx.TimeoutException:
        logger.error("Timeout fetching assistants from AIAI")
        raise HTTPException(
            status_code=504,
            detail="Timeout connecting to AIAI server"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching assistants: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AIAI API error: {e.response.text}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching assistants: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch assistants: {str(e)}"
        )


@router.post(
    "/assistants/{assistant_name}/submit",
    summary="Submit test to assistant",
    description="Submits a test prompt to an assistant via the AIAI API.",
)
async def submit_to_assistant(
    assistant_name: str,
    request_body: Dict[str, Any],
    assistant_namespace: str = Query(default="", description="Assistant namespace"),
    aiai_url: Optional[str] = Query(
        default=None,
        description="Override AIAI server URL (for local development)"
    ),
) -> Dict[str, Any]:
    """
    Submit a prompt to an assistant.

    This endpoint proxies the request to the AIAI submit endpoint.

    Args:
        assistant_name: Name of the assistant
        request_body: Request body containing prompt and options
        assistant_namespace: Optional namespace
        aiai_url: Optional override for AIAI server URL

    Returns:
        Assistant response
    """
    settings = get_settings()
    base_url = aiai_url or settings.aiai_base_url
    url = f"{base_url}/api/v1/assistants/{assistant_name}/submit"

    params = {}
    if assistant_namespace:
        params["assistant_namespace"] = assistant_namespace

    logger.info(f"Submitting to assistant {assistant_name} at {url}")

    try:
        client = await _get_client(base_url)
        try:
            response = await client.post(
                url,
                json=request_body,
                params=params,
                headers={"Content-Type": "application/json"},
                timeout=60,  # Longer timeout for AI processing
            )

            # Handle SSO redirect
            if response.status_code in (301, 302, 303, 307, 308):
                logger.warning("AIAI requires SSO authentication")
                raise HTTPException(
                    status_code=503,
                    detail="AIAI server requires authentication. Configure DASHBOARD_PASSPORT_USERNAME and DASHBOARD_PASSPORT_PASSWORD in .env"
                )

            response.raise_for_status()
            return response.json()
        finally:
            # Don't close authenticated clients (they're cached)
            if not (settings.passport_username and settings.passport_password):
                await client.aclose()

    except httpx.TimeoutException:
        logger.error("Timeout submitting to assistant")
        raise HTTPException(
            status_code=504,
            detail="Timeout waiting for AI response"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from assistant: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AIAI API error: {e.response.text}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting to assistant: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit to assistant: {str(e)}"
        )
