"""
Traces API Router

Provides endpoints for fetching and searching request traces.
This powers the Failure Locator feature.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query

from ..models.traces import (
    TraceResponse,
    TraceSearchParams,
    TraceSearchResult,
    StepStatus,
)
from ..services.jaeger_service import JaegerService

router = APIRouter(prefix="/api/traces", tags=["traces"])

# Service instance
jaeger_service = JaegerService()


@router.get(
    "/{trace_id}",
    response_model=TraceResponse,
    summary="Get trace by ID",
    description="Fetch a complete trace by its trace ID or request ID.",
)
async def get_trace(trace_id: str) -> TraceResponse:
    """
    Get a single trace by ID.

    This is the primary endpoint for the Failure Locator.
    It returns the full request flow with all steps and their status.

    Args:
        trace_id: The Jaeger trace ID or request ID

    Returns:
        Complete trace with all steps
    """
    trace = await jaeger_service.get_trace(trace_id)

    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trace not found: {trace_id}"
        )

    return trace


@router.get(
    "/",
    response_model=TraceSearchResult,
    summary="Search traces",
    description="Search for traces by time range, status, or user.",
)
async def search_traces(
    start_time: Optional[datetime] = Query(
        None,
        description="Start of time range (ISO format)"
    ),
    end_time: Optional[datetime] = Query(
        None,
        description="End of time range (ISO format)"
    ),
    status: Optional[StepStatus] = Query(
        None,
        description="Filter by status (ok, failed, skipped)"
    ),
    user_id: Optional[str] = Query(
        None,
        description="Filter by user ID"
    ),
    operation: Optional[str] = Query(
        None,
        description="Filter by operation name"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of results"
    ),
) -> TraceSearchResult:
    """
    Search for traces matching the given criteria.

    Use this to find requests without knowing the trace ID.
    For example:
    - Find all failed requests in the last hour
    - Find requests from a specific user
    - Find recent requests to investigate

    Returns:
        List of matching traces with basic info
    """
    params = TraceSearchParams(
        start_time=start_time,
        end_time=end_time,
        status=status,
        user_id=user_id,
        operation=operation,
        limit=limit,
    )

    return await jaeger_service.search_traces(params)


@router.get(
    "/search/failed",
    response_model=TraceSearchResult,
    summary="Get failed traces",
    description="Quick shortcut to find recently failed requests.",
)
async def get_failed_traces(
    hours: int = Query(
        1,
        ge=1,
        le=24,
        description="How many hours back to search"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of results"
    ),
) -> TraceSearchResult:
    """
    Get recently failed traces.

    This is a convenience endpoint for quickly finding failed requests
    without specifying all search parameters.
    """
    params = TraceSearchParams(
        start_time=datetime.utcnow() - timedelta(hours=hours),
        end_time=datetime.utcnow(),
        status=StepStatus.FAILED,
        limit=limit,
    )

    return await jaeger_service.search_traces(params)


@router.get(
    "/search/recent",
    response_model=TraceSearchResult,
    summary="Get recent traces",
    description="Get the most recent traces regardless of status.",
)
async def get_recent_traces(
    minutes: int = Query(
        30,
        ge=1,
        le=1440,
        description="How many minutes back to search"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of results"
    ),
) -> TraceSearchResult:
    """
    Get the most recent traces.

    Useful for monitoring current activity or finding a recent request
    without knowing its ID.
    """
    params = TraceSearchParams(
        start_time=datetime.utcnow() - timedelta(minutes=minutes),
        end_time=datetime.utcnow(),
        limit=limit,
    )

    return await jaeger_service.search_traces(params)


@router.get(
    "/operations",
    response_model=List[str],
    summary="Get available operations",
    description="List all operation names that can be filtered.",
)
async def get_operations() -> List[str]:
    """
    Get list of available operations.

    Operations correspond to API endpoints or entry points
    that can be used to filter trace searches.
    """
    return await jaeger_service.get_operations()
