# AI Assistant Health Dashboard - Technical Specification

**Version**: 1.0
**Date**: February 27, 2026
**Status**: Draft

---

## 1. Purpose & Scope

### 1.1 Primary Objectives
- **A. Quick glance at system health** - Red/yellow/green visual indicators for instant status assessment
- **C. Historical health tracking** - Track and display health metrics over time

### 1.2 Out of Scope (V1)
- Detailed troubleshooting dashboard
- Real-time alerting/notifications
- User-configurable thresholds
- Log viewing/searching

---

## 2. Health Status Indicators

### 2.1 Design Approach
**Selected**: **Option A - Compact single-line status bar**

**Rationale**:
- Current 3-card layout takes excessive real estate (full row)
- Primary feature is AIAI Query tool, not status monitoring
- Status is informational only (no user actions required)
- Users need quick visual confirmation, not detailed metrics in main view

**Implementation**:
- Single horizontal bar at top of dashboard
- Contains 1-3 status icons with color coding
- Minimal text labels
- Optional: Click to expand detailed view (low priority)

### 2.2 Status Color Scheme
- 🟢 **Green (Healthy)**: All systems operational
- 🟡 **Yellow (Degraded)**: Service available but experiencing issues
- 🔴 **Red (Unhealthy)**: Service unavailable or critical error
- ⚫ **Gray (Unknown)**: No data or unable to determine status

### 2.3 Auto-refresh Behavior
- **Default interval**: 30 seconds
- **User configurable**: Yes (via widget settings)
- **Manual refresh**: Available via refresh button
- **On error**: Continue polling with exponential backoff

---

## 3. AIAI Service Health Metrics

### 3.1 V1 Health Determination

#### Primary Health Check
**Endpoint**: `GET /api/v1/health` or equivalent AIAI health endpoint
**Timeout**: 5 seconds
**Frequency**: Every 30 seconds (configurable)

**Health Determination Logic**:
```
IF response_time < 2s AND http_status == 200 THEN
    status = "healthy"
ELSE IF response_time < 5s AND http_status == 200 THEN
    status = "degraded"
ELSE
    status = "unhealthy"
END IF
```

#### Secondary Indicators (V1)

1. **API Endpoint Availability**
   - Test: Successful HTTP 200 response from health endpoint
   - Weight: Primary indicator
   - Failure threshold: 1 consecutive failure = degraded, 3 consecutive = unhealthy

2. **Response Time**
   - Measure: Round-trip time for health check request
   - Thresholds:
     - < 2 seconds: Healthy
     - 2-5 seconds: Degraded
     - \> 5 seconds: Unhealthy
   - Rolling average: Last 5 measurements

3. **Assistant Count** (Nice to have for V1)
   - Test: Call `GET /api/v1/assistants` endpoint
   - Success: Returns list with count > 0
   - Failure: Empty list or error
   - Note: Cache result for 5 minutes to reduce API load

### 3.2 Additional V1 Metric Ideas

**Recommended for V1**:
1. **Last Successful Query Timestamp**
   - Track when last query successfully completed
   - If > 5 minutes ago: Show warning indicator
   - Display: "Last query: 2 min ago"

2. **Backend Proxy Status**
   - Check: `GET /api/health/all` (backend endpoint)
   - Purpose: Verify backend proxy is reachable
   - Critical: If backend down, widget cannot function

**Consider for V2**:
1. **Query Success Rate** (last 10 queries)
   - Track: Success vs failure ratio
   - Display: "9/10 queries successful"

2. **Average Query Duration**
   - Measure: Time from submit to response
   - Useful for: Performance trending

3. **LLM Model Availability**
   - Check: Which LLM models are currently available
   - Display: "3/4 models available"

### 3.3 Health Check API Response Format

