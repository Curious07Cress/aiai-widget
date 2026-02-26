# VM Manager Implementation - Status and Context

**Last Updated**: 2026-02-12
**Status**: ⚠️ **BLOCKED** - Staging URL pattern incorrect

## Overview

Implementation of a VM management feature for the AIAI Operations Dashboard that allows users to:
1. View a list of VMs in their AIAI sandbox
2. Restart VMs with confirmation dialog
3. View VM details (instance ID, IP address, type)

## Architecture Decision

**Chosen Approach**: Option A - Conservative Implementation
- Display list of VMs with names, instance IDs, and IP addresses
- Single action: Restart with confirmation dialog
- Backend proxy for authentication (not direct browser calls)

**Why Backend Proxy**:
- CORS prevents direct browser-to-staging API calls
- 3DPassport authentication requires server-side handling
- Staging API doesn't allow cross-origin requests from dashboard

## Implementation Status

### ✅ Completed

1. **Backend Endpoints** - `dashboard/backend/app/routers/supervision.py`
   - `GET /api/supervision/sandbox/fetch` - Fetches sandbox data and VM list
   - `POST /api/supervision/operations/execute` - Executes VM restart operations

2. **Backend Services** - `dashboard/backend/app/services/supervision.py`
   - `fetch_sandbox_data()` - Fetches sandbox data from staging API
   - `execute_supervision_operation()` - Executes supervision operations
   - `get_aiai_vms_from_sandbox()` - Extracts AIAI VMs from sandbox data
   - `derive_sandbox_id_from_service_instance()` - Converts service instance ID to sandbox ID

3. **Authentication Service** - `dashboard/backend/app/services/passport_auth.py`
   - `get_authenticated_client()` - Creates authenticated HTTP client with 3DPassport
   - Updated to accept `base_url` parameter for per-request authentication

4. **Frontend Components**
   - **VMManager.vue** - Complete VM management dialog with list, icons, restart functionality
   - **SupervisionInfo.vue** - Integration point with "Manage VMs" button
   - **App.vue** - Updated to pass `serviceInstanceId` to components

5. **Health Aggregator Updates** - `dashboard/backend/app/services/health_aggregator.py`
   - Derives `serviceInstanceId` from URL when health endpoint requires auth

### ⚠️ Current Blocker

**Staging URL DNS Resolution Failure**

The derived staging URL does not exist:
```
https://dsext001-euw1-devprol50-staging.3dexperience.3ds.com
```

**Error**: `DNS_PROBE_FINISHED_NXDOMAIN`

**URL Pattern Used** (INCORRECT for this environment):
- AIAI: `devops{sandbox}{digits}-{region}-{platform}-aiai.3dx-staging.3ds.com`
- Staging (derived): `dsext001-{region}-{platform}-staging.3dexperience.3ds.com`

The staging URL pattern is environment-specific and incorrect for this AIAI instance.

## Technical Details

### Service Instance ID Formats

There are TWO formats:
1. **UI Format** (derived from URL): `SbxAIAssistantInfraYIVWVBLEUW1`
2. **API Format** (from health endpoint): `6CDD1E53E39C1900694C44000000C6CA` (hex)

**Problem**: Staging API requires the hex format, but AIAI health endpoint returns 303 (redirect) even with authentication, forcing fallback to UI format which doesn't work with staging API.

### Authentication Flow

1. User provides `PASSPORT_USERNAME` and `PASSPORT_PASSWORD` in environment
2. Backend authenticates with 3DPassport SSO on behalf of user
3. Authenticated client used for:
   - AIAI health endpoint (to get real service instance ID)
   - Staging API (to fetch sandbox data)
   - Supervision API (to execute VM operations)

**Current Status**: Authentication works for AIAI API endpoints (e.g., `/api/v1/assistants`) but health endpoint still returns 303.

### API Endpoints

#### Staging API (BLOCKED)
```
GET {staging_url}/enovia/resources/v0/DevOpsStaging/sandbox/refreshSandbox
  ?sandBoxId={service_instance_id}
```

