"""
Supervision API Router

Provides endpoints for deriving and accessing supervision URLs.
"""

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from ..services.supervision import (
    derive_supervision_url,
    get_supervision_health,
    build_operation_request,
    get_available_operations,
    parse_sandbox_info,
    get_aiai_vms_from_sandbox,
    derive_sandbox_id_from_service_instance,
    fetch_sandbox_data,
    execute_supervision_operation,
    AIAI_VM_NAMES,
)
from ..services.passport_auth import get_authenticated_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/supervision", tags=["supervision"])


@router.get(
    "/derive",
    summary="Derive supervision URL from AIAI URL",
    description="Parses an AIAI URL and derives the corresponding supervision URLs.",
)
async def derive_supervision(
    aiai_url: str = Query(..., description="The AIAI server URL to parse"),
) -> Dict[str, Any]:
    """
    Derive supervision URLs from an AIAI URL.

    This endpoint parses the AIAI URL pattern to extract:
    - Sandbox ID
    - Region
    - Environment

    And then constructs the supervision URLs for that sandbox.

    Args:
        aiai_url: The AIAI server URL

    Returns:
        Dict containing derived supervision information

    Example:
        Input: https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com
        Output: {
            "sandbox_id": "yivwvbl",
            "region": "euw1",
            "environment": "3dx-staging",
            "service_instance_id": "SbxAIAssistantInfraYIVWVBLEUW1",
            "react_ops_url": "https://eu2-supstg-realtime.3dx-staging.3ds.com/react/ops/..."
        }
    """
    logger.info(f"Deriving supervision URL from: {aiai_url}")

    info = derive_supervision_url(aiai_url)
    if not info:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse AIAI URL pattern: {aiai_url}"
        )

    return {
        "sandbox_id": info.sandbox_id,
        "region": info.region,
        "environment": info.environment,
        "service_instance_id": info.service_instance_id,
        "admin_tenant": info.admin_tenant,
        "vm_instance_name": info.vm_instance_name,
        "base_url": info.base_url,
        "supervision_url": info.supervision_url,
        "supervision_api_url": info.supervision_api_url,
        "react_ops_url": info.react_ops_url,
        "vm_details_url": info.vm_details_url,
    }


@router.get(
    "/health",
    summary="Check supervision health",
    description="Checks if the supervision endpoint is reachable.",
)
async def check_supervision_health(
    aiai_url: str = Query(..., description="The AIAI server URL"),
) -> Dict[str, Any]:
    """
    Check supervision endpoint health.

    This endpoint derives the supervision URL and checks if it's reachable.
    Note: Full access to supervision data requires authentication.

    Args:
        aiai_url: The AIAI server URL

    Returns:
        Health status dict
    """
    logger.info(f"Checking supervision health for: {aiai_url}")

    info = derive_supervision_url(aiai_url)
    if not info:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse AIAI URL pattern: {aiai_url}"
        )

    health = await get_supervision_health(info)

    return {
        **health,
        "sandbox_id": info.sandbox_id,
        "region": info.region,
        "environment": info.environment,
        "vm_instance_name": info.vm_instance_name,
        "vm_details_url": info.vm_details_url,
    }


@router.get(
    "/operations",
    summary="List available operations",
    description="Returns the list of available supervision operations.",
)
async def list_operations() -> Dict[str, Any]:
    """
    List available supervision operations.

    Returns:
        Dict with list of operations
    """
    return {
        "operations": get_available_operations(),
    }


@router.get(
    "/operations/build",
    summary="Build operation request",
    description="Builds a supervision operation request for a given AIAI URL and resource.",
)
async def build_operation(
    aiai_url: str = Query(..., description="The AIAI server URL"),
    resource_id: str = Query(..., description="The VM resource ID (e.g., i-8d35997f)"),
    operation: str = Query(..., description="Operation key (e.g., restart_proxy_cas)"),
) -> Dict[str, Any]:
    """
    Build a supervision operation request.

    This endpoint generates the URL and payload needed to execute
    a supervision operation. The actual execution requires authentication
    and should be done from a trusted context.

    Args:
        aiai_url: The AIAI server URL
        resource_id: The VM resource ID from the supervision console
        operation: The operation key to execute

    Returns:
        Dict with URL, payload, and method for the operation
    """
    logger.info(f"Building operation {operation} for {aiai_url}, resource {resource_id}")

    info = derive_supervision_url(aiai_url)
    if not info:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse AIAI URL pattern: {aiai_url}"
        )

    request = build_operation_request(info, resource_id, operation)
    if not request:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown operation: {operation}. Use /operations to see available operations."
        )

    return {
        **request,
        "sandbox_id": info.sandbox_id,
        "admin_tenant": info.admin_tenant,
        "note": "Execute this request with proper 3DPassport authentication",
    }


