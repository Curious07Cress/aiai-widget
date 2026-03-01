# CRITICAL: Backend Deployment Required

**Date**: March 1, 2026
**Status**: Widget deployed but non-functional - requires backend deployment

---

## Current Situation

The AIAI Query Tool widget has been deployed to GitHub Pages with fixes, but **the assistant dropdown is not loading** because the backend proxy is not deployed to production.

**Widget URL**: https://curious07cress.github.io/aiai-widget/index.html
**Build Hash**: 910de130b286335ed802

---

## Why Backend is Required

The widget **cannot call AIAI API directly** from the browser because:

1. **CORS Restrictions**: Browser blocks cross-origin requests to AIAI
2. **Authentication**: AIAI requires 3DPassport SSO authentication which cannot be handled in browser
3. **Platform Connectors Limitation**: `call3DSpace()` only works for 3DSpace APIs, not external URLs like AIAI

**Architecture**:
```
Widget (Browser) → Backend Proxy → AIAI API
                   ↓ handles auth
                   ↓ handles CORS
```

---

## Backend Proxy Details

**Location**: `dashboard/backend/`
**Technology**: Python FastAPI
**Port**: 8080

**Required Endpoints**:
- `GET /api/aiai/assistants` - Fetch available assistants
- `POST /api/aiai/assistants/{name}/submit` - Submit prompt to assistant

**Current Status**: Running locally only (`localhost:8080`)

---

## Deployment Steps

### Step 1: Choose Deployment Platform

Options:
- **Azure App Service** (recommended - easy Python deployment)
- **AWS Elastic Beanstalk** (Python support)
- **3DEXPERIENCE Platform** (if internal hosting available)
- **Docker Container** (on any cloud provider)

### Step 2: Configure Environment Variables

Set these in your production environment:

```bash
DASHBOARD_DEBUG=false
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080

# CORS - allow GitHub Pages
DASHBOARD_CORS_ORIGINS=https://curious07cress.github.io

# AIAI API URL
DASHBOARD_AIAI_BASE_URL=https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com

# 3DPassport Authentication (REQUIRED)
DASHBOARD_PASSPORT_USERNAME=<your-username>
DASHBOARD_PASSPORT_PASSWORD=<your-password>

# Timeouts
DASHBOARD_HEALTH_CHECK_TIMEOUT=10
DASHBOARD_TRACE_FETCH_TIMEOUT=30
```

**CRITICAL**: The `DASHBOARD_PASSPORT_USERNAME` and `DASHBOARD_PASSPORT_PASSWORD` are required for authenticating to AIAI.

### Step 3: Deploy Backend

Example for Azure:
```bash
cd dashboard/backend
az webapp up --name aiai-dashboard-backend --runtime "PYTHON:3.11" --sku B1
```

Example for Docker:
```bash
cd dashboard/backend
docker build -t aiai-dashboard-backend .
docker run -p 8080:8080 --env-file .env aiai-dashboard-backend
```

### Step 4: Get Backend URL

After deployment, note the backend URL (e.g., `https://aiai-dashboard-backend.azurewebsites.net`)

### Step 5: Configure Widget

In 3DDashboard:
1. Open widget settings (gear icon)
2. Set **Backend Proxy URL** preference to your deployed backend URL
3. Save and refresh widget

---

## Testing Backend Deployment

Test the backend is working:

```bash
# Test assistants endpoint
curl -X GET "https://your-backend-url/api/aiai/assistants?aiai_url=https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com"

# Should return JSON array of assistants
```

---

## Recent Changes (March 1, 2026)

### Source Code (Commit: 338cefbb)
- Added `backendUrl` as configurable widget preference
- Updated AssistantQuery.vue to load backendUrl from preferences
- Added detailed logging in apiService.js for debugging

### Deployed Widget (Commit: 5aef3560)
- Build hash: 910de130b286335ed802
- Includes all fixes above
- Deployed to https://curious07cress.github.io/aiai-widget/index.html

---

## Files Reference

- **Backend Code**: `dashboard/backend/`
- **Backend Config**: `dashboard/backend/.env` (local development)
- **Widget Preferences**: Configured in 3DDashboard widget settings
- **AIAI Proxy Router**: `dashboard/backend/app/routers/aiai.py`
- **Authentication Service**: `dashboard/backend/app/services/passport_auth.py`

---

## Quick Deploy Checklist

- [ ] Choose deployment platform
- [ ] Set environment variables (especially PASSPORT credentials)
- [ ] Deploy backend
- [ ] Test backend endpoints
- [ ] Get production backend URL
- [ ] Configure widget backendUrl preference in 3DDashboard
- [ ] Refresh widget
- [ ] Verify assistant dropdown loads
- [ ] Test submit query functionality

---

## Support

If you need help deploying:
1. Azure: https://docs.microsoft.com/en-us/azure/app-service/quickstart-python
2. AWS: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-apps.html
3. Docker: See `dashboard/backend/Dockerfile` (may need to be created)

---

## Current Widget Behavior

**What works**:
- Widget loads and displays
- UI renders correctly
- Preferences load from 3DDashboard

**What doesn't work**:
- Assistant dropdown shows "Failed to fetch"
- Cannot submit queries
- Console error: "TypeError: Failed to fetch"

**Logs to check** (Browser console):
```
[AssistantQuery] Loaded backendUrl from preferences: <url>
[ApiService] getAssistants called with backendUrl: <url>
[ApiService] callWithFallback - isTrusted: false, backendUrl: <url>
```

These logs will help verify the backend URL is configured correctly.