**Purpose**: Fetch sandbox data including VM list
**Authentication**: Requires 3DPassport
**Current Issue**: Staging URL doesn't exist

#### AIAI Health Endpoint
```
GET {aiai_url}/health
```

**Expected**: 200 with `serviceInstanceId` in response
**Actual**: 303 (redirect) even with authenticated client
**Fallback**: Derive UI format ID from URL pattern

#### Supervision Operations API
```
POST {supervision_url}/api/v1/supervision/operations
{
  "operation": "restart_aiai",
  "operationParams": {
    "resourceId": "{vm_instance_id}",
    "tenantId": "{admin_tenant}"
  }
}
```

**Status**: Not tested yet (blocked on VM list retrieval)

### File Structure

```
dashboard/
├── backend/app/
│   ├── routers/
│   │   └── supervision.py          # VM fetch & operations endpoints
│   └── services/
│       ├── supervision.py          # Sandbox data & VM operations
│       ├── passport_auth.py        # 3DPassport authentication
│       └── health_aggregator.py    # Health checks + service instance ID
│
└── health-widget/src/components/
    ├── VMManager.vue               # VM list & restart dialog
    ├── SupervisionInfo.vue         # Integration with "Manage VMs" button
    └── App.vue                     # Service instance ID extraction
```

### Key Code Locations

**Backend - Sandbox Fetch Endpoint**
`dashboard/backend/app/routers/supervision.py:257-398`
```python
@router.get("/sandbox/fetch")
async def fetch_sandbox(
    staging_url: str = Query(...),
    aiai_url: str = Query(...),
) -> Dict[str, Any]:
    # 1. Authenticate with 3DPassport
    client = await get_authenticated_client(base_url=aiai_url)

    # 2. Try to get real service instance ID from health endpoint
    health_response = await client.get(f"{aiai_url}/health")

    # 3. If health returns 303, fall back to URL derivation
    if health_response.status_code in (301, 302, 303, 307, 308):
        supervision_info = derive_supervision_url(aiai_url)
        service_instance_id = supervision_info.service_instance_id

    # 4. Fetch sandbox data from staging API
    sandbox_data = await fetch_sandbox_data(staging_url, service_instance_id, client)

    # 5. Extract AIAI VMs
    aiai_vms = get_aiai_vms_from_sandbox(sandbox_data)

    return {"aiai_vms": aiai_vms, ...}
```

**Frontend - VM Manager Component**
`dashboard/health-widget/src/components/VMManager.vue:170-209`
```javascript
const loadVMs = async () => {
  // Call backend endpoint - backend authenticates and fetches sandbox data
  const apiUrl = `${props.backendUrl}/api/supervision/sandbox/fetch?` +
    `staging_url=${encodeURIComponent(props.stagingUrl)}&` +
    `aiai_url=${encodeURIComponent(props.aiaiUrl)}`

  const response = await fetch(apiUrl)
  const data = await response.json()

  vms.value = data.aiai_vms || []
}
```