**Expected Response** from AIAI health endpoint:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-27T14:30:00Z",
  "services": {
    "llm": "available",
    "database": "available"
  },
  "metadata": {
    "version": "1.0.0",
    "uptime_seconds": 86400
  }
}
```

**Backend Proxy Response** from `/api/health/all`:
```json
{
  "overall": "healthy",
  "timestamp": "2026-02-27T14:30:00Z",
  "services": {
    "aiai": {
      "status": "healthy",
      "response_time_ms": 145,
      "assistant_count": 35,
      "last_check": "2026-02-27T14:30:00Z"
    }
  }
}
```

---

## 4. MCP Service Health Metrics

### 4.1 V1 Status
**Decision**: **Hidden until MCP service is fully developed**

**Rationale**:
- MCP service is marked "Under Development"
- No queryable health endpoint available
- Displaying unknown/unavailable status provides no value
- Will be added in future version when MCP is production-ready

### 4.2 Future Implementation (V2+)
When MCP is ready:
- Similar health check pattern as AIAI
- Check MCP server availability
- Validate MCP tool accessibility
- Monitor tool execution success rate

---

## 5. Overall Status Calculation

### 5.1 Aggregation Logic

**Overall Status** = Aggregate of all monitored services

```
IF all_services == "healthy" THEN
    overall = "healthy"
ELSE IF any_service == "unhealthy" THEN
    overall = "unhealthy"
ELSE IF any_service == "degraded" THEN
    overall = "degraded"
ELSE
    overall = "unknown"
END IF
```

### 5.2 V1 Implementation
Since only AIAI service is monitored in V1:
```
overall_status = aiai_status
```

When MCP is added:
```
IF aiai == "healthy" AND mcp == "healthy" THEN
    overall = "healthy"
ELSE IF aiai == "unhealthy" OR mcp == "unhealthy" THEN
    overall = "unhealthy"
ELSE IF aiai == "degraded" OR mcp == "degraded" THEN
    overall = "degraded"
ELSE
    overall = "unknown"
END IF
```

---

## 6. Historical Health Tracking

### 6.1 Data Collection

**Storage**: Client-side (browser localStorage)
**Retention**: Last 24 hours of data
**Granularity**: 1 data point per health check (every 30 seconds)
**Maximum points**: 2,880 (24 hours * 60 minutes * 2 checks/min)

**Data Structure**:
```json
{
  "health_history": [
    {
      "timestamp": "2026-02-27T14:30:00Z",
      "overall": "healthy",
      "aiai_status": "healthy",
      "aiai_response_time_ms": 145
    }
  ]
}
```

### 6.2 Historical View (V1 - Simple)

**Display Options**:
1. **Status Timeline** (Recommended for V1)
   - Horizontal bar showing last 24 hours
   - Color-coded segments (green/yellow/red)
   - Hoverable for timestamp details
   - Minimal height: 20-30px

2. **Uptime Percentage**
   - Calculate: (healthy_checks / total_checks) * 100
   - Display: "99.5% uptime (24h)"

3. **Incident Count**
   - Count: Number of status changes from healthy → degraded/unhealthy
   - Display: "2 incidents in last 24h"

### 6.3 Historical View (V2 - Advanced)

**Future Enhancements**:
- Line chart for response time trends
- Downloadable CSV export
- Configurable time ranges (1h, 6h, 24h, 7d)
- Correlation with query success rate

---

## 7. User Interface Design

### 7.1 V1 Layout - Compact Status Bar

```
┌─────────────────────────────────────────────────────────────┐
│  AI Assistant Health Dashboard                    [Settings]│
├─────────────────────────────────────────────────────────────┤
│  Status: ●  Healthy  │  AIAI: ●  145ms  │  Updated: 2s ago  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [AIAI Query Tool - Full Size]                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Assistant: [dropdown]    [Copy ID] [New]              │  │
│  │ Prompt: [text area]                                    │  │
│  │ [Submit Query]                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  [Query Results]                                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Status Bar Components

**Component 1: Overall Status**
- Icon: ● (circle)
- Color: Green/Yellow/Red/Gray
- Text: "Healthy" / "Degraded" / "Unhealthy" / "Unknown"
- Size: 14px icon + text

**Component 2: AIAI Service**
- Icon: 🤖 or ●
- Color: Green/Yellow/Red/Gray
- Text: "AIAI: 145ms" (response time)
- Hover: Shows full details tooltip

**Component 3: Last Updated**
- Icon: 🕐
- Text: "Updated: 2s ago"
- Refresh button (icon only)

### 7.3 Detailed View (Optional Click-to-Expand)

**Trigger**: Click on status bar
**Action**: Expand to show:
- Detailed metrics table
- 24-hour timeline visualization
- Uptime percentage
- Last 5 status changes with timestamps

---

## 8. User Actions & Interactions

### 8.1 V1 User Actions
**Decision**: **No user actions required for status indicators**

