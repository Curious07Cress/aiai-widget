# Dashboard Project - Comprehensive Conversation Summary

**Date:** 2026-02-11
**Last Updated:** Based on conversation ending at line 3406

---

## 1. Project Overview

### What is Being Built
An **AI Operations Dashboard** for monitoring and managing the AI Assistant (AIAI) infrastructure. The dashboard provides:

1. **Health Monitoring** - Real-time health status of all system components
2. **Test AI Functionality** - Ability to test AI assistants with mock mode
3. **Supervision Access** - Direct links to supervision/operations console
4. **Settings Management** - Configure server URLs and display preferences

### Why It Was Built
To provide developers and operators with:
- Quick visibility into system health
- Easy testing of AI assistants without needing full integration
- Access to supervision tools for system management
- A single pane of glass for AI infrastructure operations

### Target Audience
- DevOps engineers managing AIAI infrastructure
- Developers testing AI assistants
- Operations staff monitoring system health
- Support teams troubleshooting issues

---

## 2. Architecture & Components

### Backend (FastAPI)
**Location:** `E:\repo\ai-assistant-assem-struct\dashboard\backend`

**Stack:**
- FastAPI (Python web framework)
- HTTPX (async HTTP client)
- Uvicorn (ASGI server)
- Pydantic (data validation)
- cachetools (session caching)

**Architecture Pattern:**
- RESTful API
- Service layer pattern (services/ directory)
- Router-based endpoints (routers/ directory)
- Configuration via environment variables
- Async/await for all I/O operations

### Frontend (Vue.js 3 + Vuetify)
**Location:** `E:\repo\ai-assistant-assem-struct\dashboard\health-widget`

**Stack:**
- Vue.js 3 (Composition API)
- Vuetify 3 (Material Design components)
- Vite (build tool)
- Widget Lab SDK (@widget-lab/platform-connectors, @widget-lab/3ddashboard-utils)

**Architecture Pattern:**
- Component-based architecture
- Reactive state management with refs
- Props for component communication
- Widget SDK for 3DDashboard integration

### Integration Points
1. **AIAI API** - Main AI Assistant service
2. **MLI (Machine Learning Interface)** - Dassault Systemes enterprise LLM
3. **MCP Proxy** - MCP tools registry
4. **Jaeger** - Distributed tracing
5. **Supervision API** - Infrastructure management
6. **3DPassport SSO** - Authentication service

---

## 3. Files Created/Modified

### Backend Files

#### Created Files

**`dashboard/backend/app/routers/aiai.py`**
- Proxy router for AIAI API calls
- Handles CORS and authentication issues
- Endpoints:
  - `GET /api/aiai/assistants` - List available assistants
  - `POST /api/aiai/assistants/{name}/submit` - Submit test prompts

**`dashboard/backend/app/services/passport_auth.py`**
- 3DPassport SSO authentication service
- Session caching (30 min TTL)
- Handles CASTGC cookie flow
- Methods:
  - `get_authenticated_client()` - Returns authenticated HTTP client
  - `_authenticate()` - Performs SSO login flow
  - `clear_session()` - Clears cached session

**`dashboard/backend/app/services/supervision.py`**
- Supervision URL parsing and operations
- Functions:
  - `parse_aiai_url()` - Extract sandbox ID, region, environment
  - `derive_supervision_url()` - Build supervision URLs
  - `get_supervision_health()` - Check supervision endpoint
  - `build_operation_request()` - Build restart/control requests
  - `parse_sandbox_info()` - Parse sandbox dashboard JSON
  - `get_aiai_vms_from_sandbox()` - Extract AIAI VM details

**`dashboard/backend/app/routers/supervision.py`**
- API endpoints for supervision operations
- Endpoints:
  - `GET /api/supervision/derive` - Derive supervision URLs
  - `GET /api/supervision/health` - Check supervision health
  - `GET /api/supervision/operations` - List available operations
  - `GET /api/supervision/operations/build` - Build operation request
  - `POST /api/supervision/sandbox/parse` - Parse sandbox JSON
  - `POST /api/supervision/sandbox/aiai-vms` - Extract AIAI VMs

#### Modified Files

**`dashboard/backend/app/config.py`**
- Added passport authentication settings
- Fields:
  - `passport_username: Optional[str]`
  - `passport_password: Optional[str]`

