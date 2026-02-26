"""
Supervision URL Parser and Health Service

Provides utilities to derive supervision URLs from AIAI URLs
and check system health via supervision endpoints.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SupervisionInfo:
    """Parsed supervision URL information."""

    sandbox_id: str
    region: str
    environment: str  # staging, prod, etc.
    base_url: str
    service_instance_id: str  # For React Ops UI (all uppercase)
    admin_tenant: str  # For API calls (sandbox upper, region lower)
    vm_instance_name: str
    supervision_url: str
    supervision_api_url: str  # Base API URL
    react_ops_url: str
    vm_details_url: str  # Direct link to VM details


# Default VM instance name for AIAI services
DEFAULT_VM_INSTANCE_NAME = "AIWFL_EXEC_0"

# Supervision API version
SUPERVISION_API_VERSION = "v7"

# Known VM names for AIAI services
AIAI_VM_NAMES = [
    "AIWFL_EXEC_0",  # Main AIAI workflow executor
    "ScalableLB_0",  # Load balancer
    "KAFKA_0",       # Kafka message broker
    "ES_MASTERHA_0", # Elasticsearch master
    "ES_DATA_0",     # Elasticsearch data node
    "ES_COORD_0",    # Elasticsearch coordinator
    "NIFI_NV_0",     # NiFi data flow
    "zookeeper_0",   # Zookeeper coordination
]

# Known supervision operations for AIAI services
SUPERVISION_OPERATIONS = {
    "restart_proxy_cas": {
        "name": "maintenance",
        "xmlScript": "RestartProxyCas",
        "displayName": "Restart Proxy CAS",
        "maxDuration": 300,
        "parameters": [],
    },
    "restart_aiai": {
        "name": "maintenance",
        "xmlScript": "RestartAIAI",
        "displayName": "Restart AIAI Service",
        "maxDuration": 300,
        "parameters": [],
    },
}

# Environment mappings
ENV_MAPPINGS = {
    "3dx-staging": {
        "supervision_env": "supstg",
        "supervision_region": "eu2",  # Supervision is centralized in EU
    },
    "3dx-cloud": {
        "supervision_env": "sup",
        "supervision_region": "eu1",
    },
}


def parse_aiai_url(aiai_url: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse an AIAI URL to extract sandbox ID, region, and environment.

    Args:
        aiai_url: The AIAI server URL

    Returns:
        Tuple of (sandbox_id, region, environment) or None if parsing fails

    Example:
        Input: https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com
        Output: ("yivwvbl", "euw1", "3dx-staging")
    """
    try:
        parsed = urlparse(aiai_url)
        hostname = parsed.netloc or parsed.path

        # Pattern: devops{sandbox_id}{digits}-{region}-{platform}-aiai.{environment}.3ds.com
        # Example: devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com
        pattern = r"devops([a-z]+)\d+-([a-z]+\d+)-[a-z]+\d+-aiai\.([a-z0-9-]+)\.3ds\.com"

        match = re.match(pattern, hostname, re.IGNORECASE)
        if match:
            sandbox_id = match.group(1).lower()
            region = match.group(2).lower()
            environment = match.group(3).lower()
            return (sandbox_id, region, environment)

        # Try alternative pattern for different URL formats
        # Pattern: {prefix}-{region}-{platform}-aiai.{environment}.3ds.com
        alt_pattern = r"([a-z]+)-([a-z]+\d+)-[a-z]+\d+-aiai\.([a-z0-9-]+)\.3ds\.com"
        match = re.match(alt_pattern, hostname, re.IGNORECASE)
        if match:
            prefix = match.group(1).lower()
            region = match.group(2).lower()
            environment = match.group(3).lower()
            # Extract sandbox from prefix (e.g., "devopsyivwvbl820289" -> "yivwvbl")
            sandbox_match = re.search(r"devops([a-z]+)", prefix)
            if sandbox_match:
                sandbox_id = sandbox_match.group(1)
                return (sandbox_id, region, environment)

        logger.warning(f"Could not parse AIAI URL pattern: {hostname}")
        return None

    except Exception as e:
        logger.error(f"Error parsing AIAI URL: {e}")
        return None