@router.post(
    "/sandbox/parse",
    summary="Parse sandbox dashboard data",
    description="Parses sandbox dashboard JSON to extract service and VM information.",
)
async def parse_sandbox(
    sandbox_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Parse sandbox dashboard JSON response.

    This endpoint extracts structured information from the sandbox dashboard
    JSON, including all services and their VMs with instance IDs.

    Args:
        sandbox_data: The raw sandbox dashboard JSON

    Returns:
        Parsed sandbox info with services and VMs
    """
    logger.info(f"Parsing sandbox data for ID: {sandbox_data.get('ID', 'unknown')}")

    parsed = parse_sandbox_info(sandbox_data)
    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="Failed to parse sandbox data"
        )

    return parsed


@router.post(
    "/sandbox/aiai-vms",
    summary="Extract AIAI VMs from sandbox data",
    description="Extracts AIAssistantInfra VMs from sandbox dashboard JSON.",
)
async def get_aiai_vms(
    sandbox_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract AIAI service VMs from sandbox data.

    This is a convenience endpoint that extracts just the AIAssistantInfra
    VMs, which are needed for supervision operations.

    Args:
        sandbox_data: The raw sandbox dashboard JSON

    Returns:
        Dict with AIAI VMs and their instance IDs
    """
    vms = get_aiai_vms_from_sandbox(sandbox_data)

    # Find the main workflow executor VM
    main_vm = next((vm for vm in vms if vm["name"] == "AIWFL_EXEC_0"), None)

    return {
        "sandbox_id": sandbox_data.get("ID", "").upper(),
        "vms": vms,
        "main_vm": main_vm,
        "known_vm_names": AIAI_VM_NAMES,
    }


@router.get(
    "/sandbox/fetch",
    summary="Fetch sandbox data and VMs",
    description="Fetches sandbox data from staging API and extracts VM information.",
)
async def fetch_sandbox(
    staging_url: str = Query(..., description="Staging URL (e.g., https://dsext001-eu1-215dsi0708-staging.3dexperience.3ds.com)"),
    aiai_url: str = Query(..., description="AIAI URL to fetch real service instance ID"),
) -> Dict[str, Any]:
    """
    Fetch sandbox data and extract VMs.

    This endpoint:
    1. Authenticates with 3DPassport
    2. Fetches AIAI health endpoint to get real service instance ID (hex format)
    3. Fetches sandbox data from the staging API using the real ID
    4. Parses and returns VM information

    Args:
        staging_url: The staging server URL
        aiai_url: The AIAI server URL to fetch service instance ID from

    Returns:
        Dict with parsed sandbox info including VMs
    """
    logger.info(f"Fetching sandbox data for AIAI: {aiai_url}")

    # Check if credentials are configured
    import os
    has_credentials = bool(os.getenv("PASSPORT_USERNAME") and os.getenv("PASSPORT_PASSWORD"))
    if not has_credentials:
        logger.warning("No 3DPassport credentials configured in environment")

    # Get authenticated client for this specific AIAI URL
    try:
        client = await get_authenticated_client(base_url=aiai_url)
        logger.info(f"Obtained client for {aiai_url} (authenticated: {has_credentials})")
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )

    # Fetch real service instance ID from AIAI health endpoint
    service_instance_id = None
    try:
        health_url = f"{aiai_url}/health"
        logger.info(f"Fetching service instance ID from: {health_url}")
        health_response = await client.get(health_url)

        if health_response.status_code == 200:
            health_data = health_response.json()
            service_instance_id = health_data.get("serviceInstanceId")

            if service_instance_id:
                logger.info(f"Got real service instance ID from health endpoint: {service_instance_id}")
            else:
                logger.warning(f"No serviceInstanceId in AIAI health response: {health_data}")

        elif health_response.status_code in (301, 302, 303, 307, 308):
            # Redirect means server requires authentication or redirects to login
            # Fall back to deriving from URL pattern
            logger.warning(
                f"AIAI health endpoint returned {health_response.status_code} (redirect). "
                "Falling back to deriving service instance ID from URL pattern."
            )
            service_instance_id = None

        else:
            logger.warning(
                f"AIAI health endpoint returned {health_response.status_code}. "
                "Falling back to deriving service instance ID from URL pattern."
            )
            service_instance_id = None

    except httpx.HTTPError as e:
        logger.warning(f"HTTP error fetching AIAI health: {e}. Falling back to URL pattern derivation.")
        service_instance_id = None

    # If we couldn't get the real ID from the health endpoint, derive from URL
    if not service_instance_id:
        logger.info("Attempting to derive service instance ID from AIAI URL pattern")
        supervision_info = derive_supervision_url(aiai_url)

        if not supervision_info:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Could not get service instance ID. AIAI health endpoint returned a redirect "
                    f"(likely due to missing authentication) and URL pattern derivation failed. "
                    f"Please ensure PASSPORT_USERNAME and PASSPORT_PASSWORD are configured."
                )
            )

        service_instance_id = supervision_info.service_instance_id
        logger.warning(
            f"Using derived service instance ID from URL: {service_instance_id}. "
            "This is a UI format ID and may not work with the staging API. "
            "For best results, configure PASSPORT_USERNAME and PASSPORT_PASSWORD."
        )

    # Validate we have a service instance ID
    if not service_instance_id:
        raise HTTPException(
            status_code=500,
            detail="Could not obtain service instance ID from health endpoint or URL pattern"
        )

    # Derive sandbox ID from the real service instance ID
    sandbox_id = derive_sandbox_id_from_service_instance(service_instance_id)
    if not sandbox_id:
        raise HTTPException(
            status_code=400,
            detail="Could not derive sandbox ID from service instance ID"
        )

    # Fetch sandbox data
    sandbox_data = await fetch_sandbox_data(staging_url, sandbox_id, client)

    if not sandbox_data:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch sandbox data for ID: {sandbox_id}"
        )

    # Parse the data
    parsed = parse_sandbox_info(sandbox_data)
    if not parsed:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse sandbox data"
        )

    # Extract AIAI VMs
    aiai_vms = get_aiai_vms_from_sandbox(sandbox_data)

    return {
        **parsed,
        "aiai_vms": aiai_vms,
        "total_vms": sum(len(service["vms"]) for service in parsed["services"]),
    }