**`dashboard/backend/app/main.py`**
- Registered new routers (aiai, supervision)
- CORS middleware configuration

**`dashboard/backend/app/routers/__init__.py`**
- Exported new routers

**`dashboard/backend/app/services/health_aggregator.py`**
- Modified to treat 302 redirects as "OK (requires auth)"

**`dashboard/backend/app/services/mli_service.py`**
- Modified `_get_auth_token()` to return tuple `(token, auth_required)`

**`dashboard/backend/.env`**
- Added passport credentials (commented)
- Set CORS to wildcard for development

**`dashboard/backend/requirements.txt`**
- Added `cachetools>=5.3.0`

### Frontend Files

#### Created Files

**`dashboard/health-widget/src/components/TestAI.vue`**
- Component for testing AI assistants
- Features:
  - Assistant dropdown (fetched from AIAI)
  - Test prompt input (up to 100 chars)
  - Run test button
  - Result display with copy button
  - Status indicators (running/success/failed)
- Key request format:
  ```javascript
  {
    prompt: testPrompt.value,
    mock: true,
    'llm.stream': false,
    'llm.model': 'mistralai/mistral-small-2506',
    conversation_id: `test-${Date.now()}`,
    prompt_language: 'en',
    context: {
      message: {
        selected_dimensions: {
          app_id: ['SWXCSWK_AP']
        }
      }
    }
  }
  ```

**`dashboard/health-widget/src/components/SupervisionInfo.vue`**
- Component for supervision console access
- Features:
  - Display sandbox ID, region, environment
  - Service Instance ID with copy button
  - Admin tenant (mixed case for API)
  - Button to open React Ops console
  - VM details URL

**`dashboard/health-widget/src/components/SettingsPanel.vue`**
- Settings dialog for configuration
- Features:
  - Environment selector (Local/Staging/Custom)
  - AIAI Server URL input
  - Dashboard Backend URL input
  - Auto-refresh interval slider
  - Display options toggles
  - Reset/Cancel/Save buttons

#### Modified Files

**`dashboard/health-widget/src/App.vue`**
- Integrated TestAI component
- Integrated SupervisionInfo component
- Integrated SettingsPanel component
- Passes settings props to child components

**`dashboard/health-widget/src/widgetInit.js`**
- Updated default AIAI URL to staging environment
- Widget preference management

---

## 4. Key Technical Decisions

### 1. Backend Proxy Pattern
**Decision:** Route all AIAI/external API calls through dashboard backend
**Reason:** Avoid CORS issues and handle SSO authentication centrally
**Impact:** Frontend code simplified, authentication managed in one place

### 2. AIAI API Uses POST for Listing Assistants
**Decision:** Use POST instead of GET for `/api/v1/assistants`
**Reason:** AIAI deprecated GET endpoint, requires POST with empty body
**Impact:** Non-intuitive but required for compatibility
**Code:**
```python
response = await client.post(
    url,
    params=params,
    json={},  # Empty body required
    headers={"Content-Type": "application/json"}
)
```

### 3. Mixed Case Service Instance ID
**Decision:** Maintain two formats for Service Instance ID
**Reason:** UI URLs need uppercase, API calls need mixed case
**Formats:**
- UI: `SbxAIAssistantInfraYIVWVBLEUW1` (all uppercase)
- API: `SbxAIAssistantInfraYIVWVBLeuw1` (sandbox upper, region lower)

### 4. Treat 302 Redirects as "OK"
**Decision:** Health checks return OK status for 302 redirects
**Reason:** Services behind SSO redirect to 3DPassport, but are healthy
**Message:** "Reachable (requires auth)"

### 5. Session Caching for SSO
**Decision:** Cache authenticated HTTP clients for 30 minutes
**Reason:** Avoid repeated SSO login flows, improve performance
**Library:** cachetools.TTLCache

### 6. vmInstanceName as Constant
**Decision:** Hardcode `vmInstanceName=AIWFL_EXEC_0`
**Reason:** Standard value for AIAI workflow executor VM
**Note:** May need to become configurable if multiple VMs exist

### 7. Widget SDK Integration
**Decision:** Use Widget Lab SDK for 3DDashboard deployment
**Reason:** Standard approach for 3DDashboard widgets
**Storage:** Widget preferences persist settings locally

---

## 5. Current State