def derive_supervision_url(aiai_url: str) -> Optional[SupervisionInfo]:
    """
    Derive the supervision URL from an AIAI URL.

    Args:
        aiai_url: The AIAI server URL

    Returns:
        SupervisionInfo with all derived URLs, or None if parsing fails
    """
    parsed = parse_aiai_url(aiai_url)
    if not parsed:
        return None

    sandbox_id, region, environment = parsed

    # Get environment-specific mappings
    env_config = ENV_MAPPINGS.get(environment)
    if not env_config:
        logger.warning(f"Unknown environment: {environment}")
        # Default to staging config
        env_config = ENV_MAPPINGS["3dx-staging"]

    supervision_env = env_config["supervision_env"]
    supervision_region = env_config["supervision_region"]

    # Build the supervision base URL
    base_url = f"https://{supervision_region}-{supervision_env}-realtime.{environment}.3ds.com"

    # Service instance ID format for UI: SbxAIAssistantInfra{SANDBOX_ID}{REGION} (all uppercase)
    service_instance_id = f"SbxAIAssistantInfra{sandbox_id.upper()}{region.upper()}"

    # Admin tenant for API calls: SbxAIAssistantInfra{SANDBOX_ID}{region} (sandbox upper, region lower)
    admin_tenant = f"SbxAIAssistantInfra{sandbox_id.upper()}{region.lower()}"

    # VM instance name (constant for AIAI services)
    vm_instance_name = DEFAULT_VM_INSTANCE_NAME

    # Build the React Ops URL (the visual dashboard)
    react_ops_url = f"{base_url}/react/ops/group=DEVENV/serviceInstanceID={service_instance_id}"

    # Build the VM details URL (direct link to specific VM)
    vm_details_url = f"{react_ops_url}/vmInstanceName={vm_instance_name}"

    # Build the supervision API URLs
    supervision_url = f"{base_url}/supervision"
    supervision_api_url = f"{supervision_url}/api/{SUPERVISION_API_VERSION}"

    return SupervisionInfo(
        sandbox_id=sandbox_id,
        region=region,
        environment=environment,
        base_url=base_url,
        service_instance_id=service_instance_id,
        admin_tenant=admin_tenant,
        vm_instance_name=vm_instance_name,
        supervision_url=supervision_url,
        supervision_api_url=supervision_api_url,
        react_ops_url=react_ops_url,
        vm_details_url=vm_details_url,
    )


def build_operation_request(
    supervision_info: SupervisionInfo,
    resource_id: str,
    operation_key: str,
) -> Optional[dict]:
    """
    Build a supervision operation request.

    Args:
        supervision_info: Parsed supervision information
        resource_id: The VM resource ID (e.g., "i-8d35997f")
        operation_key: Key from SUPERVISION_OPERATIONS (e.g., "restart_proxy_cas")

    Returns:
        Dict with 'url' and 'payload' for the operation request, or None if operation unknown

    Example:
        {
            "url": "https://eu2-supstg-realtime.../supervision/api/v7/resourceoperations/resource?...",
            "payload": {"resourceOperation": {...}},
            "method": "POST"
        }
    """
    operation = SUPERVISION_OPERATIONS.get(operation_key)
    if not operation:
        logger.warning(f"Unknown operation: {operation_key}")
        return None

    # Build the API URL with query parameters
    url = (
        f"{supervision_info.supervision_api_url}/resourceoperations/resource"
        f"?environment=DEVENV"
        f"&adminTenant={supervision_info.admin_tenant}"
        f"&resourceId={resource_id}"
    )

    # Build the payload
    payload = {
        "resourceOperation": operation.copy()
    }

    return {
        "url": url,
        "payload": payload,
        "method": "POST",
        "operation": operation_key,
        "display_name": operation["displayName"],
    }


