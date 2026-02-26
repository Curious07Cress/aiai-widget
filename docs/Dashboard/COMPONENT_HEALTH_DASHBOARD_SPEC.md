# Component Health Dashboard Specification

**Version:** 0.2.0
**Status:** Draft
**Last Updated:** 2026-02-08
**Authors:** Development Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Goals and Non-Goals](#goals-and-non-goals)
3. [Target Audiences](#target-audiences)
4. [Architecture Decision: Widget Lab Toolkits](#architecture-decision-widget-lab-toolkits)
5. [Recommended Technology Stack](#recommended-technology-stack)
6. [Phase 1: Foundation](#phase-1-foundation)
7. [Phase 2: MCP Diagnostics](#phase-2-mcp-diagnostics)
8. [Phase 3: Full Monitoring](#phase-3-full-monitoring)
9. [Technical Specifications](#technical-specifications)
10. [API Contracts](#api-contracts)
11. [UI Wireframes](#ui-wireframes)
12. [Open Questions](#open-questions)

**Related Documents:**
- [WIDGET_LAB_TOOLKIT_REFERENCE.md](WIDGET_LAB_TOOLKIT_REFERENCE.md) - Complete toolkit documentation
- [3DEXPERIENCE_Widget_Development_Fundamentals_R2020x_v2.3.md](3DEXPERIENCE_Widget_Development_Fundamentals_R2020x_v2.3.md) - Platform fundamentals

---

## Executive Summary

The Component Health Dashboard provides real-time visibility into the health and status of the AI Assistant system components. It enables developers, QA, tech support, and ops teams to quickly diagnose issues, with a primary focus on MCP (Model Context Protocol) connectivity problems.

---

## Goals and Non-Goals

### Goals

- **Phase 1:** Get a working dashboard framework with basic server health checks
- **Phase 2:** Add MCP-specific diagnostics (the most problematic area)
- **Phase 3:** Full component monitoring with logs integration
- Enable all team roles to understand system status at a glance
- Reduce mean-time-to-diagnosis for production issues

### Non-Goals (Phase 1)

- Interactive actions (restart services, clear cache, etc.)
- Alerting and notifications
- Historical trend analysis
- Performance metrics beyond health status

---

## Target Audiences

| Audience | Primary Needs | Dashboard Usage |
|----------|---------------|-----------------|
| **Developers** | Debug failures, trace requests, understand component state | Deep-dive into MCP connections, view logs, check agent endpoints |
| **QA** | Verify system readiness, identify test blockers | Quick health check before test runs, identify flaky components |
| **Tech Support** | Diagnose customer issues, escalate appropriately | Status overview, identify which component is failing |
| **Ops** | Monitor production health, respond to incidents | Real-time status, service availability |

---

## Architecture Decision: Widget Lab Toolkits

### Recommendation: **Use Widget Lab Toolkits**

After thorough analysis of the Widget Lab ecosystem, I **strongly recommend** using these existing toolkits. They eliminate weeks of boilerplate development.

### Why Widget Lab Toolkits Are the Right Choice

| Concern | Without Toolkits | With Widget Lab Toolkits |
|---------|------------------|--------------------------|
| Authentication | Manual CAS/CSRF/token handling | Automatic (1 line init) |
| 3DSpace calls | 50+ lines of setup | `call3DSpace(url)` |
| Tenant management | Complex preference logic | Built-in dropdown |
| Local development | Must deploy to test | Works standalone |
| Security context | Manual header management | Automatic |
| Error handling | Custom implementation | Standardized |

### Cost-Benefit Analysis

**Development Time Savings:**
- Authentication setup: ~2 weeks -> 1 hour
- API call boilerplate: ~1 week -> 0 (handled)
- Local dev environment: ~3 days -> `docker compose up`
- Total estimated savings: **3+ weeks of development**

**Risk Reduction:**
- Authentication bugs: Eliminated (battle-tested code)
- CSRF issues: Eliminated (auto-handled)
- Session management: Eliminated (built-in)

### Decision: Use This Stack

```
FRONTEND (Widget)
+------------------------------------------+
| @widget-lab/platform-connectors          |  <- ALL platform calls
| @widget-lab/3ddashboard-utils            |  <- Local development
| Vue.js 3 + Vuetify (or similar)          |  <- UI framework
+------------------------------------------+

BACKEND (Health Service - if needed)
+------------------------------------------+
| @widget-lab/http-platform-connector      |  <- Node.js backend
| @widget-lab/cas-client                   |  <- Authentication
| Express + TypeScript                     |  <- Per backend-template
+------------------------------------------+

INFRASTRUCTURE
+------------------------------------------+
| Docker local-dev-stack                   |  <- Local HTTPS + CAS
| @widget-lab/ci-cd-best-practices         |  <- GitLab deployment
+------------------------------------------+
```

---

## Recommended Technology Stack

### Package Installation

**Step 1: Configure npm registry (one-time)**
```bash
npm config set @widget-lab:registry https://itgit.dsone.3ds.com/api/v4/groups/774/-/packages/npm/
npm config set //itgit.dsone.3ds.com/api/v4/groups/774/-/packages/npm/:_authToken 61qKzSxnrLqyeyBy1H-o
```

**Step 2: Install widget packages**
```bash
npm i @widget-lab/platform-connectors @widget-lab/3ddashboard-utils
npm i vue@3 vuetify  # UI framework (recommended per WBP002)
```

**Step 3: Install backend packages (if needed)**
```bash
npm i @widget-lab/http-platform-connector @widget-lab/cas-client
```

### File Structure (Updated)

```
ai-assembly-structure/
  dashboard/
    health-widget/
      package.json               # npm dependencies
      Widget.html                # 3DEXPERIENCE entry point
      src/
        main.js                  # Widget initialization
        App.vue                  # Main Vue component
        components/
          StatusCard.vue         # Health status card
          MCPDiagnostics.vue     # MCP panel
          ErrorLog.vue           # Error viewer
        services/
          healthService.js       # Health API calls
        styles/
          health-widget.css
      dist/                      # Built output
      nls/
        Widget_en.json
```

### Key Implementation Patterns

**Widget Initialization (platform-connectors):**
```javascript
import { initPlatformConnectors, call3DSpace } from "@widget-lab/platform-connectors";
import { widget } from "@widget-lab/3ddashboard-utils";

// Initialize platform connectors FIRST
initPlatformConnectors({
    allowTenantsSelection: true,
    allowSecurityContextSelection: true
});

// Add preferences via JS (per WBP004)
widget.addPreference({
    type: 'text',
    name: "healthApiUrl",
    label: "Health API URL",
    defaultValue: 'https://your-aiai-server.com'
});

// Widget lifecycle
widget.addEvent("onLoad", async () => {
    const apiUrl = widget.getValue("healthApiUrl");
    await loadHealthStatus(apiUrl);
});
```

**Health Service (using platform-connectors):**
```javascript
import { call3DSpace } from "@widget-lab/platform-connectors";

export const HealthService = {
    async checkHealth(baseUrl) {
        // CSRF and auth handled automatically!
        return await call3DSpace(`${baseUrl}/health`, {
            method: "GET",
            timeout: 10000
        });
    },

    async checkMCPStatus(baseUrl) {
        return await call3DSpace(`${baseUrl}/mcp/status`);
    },

    async getMCPTools(baseUrl) {
        return await call3DSpace(`${baseUrl}/mcp/tools`);
    },

    async getRecentErrors(baseUrl, limit = 10) {
        return await call3DSpace(`${baseUrl}/logs/errors?limit=${limit}`);
    }
};
```

**Local Development (without 3DDashboard):**
```javascript
import { isTrusted } from "@widget-lab/3ddashboard-utils";

// Code works BOTH in 3DDashboard AND standalone!
if (!isTrusted()) {
    console.log("Running in standalone mode - using mock data");
    // 3ddashboard-utils automatically mocks widget object
}
```

---

## Phase 1: Foundation

**Goal:** Working dashboard with basic health checks

### Components to Monitor

| Component | Health Check Method | Priority |
|-----------|---------------------|----------|
| AIAI API Server | `GET /health` | P0 |
| 3DSpace Connection | `GET /3dspace/health` | P0 |
| 3DPassport Auth | Token validation | P1 |
| Widget Registry | `GET /api/v1/status` | P1 |

### Widget Features

1. **Status Grid** - Visual overview of all components
   - Green: Healthy
   - Yellow: Degraded
   - Red: Unhealthy
   - Gray: Unknown/Checking

2. **Auto-refresh** - Poll every 30 seconds (configurable)

3. **Last Check Timestamp** - Show when status was last updated

4. **Manual Refresh** - Button to force immediate check

### Success Criteria

- [ ] Widget loads in 3DDashboard
- [ ] Shows status of AIAI API server
- [ ] Auto-refreshes every 30 seconds
- [ ] Handles offline/error states gracefully

---

## Phase 2: MCP Diagnostics

**Goal:** Deep visibility into MCP connectivity (primary pain point)

### MCP Components to Monitor

| Component | Health Check | Details Shown |
|-----------|--------------|---------------|
| MCP Proxy Server | Connection status | URL, port, uptime |
| MCP Tool Registry | Tools list | Available tools, versions |
| MCP Session State | Active sessions | Session count, oldest session |
| Individual MCP Tools | Tool availability | Per-tool status |

### MCP-Specific Features

1. **MCP Connection Test** - Verify proxy connectivity
2. **Tool Discovery** - List all registered MCP tools
3. **Session Inspector** - View active MCP sessions
4. **Error Log Viewer** - Recent MCP errors (from logs)

### Data Sources

- MCP Proxy REST API (see `docs/mcp_proxy.md`)
- Server logs (Grafana or direct file access)
- `AIAIWidgetEventsManager` for real-time MCP events

### Success Criteria

- [ ] Can see MCP proxy status
- [ ] Can list available MCP tools
- [ ] Can see recent MCP errors
- [ ] Helps diagnose "MCP not connecting" issues

---

## Phase 3: Full Monitoring

**Goal:** Comprehensive system visibility

### Additional Components

| Component | Health Check | Details |
|-----------|--------------|---------|
| LLM Connections | Model availability | Provider status, latency |
| Agent Endpoints | Agent health | Per-agent status |
| Prompt Registry | Template availability | Template count, versions |
| Checkpointer | State persistence | Storage status |
| Streaming Service | WebSocket status | Active streams |

### Log Integration

- **Grafana Integration** (if available)
  - Embed Grafana panels
  - Link to full Grafana dashboard

- **Direct Log Access** (fallback)
  - Tail recent log entries
  - Filter by component
  - Search for request_id

### Success Criteria

- [ ] Full component visibility
- [ ] Log viewing capability
- [ ] Can trace a request through the system

---

## Technical Specifications

### Widget Configuration

**Widget.html (minimal - preferences via JS per WBP004):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Component Health Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="dist/health-widget.css">
</head>
<body>
    <div id="app"></div>
    <script data-main="src/main" src="require.js"></script>
</body>
</html>
```

**Preferences via JavaScript (recommended):**
```javascript
// main.js
import { widget } from "@widget-lab/3ddashboard-utils";

// Declare preferences programmatically (avoids 3DDashboard cache issues)
widget.addPreference({
    type: 'text',
    name: "apiBaseUrl",
    label: "API Base URL",
    defaultValue: 'https://your-aiai-server.com'
});

widget.addPreference({
    type: 'text',
    name: "refreshInterval",
    label: "Refresh Interval (seconds)",
    defaultValue: '30'
});

widget.addPreference({
    type: 'boolean',
    name: "showLogs",
    label: "Show Log Panel",
    defaultValue: false
});
```

### Health Service (Using platform-connectors)

```javascript
// services/healthService.js
import { call3DSpace, call3DWebServices } from "@widget-lab/platform-connectors";

/**
 * Health Service using Widget Lab platform-connectors.
 * Authentication, CSRF, and tenant handling are automatic.
 */
export const HealthService = {

    /**
     * Check overall system health
     * @param {string} baseUrl - AIAI API base URL
     * @returns {Promise<Object>} Health status response
     */
    async checkSystemHealth(baseUrl) {
        try {
            const response = await call3DSpace(`${baseUrl}/health`, {
                method: "GET",
                timeout: 10000
            });
            return { status: "healthy", data: response };
        } catch (error) {
            return { status: "unhealthy", error: error.message };
        }
    },

    /**
     * Check MCP proxy status
     * @param {string} baseUrl - AIAI API base URL
     * @returns {Promise<Object>} MCP status response
     */
    async checkMCPStatus(baseUrl) {
        try {
            const response = await call3DSpace(`${baseUrl}/mcp/status`, {
                method: "GET",
                timeout: 15000  // MCP can be slow
            });
            return { status: "healthy", data: response };
        } catch (error) {
            return { status: "unhealthy", error: error.message };
        }
    },

    /**
     * List MCP tools
     * @param {string} baseUrl - AIAI API base URL
     * @returns {Promise<Object>} Tools list
     */
    async listMCPTools(baseUrl) {
        return await call3DSpace(`${baseUrl}/mcp/tools`);
    },

    /**
     * Get recent errors from logs
     * @param {string} baseUrl - AIAI API base URL
     * @param {number} limit - Max errors to return
     * @returns {Promise<Object>} Recent errors
     */
    async getRecentErrors(baseUrl, limit = 10) {
        return await call3DSpace(`${baseUrl}/logs/errors?limit=${limit}`);
    },

    /**
     * Perform all health checks in parallel
     * @param {string} baseUrl - AIAI API base URL
     * @returns {Promise<Object>} Aggregated health status
     */
    async checkAllComponents(baseUrl) {
        const [system, mcp, tools] = await Promise.allSettled([
            this.checkSystemHealth(baseUrl),
            this.checkMCPStatus(baseUrl),
            this.listMCPTools(baseUrl)
        ]);

        return {
            timestamp: new Date().toISOString(),
            system: system.status === 'fulfilled' ? system.value : { status: 'error' },
            mcp: mcp.status === 'fulfilled' ? mcp.value : { status: 'error' },
            tools: tools.status === 'fulfilled' ? tools.value : { tools: [] },
            overall: this._calculateOverallStatus(system, mcp)
        };
    },

    _calculateOverallStatus(system, mcp) {
        if (system.status === 'rejected' || system.value?.status === 'unhealthy') {
            return 'unhealthy';
        }
        if (mcp.status === 'rejected' || mcp.value?.status === 'unhealthy') {
            return 'degraded';
        }
        return 'healthy';
    }
};
```

### Vue Component Example (Phase 1)

```vue
<!-- components/StatusCard.vue -->
<template>
  <v-card :color="statusColor" class="status-card">
    <v-card-title>{{ component.name }}</v-card-title>
    <v-card-text>
      <div class="status-indicator">
        <v-icon :color="iconColor">{{ statusIcon }}</v-icon>
        {{ component.status }}
      </div>
      <div v-if="component.responseTime" class="response-time">
        {{ component.responseTime }}ms
      </div>
      <div v-if="component.error" class="error-message">
        {{ component.error }}
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  props: {
    component: {
      type: Object,
      required: true
    }
  },
  computed: {
    statusColor() {
      const colors = {
        healthy: 'green lighten-4',
        degraded: 'orange lighten-4',
        unhealthy: 'red lighten-4',
        unknown: 'grey lighten-3'
      };
      return colors[this.component.status] || colors.unknown;
    },
    iconColor() {
      const colors = {
        healthy: 'green',
        degraded: 'orange',
        unhealthy: 'red',
        unknown: 'grey'
      };
      return colors[this.component.status] || colors.unknown;
    },
    statusIcon() {
      const icons = {
        healthy: 'mdi-check-circle',
        degraded: 'mdi-alert',
        unhealthy: 'mdi-close-circle',
        unknown: 'mdi-help-circle'
      };
      return icons[this.component.status] || icons.unknown;
    }
  }
};
</script>
```

### Component Status Model

```javascript
// Component status structure
{
  "components": [
    {
      "name": "AIAI API Server",
      "id": "aiai-api",
      "status": "healthy",        // healthy | degraded | unhealthy | unknown
      "lastCheck": "2026-02-08T12:00:00Z",
      "responseTime": 45,         // ms
      "details": {
        "version": "1.2.3",
        "uptime": "5d 12h 30m"
      }
    },
    {
      "name": "MCP Proxy",
      "id": "mcp-proxy",
      "status": "unhealthy",
      "lastCheck": "2026-02-08T12:00:00Z",
      "error": "Connection refused",
      "details": {
        "url": "http://localhost:8080",
        "lastSuccessful": "2026-02-08T11:45:00Z"
      }
    }
  ],
  "overall": "degraded",
  "timestamp": "2026-02-08T12:00:00Z"
}
```

---

## API Contracts

### Required Backend Endpoints

These endpoints need to be implemented on the AIAI server:

#### GET /health

Overall system health check.

```json
// Response
{
  "status": "healthy",
  "version": "1.2.3",
  "uptime": "5d 12h 30m",
  "components": {
    "database": "healthy",
    "llm": "healthy",
    "mcp": "degraded"
  }
}
```

#### GET /mcp/status

MCP-specific health check.

```json
// Response
{
  "proxy": {
    "status": "connected",
    "url": "http://mcp-proxy:8080",
    "latency": 12
  },
  "sessions": {
    "active": 3,
    "total": 150
  },
  "tools": {
    "registered": 5,
    "available": 4
  }
}
```

#### GET /mcp/tools

List registered MCP tools.

```json
// Response
{
  "tools": [
    {
      "name": "solidworks_assembly_structure_tool",
      "version": "1.0.0",
      "status": "available",
      "server_id": "sw-mcp-001"
    }
  ]
}
```

#### GET /logs/errors?limit=N

Recent error logs.

```json
// Response
{
  "errors": [
    {
      "timestamp": "2026-02-08T11:55:00Z",
      "level": "ERROR",
      "component": "mcp-proxy",
      "message": "Connection timeout to MCP server",
      "request_id": "abc-123"
    }
  ]
}
```

---

## UI Wireframes

### Phase 1: Basic Health Grid

```
+----------------------------------------------------------+
|  Component Health Dashboard                    [Refresh]  |
+----------------------------------------------------------+
|                                                           |
|  +-------------+  +-------------+  +-------------+        |
|  | AIAI API    |  | 3DSpace     |  | 3DPassport  |        |
|  |   [GREEN]   |  |   [GREEN]   |  |   [YELLOW]  |        |
|  | 45ms        |  | 120ms       |  | Token exp.  |        |
|  +-------------+  +-------------+  +-------------+        |
|                                                           |
|  +-------------+  +-------------+                         |
|  | MCP Proxy   |  | Registry    |                         |
|  |   [RED]     |  |   [GREEN]   |                         |
|  | Conn. ref.  |  | 5 tools     |                         |
|  +-------------+  +-------------+                         |
|                                                           |
|  Last updated: 2026-02-08 12:00:00 (30s ago)              |
+----------------------------------------------------------+
```

### Phase 2: MCP Details Panel

```
+----------------------------------------------------------+
|  MCP Diagnostics                               [Test All] |
+----------------------------------------------------------+
|                                                           |
|  Proxy Status: [RED] DISCONNECTED                         |
|  URL: http://mcp-proxy:8080                               |
|  Last successful: 15 minutes ago                          |
|                                                           |
|  +------------------------------------------------------+ |
|  | Registered Tools                                     | |
|  +------------------------------------------------------+ |
|  | Tool Name                    | Status    | Server ID | |
|  | solidworks_assembly_tool     | [RED]     | sw-001    | |
|  | catia_assembly_tool          | [GRAY]    | cat-001   | |
|  +------------------------------------------------------+ |
|                                                           |
|  +------------------------------------------------------+ |
|  | Recent MCP Errors                                    | |
|  +------------------------------------------------------+ |
|  | 11:55:00 | Connection timeout to MCP server          | |
|  | 11:50:00 | Tool invocation failed: sw_assembly_tool  | |
|  | 11:45:00 | Session expired: sess-abc-123             | |
|  +------------------------------------------------------+ |
|                                                           |
+----------------------------------------------------------+
```

---

## Open Questions

1. **Authentication:** How should the dashboard authenticate to health endpoints?
   - Use existing 3DPassport token?
   - Separate service account?
   - Public health endpoints (no auth)?

2. **Log Access:** What is the preferred method for accessing logs?
   - Grafana API integration?
   - Direct log file access via REST API?
   - Log aggregation service?

3. **Deployment:** Where will the widget be hosted?
   - Same server as AIAI?
   - Separate widget server?
   - CDN?

4. **Backend Endpoints:** Do the proposed health endpoints exist?
   - Need to implement `/health`?
   - Need to implement `/mcp/status`?
   - Need to implement `/logs/errors`?

5. **Permissions:** Who should have access to the dashboard?
   - All platform users?
   - Admin role only?
   - Specific security context?

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.2.0 | 2026-02-08 | Added Widget Lab toolkit recommendations, updated architecture |
| 0.1.0 | 2026-02-08 | Initial draft |

---

## Next Steps

1. **Configure npm registry** for Widget Lab packages (one-time setup)
2. **Answer open questions** especially around auth and log access
3. **Verify backend endpoints** or plan their implementation
4. **Setup local dev environment** with Docker stack
5. **Create Phase 1 widget** using platform-connectors + Vue
6. **Test locally** using 3ddashboard-utils standalone mode
7. **Deploy to 3DDashboard** and validate

---

## References

### Widget Lab Documentation
- [WIDGET_LAB_TOOLKIT_REFERENCE.md](WIDGET_LAB_TOOLKIT_REFERENCE.md) - Complete toolkit reference
- npm registry: `https://itgit.dsone.3ds.com/api/v4/groups/774/-/packages/npm/`

### Key Packages
| Package | Purpose |
|---------|---------|
| `@widget-lab/platform-connectors` | Platform API calls (REQUIRED) |
| `@widget-lab/3ddashboard-utils` | Local development mocking |
| `@widget-lab/http-platform-connector` | Node.js backend calls |
| `@widget-lab/cas-client` | Backend authentication |
| `@widget-lab/ci-cd-best-practices` | GitLab CI/CD |

### Best Practices (WBP)
| ID | Summary |
|----|---------|
| WBP001 | Host widgets on dedicated HTTPS server, not 3DSpace |
| WBP002 | Use standard UI libraries (Vuetify, Bootstrap), not OOTB |
| WBP003 | Implement i18n with vue-i18n |
| WBP004 | Declare preferences via JS API, not HTML |
| WBP005 | Use indexed data (federated search) for performance |
| WBP007 | Use frameworks (Vue, React) for DOM manipulation |
| WBP008 | Wrap RequireJS calls in Promises |
| WBP009 | Prefer async/await over promise chains |
| WBP011 | Never store sensitive data in widget code |