### What Works

✅ **Health Monitoring**
- All service health checks functional
- 302 redirects handled correctly
- Health aggregation working

✅ **Test AI Feature**
- Assistant dropdown loads from AIAI
- Test submission works with mock mode
- Results display correctly
- Copy to clipboard functional

✅ **Settings Panel**
- Environment selection (Local/Staging/Custom)
- URL configuration persisted
- Auto-refresh working

✅ **Supervision URL Derivation**
- Parse AIAI URL correctly
- Derive supervision URLs
- Build admin tenant correctly
- Generate React Ops URLs

✅ **Authentication**
- 3DPassport SSO working
- Session caching functional
- Credentials from .env file

### What Was Being Worked On

🔄 **Supervision API Discovery**
The conversation ended with trying to find the API endpoint that returns the full sandbox dashboard JSON. This JSON contains:
- VM instance IDs (e.g., `i-8d35997f`)
- IP addresses (public/private)
- VM status and revisions
- All service details

**Last Request:** User asked to analyze HAR (HTTP Archive) data to find which API endpoint returns sandbox information, but the file was too large to attach.

**Known Data Points:**
- Sandbox JSON contains everything needed
- Example data structure received
- Need to find API URL pattern (likely `/supervision/api/v7/...`)

🔄 **Restart Operations**
- Operation structure discovered from Chrome DevTools:
  ```json
  {
    "resourceOperation": {
      "name": "maintenance",
      "xmlScript": "RestartProxyCas",
      "displayName": "Restart Proxy CAS",
      "maxDuration": 300,
      "parameters": []
    }
  }
  ```
- URL pattern known: `/supervision/api/v7/resourceoperations/resource?environment=DEVENV&adminTenant={tenant}&resourceId={vm_id}`
- Backend can build operation requests
- Need VM instance ID from sandbox JSON

---

## 6. Next Steps

### Immediate (To Continue Current Work)

1. **Find Sandbox Dashboard API Endpoint**
   - Analyze browser HAR data to find API endpoint
   - Likely patterns:
     - `GET /supervision/api/v7/sandboxes/{sandbox_id}`
     - `GET /supervision/api/v7/environments/DEVENV/tenants/{admin_tenant}`
     - `GET /supervision/api/v7/resources?adminTenant={admin_tenant}`
   - Add backend endpoint to fetch sandbox data programmatically