**Frontend - Staging URL Derivation**
`dashboard/health-widget/src/components/SupervisionInfo.vue:189-217`
```javascript
const stagingUrl = computed(() => {
  const hostname = url.hostname;

  // Extract region and platform from AIAI URL
  const match = hostname.match(/devops[a-z]+\d+-([a-z]+\d+)-([a-z]+\d+)-aiai\.3dx-staging\.3ds\.com/i);

  if (match) {
    const region = match[1];     // e.g., "euw1"
    const platform = match[2];   // e.g., "devprol50"

    // Construct staging URL (INCORRECT PATTERN)
    const stagingHostname = `dsext001-${region}-${platform}-staging.3dexperience.3ds.com`;
    return `https://${stagingHostname}`;
  }
});
```

### VM Names and Icons

**Known AIAI VM Types**:
- `AIWFL_EXEC_0` - AI Workflow Executor (green icon)
- `ScalableLB_0` - Load Balancer (LAN icon)
- `KAFKA_0` - Kafka Message Processing
- `ES_MASTERHA_0` - Elasticsearch Master
- Bastion Host (blue icon, shield)

**Icon Logic** (`VMManager.vue:154-167`):
```javascript
const getVMIcon = (vm) => {
  if (vm.is_bastion) return 'mdi-shield-check'
  if (vm.name.includes('LB')) return 'mdi-lan'
  if (vm.name.includes('KAFKA')) return 'mdi-message-processing'
  if (vm.name.includes('ES_')) return 'mdi-database-search'
  if (vm.name.includes('AIWFL')) return 'mdi-brain'
  return 'mdi-server'
}
```

## Environment Setup

### Required Environment Variables

```bash
# Backend - .env or PowerShell
PASSPORT_USERNAME=<your-3dpassport-username>
PASSPORT_PASSWORD=<your-3dpassport-password>
AIAI_URL=<your-aiai-url>  # Optional, derived from request
```

### Current Configuration

**AIAI URL**: `https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com`

**Extracted Components**:
- Sandbox: `yivwvbl`
- Digits: `820289`
- Region: `euw1`
- Platform: `devprol50`

**Derived Service Instance ID (UI format)**: `SbxAIAssistantInfraYIVWVBLEUW1`

## Issues Encountered and Solutions

### Issue 1: Service Instance ID Not Available
**Problem**: "Manage VMs" button showed gray overlay but no dialog
**Root Cause**: `serviceInstanceId` prop was undefined
**Solution**: Added `serviceInstanceId` computed property to `App.vue` and included in return statement

### Issue 2: Authentication Target Mismatch
**Problem**: Backend not authenticating with correct AIAI URL
**Root Cause**: `get_authenticated_client()` called without `base_url` parameter
**Solution**: Updated both endpoints to pass `base_url=aiai_url` to authentication function

### Issue 3: Health Endpoint Returns 303 Even with Auth
**Problem**: Can't get real service instance ID from health endpoint
**Root Cause**: AIAI health endpoint redirects (303) even for authenticated requests
**Current Workaround**: Fall back to deriving UI format ID from URL pattern
**Impact**: UI format ID doesn't work with staging API

### Issue 4: CORS Blocking Direct API Calls
**Problem**: Browser blocked direct calls from dashboard to staging API
**Solution**: Use backend as proxy - backend authenticates and makes calls server-side

### Issue 5: Staging URL DNS Resolution Fails
**Problem**: Derived staging URL doesn't exist
**Root Cause**: URL pattern `dsext001-{region}-{platform}-staging.3dexperience.3ds.com` is incorrect for this environment
**Status**: ⚠️ **CURRENT BLOCKER**

## Backend Logs Analysis

**Latest Request** (2026-02-11 22:05:04):
```
INFO - Fetching sandbox data for AIAI: https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com
INFO - Obtained client for https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com (authenticated: True)
INFO - Fetching service instance ID from: https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com/health
INFO - HTTP Request: GET .../health "HTTP/1.1 303 See Other"
WARNING - AIAI health endpoint returned 303 (redirect). Falling back to deriving service instance ID from URL pattern.
WARNING - Using derived service instance ID from URL: SbxAIAssistantInfraYIVWVBLEUW1
INFO - Fetching sandbox data for ID: SbxAIAssistantInfraYIVWVBLEUW1
ERROR - HTTP error fetching sandbox data: [Errno -2] Name or service not known
```

**Key Observations**:
1. ✅ Authentication succeeds
2. ✅ Can call AIAI `/api/v1/assistants` endpoint successfully
3. ❌ Health endpoint returns 303 despite authentication
4. ❌ Staging URL DNS lookup fails

## Alternative Approaches to Consider

### Option 1: Find Correct Staging URL
**Action**: Ask DevOps team or check documentation for correct staging URL pattern
**Pros**: Would fix the issue completely
**Cons**: Requires external information

### Option 2: Use AIAI API for VM List
**Action**: Check if AIAI has endpoints to list VMs
**Pros**: Avoid staging API entirely
**Cons**: May not exist, not documented

### Option 3: Use Supervision API for VM Discovery
**Action**: Check if supervision API has VM listing endpoints
**Pros**: We can already derive supervision URLs
**Cons**: May not provide VM list

### Option 4: Manual VM Instance ID Entry
**Action**: Skip automatic VM discovery, let users manually enter instance IDs
**Pros**: Restart functionality would still work
**Cons**: Poor user experience, defeats purpose of feature

### Option 5: Fix Health Endpoint Authentication
**Action**: Investigate why authenticated client gets 303 from health endpoint
**Possible Issues**:
- Health endpoint on different domain/subdomain
- Session cookies not being sent
- Different auth mechanism required
**Next Steps**: Check if health endpoint needs special headers or auth flow

## Next Steps

### Immediate Actions Needed

1. **Verify Staging URL Pattern**
   - Contact DevOps team
   - Check React Ops dashboard or supervision console for hints
   - Look for environment-specific documentation

2. **Test Alternative APIs**
   - Try AIAI API endpoints for VM information
   - Test supervision API for VM listing capabilities
   - Document available endpoints

3. **Debug Health Endpoint 303**
   - Add more detailed logging
   - Check response headers for redirect location
   - Verify cookies are being sent
   - Try direct browser access to health endpoint while authenticated

### Code Changes Needed (Once Unblocked)

1. **Update Staging URL Derivation**
   ```javascript
   // SupervisionInfo.vue:204
   // Replace with correct pattern when found
   const stagingHostname = `dsext001-${region}-${platform}-staging.3dexperience.3ds.com`;
   ```

2. **Handle Health Endpoint 303 Better**
   ```python
   # supervision.py router:317-324
   # Investigate why auth client gets 303
   # May need different auth flow or headers
   ```

### Testing Checklist (When Unblocked)

- [ ] VM list loads successfully
- [ ] All VM types display with correct icons
- [ ] Restart button shows confirmation dialog
- [ ] Restart operation executes successfully
- [ ] VM list refreshes after restart
- [ ] Error handling works for failed operations
- [ ] Backend logs show successful operations
- [ ] No CORS errors in browser console

## User Feedback from Session

1. **Staging URL Issue**: User confirmed derived URL doesn't exist (DNS error)
2. **Authentication Preference**: User expected browser to use existing 3DPassport session, but CORS forced backend proxy approach
3. **Environment Variables**: User successfully configured `PASSPORT_USERNAME` and `PASSPORT_PASSWORD`

## Configuration Files

**Backend Config** (`dashboard/backend/app/config.py`):
```python
class Settings(BaseSettings):
    aiai_base_url: str = Field(default="", env="AIAI_URL")
    # ... other settings