**Rationale**:
- Status is informational only
- Users cannot fix infrastructure issues from widget
- Primary action is using AIAI Query tool
- Admin actions (if needed) happen outside widget

### 8.2 Available Interactions (Read-only)

1. **View Status**
   - See current color-coded health status
   - Read response time metrics
   - Check last update timestamp

2. **Manual Refresh** (Optional)
   - Button to trigger immediate health check
   - Useful if auto-refresh is disabled
   - Shows loading indicator during check

3. **Hover Tooltips** (Optional)
   - Show detailed metrics on hover
   - Display historical uptime %
   - Show last incident timestamp

---

## 9. Backend API Requirements

### 9.1 Health Check Endpoint

**Endpoint**: `GET /api/health/all`
**Purpose**: Aggregate health check for all monitored services
**Response Time**: < 2 seconds
**Caching**: 10 second TTL recommended

**Request**:
```http
GET /api/health/all HTTP/1.1
Host: localhost:8080
```

**Response** (Success):
```json
{
  "overall": "healthy",
  "timestamp": "2026-02-27T14:30:00.123Z",
  "services": {
    "aiai": {
      "status": "healthy",
      "response_time_ms": 145,
      "endpoint": "https://aiai.example.com/api/v1/health",
      "last_check": "2026-02-27T14:30:00.100Z",
      "details": {
        "assistant_count": 35,
        "version": "1.0.0"
      }
    }
  }
}
```

**Response** (Degraded):
```json
{
  "overall": "degraded",
  "timestamp": "2026-02-27T14:30:00.123Z",
  "services": {
    "aiai": {
      "status": "degraded",
      "response_time_ms": 4500,
      "endpoint": "https://aiai.example.com/api/v1/health",
      "last_check": "2026-02-27T14:30:00.100Z",
      "error": "High response time",
      "details": {
        "assistant_count": 35,
        "version": "1.0.0"
      }
    }
  }
}
```

**Response** (Unhealthy):
```json
{
  "overall": "unhealthy",
  "timestamp": "2026-02-27T14:30:00.123Z",
  "services": {
    "aiai": {
      "status": "unhealthy",
      "response_time_ms": null,
      "endpoint": "https://aiai.example.com/api/v1/health",
      "last_check": "2026-02-27T14:30:00.100Z",
      "error": "Connection timeout",
      "details": null
    }
  }
}
```

### 9.2 AIAI Health Check Implementation

**Backend Pseudo-code**:
```python
async def check_aiai_health(aiai_url: str) -> dict:
    start_time = time.time()

    try:
        response = await http.get(
            f"{aiai_url}/api/v1/health",
            timeout=5.0
        )

        response_time_ms = (time.time() - start_time) * 1000

        if response.status_code == 200:
            if response_time_ms < 2000:
                status = "healthy"
            elif response_time_ms < 5000:
                status = "degraded"
            else:
                status = "unhealthy"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "response_time_ms": response_time_ms,
            "endpoint": f"{aiai_url}/api/v1/health",
            "last_check": datetime.utcnow().isoformat(),
            "details": response.json() if response.ok else None,
            "error": None if response.ok else f"HTTP {response.status_code}"
        }

    except TimeoutError:
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "endpoint": f"{aiai_url}/api/v1/health",
            "last_check": datetime.utcnow().isoformat(),
            "error": "Connection timeout",
            "details": None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "endpoint": f"{aiai_url}/api/v1/health",
            "last_check": datetime.utcnow().isoformat(),
            "error": str(e),
            "details": None
        }
```

---

## 10. Frontend Implementation

### 10.1 Component Architecture

```
HealthDashboard.vue
├── StatusBar.vue (NEW)
│   ├── StatusIndicator.vue
│   └── MetricDisplay.vue
├── HistoricalView.vue (NEW - Optional V1)
│   └── TimelineChart.vue
└── AssistantQuery.vue (EXISTING)
```

### 10.2 State Management

**Data Structure**:
```javascript
{
  // Current health status
  healthStatus: {
    overall: 'healthy',
    timestamp: '2026-02-27T14:30:00Z',
    services: {
      aiai: {
        status: 'healthy',
        response_time_ms: 145,
        last_check: '2026-02-27T14:30:00Z'
      }
    }
  },

  // Historical data (localStorage)
  healthHistory: [
    {
      timestamp: '2026-02-27T14:30:00Z',
      overall: 'healthy',
      aiai_status: 'healthy',
      aiai_response_time_ms: 145
    }
  ],

  // UI state
  loading: false,
  lastUpdateTime: Date.now(),
  autoRefreshInterval: 30000
}
```

