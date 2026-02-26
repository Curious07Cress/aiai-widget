# Widget Lab Toolkit Reference Guide

**Version:** 1.0.0
**Last Updated:** 2026-02-08
**Purpose:** Comprehensive reference for 3DEXPERIENCE widget/dashboard development using Widget Lab toolkits

---

## Executive Summary

Widget Lab provides a complete ecosystem of toolkits that dramatically simplify 3DEXPERIENCE platform development. These tools handle the complex authentication, CSRF tokens, tenant management, and API calls that would otherwise require significant development effort.

**Key Insight:** Using these toolkits reduces widget development time from weeks to days by eliminating boilerplate code for authentication, session management, and platform API calls.

---

## Table of Contents

1. [Toolkit Ecosystem Overview](#toolkit-ecosystem-overview)
2. [Frontend Development (Widgets)](#frontend-development-widgets)
3. [Backend Development](#backend-development)
4. [Authentication & Security](#authentication--security)
5. [Local Development Environment](#local-development-environment)
6. [CI/CD & Deployment](#cicd--deployment)
7. [Best Practices](#best-practices)
8. [Recommended Stack for Health Dashboard](#recommended-stack-for-health-dashboard)
9. [Quick Start Guide](#quick-start-guide)

---

## Toolkit Ecosystem Overview

```
+------------------------------------------------------------------+
|                    WIDGET LAB ECOSYSTEM                           |
+------------------------------------------------------------------+
|                                                                   |
|  FRONTEND (Widgets)              BACKEND (Services)               |
|  +------------------------+      +------------------------+       |
|  | platform-connectors    |      | http-platform-connector|       |
|  | (call3DSpace, etc.)    |      | (Node.js)              |       |
|  +------------------------+      +------------------------+       |
|  | 3ddashboard-utils      |      | py3dxhttp              |       |
|  | (widget mocking)       |      | (Python)               |       |
|  +------------------------+      +------------------------+       |
|  | 3dexperience-crossenv  |      | cas-client             |       |
|  | -sdk (shared API)      |      | (Authentication)       |       |
|  +------------------------+      +------------------------+       |
|                                                                   |
|  INFRASTRUCTURE                  TEMPLATES                        |
|  +------------------------+      +------------------------+       |
|  | ci-cd-best-practices   |      | backend-template       |       |
|  | (GitLab CI/CD)         |      | (Express + TypeScript) |       |
|  +------------------------+      +------------------------+       |
|  | local-dev-stack        |                                       |
|  | (Docker + nginx + CAS) |                                       |
|  +------------------------+                                       |
+------------------------------------------------------------------+
```

### Package Registry

All packages available from Widget Lab npm registry:

```bash
npm config set @widget-lab:registry https://itgit.dsone.3ds.com/api/v4/groups/774/-/packages/npm/
npm config set //itgit.dsone.3ds.com/api/v4/groups/774/-/packages/npm/:_authToken 61qKzSxnrLqyeyBy1H-o
```

---

## Frontend Development (Widgets)

### 1. Platform Connectors (`@widget-lab/platform-connectors`)

**Purpose:** The PRIMARY toolkit for widget development. Handles all platform communication complexity.

**Install:**
```bash
npm i @widget-lab/platform-connectors
```

**What it handles automatically:**
- Tenant selection and management
- Security context selection
- 3DSpace CSRF tokens
- 3DSwym CSRF tokens
- Service URL retrieval
- 3DCompass URL auto-detection (untrusted mode)

**Core Methods:**

| Method | Purpose |
|--------|---------|
| `initPlatformConnectors()` | Initialize module (MUST call first) |
| `call3DSpace(url, options)` | Call 3DSpace APIs with auto CSRF + SecurityContext |
| `call3DSwym(url, options)` | Call 3DSwym APIs with auto CSRF |
| `call3DCompass(url, options)` | Call 3DCompass APIs |
| `call3DWebServices(service, path, options)` | Call any 3DS service |
| `getCurrentTenantId()` | Get current tenant ID |
| `getCurrentSecurityContext()` | Get current security context |
| `get3DSpaceServiceUrl()` | Get 3DSpace base URL |
| `getTransientTicket()` | Get 3DPassport TGT for backend calls |

**Basic Usage:**
```javascript
import { initPlatformConnectors, call3DSpace } from "@widget-lab/platform-connectors";

// Initialize FIRST
initPlatformConnectors({
    allowTenantsSelection: true,
    allowSecurityContextSelection: true
});

// Then call APIs - CSRF and SecurityContext handled automatically!
const tasks = await call3DSpace("/resources/v1/modeler/tasks");
```

**Request Options:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| method | "GET" | HTTP method |
| data | {} | Request body |
| headers | {} | Additional headers |
| type | "json" | Response type (json/text/blob/arraybuffer/document) |
| useSecurityContext | true | Auto-add security context |
| useCsrf | true | Auto-add CSRF token |
| timeout | 25000 | Request timeout (ms) |
| returnHeader | false | Return headers with response |

---

### 2. 3DDashboard Utils (`@widget-lab/3ddashboard-utils`)

**Purpose:** Enables widget development OUTSIDE 3DDashboard (standalone mode) by mocking platform APIs.

**Install:**
```bash
npm i @widget-lab/3ddashboard-utils
```

**What it mocks:**
- `widget` object (preferences, events, body)
- WAFData (HTTP requests)
- TagNavigatorProxy (tagger)
- i3DXCompassServices

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `isTrusted()` | Check if running in 3DDashboard vs standalone |
| `requirejsPromise()` | Wrap RequireJS in Promise |
| `widget` | Unified widget object (works in both contexts) |

**Usage:**
```javascript
import { widget, isTrusted } from "@widget-lab/3ddashboard-utils";

// Works in 3DDashboard AND standalone!
widget.addEvent("onLoad", () => {
    console.log("Widget loaded!");
    console.log("Running in 3DDashboard:", isTrusted());
});
```

**Why this matters:** You can develop and debug widgets locally without deploying to 3DDashboard every time.

---

### 3. Cross-env SDK (`@widget-lab/3dexperience-crossenv-sdk`)

**Purpose:** Type-safe API client that works in BOTH browser widgets AND Node.js backends.

**Install:**
```bash
npm i @widget-lab/3dexperience-crossenv-sdk
```

**Key Benefit:** TypeScript autocompletion for all 3DEXPERIENCE APIs!

**Available Clients:**
- `SwymAPIClient` - 3DSwym operations
- `UsersGroupAPIClient` - User group management
- (More being added)

**Usage in Widget (with platform-connectors):**
```javascript
import { SwymAPIClient } from "@widget-lab/3dexperience-crossenv-sdk";
import { call3DSwym, initPlatformConnectors } from "@widget-lab/platform-connectors";

initPlatformConnectors({ /* ... */ });

const swymClient = new SwymAPIClient(call3DSwym);
const members = await swymClient.community.listMembers({
    communityId: "community-id",
    limit: 10
});
```

**Usage in Backend (with http-platform-connector):**
```javascript
import { SwymAPIClient } from "@widget-lab/3dexperience-crossenv-sdk";
import { HTTPPlatformConnector } from "@widget-lab/http-platform-connector";

const auth = HTTPPlatformConnector.createLoginAuth(env, "user", "pass");
const swymHTTPClient = await auth.create3DSwymClient();
const swymAPIClient = new SwymAPIClient(swymHTTPClient.request);
```

**Error Handling:**
```javascript
import { HTTPRequestError } from "@widget-lab/3dexperience-crossenv-sdk";

try {
    await swymClient.community.getCommunity({ id: "BAD_ID" });
} catch (e) {
    if (e instanceof HTTPRequestError) {
        console.log(await e.response.json());
    }
}
```

---

## Backend Development

### 1. Node.js HTTP Client (`@widget-lab/http-platform-connector`)

**Purpose:** Make authenticated 3DEXPERIENCE API calls from Node.js backends.

**Install:**
```bash
npm i @widget-lab/http-platform-connector
```

**Requires:** Node.js >= 22

**Authentication Methods:**

| Method | Use Case |
|--------|----------|
| `createLoginAuth(env, login, password)` | User credentials |
| `createOpennessAgentAuth(env, agentName, agentKey)` | Cloud automation (Openness Agent) |
| `createBatchAuth(env, batchUser, batchName, batchKey)` | On-premise automation |
| `createTransientTokenAuth(env)` | Backend impersonation with TGT |

**Environment Configuration:**
```javascript
// Cloud
const env = {
    compassURL: "https://eu1-compass.3dexperience.3ds.com/enovia",
    tenant: "R1132100206868"
};

// On-premise
const env = {
    compassURL: "https://your-server/3DSpace",
    tenant: "OnPremise",
    verify_ssl: false  // If needed
};

// With proxy
const env = {
    compassURL: "https://...",
    tenant: "...",
    proxy: {
        url: "http://proxy:8888",
        username: "user",  // optional
        password: "pass"   // optional
    }
};
```

**Service Clients:**

| Client | Features |
|--------|----------|
| `create3DSpaceClient()` | Auto CSRF + SecurityContext |
| `create3DSwymClient()` | Auto CSRF + throttling protection |
| `create3DDriveClient()` | Auto CSRF + file upload helper |
| `create3DPlanClient()` | X-Requested-With header |
| `createClient(serviceName)` | Generic client for any service |

**Example:**
```javascript
import { HTTPPlatformConnector } from "@widget-lab/http-platform-connector";

const auth = HTTPPlatformConnector.createLoginAuth(env, "user", "password");
const spaceClient = await auth.create3DSpaceClient();

// CSRF and SecurityContext handled automatically!
const tasks = await spaceClient.request("/resources/v1/modeler/tasks", {
    method: "POST",
    body: JSON.stringify({ data: [{ dataelements: { title: "New Task" }}]})
});
```

**Debugging:**
```javascript
// Log levels: 0=silly, 1=trace, 2=debug, 3=info, 4=warn, 5=error, 6=fatal
HTTPPlatformConnector.setLogLevel(2);  // debug - shows all HTTP requests
```

---

### 2. Python HTTP Client (`py3dxhttp`)

**Purpose:** Make authenticated 3DEXPERIENCE API calls from Python backends.

**Install:**
```bash
pip install py3dxhttp --index-url https://_authToken:61qKzSxnrLqyeyBy1H-o@itgit.dsone.3ds.com/api/v4/groups/774/-/packages/pypi/simple --extra-index-url https://pypi.org/simple
```

**Requires:** Python >= 3.10

**Authentication Methods:** Same as Node.js version

**Example:**
```python
import py3dxhttp

env = {
    "compass_url": "https://eu1-compass.3dexperience.3ds.com/enovia",
    "tenant": "R1132100206868"
}

auth = py3dxhttp.create_login_auth(env, login=username, password=password)
client = await auth.create_3d_space_client()
response = await client.request("/resources/v1/modeler/tasks", {"method": "GET"})
```

**Key Feature:** All methods are async - use `asyncio` or async functions.

---

### 3. Backend Template

**Purpose:** Pre-configured Node.js backend scaffold with Express + TypeScript.

**Features:**
- Express with `routing-controller` decorators
- TypeScript configured
- MongoDB ready
- CAS authentication integrated
- Environment-based configuration

**Start new backend:**
```bash
# Download template and rename
# Edit package.json with your names
npm install
npm run dev  # Development with hot reload
```

---

## Authentication & Security

### CAS Client (`@widget-lab/cas-client`)

**Purpose:** Add 3DPassport authentication to Express backends.

**Install:**
```bash
npm i @widget-lab/cas-client
```

**As Express Middleware:**
```javascript
import * as express from "express";
import { casFilter } from "@widget-lab/cas-client";

const app = express();

app.use(casFilter({
    publicUrl: "https://my.server.com/api/",
    passportUrl: "https://passport.3dexperience.3ds.com/cas",
    whitelist: ["/health", "/about"],  // No auth required
    token: {
        secretKey: "change-this-secret-key!",
        duration: "15m"
    }
}));

app.get("/protected", (req, res) => {
    // User info available!
    res.send(`Hello ${req.casAuth.userId}`);
});
```

**User Info Available:**
```typescript
req.casAuth = {
    userId: string,
    firstname?: string,
    lastname?: string,
    email?: string,
    pgt?: string  // Proxy Granting Ticket for backend-to-backend
};
```

**Agent Token Authentication:**
For service-to-service calls without user context:

```javascript
// Configuration
app.use(casFilter({
    // ...
    agentSecretKey: "32-char-minimum-secret-key!!!!!"
}));

// Client sends: Authorization: Bearer <JWT>
// Server gets:
req.casAgent = {
    agentId: string,   // from JWT 'sub'
    tokenId?: string   // from JWT 'jti'
};
```

---

## Local Development Environment

### Docker Stack for Local Development

**Purpose:** Run nginx reverse proxy + CAS client + MongoDB locally.

**Components:**
- `dc-http.yml` - HTTPS reverse proxy + CAS client
- `dc-mongo.yml` - MongoDB
- `dc-mongo-rs.yml` - MongoDB replica set

**Setup:**
```bash
# Login to Widget Lab Docker registry
docker login -u 3dswidgetlab
# password: dckr_pat_AFmsQ7nAG-jf0sgNW4iH1mYqt-A

# Start HTTPS + CAS
docker compose -f dc-http.yml up -d

# Start with MongoDB
docker compose -f dc-http.yml -f dc-mongo.yml up -d
```

**URL Mappings:**
| Local URL | Routes To |
|-----------|-----------|
| `http://localhost/app/...` | `http://localhost:8045/...` (your backend) |
| `https://localhost/app/...` | Same with HTTPS |
| `https://hostname/cas-app/...` | With CAS authentication |
| `https://localhost/uncors/api.site.com/...` | Bypass CORS |

**MongoDB:**
- Standard: `mongodb://localhost:27018/dbname`
- Replica Set: `mongodb://mongo1:27021,mongo2:27022,mongo3:27023/dbname`

---

## CI/CD & Deployment

### CI/CD Best Practices (`@widget-lab/ci-cd-best-practices`)

**Purpose:** Pre-built GitLab CI/CD configuration for widgets and npm packages.

**Install:**
```bash
npx @widget-lab/ci-cd-best-practices@latest
```

**Versioning Strategy:**
```bash
# Stable release
npm version patch|minor|major  # Creates tag v1.2.3

# Beta release (on feature branch)
npm version prepatch --preid=beta  # v1.2.4-beta.0
npm version pre                     # v1.2.4-beta.1

# Auto push with tags
# Add to package.json scripts:
"postversion": "git push --follow-tags"
```

**Deployment Targets:**
- **Widgets:** S3 bucket at versioned paths
- **npm packages:** GitLab npm registry + S3

**Configuration (`.gitlab-ci.yml`):**
```yaml
variables:
    PROJECT_TYPE: widget  # or 'npm'
    PROJECT_CONTEXT: widget-lab
    PROJECT_CATEGORY: widgets
    S3_BUCKET_NAME: your-bucket
    S3_REGION: eu-west-1
    BUILD: "YES"
    LINT: "YES"
```

---

## Best Practices

### Widget Development Best Practices

| ID | Practice | Recommendation |
|----|----------|----------------|
| WBP001 | **Code Hosting** | Use dedicated HTTPS server (S3, Azure), NOT 3DSpace |
| WBP002 | **UI Libraries** | Use standard libraries (Vuetify, Bootstrap), NOT OOTB WebUx/UIKIT |
| WBP003 | **Internationalization** | Use vue-i18n or 3DEXPERIENCE NLS APIs |
| WBP004 | **Preferences** | Declare via JS API, not HTML. Don't store large data |
| WBP005 | **Data Loading** | Use indexed data (federated search) for performance |
| WBP006 | **API Calls** | Wait for response before next request to same service |
| WBP007 | **DOM Manipulation** | Use frameworks (Vue, React), NOT getElementById |
| WBP008 | **RequireJS** | Always wrap in Promises |
| WBP009 | **Async Code** | Prefer async/await over promise chains |
| WBP010 | **JavaScript** | Use ESNext with transpilation (babel) |
| WBP011 | **Sensitive Data** | NEVER in widget code - use backend |

### Code Examples

**RequireJS with Promises:**
```javascript
// taggerProxy.js
const taggerPromise = new Promise((resolve) => {
    requirejs(["DS/TagNavigatorProxy/TagNavigatorProxy"], TagNavigatorProxy => {
        resolve(TagNavigatorProxy.createProxy({ widgetId: widget.id }));
    });
});
export const getTaggerProxy = () => taggerPromise;

// usage.js
const tagger = await getTaggerProxy();
```

**Widget Preferences via JS:**
```javascript
widget.addPreference({
    type: 'text',
    name: "apiEndpoint",
    label: "API Endpoint",
    defaultValue: 'https://api.example.com'
});
```

**Indexed Data for Performance:**
```javascript
const searchUrl = fedUrl + "/search";
const payload = {
    select_predicate: ["physicalid", "ds6w:identifier"],
    query: "your-query",
    source: ["3dspace"],
    tenant: "OnPremise"
};
const response = await call3DWebServices("federated", searchUrl, {
    method: "POST",
    data: JSON.stringify(payload)
});
```

---

## Recommended Stack for Health Dashboard

Based on analysis of all toolkits, here is the recommended stack:

### Frontend Widget

```
@widget-lab/platform-connectors     # Platform API calls
@widget-lab/3ddashboard-utils       # Development outside 3DDashboard
Vue.js 3 + Vuetify                  # UI framework (per best practices)
```

### Backend Health Service (if needed)

```
@widget-lab/http-platform-connector  # If calling 3DEXPERIENCE APIs
@widget-lab/cas-client               # If authentication required
Express + TypeScript                 # Per backend-template
```

### Development Environment

```
Docker stack (dc-http.yml)           # Local HTTPS + CAS
@widget-lab/ci-cd-best-practices     # GitLab CI/CD
```

### Why This Stack Works

1. **platform-connectors** handles ALL the complex platform authentication
2. **3ddashboard-utils** enables rapid local development without deployment
3. **Vue + Vuetify** is modern, supported, and not OOTB (per WBP002)
4. **Docker stack** provides local HTTPS with CAS authentication
5. **CI/CD** automates deployment to S3

---

## Quick Start Guide

### 1. Setup npm registry (one-time)

```bash
npm config set @widget-lab:registry https://itgit.dsone.3ds.com/api/v4/groups/774/-/packages/npm/
npm config set //itgit.dsone.3ds.com/api/v4/groups/774/-/packages/npm/:_authToken 61qKzSxnrLqyeyBy1H-o
```

### 2. Create new widget project

```bash
mkdir my-health-widget && cd my-health-widget
npm init -y
npm i @widget-lab/platform-connectors @widget-lab/3ddashboard-utils
npm i vue vuetify  # Or your preferred framework
```

### 3. Basic widget structure

```javascript
// main.js
import { initPlatformConnectors, call3DSpace } from "@widget-lab/platform-connectors";
import { widget } from "@widget-lab/3ddashboard-utils";

initPlatformConnectors({
    allowTenantsSelection: true,
    allowSecurityContextSelection: true
});

widget.addEvent("onLoad", async () => {
    try {
        const health = await call3DSpace("/api/health");
        renderDashboard(health);
    } catch (error) {
        console.error("Health check failed:", error);
    }
});
```

### 4. Setup CI/CD

```bash
npx @widget-lab/ci-cd-best-practices@latest
# Edit .gitlab-ci.yml with your settings
git add . && git commit -m "Initial widget setup"
git push
```

---

## Appendix: Package Summary

| Package | Purpose | When to Use |
|---------|---------|-------------|
| `@widget-lab/platform-connectors` | Widget platform calls | Every widget |
| `@widget-lab/3ddashboard-utils` | Widget mocking | Local widget dev |
| `@widget-lab/3dexperience-crossenv-sdk` | Typed API client | Type-safe API calls |
| `@widget-lab/http-platform-connector` | Node.js platform calls | Node.js backends |
| `py3dxhttp` | Python platform calls | Python backends |
| `@widget-lab/cas-client` | Express auth middleware | Protected backends |
| `@widget-lab/ci-cd-best-practices` | GitLab CI/CD | All projects |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-02-08 | Development Team | Initial creation from Widget Lab docs |