@router.post(
    "/operations/execute",
    summary="Execute supervision operation",
    description="Executes a supervision operation on a VM (requires authentication).",
)
async def execute_operation(
    aiai_url: str = Query(..., description="The AIAI server URL"),
    resource_id: str = Query(..., description="The VM resource ID (instance ID like i-8d35997f)"),
    operation: str = Query(..., description="Operation key (e.g., restart_aiai)"),
) -> Dict[str, Any]:
    """
    Execute a supervision operation on a VM.

    This endpoint:
    1. Derives supervision info from AIAI URL
    2. Gets authenticated client with 3DPassport
    3. Executes the operation via supervision API
    4. Returns the result

    Args:
        aiai_url: The AIAI server URL
        resource_id: The VM instance ID (e.g., i-8d35997f)
        operation: The operation key (restart_aiai, restart_proxy_cas)

    Returns:
        Dict with execution result
    """
    logger.info(f"Executing operation {operation} on {resource_id} for {aiai_url}")

    # Derive supervision info
    info = derive_supervision_url(aiai_url)
    if not info:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse AIAI URL pattern: {aiai_url}"
        )

    # Get authenticated client for this specific AIAI URL
    try:
        client = await get_authenticated_client(base_url=aiai_url)
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )

    # Execute the operation
    try:
        result = await execute_supervision_operation(
            supervision_info=info,
            resource_id=resource_id,
            operation_key=operation,
            client=client,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Operation failed")
            )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error executing operation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute operation: {str(e)}"
        )