def parse_sandbox_info(sandbox_data: dict) -> Optional[dict]:
    """
    Parse sandbox dashboard JSON to extract relevant service and VM information.

    Args:
        sandbox_data: The raw sandbox dashboard JSON response

    Returns:
        Dict with parsed sandbox info including VMs and their instance IDs
    """
    try:
        result = {
            "sandbox_id": sandbox_data.get("ID", "").upper(),
            "status": sandbox_data.get("Status"),
            "region": sandbox_data.get("Deployment Region", "").lower(),
            "parent_cluster": sandbox_data.get("Parent Cluster"),
            "creation_date": sandbox_data.get("Creation Date"),
            "services": [],
        }

        # Parse sandboxed services
        for service in sandbox_data.get("Sandboxed Services", []):
            service_info = {
                "name": service.get("Name", ""),
                "status": service.get("Status"),
                "admin_tenant": None,
                "service_dns": service.get("Service DNS"),
                "urls": service.get("URLs", []),
                "version": None,
                "vms": [],
            }

            # Find the admin tenant key (e.g., "Admin AIAssistantInfra")
            for key, value in service.items():
                if key.startswith("Admin "):
                    service_info["admin_tenant"] = value
                    service_info["service_type"] = key.replace("Admin ", "")
                    break

            # Get version info
            deployed_from = service.get("Deployed From", {})
            if deployed_from:
                service_info["version"] = deployed_from.get("VersionName")
                service_info["service_name"] = deployed_from.get("ServiceName")

            # Parse VMs
            for vm in service.get("VMs", []):
                vm_info = {
                    "name": vm.get("Name"),
                    "instance_id": vm.get("Instance ID"),
                    "public_ip": vm.get("Public IP"),
                    "private_ip": vm.get("Private IP"),
                    "is_bastion": vm.get("isVMBastion", False),
                    "revision": vm.get("Revision"),
                }
                service_info["vms"].append(vm_info)

            result["services"].append(service_info)

        return result

    except Exception as e:
        logger.error(f"Error parsing sandbox info: {e}")
        return None


def get_aiai_vms_from_sandbox(sandbox_data: dict) -> list:
    """
    Extract AIAI service VMs from sandbox data.

    Args:
        sandbox_data: The raw sandbox dashboard JSON response

    Returns:
        List of VM dicts with name, instance_id, etc.
    """
    parsed = parse_sandbox_info(sandbox_data)
    if not parsed:
        return []

    # Find AIAssistantInfra service
    for service in parsed.get("services", []):
        if service.get("service_type") == "AIAssistantInfra":
            return service.get("vms", [])

    return []


def get_available_operations() -> list:
    """
    Get list of available supervision operations.

    Returns:
        List of operation info dicts
    """
    return [
        {
            "key": key,
            "name": op["name"],
            "display_name": op["displayName"],
            "max_duration": op["maxDuration"],
        }
        for key, op in SUPERVISION_OPERATIONS.items()
    ]


def derive_sandbox_id_from_service_instance(service_instance_id: str) -> Optional[str]:
    """
    Derive sandbox ID from service instance ID.

    Args:
        service_instance_id: The service instance ID (e.g., "6CDD1E53E39C1900694C44000000C6CA")

    Returns:
        Sandbox ID suitable for the refreshSandbox API

    Note:
        The service instance ID from the health endpoint can be used directly
        as the sandBoxId parameter in the refreshSandbox API.
    """
    if not service_instance_id:
        return None

    # The service instance ID can be used directly as the sandbox ID
    # Example: 6CDD1E53E39C1900694C44000000C6CA
    return service_instance_id


async def fetch_sandbox_data(
    staging_url: str,
    sandbox_id: str,
    client: Optional[httpx.AsyncClient] = None,
    timeout: int = 30,
) -> Optional[dict]:
    """
    Fetch sandbox data from the staging API.

    Args:
        staging_url: Base staging URL (e.g., https://dsext001-eu1-215dsi0708-staging.3dexperience.3ds.com)
        sandbox_id: The sandbox ID to fetch
        client: Optional authenticated HTTP client
        timeout: Request timeout in seconds

    Returns:
        Raw sandbox data dict from the API, or None if failed

    Example URL:
        https://dsext001-eu1-215dsi0708-staging.3dexperience.3ds.com/enovia/resources/v0/DevOpsStaging/sandbox/refreshSandbox?sandBoxId=6CDD1E53E39C1900694C44000000C6CA
    """
    close_client = False
    if client is None:
        logger.warning("fetch_sandbox_data called without authenticated client, creating unauthenticated client")
        client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        close_client = True

    try:
        # Build the refreshSandbox API URL
        api_url = f"{staging_url}/enovia/resources/v0/DevOpsStaging/sandbox/refreshSandbox"

        logger.info(f"Fetching sandbox data for ID: {sandbox_id}")

        # Make the request
        response = await client.get(
            api_url,
            params={"sandBoxId": sandbox_id},
        )

        if response.status_code != 200:
            logger.error(f"Failed to fetch sandbox data: HTTP {response.status_code}")
            return None

        data = response.json()

        # Extract the sandbox object and readSandboxContent
        sandbox = data.get("sandbox", {})
        sandbox_config = sandbox.get("sandboxConfig", {})
        read_sandbox_content = sandbox_config.get("readSandboxContent")

        if not read_sandbox_content:
            logger.error("No readSandboxContent found in response")
            return None

        # Parse the JSON string inside readSandboxContent
        import json
        sandbox_content = json.loads(read_sandbox_content)

        logger.info(f"Successfully fetched sandbox data for {sandbox_content.get('ID', 'unknown')}")
        return sandbox_content

    except httpx.TimeoutException:
        logger.error(f"Timeout fetching sandbox data for {sandbox_id}")
        return None
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching sandbox data: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error fetching sandbox data: {e}")
        return None
    finally:
        if close_client:
            await client.aclose()


