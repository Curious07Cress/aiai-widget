# AI Operations Dashboard - MVP Specification

**Version:** 0.3.0
**Status:** Specification Complete - Ready for Implementation
**Last Updated:** 2026-02-10

---

## Core Problem Statement

**Primary Use Case:** "Find out where in the system the code failed."

When a request fails, teams need to quickly identify:
- Which component failed (Classifier? LLM? MCP? MLI?)
- What was the input to that component?
- What was the error?
- What was the request flow up to that point?

---

## Design Principles

### Like a Car Dashboard
- **Simple and obvious** - no learning curve
- **At-a-glance status** - green/yellow/red indicators
- **Drill-down on demand** - click to see details
- **Clean UI** - no mixed/confusing views
- **NOT embedding Grafana** - we query the data, we present it our way

### Data Sources (Backend)
| Source | Data Available | Access Method |
|--------|---------------|---------------|
| **Jaeger (OpenTelemetry)** | Request traces, spans, timing, LangGraph steps | Jaeger API |
| **Grafana/Loki** | Logs (query via API) | Grafana API |
| **MLFlow** | Experiment data, model versions | MLFlow API |
| **MLI Service** | LLM health, response times | Direct REST API |
| **Probes** | Health checks | HTTP endpoints |

#### Jaeger Trace Endpoints (Confirmed Available)
| Environment | URL |
|-------------|-----|
| **Staging** | `https://eu2-supstg-disttracing.3dx-staging.3ds.com/jaeger/search` |
| **Pre-Prod** | `https://eu2-supppd-disttracing.3dexperience.3ds.com/jaeger/search` |
| **Production** | `https://eu2-supprd-disttracing.3dexperience.3ds.com/jaeger/search` |

**Service Filter:** `AIAssistantInfra/aiai-api`
**Entry Point:** `agents/entrypoint/submit` - shows LangGraph steps and calls inside each step

#### Analytics/Kibana Endpoints (For Future Reference)
| Dashboard | URL |
|-----------|-----|
| **Production Details** | `https://analytics.3dexperience.3ds.com/kbn/app/data-explorer/discover?security_tenant=aiassistantinfra` |
| **Production Overview** | `https://analytics.3dexperience.3ds.com/kbn/app/dashboards?security_tenant=aiassistantinfra` |

*Note: Analytics available in AIAI version 1.3.5+. Non-sensitive usages only (input/output excluded).*

---

## System Components to Monitor

| Component | Description | Health Check |
|-----------|-------------|--------------|
| **AIAI API Server** | Main application server | `/health` endpoint |
| **MLI Service** | Dassault Systemes enterprise LLM | See MLI Health Check below |
| **MCP Proxy** | Tool integration layer | Proxy status, tool availability |
| **3DSpace** | Platform services | Authentication, API access |
| **3DPassport** | Authentication service | Token validation |
| **Agent Endpoints** | Individual agent health | Per-agent status |

### MLI Health Check (Confirmed)

**Base URL:** `https://euw1-devprol50-mlinference.3dx-staging.3ds.com`

**Step 1 - Get Auth Token:**
```bash
GET /auth/token
Headers: accept: application/json
Response: Bearer token
```

**Step 2 - Check Health:**
```bash
GET /health
Headers:
  accept: application/json
  Authorization: Bearer <token>
```

---

## Phase 1: MVP - "Where Did It Fail?"

**Goal:** Answer the #1 question quickly and clearly.

### Tool 1: Failure Locator (PRIMARY)

**Input:** `request_id` (from user or from error log)

**Output:** Visual flow diagram showing:

```
[User Input] --> [Classifier] --> [Agent Selection] --> [LLM Call] --> [MCP Tool] --> [Response]
     OK              OK              OK                  FAILED           --            --
                                                           |
                                                    [Click for details]
```

**Features:**
- Each step shows: OK / FAILED / SKIPPED
- Failed step is highlighted RED
- Click any step to see:
  - Input to that step
  - Output (or error message)
  - Timing
  - Relevant logs