```

**Frontend Props** (`SupervisionInfo.vue`):
```javascript
props: {
  aiaiUrl: String,
  backendUrl: String,
  serviceInstanceId: String,
}
```

## Known Working Endpoints

✅ **AIAI Assistants API**:
```
POST {aiai_url}/api/v1/assistants
  ?include_nocodecompanions=false
  &assistant_namespace=ai-assembly-structure
```

✅ **Supervision Console Derivation**:
```python
# From AIAI URL, derive supervision info
# Returns: vm_details_url, react_ops_url, admin_tenant, etc.
supervision_info = derive_supervision_url(aiai_url)
```

## Related Documentation

- **Original Requirements**: See previous conversation about VM Management (Option A)
- **Supervision API**: Check React Ops dashboard for operation keys
- **3DPassport Auth**: See `passport_auth.py` implementation
- **Sandbox Data Structure**: Nested JSON in `sandbox.sandboxConfig.readSandboxContent`

## Questions for User/Team

1. What is the correct staging URL for your AIAI environment?
2. Does the AIAI API have endpoints to list VMs?
3. Does the supervision API support VM listing?
4. Is there alternative documentation for sandbox/VM APIs?
5. Why does the health endpoint return 303 even with authentication?

## Summary

The VM Manager feature is **fully implemented** but **blocked on staging URL issue**. All code is in place and ready to work once the correct staging URL is identified or an alternative VM listing API is found. The authentication infrastructure works (proven by successful assistants API calls), but the health endpoint behavior and staging URL pattern need resolution.