### 10.3 API Service Methods

```javascript
// healthService.js

/**
 * Check health of all services
 */
async checkAll(backendUrl) {
  const response = await fetch(`${backendUrl}/api/health/all`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return await response.json();
}

/**
 * Store health data point in history
 */
storeHealthHistory(healthData) {
  const history = this.getHealthHistory();

  history.push({
    timestamp: healthData.timestamp,
    overall: healthData.overall,
    aiai_status: healthData.services.aiai.status,
    aiai_response_time_ms: healthData.services.aiai.response_time_ms
  });

  // Keep only last 24 hours
  const cutoff = Date.now() - (24 * 60 * 60 * 1000);
  const filtered = history.filter(h =>
    new Date(h.timestamp).getTime() > cutoff
  );

  localStorage.setItem('health_history', JSON.stringify(filtered));
}

/**
 * Get health history from localStorage
 */
getHealthHistory() {
  const data = localStorage.getItem('health_history');
  return data ? JSON.parse(data) : [];
}

/**
 * Calculate uptime percentage
 */
calculateUptime() {
  const history = this.getHealthHistory();

  if (history.length === 0) return null;

  const healthyCount = history.filter(h =>
    h.overall === 'healthy'
  ).length;

  return (healthyCount / history.length * 100).toFixed(2);
}
```

---

## 11. Error Handling & Edge Cases

### 11.1 Network Errors

**Scenario**: Backend proxy unreachable

**Handling**:
1. Show status as "Unknown" (gray)
2. Display error message: "Unable to connect to backend"
3. Continue retrying with exponential backoff
4. Max retry interval: 5 minutes

### 11.2 Timeout Errors

**Scenario**: Health check takes > 5 seconds

**Handling**:
1. Mark service as "Unhealthy" (red)
2. Display: "AIAI: timeout"
3. Log error for debugging
4. Retry on next interval

### 11.3 Partial Data

**Scenario**: Some services return data, others fail

**Handling**:
1. Display available data
2. Show "Unknown" for failed services
3. Calculate overall status from available data only

### 11.4 Browser localStorage Full

**Scenario**: Cannot store health history

**Handling**:
1. Clear oldest 50% of history data
2. If still failing, disable history storage
3. Continue showing real-time status
4. Log warning to console

---

## 12. Performance Considerations

### 12.1 Frontend

**Optimization Strategies**:
1. Throttle health checks to prevent API flooding
2. Cache health data for 10 seconds
3. Use requestIdleCallback for history storage
4. Limit localStorage writes to once per minute
5. Virtualize historical timeline if > 1000 points

### 12.2 Backend

**Optimization Strategies**:
1. Implement 10-second cache for health checks
2. Parallel health checks for multiple services
3. Circuit breaker pattern for failing services
4. Rate limiting: Max 10 checks/minute per client

### 12.3 Network

**Bandwidth Considerations**:
- Health check request: ~200 bytes
- Health check response: ~500 bytes
- Total per check: ~700 bytes
- Per hour: 700 bytes * 120 checks = 84 KB/hour
- Per day: ~2 MB/day

---

## 13. Testing Strategy

### 13.1 Unit Tests

**Coverage**:
- Health status aggregation logic
- Color determination from status
- Uptime calculation
- History storage/retrieval
- Timestamp formatting

### 13.2 Integration Tests

**Scenarios**:
1. Backend returns healthy status
2. Backend returns degraded status
3. Backend returns unhealthy status
4. Backend timeout
5. Backend connection refused
6. Partial service failures

### 13.3 End-to-End Tests

**User Flows**:
1. Widget loads → See current health status
2. Service degrades → Status bar updates to yellow
3. Service recovers → Status bar updates to green
4. Manual refresh → Status updates immediately
5. 24 hours pass → Old history data pruned

---

## 14. Accessibility (A11y)

### 14.1 Requirements

1. **Color Blindness**
   - Use icons in addition to colors
   - ✓ (checkmark) = healthy
   - ! (exclamation) = degraded
   - ✗ (X) = unhealthy
   - ? = unknown

2. **Screen Readers**
   - ARIA labels for all status indicators
   - Announce status changes
   - Semantic HTML structure