**Data Source:** OpenTelemetry traces

---

### Tool 2: Service Health Panel

**Purpose:** Quick "is everything up?" at a glance

**Display:**
```
+------------------+------------------+------------------+
|    AIAI API      |       MLI        |    MCP Proxy     |
|      [OK]        |      [OK]        |    [DEGRADED]    |
|      45ms        |     120ms        |  1/3 tools down  |
+------------------+------------------+------------------+
|    3DSpace       |   3DPassport     |     Agents       |
|      [OK]        |      [OK]        |      [OK]        |
+------------------+------------------+------------------+
```

**Features:**
- Auto-refresh every 30 seconds
- Click any card for details
- Color coding: Green=OK, Yellow=Degraded, Red=Down

**Data Source:** Health probes

---

### Tool 3: Request Lookup

**Purpose:** Find a request to trace

**Options:**
1. **Enter request_id directly** - if user has it from error message
2. **Search by time range** - show recent requests
3. **Filter by status** - show only failed requests
4. **Filter by user** - show requests from specific user

**Output:** List of matching requests, click to open Failure Locator

**Data Source:** OpenTelemetry + Logs

---

### Tool 4: LLM Response Viewer

**Purpose:** See exactly what was sent to and received from LLM

**Display:**
```
+----------------------------------+----------------------------------+
|          PROMPT SENT             |        RESPONSE RECEIVED         |
+----------------------------------+----------------------------------+
| System: You are an assistant...  | {                                |
| User: Create a laptop assembly   |   "summary": "Created laptop..." |
|                                  |   "structure": { ... }           |
+----------------------------------+----------------------------------+
| Model: gpt-4 | Tokens: 523->210  | Latency: 2.3s                   |
+----------------------------------+----------------------------------+
```

**Features:**
- Syntax highlighting for JSON
- Copy buttons
- Token counts
- Latency display

**Data Source:** OpenTelemetry spans + Logs

---

### Tool 5: MCP Tool Viewer

**Purpose:** See what was sent to and received from MCP tools

**Display:**
```
Tool: solidworks_assembly_structure_tool
Status: SUCCESS | Latency: 450ms

INPUT:                              OUTPUT:
{                                   {
  "name": "Laptop",                   "status": "created",
  "components": [...]                 "object_id": "abc123"
}                                   }
```

**Features:**
- JSON diff view (if comparing)
- Error highlighting if failed
- Retry suggestion if applicable

**Data Source:** OpenTelemetry spans + Logs

---

## Phase 1 User Flows

### Flow 1: "A user reported an error"

1. Tech support receives error with `request_id`
2. Opens dashboard, enters `request_id` in Failure Locator
3. Sees visual flow - immediately sees MCP step is RED
4. Clicks MCP step - sees "Connection timeout to sw-mcp-001"
5. **Result:** Knows exactly where and why it failed in < 30 seconds

### Flow 2: "Is the system working?"

1. User opens dashboard
2. Sees Service Health Panel - all green
3. **Result:** Confidence that system is operational in < 5 seconds

### Flow 3: "Something failed but I don't have the request_id"

1. Opens Request Lookup
2. Filters: Last 1 hour, Status=Failed
3. Sees list of 3 failed requests
4. Clicks one to open Failure Locator
5. **Result:** Found the issue without needing request_id upfront

---

## Phase 2: Enhanced Debugging

**Goal:** Deeper analysis for developers

| Tool | Description |
|------|-------------|
| **Agent State Viewer** | View LangGraph state at each node |
| **Permission Checker** | Validate user has correct access |
| **Log Search** | Search logs by component, level, time |
| **Error Pattern Analysis** | Show common failure patterns |

---

## Phase 3: Operations

**Goal:** Infrastructure visibility

| Tool | Description |
|------|-------------|
| **MLFlow Link** | Quick access to experiment tracking |
| **Grafana Link** | Deep link to detailed metrics |
| **Pod Status** | Kubernetes pod health (simplified view) |
| **Performance Trends** | Response time over time |