2. **Complete VM Instance ID Lookup**
   - Use sandbox API to get VM details
   - Extract AIAI_WFLE_EXEC_0 instance ID automatically
   - Cache results (VMs don't change often)

3. **Implement Restart Operations UI**
   - Add UI component for operations
   - List available VMs
   - Show restart buttons
   - Handle operation submission
   - Show operation status/progress

### Future Enhancements

4. **Enhanced Health Checks**
   - Query specific agent status
   - Check LLM connectivity
   - Verify MCP tool availability
   - Database connection checks

5. **Failure Locator Integration**
   - Connect Jaeger traces
   - Request flow visualization
   - Error path highlighting

6. **Error Log Panel**
   - Recent error logs
   - Error filtering
   - Error details expansion

7. **MCP Tools Registry**
   - Show registered tools
   - Tool health status
   - Tool usage statistics

8. **Deployment**
   - Package as 3DDashboard widget
   - Deploy to staging environment
   - Production deployment

---

## 7. Important Code Patterns

### Authentication Flow

**3DPassport SSO:**
```python
# 1. Hit AIAI to get redirected
response = await client.get(f"{aiai_url}/health")

# 2. Extract Passport URL from redirect
location = response.headers.get("location")

# 3. Get login ticket
response = await client.get(f"{passport_url}/login?action=get_auth_params")
lt = response.json().get("lt")

# 4. Login with credentials
response = await client.post(
    f"{passport_url}/login",
    data={"lt": lt, "username": username, "password": password}
)

# 5. Get CASTGC cookie (proves authentication)

# 6. Get service ticket for AIAI

# 7. Access AIAI with authenticated session
```

### API Request Patterns

**List Assistants (POST, not GET):**
```python
response = await client.post(
    f"{aiai_url}/api/v1/assistants",
    params={"assistant_namespace": "ai-assembly-structure"},
    json={},  # Empty body required
    headers={"Content-Type": "application/json"}
)
```

**Submit Test Prompt:**
```python
response = await client.post(
    f"{aiai_url}/api/v1/assistants/{assistant}/submit",
    json={
        "prompt": "test prompt",
        "mock": True,
        "llm.stream": False,
        "llm.model": "mistralai/mistral-small-2506",
        "conversation_id": f"test-{timestamp}",
        "prompt_language": "en",
        "context": {
            "message": {
                "selected_dimensions": {
                    "app_id": ["SWXCSWK_AP"]
                }
            }
        }
    }
)
```

**Supervision Operation:**
```python
url = f"{supervision_api_url}/resourceoperations/resource"
params = {
    "environment": "DEVENV",
    "adminTenant": "SbxAIAssistantInfraYIVWVBLeuw1",  # Mixed case!
    "resourceId": "i-8d35997f"
}
payload = {
    "resourceOperation": {
        "name": "maintenance",
        "xmlScript": "RestartProxyCas",
        "displayName": "Restart Proxy CAS",
        "maxDuration": 300,
        "parameters": []
    }
}
response = await client.post(url, params=params, json=payload)
```

### Data Flow Patterns

**Frontend → Backend → AIAI:**
```
Frontend (TestAI.vue)
  ↓ fetch(`${backendUrl}/api/aiai/assistants`)
Backend (aiai.py router)
  ↓ get_authenticated_client()
Auth Service (passport_auth.py)
  ↓ [cached client or fresh auth]
Backend makes request
  ↓ client.post(aiai_url)
AIAI API
  ↓ response
Backend
  ↓ return response.json()
Frontend receives and displays
```

### URL Parsing Pattern

**Parse AIAI URL:**
```python
# Input: https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com
pattern = r"devops([a-z]+)\d+-([a-z]+\d+)-[a-z]+\d+-aiai\.([a-z0-9-]+)\.3ds\.com"

# Extracted:
# - sandbox_id: "yivwvbl"
# - region: "euw1"
# - environment: "3dx-staging"

# Derived:
# - admin_tenant: "SbxAIAssistantInfra" + sandbox.upper() + region.lower()
#   = "SbxAIAssistantInfraYIVWVBLeuw1"
# - service_instance_id: "SbxAIAssistantInfra" + sandbox.upper() + region.upper()
#   = "SbxAIAssistantInfraYIVWVBLEUW1"
```

---

## 8. Configuration

### Backend Environment Variables

**File:** `dashboard/backend/.env`

```bash
# Server Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DASHBOARD_ENV=development

# CORS (use * for development)
DASHBOARD_CORS_ORIGINS=*

# Service URLs
DASHBOARD_AIAI_BASE_URL=https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com
DASHBOARD_MLI_BASE_URL=https://euw1-devprol50-mlinference.3dx-staging.3ds.com
DASHBOARD_MCP_PROXY_URL=http://localhost:3000
DASHBOARD_JAEGER_URL=https://eu2-supstg-disttracing.3dx-staging.3ds.com

# Health Check Settings
DASHBOARD_HEALTH_CHECK_TIMEOUT=10

# 3DPassport SSO (required for authenticated operations)
# DASHBOARD_PASSPORT_USERNAME=your_username
# DASHBOARD_PASSPORT_PASSWORD=your_password
```

### Frontend Settings

**File:** `dashboard/health-widget/src/widgetInit.js`

Predefined environments:
- **Local:** localhost URLs
- **Staging:** 3dx-staging.3ds.com URLs
- **Custom:** User-defined URLs

Default settings:
```javascript
{
  apiBaseUrl: 'https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com',
  backendUrl: 'http://localhost:8080',
  refreshInterval: 30,  // seconds
  showMCPDetails: true,
  showErrorLog: false
}
```

### Running the Applications

**Backend:**
```bash
cd dashboard/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8080
```

**Frontend:**
```bash
cd dashboard/health-widget
npm install
npm run dev
# Opens on http://localhost:5173
```

---

## 9. Outstanding Issues

### 1. Sandbox API Endpoint Unknown
**Issue:** Don't know the API endpoint to fetch sandbox JSON programmatically
**Impact:** Can't automatically get VM instance IDs
**Workaround:** Manual copy-paste of sandbox JSON to `/api/supervision/sandbox/aiai-vms`
**Next Step:** Analyze HAR data to find API endpoint

### 2. vmID Not Derivable
**Issue:** AWS instance ID (e.g., `i-8d35997f`) varies per deployment
**Impact:** Can't build supervision operation URLs without it
**Solution:** Must fetch from sandbox API (blocked on issue #1)

### 3. SSO Required for Most Operations
**Issue:** Most endpoints require 3DPassport authentication
**Impact:** Must configure credentials in .env
**Security:** Credentials in .env file (not ideal for production)
**Future:** Need proper secrets management

### 4. CORS Configuration
**Issue:** Wildcard CORS (`*`) is used for development
**Impact:** Not suitable for production
**Next Step:** Configure specific origins for production

### 5. Error Handling in Frontend
**Issue:** Some error messages are generic
**Impact:** Harder to debug issues
**Improvement:** Add more specific error messages

---

## 10. API Endpoints Reference

### Health Endpoints
```
GET /api/health/all
  - Returns health status of all services
  - Response: {overall: "ok", services: {...}}

GET /api/health/aiai
  - AIAI API health only

GET /api/health/mli
  - MLI service health only

GET /api/health/mcp
  - MCP Proxy health only

GET /api/health/jaeger
  - Jaeger tracing health only
```

### AIAI Proxy Endpoints
```
GET /api/aiai/assistants?assistant_namespace=ai-assembly-structure
  - List available assistants
  - Returns: [{assistant__id, assistant__name, ...}]

POST /api/aiai/assistants/{name}/submit?assistant_namespace=ai-assembly-structure
  - Submit test prompt to assistant
  - Body: {prompt, mock, llm.model, ...}
  - Returns: {response: "..."}
```

### Supervision Endpoints
```
GET /api/supervision/derive?aiai_url={url}
  - Derive supervision URLs from AIAI URL
  - Returns: {sandbox_id, region, service_instance_id, admin_tenant, react_ops_url, ...}

GET /api/supervision/health?aiai_url={url}
  - Check supervision endpoint reachability
  - Returns: {reachable, requires_auth, error, ...}

GET /api/supervision/operations
  - List available supervision operations
  - Returns: [{key, name, display_name, xml_script}]

GET /api/supervision/operations/build?aiai_url={url}&resource_id={vm_id}&operation={op}
  - Build supervision operation request
  - Returns: {url, payload, method}

POST /api/supervision/sandbox/parse
  - Parse full sandbox dashboard JSON
  - Body: {sandbox dashboard JSON}
  - Returns: {sandbox_id, region, status, services: [...]}

POST /api/supervision/sandbox/aiai-vms
  - Extract AIAI VMs from sandbox JSON
  - Body: {sandbox dashboard JSON}
  - Returns: [{name, instance_id, public_ip, ...}]
```

---

## 11. Data Structures

### Health Check Response
```python
{
    "overall": "ok" | "degraded" | "down",
    "services": {
        "aiai_api": {
            "status": "ok" | "degraded" | "down",
            "latency_ms": 123,
            "message": "Healthy" | "Reachable (requires auth)" | "Connection refused",
            "details": {}
        },
        "mli": {...},
        "mcp_proxy": {...},
        "jaeger": {...}
    }
}
```

### Assistant Object
```python
{
    "assistant__id": "asmstruct_1.0.0",
    "assistant__name": "asmstruct",
    "assistant__namespace": "ai-assembly-structure",
    "assistant__description": "This assistant creates and modifies assembly structures...",
    "assistant__version": "1.0.0",
    "assistant__is_companion": false,
    "companion__display_name": "Assembly Structure",
    "assistant__packaging__name": "Assembly Structure",
    "assistant__packaging__description": "Assembly Structure"
}
```

### Supervision Info
```python
{
    "sandbox_id": "yivwvbl",
    "region": "euw1",
    "environment": "3dx-staging",
    "base_url": "https://eu2-supstg-realtime.3dx-staging.3ds.com",
    "service_instance_id": "SbxAIAssistantInfraYIVWVBLEUW1",  # UI format (all caps)
    "admin_tenant": "SbxAIAssistantInfraYIVWVBLeuw1",        # API format (mixed)
    "supervision_url": "https://.../supervision",
    "supervision_api_url": "https://.../supervision/api/v7",
    "react_ops_url": "https://.../react/ops/group=DEVENV/serviceInstanceID=...",
    "vm_instance_name": "AIWFL_EXEC_0",
    "vm_details_url": "https://.../react/ops/.../vmInstanceName=AIWFL_EXEC_0"
}
```

### Sandbox Dashboard JSON (Partial)
```json
{
    "ID": "YIVWVBL",
    "Status": "active",
    "Deployment Region": "euw1",
    "Parent Cluster": "devprol50",
    "Sandboxed Services": [
        {
            "Admin AIAssistantInfra": "SbxAIAssistantInfraYIVWVBLeuw1",
            "Name": "AIAssistantInfra_...",
            "Status": "active",
            "VMs": [
                {
                    "Name": "AIWFL_EXEC_0",
                    "Instance ID": "i-8d35997f",
                    "Public IP": "10.0.144.216",
                    "Private IP": "10.0.142.177"
                },
                {
                    "Name": "ScalableLB_0",
                    "Instance ID": "i-7a696ee2",
                    "Public IP": "171.33.70.157"
                }
            ]
        }
    ]
}
```

---

## 12. Common Operations

### Test an AI Assistant
1. Open dashboard
2. Select assistant from dropdown
3. Enter test prompt
4. Click "Test" button
5. View result, copy if needed

### Change AIAI Server URL
1. Click gear icon (settings)
2. Select environment or enter custom URL
3. Click "Save"
4. Dashboard reloads with new URL

### Access Supervision Console
1. SupervisionInfo card shows derived URLs
2. Click "Open Supervision Console" button
3. Opens React Ops dashboard in new tab
4. Login with 3DPassport if needed

### Restart a Service (Manual)
1. Get sandbox JSON from dashboard
2. POST to `/api/supervision/sandbox/aiai-vms`
3. Extract VM instance ID
4. GET `/api/supervision/operations/build?resource_id={id}&operation=restart_proxy_cas`
5. Use returned URL and payload to POST operation
6. (Requires authentication)

---

## 13. Testing & Development

### Backend Testing
```bash
cd dashboard/backend

# Test supervision URL parser
python -c "
from app.services.supervision import derive_supervision_url
info = derive_supervision_url('https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com')
print(f'Service ID: {info.service_instance_id}')
print(f'Admin Tenant: {info.admin_tenant}')
"

# Test imports
python -c "from app.main import app; print('OK')"

# Run backend
python -m uvicorn app.main:app --reload --port 8080
```

### Frontend Testing
```bash
cd dashboard/health-widget

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

### Manual Testing Checklist
- [ ] Health checks show correct status
- [ ] Settings persist after refresh
- [ ] Test AI loads assistants
- [ ] Test AI submits and shows results
- [ ] Supervision URLs derived correctly
- [ ] Copy buttons work
- [ ] All links open in new tabs

---

## 14. Deployment Notes

### Widget Deployment (3DDashboard)
**Not yet completed**, but planned steps:
1. Build frontend: `npm run build`
2. Package with Widget Lab toolkit
3. Register widget in 3DDashboard
4. Configure widget permissions
5. Deploy to target environment

### Backend Deployment
**Not yet completed**, but considerations:
- Use production WSGI server (not uvicorn --reload)
- Configure proper CORS origins (not *)
- Store secrets in secure vault (not .env)
- Set up logging to central service
- Configure health check endpoints for monitoring
- Use reverse proxy (nginx/Apache)

---

## 15. Known Limitations

1. **No Real-Time Updates** - Must click refresh button
2. **No Historical Data** - Only shows current state
3. **Limited Error Details** - Some errors show generic messages
4. **No Metrics/Charts** - Just status indicators
5. **Manual Sandbox JSON** - Can't fetch programmatically yet
6. **Single VM Assumption** - Assumes AIWFL_EXEC_0 is only executor
7. **No Operation History** - Can't see past restart operations
8. **No Alerts** - No notifications when services go down

---

## 16. Security Considerations

### Authentication
- 3DPassport SSO credentials in .env (development only)
- Session caching reduces login frequency
- No token storage in frontend
- All auth handled server-side

### CORS
- Wildcard (*) for development
- Must restrict in production
- Credentials mode disabled with wildcard

### Sensitive Data
- Sandbox JSON contains IP addresses
- VM instance IDs are internal identifiers
- Service URLs may be considered sensitive

### Future Improvements
- Move to OAuth2/OpenID Connect
- Use Azure Key Vault or similar for secrets
- Implement RBAC for operations
- Audit log for all operations

---

## 17. Dependencies

### Backend
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
pydantic>=2.4.0
pydantic-settings>=2.0.0
cachetools>=5.3.0
python-dotenv>=1.0.0
```

### Frontend
```
vue@^3.3.4
vuetify@^3.3.15
@mdi/font@^7.2.96
@widget-lab/platform-connectors
@widget-lab/3ddashboard-utils
vite@^4.4.9
```

---

## 18. Glossary

**AIAI** - AI Assistant Infrastructure, the main service hosting AI assistants

**MLI** - Machine Learning Interface, Dassault Systemes' enterprise LLM service

**MCP** - Model Context Protocol, for AI tool integration

**3DPassport** - Dassault Systemes' SSO authentication service

**CASTGC** - CAS Ticket Granting Cookie, proves SSO authentication

**Sandbox** - Isolated deployment environment for testing

**Admin Tenant** - Service instance identifier in supervision system

**React Ops** - Web UI for supervision console

**vmInstanceName** - Name of VM in sandbox (e.g., AIWFL_EXEC_0)

**resourceId** - AWS instance ID (e.g., i-8d35997f)

**Widget Lab** - 3DDashboard widget development toolkit

**Service Instance ID** - Unique identifier for sandboxed service

---

## 19. Useful Commands

```bash
# Start backend
cd dashboard/backend && python -m uvicorn app.main:app --reload --port 8080

# Start frontend
cd dashboard/health-widget && npm run dev

# Install swym2py for wiki search
pip install -e Swym2Py/swym2py

# Search wiki (requires password)
python Swym2Py/swym2py/wiki_search_v2.py --user yiv --search "supervision API"

# Test supervision URL parsing
cd dashboard/backend && python -c "from app.services.supervision import derive_supervision_url; print(derive_supervision_url('your-aiai-url'))"

# Check backend health
curl http://localhost:8080/api/health/all

# List assistants
curl http://localhost:8080/api/aiai/assistants?assistant_namespace=ai-assembly-structure

# Derive supervision URL
curl "http://localhost:8080/api/supervision/derive?aiai_url=https://..."
```

---

## 20. Wiki Search Terms (For Finding Supervision API)

Based on the conversation, these search terms were suggested to find documentation:

- "realtime API"
- "supervision API"
- "React Ops"
- "service instance control"
- "serviceInstanceID"
- "VM control"
- "vmInstanceName"
- "restart service"
- "stop service"
- "DEVENV monitoring"
- "3DSpace supervision"
- "sandbox monitoring"

Key questions to answer:
- What REST endpoints does /supervision expose?
- Can we GET service status programmatically?
- Can we POST to restart/stop/start services?
- What authentication is required for API calls?

---

## 21. Contact & Resources

**Project Location:** `E:\repo\ai-assistant-assem-struct\dashboard`

**Key People:**
- User: yiv (trigram)
- Colleague helped with supervision API discovery

**Related Documentation:**
- CLAUDE.md (coding guidelines) - `E:\repo\ai-assistant-assem-struct\.claude\CLAUDE.md`
- Swym2Py README - `E:\repo\ai-assistant-assem-struct\Swym2Py\README.md`
- Dashboard MVP Spec - `E:\repo\ai-assistant-assem-struct\docs\Dashboard\DASHBOARD_MVP_SPECIFICATION.md`

**URLs:**
- Staging AIAI: https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com
- Supervision Console: https://eu2-supstg-realtime.3dx-staging.3ds.com/react/ops/...
- Local Backend: http://localhost:8080
- Local Frontend: http://localhost:5173

---

## Summary

This dashboard project successfully implements health monitoring and AI testing capabilities. The conversation ended while working on programmatically fetching sandbox information to enable automated VM instance ID lookup for supervision operations. The next developer should focus on:

1. Finding the sandbox dashboard API endpoint (analyze HAR data)
2. Implementing automatic VM instance ID lookup
3. Building UI for restart operations
4. Testing end-to-end operation flows

All core infrastructure is in place and working. The main gap is discovering the sandbox API endpoint to complete the automation chain.

---

**Document Version:** 1.0
**Generated:** 2026-02-11
**Source:** Full conversation transcript (3406 lines)