async def execute_supervision_operation(
    supervision_info: SupervisionInfo,
    resource_id: str,
    operation_key: str,
    client: Optional[httpx.AsyncClient] = None,
    timeout: int = 300,
) -> dict:
    """
    Execute a supervision operation on a VM.

    Args:
        supervision_info: Parsed supervision information
        resource_id: The VM resource ID (instance ID)
        operation_key: Operation key from SUPERVISION_OPERATIONS
        client: Authenticated HTTP client (required for supervision API)
        timeout: Request timeout in seconds (default 300 for long operations)

    Returns:
        Dict with execution result

    Raises:
        ValueError: If operation is unknown or client not provided
    """
    if client is None:
        raise ValueError("Authenticated client is required for supervision operations")

    # Build the operation request
    request = build_operation_request(supervision_info, resource_id, operation_key)
    if not request:
        raise ValueError(f"Unknown operation: {operation_key}")

    result = {
        "success": False,
        "operation": operation_key,
        "resource_id": resource_id,
        "display_name": request["display_name"],
        "error": None,
        "response_data": None,
    }

    try:
        logger.info(f"Executing operation {operation_key} on resource {resource_id}")

        # Execute the operation
        response = await client.post(
            request["url"],
            json=request["payload"],
            timeout=timeout,
        )

        result["response_data"] = response.json() if response.text else None

        if response.status_code in (200, 201, 202):
            result["success"] = True
            logger.info(f"Operation {operation_key} executed successfully on {resource_id}")
        else:
            result["error"] = f"HTTP {response.status_code}"
            if result["response_data"]:
                result["error"] += f": {result['response_data']}"
            logger.error(f"Operation failed: {result['error']}")

    except httpx.TimeoutException:
        result["error"] = "Operation timed out"
        logger.error(f"Operation {operation_key} timed out for {resource_id}")
    except httpx.HTTPError as e:
        result["error"] = f"HTTP error: {str(e)}"
        logger.error(f"HTTP error during operation: {e}")
    except Exception as e:
        result["error"] = str(e)
        logger.exception(f"Error executing operation {operation_key}: {e}")

    return result


async def get_supervision_health(
    supervision_info: SupervisionInfo,
    client: Optional[httpx.AsyncClient] = None,
    timeout: int = 10,
) -> dict:
    """
    Check health via supervision endpoints.

    Note: This requires authentication to access supervision APIs.

    Args:
        supervision_info: Parsed supervision information
        client: Optional authenticated HTTP client
        timeout: Request timeout in seconds

    Returns:
        Health status dict
    """
    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)
        close_client = True

    result = {
        "service_instance_id": supervision_info.service_instance_id,
        "react_ops_url": supervision_info.react_ops_url,
        "reachable": False,
        "requires_auth": False,
        "error": None,
    }

    try:
        # Try to access the supervision base
        response = await client.get(
            supervision_info.base_url,
            follow_redirects=False,
        )

        if response.status_code in (301, 302, 303, 307, 308):
            result["requires_auth"] = True
            result["reachable"] = True
        elif response.status_code == 200:
            result["reachable"] = True
        else:
            result["error"] = f"HTTP {response.status_code}"

    except httpx.TimeoutException:
        result["error"] = "Connection timeout"
    except httpx.ConnectError as e:
        result["error"] = f"Connection failed: {str(e)}"
    except Exception as e:
        result["error"] = str(e)
    finally:
        if close_client:
            await client.aclose()

    return result