---

## UI/UX Requirements

### Dashboard Layout (Phase 1)

```
+------------------------------------------------------------------+
|  AI Operations Dashboard                    [Refresh] [Settings] |
+------------------------------------------------------------------+
|                                                                  |
|  SERVICE HEALTH                                                  |
|  +--------+ +--------+ +--------+ +--------+ +--------+ +------+ |
|  | AIAI   | |  MLI   | |  MCP   | | Space  | | Pass   | | Agnt | |
|  |  [OK]  | |  [OK]  | | [WARN] | |  [OK]  | |  [OK]  | | [OK] | |
|  +--------+ +--------+ +--------+ +--------+ +--------+ +------+ |
|                                                                  |
+------------------------------------------------------------------+
|                                                                  |
|  FAILURE LOCATOR                          [Enter request_id: __] |
|                                                                  |
|  [Search Recent Requests]  [Show Failed Only]                    |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  REQUEST FLOW (when request_id entered)                    |  |
|  |                                                            |  |
|  |  [Input] --> [Classifier] --> [Generator] --> [LLM] -->   |  |
|  |    OK           OK              OK          FAILED         |  |
|  |                                               |            |  |
|  |                                        [View Details]      |  |
|  +------------------------------------------------------------+  |
|                                                                  |
+------------------------------------------------------------------+
|                                                                  |
|  DETAILS PANEL (when step clicked)                               |
|  +------------------------------------------------------------+  |
|  |  LLM Call - FAILED                                         |  |
|  |  Error: Rate limit exceeded                                |  |
|  |  Time: 2026-02-09 10:23:45                                 |  |
|  |  [View Prompt] [View Response] [View Logs]                 |  |
|  +------------------------------------------------------------+  |
|                                                                  |
+------------------------------------------------------------------+
```

### Design Guidelines

1. **Maximum 3 clicks** to find any information
2. **Color meanings are consistent:**
   - Green = OK
   - Yellow = Warning/Degraded
   - Red = Error/Failed
   - Gray = Unknown/Checking
3. **No jargon** - use plain language
4. **Responsive** - works on different screen sizes
5. **Fast** - results in < 2 seconds

---

## API Requirements

### Required Endpoints

| Endpoint | Purpose | Data Source |
|----------|---------|-------------|
| `GET /api/health/all` | All service health | Probes |
| `GET /api/traces/{request_id}` | Full trace for request | OpenTelemetry |
| `GET /api/traces/search` | Search/filter requests | OpenTelemetry |
| `GET /api/traces/{request_id}/llm` | LLM details for request | Logs |
| `GET /api/traces/{request_id}/mcp` | MCP details for request | Logs |

### Health Check Response Format

```json
{
  "timestamp": "2026-02-09T10:30:00Z",
  "services": {
    "aiai_api": { "status": "ok", "latency_ms": 45 },
    "mli": { "status": "ok", "latency_ms": 120 },
    "mcp_proxy": { "status": "degraded", "message": "1/3 tools unavailable" },
    "3dspace": { "status": "ok", "latency_ms": 200 },
    "3dpassport": { "status": "ok", "latency_ms": 80 },
    "agents": { "status": "ok", "count": 5 }
  }
}
```

### Trace Response Format

```json
{
  "request_id": "abc-123",
  "timestamp": "2026-02-09T10:23:45Z",
  "status": "failed",
  "user_id": "user@company.com",
  "duration_ms": 3450,
  "steps": [
    {
      "name": "input",
      "status": "ok",
      "start_time": "...",
      "end_time": "...",
      "data": { "message": "Create a laptop assembly" }
    },
    {
      "name": "classifier",
      "status": "ok",
      "start_time": "...",
      "end_time": "...",
      "data": { "question_type": "generate", "confidence": 0.95 }
    },
    {
      "name": "llm_call",
      "status": "failed",
      "start_time": "...",
      "end_time": "...",
      "error": "Rate limit exceeded",
      "data": { "model": "gpt-4", "prompt_preview": "..." }
    }
  ]
}
```

