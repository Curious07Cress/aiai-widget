"""
Jaeger Service

Integrates with Jaeger API to fetch OpenTelemetry traces.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import httpx

from ..config import get_settings
from ..models.traces import (
    TraceResponse,
    TraceStep,
    TraceSearchParams,
    TraceSearchResult,
    StepStatus,
)

logger = logging.getLogger(__name__)


class JaegerService:
    """Service for fetching traces from Jaeger."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.jaeger_base_url
        self.service_name = self.settings.jaeger_service_name
        self.timeout = self.settings.trace_fetch_timeout

    async def get_trace(self, trace_id: str) -> Optional[TraceResponse]:
        """
        Fetch a single trace by trace ID.

        Args:
            trace_id: The Jaeger trace ID

        Returns:
            TraceResponse or None if not found
        """
        url = f"{self.base_url}/api/traces/{trace_id}"
        logger.info(f"Fetching trace: {trace_id}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return self._parse_trace(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Trace not found: {trace_id}")
                return None
            logger.error(f"HTTP error fetching trace {trace_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching trace {trace_id}: {e}")
            raise

    async def search_traces(self, params: TraceSearchParams) -> TraceSearchResult:
        """
        Search for traces matching the given parameters.

        Args:
            params: Search parameters

        Returns:
            TraceSearchResult with matching traces
        """
        url = f"{self.base_url}/api/traces"

        # Build query parameters for Jaeger API
        query_params = {
            "service": self.service_name,
            "limit": params.limit,
        }

        # Time range
        if params.end_time:
            query_params["end"] = int(params.end_time.timestamp() * 1_000_000)
        else:
            query_params["end"] = int(datetime.utcnow().timestamp() * 1_000_000)

        if params.start_time:
            query_params["start"] = int(params.start_time.timestamp() * 1_000_000)
        else:
            # Default to last 1 hour
            start = datetime.utcnow() - timedelta(hours=1)
            query_params["start"] = int(start.timestamp() * 1_000_000)

        if params.operation:
            query_params["operation"] = params.operation

        logger.info(f"Searching traces with params: {query_params}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=query_params)
                response.raise_for_status()
                data = response.json()

                traces = []
                for trace_data in data.get("data", []):
                    trace = self._parse_trace({"data": [trace_data]})
                    if trace:
                        # Filter by status if specified
                        if params.status and trace.status != params.status:
                            continue
                        # Filter by user_id if specified
                        if params.user_id and trace.user_id != params.user_id:
                            continue
                        traces.append(trace)

                return TraceSearchResult(
                    total=len(traces),
                    traces=traces[:params.limit],
                    has_more=len(traces) > params.limit,
                )
        except Exception as e:
            logger.error(f"Error searching traces: {e}")
            raise

    async def get_services(self) -> List[str]:
        """Get list of available services in Jaeger."""
        url = f"{self.base_url}/api/services"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching services: {e}")
            raise

    async def get_operations(self, service: Optional[str] = None) -> List[str]:
        """Get list of operations for a service."""
        service = service or self.service_name
        url = f"{self.base_url}/api/services/{service}/operations"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching operations: {e}")
            raise

    def _parse_trace(self, jaeger_response: Dict[str, Any]) -> Optional[TraceResponse]:
        """
        Parse Jaeger trace response into our TraceResponse model.

        Args:
            jaeger_response: Raw Jaeger API response

        Returns:
            Parsed TraceResponse or None
        """
        data = jaeger_response.get("data", [])
        if not data:
            return None

        trace_data = data[0]
        trace_id = trace_data.get("traceID", "")
        spans = trace_data.get("spans", [])

        if not spans:
            return None

        # Find root span
        root_span = self._find_root_span(spans)
        if not root_span:
            root_span = spans[0]

        # Extract request_id from tags if available
        request_id = self._extract_tag(root_span, "request_id") or trace_id

        # Extract user_id from tags
        user_id = self._extract_tag(root_span, "user_id") or self._extract_tag(root_span, "user")

        # Parse all spans into steps
        steps = self._parse_spans_to_steps(spans, trace_data.get("processes", {}))

        # Calculate overall status
        overall_status = StepStatus.OK
        for step in steps:
            if step.status == StepStatus.FAILED:
                overall_status = StepStatus.FAILED
                break

        # Calculate total duration
        start_time = min(s.start_time for s in steps) if steps else datetime.utcnow()
        end_time = max(s.end_time for s in steps if s.end_time) if steps else start_time
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        return TraceResponse(
            request_id=request_id,
            trace_id=trace_id,
            timestamp=start_time,
            status=overall_status,
            user_id=user_id,
            duration_ms=duration_ms,
            steps=steps,
            service=self.service_name,
            operation=root_span.get("operationName"),
        )

    def _find_root_span(self, spans: List[Dict]) -> Optional[Dict]:
        """Find the root span (no parent references)."""
        span_ids = {s["spanID"] for s in spans}
        for span in spans:
            refs = span.get("references", [])
            if not refs:
                return span
            # Check if parent is in this trace
            parent_refs = [r for r in refs if r.get("refType") == "CHILD_OF"]
            if not parent_refs or parent_refs[0].get("spanID") not in span_ids:
                return span
        return None

    def _parse_spans_to_steps(
        self,
        spans: List[Dict],
        processes: Dict[str, Any]
    ) -> List[TraceStep]:
        """Convert Jaeger spans to TraceStep objects."""
        steps = []

        # Sort spans by start time
        sorted_spans = sorted(spans, key=lambda s: s.get("startTime", 0))

        for span in sorted_spans:
            start_time = datetime.fromtimestamp(span.get("startTime", 0) / 1_000_000)
            duration_us = span.get("duration", 0)
            end_time = datetime.fromtimestamp(
                (span.get("startTime", 0) + duration_us) / 1_000_000
            )

            # Determine status from tags
            status = StepStatus.OK
            error_msg = None

            tags = {t["key"]: t["value"] for t in span.get("tags", [])}
            if tags.get("error") == True or tags.get("otel.status_code") == "ERROR":
                status = StepStatus.FAILED
                error_msg = tags.get("otel.status_description") or tags.get("error.message")

            # Extract logs for error details
            logs = span.get("logs", [])
            for log in logs:
                log_fields = {f["key"]: f["value"] for f in log.get("fields", [])}
                if "error" in log_fields or "exception" in log_fields:
                    status = StepStatus.FAILED
                    error_msg = error_msg or log_fields.get("message") or log_fields.get("error")

            steps.append(TraceStep(
                name=span.get("operationName", "unknown"),
                status=status,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_us // 1000,
                error=error_msg,
                data=tags,
                span_id=span.get("spanID"),
            ))

        return steps

    def _extract_tag(self, span: Dict, tag_name: str) -> Optional[str]:
        """Extract a tag value from a span."""
        tags = span.get("tags", [])
        for tag in tags:
            if tag.get("key") == tag_name:
                return str(tag.get("value"))
        return None
