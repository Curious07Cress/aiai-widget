"""
Trace Data Models

Defines the structure for request traces from Jaeger/OpenTelemetry.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    """Status values for trace steps."""
    OK = "ok"
    FAILED = "failed"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class TraceStep(BaseModel):
    """A single step in a request trace (represents a span)."""
    name: str = Field(description="Step name (e.g., classifier, llm_call, mcp_tool)")
    status: StepStatus = Field(description="Step execution status")
    start_time: datetime = Field(description="Step start timestamp")
    end_time: Optional[datetime] = Field(None, description="Step end timestamp")
    duration_ms: Optional[int] = Field(None, description="Step duration in milliseconds")
    error: Optional[str] = Field(None, description="Error message if failed")
    data: Optional[Dict[str, Any]] = Field(None, description="Step-specific data")
    span_id: Optional[str] = Field(None, description="Jaeger span ID")
    children: Optional[List["TraceStep"]] = Field(None, description="Child spans")


class TraceResponse(BaseModel):
    """Full trace for a request."""
    request_id: str = Field(description="Unique request identifier")
    trace_id: str = Field(description="Jaeger trace ID")
    timestamp: datetime = Field(description="Request start timestamp")
    status: StepStatus = Field(description="Overall request status")
    user_id: Optional[str] = Field(None, description="User who made the request")
    duration_ms: int = Field(description="Total request duration in milliseconds")
    steps: List[TraceStep] = Field(description="Ordered list of trace steps")
    service: str = Field(description="Service name")
    operation: Optional[str] = Field(None, description="Operation name")


class TraceSearchParams(BaseModel):
    """Parameters for searching traces."""
    start_time: Optional[datetime] = Field(None, description="Start of time range")
    end_time: Optional[datetime] = Field(None, description="End of time range")
    status: Optional[StepStatus] = Field(None, description="Filter by status")
    user_id: Optional[str] = Field(None, description="Filter by user")
    limit: int = Field(20, ge=1, le=100, description="Maximum results to return")
    operation: Optional[str] = Field(None, description="Filter by operation name")


class TraceSearchResult(BaseModel):
    """Search results for traces."""
    total: int = Field(description="Total matching traces")
    traces: List[TraceResponse] = Field(description="Matching traces")
    has_more: bool = Field(description="Whether more results exist")