---

## Architecture Decision: Separate Backend Service

**Constraint:** AIAI server cannot be modified without proving value first.

**Solution:** Dashboard requires its own lightweight backend service that:
1. Queries Jaeger API for trace data
2. Queries MLI health endpoint directly
3. Queries MCP proxy for tool status
4. Aggregates health checks from all services
5. Provides unified API for the frontend widget

```
+------------------+       +----------------------+       +------------------+
|                  |       |                      |       |                  |
|   3DDashboard    | <---> |  Dashboard Backend   | <---> |  Jaeger API      |
|   Widget (Vue)   |       |  (New Service)       |       |  MLI API         |
|                  |       |                      |       |  MCP Proxy       |
+------------------+       +----------------------+       |  AIAI /health    |
        ^                           ^                     +------------------+
        |                           |
        v                           v
+------------------+       +----------------------+
|   3DPassport     |       |   Analytics/Logs     |
|   (SSO Auth)     |       |   (Kibana)           |
+------------------+       +----------------------+
```

### Backend Technology Options

| Option | Pros | Cons |
|--------|------|------|
| **Python FastAPI** | Consistent with AIAI codebase, async support | Another Python service |
| **Node.js Express** | Lightweight, fast startup, good for proxying | Different language |

**Recommendation:** Python FastAPI for consistency with existing codebase.

---

## Resolved Questions

### 1. Trace Data Availability - CONFIRMED
- OpenTelemetry traces ARE available via Jaeger
- LangGraph steps ARE visible ("you can see the different graph step and the call made inside it")
- Service filter: `AIAssistantInfra/aiai-api`
- Entry point API: `agents/entrypoint/submit`

### 2. MLI Health Check - DEFINED
- Auth endpoint: `GET /auth/token`
- Health endpoint: `GET /health` (requires Bearer token)
- Base URL: `https://euw1-devprol50-mlinference.3dx-staging.3ds.com`

### 3. Backend API - NEW SERVICE
- Cannot modify AIAI server
- Must create separate lightweight backend
- Backend aggregates data from multiple sources

### 4. Authentication - 3DPassport SSO
- Use 3DPassport for authentication
- Leverage existing session (no re-login if already authenticated)
- Widget Lab's `@widget-lab/platform-connectors` handles this automatically

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Time to identify failed component | < 30 seconds |
| Time to determine system health | < 5 seconds |
| Maximum clicks to find info | 3 |
| Page load time | < 2 seconds |

---

## Next Steps

1. **User Approval** - Confirm this specification is complete
2. **Backend Implementation** - Build dashboard backend service (FastAPI)
3. **Frontend Implementation** - Build Vue.js widget with Failure Locator
4. **Integration Testing** - Test with real Jaeger/MLI data
5. **Deployment** - Deploy to 3DDashboard

---

## Implementation Order

### Sprint 1: Foundation
- [ ] Create dashboard backend service (FastAPI)
- [ ] Implement Jaeger API integration
- [ ] Implement MLI health check
- [ ] Basic health endpoint aggregation

### Sprint 2: Failure Locator
- [ ] Trace lookup by request_id
- [ ] Visual flow diagram component
- [ ] Step detail panel
- [ ] Error highlighting

### Sprint 3: Service Health + Polish
- [ ] Service health cards
- [ ] Auto-refresh mechanism
- [ ] Request search/filter
- [ ] LLM/MCP viewers

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.3.0 | 2026-02-10 | All questions resolved: Jaeger endpoints, MLI health check, separate backend architecture, 3DPassport SSO |
| 0.2.0 | 2026-02-09 | Added user feedback: clean UI, OpenTelemetry data, MLI definition, #1 pain point |
| 0.1.0 | 2026-02-09 | Initial draft |