3. **Keyboard Navigation**
   - Tab through status components
   - Enter to expand detailed view
   - Escape to close expanded view

---

## 15. Monitoring & Analytics

### 15.1 Widget Analytics (Optional)

**Track (Client-side)**:
1. Widget load time
2. Health check failure rate
3. User interactions with status bar
4. Average response times
5. Most common error types

**Privacy**: All analytics stay client-side, no external tracking

---

## 16. Implementation Phases

### Phase 1: Minimal V1 (MVP)

**Deliverables**:
- ✅ Compact status bar (single line)
- ✅ AIAI health check (response time + availability)
- ✅ Color-coded status (green/yellow/red/gray)
- ✅ Auto-refresh every 30 seconds
- ✅ Manual refresh button
- ✅ Hide MCP service

**Timeline**: 1-2 days

### Phase 2: Historical Tracking

**Deliverables**:
- ✅ Store health history in localStorage
- ✅ Display 24-hour uptime percentage
- ✅ Show status timeline bar
- ✅ Count incidents in last 24h

**Timeline**: 1 day

### Phase 3: Enhanced V1

**Deliverables**:
- ✅ Click-to-expand detailed view
- ✅ Hover tooltips with metrics
- ✅ Last successful query timestamp
- ✅ Backend proxy status check

**Timeline**: 1 day

### Phase 4: MCP Integration (V2)

**Deliverables**:
- ✅ Enable MCP service monitoring
- ✅ MCP health check endpoint
- ✅ Multi-service status aggregation

**Timeline**: TBD (when MCP is ready)

---

## 17. Open Questions

### 17.1 Technical Decisions Needed

1. **Does AIAI have a dedicated `/health` endpoint?**
   - If not, can we use `/api/v1/assistants` as proxy?
   - Or should backend implement synthetic health check?

2. **Should we track query success rate in widget?**
   - Pro: Useful metric for service health
   - Con: Adds complexity, privacy concerns

3. **Should history data be per-user or global?**
   - Currently: Per browser (localStorage)
   - Alternative: Store in backend per user

### 17.2 Product Decisions Needed

1. **What is acceptable response time threshold?**
   - Current: < 2s healthy, 2-5s degraded, >5s unhealthy
   - Needs validation with real-world data

2. **Should we alert users when status degrades?**
   - Current: No (passive display only)
   - Alternative: Browser notification or banner

---

## 18. References

### 18.1 Related Documents
- [Widget README](README.md) - Architecture overview
- [Conversation Summary](../CONVERSATION_SUMMARY_2026-02-24.md) - Development history

### 18.2 API Documentation
- AIAI API: `https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com`
- Backend Proxy: `http://localhost:8080`

### 18.3 Design References
- [Vue 2 Documentation](https://v2.vuejs.org/)
- [Vuetify 2 Components](https://v2.vuetifyjs.com/)

---

## Appendix A: Current Backend Health Endpoint Analysis

**Current Implementation** (from code review):
```javascript
// apiService.js - healthService.checkAll()
const health = await healthService.checkAll(this.backendUrl);
```

**Observed Response Format**:
```json
{
  "overall": "healthy",
  "timestamp": "2026-02-27T14:30:00Z",
  "services": {
    "aiai": {
      "status": "healthy"
    },
    "mcp": {
      "status": "unknown"
    }
  }
}
```

**Gaps for V1**:
- ❌ No response time metrics
- ❌ No error details
- ❌ No assistant count
- ❌ No last_check timestamp per service

**Recommendation**: Update backend `/api/health/all` to include these fields.

---

## Appendix B: V1 vs Current Implementation Comparison

| Feature | Current | V1 Spec | Change Required |
|---------|---------|---------|-----------------|
| Status Cards | 3 large cards (1/3 width each) | Compact status bar | **Major redesign** |
| MCP Service | Visible with "Under Development" tag | Hidden | **Remove from UI** |
| Real Estate | Full row (33% width each) | Single line (~60px height) | **80% reduction** |
| Historical Data | None | 24-hour tracking | **New feature** |
| Response Time | Not displayed | Show in status bar | **Backend + frontend** |
| User Actions | Click (details dialog), Refresh button | No actions (read-only) | **Simplification** |
| Refresh Interval | 30s (configurable) | 30s (configurable) | **No change** |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-27 | AI Assistant Team | Initial specification based on user requirements |

