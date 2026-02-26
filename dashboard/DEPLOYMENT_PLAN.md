# Dashboard Deployment Plan - Phase 1 (Hello World)

## Objective
Deploy a minimal "hello world" dashboard widget to 3DDashboard that validates the architecture and serves as a foundation for full functionality.

## Architecture Decision: Optional Backend

**Production (3DDashboard)**: Widget calls APIs directly via `call3DSpace()`
- Leverages user's existing 3DPassport SSO session
- No backend deployment required
- No cloud authorization needed

**Local Development**: Widget uses backend proxy
- Backend handles 3DPassport authentication with credentials from .env
- Allows developers to test without 3DDashboard

## Phase 1: Minimal Widget Deployment

### Step 1: Build Minimal Widget
**Goal**: Create simplest possible widget that proves architecture works

**What to include:**
- Basic UI with "Hello from 3DDashboard" message
- Environment detection (Trusted vs Standalone)
- Single API health check using `call3DSpace()`
- Fallback to backend if direct call fails
- Display connection status

**What to exclude (for Phase 2+):**
- Full dashboard UI
- Complex components
- Multiple API integrations
- Advanced features

**Files to modify:**
- `dashboard/health-widget/src/App.vue` - Minimal UI
- `dashboard/health-widget/src/services/apiService.js` - NEW: API client with fallback logic
- `dashboard/health-widget/vite.config.js` - Build configuration
- `dashboard/health-widget/package.json` - Widget metadata

### Step 2: Widget Manifest Configuration
**Goal**: Configure widget for 3DDashboard deployment

**Create/Update:**
- `dashboard/health-widget/widget.json` - Widget manifest
  - Widget ID, title, description
  - Required permissions
  - Entry point configuration

### Step 3: Build for Production
```bash
cd dashboard/health-widget
npm run build
```

**Output**: `dist/` directory with deployable widget files

### Step 4: Package for Deployment
**Options:**
1. **Manual Deployment**: Zip `dist/` folder, upload via 3DDashboard admin
2. **Widget Lab CLI**: Use `@widget-lab/cli` for deployment
3. **CI/CD Pipeline**: Automate deployment (future)

### Step 5: Deploy to 3DDashboard
**Target Environment**: Staging 3DDashboard instance
- URL: `https://devopsyivwvbl820289-euw1-devprol50.3dx-staging.3ds.com` (or similar)
- User: `yiv` (already has credentials)

**Validation Steps:**
1. Widget appears in dashboard widget library
2. Widget loads without errors
3. Environment shows "Trusted (3DDashboard)"
4. API health check succeeds via `call3DSpace()`
5. No backend proxy needed

### Step 6: Validate Fallback Logic
**Test Scenarios:**
1. ✅ **3DDashboard (Trusted)**: Direct API calls work
2. ✅ **Standalone (Vite Dev Server)**: Falls back to backend proxy
3. ✅ **Backend unavailable**: Shows clear error message

## Phase 2: Incremental Feature Addition
*After Phase 1 validates architecture*

1. Add status cards (AIAI, Jaeger, MLI)
2. Add Test AI functionality
3. Add Failure Locator
4. Add Supervision Console
5. Add advanced features

## Files Structure
```
dashboard/
├── health-widget/              # Frontend widget
│   ├── src/
│   │   ├── App.vue            # Minimal UI for Phase 1
│   │   ├── services/
│   │   │   └── apiService.js  # NEW: API client with fallback
│   │   ├── widgetInit.js      # Widget initialization
│   │   └── main.js            # Entry point
│   ├── public/
│   │   └── widget.json        # NEW: Widget manifest
│   ├── vite.config.js         # Build config
│   ├── package.json           # Widget metadata
│   └── dist/                  # Build output (after npm run build)
│
└── backend/                   # Backend proxy (optional)
    ├── app/
    │   ├── main.py            # FastAPI app
    │   ├── routers/           # API routes
    │   └── services/          # Auth services
    ├── .env                   # Credentials for local dev
    └── requirements.txt

```

## Success Criteria
- [ ] Widget deploys to 3DDashboard without errors
- [ ] Widget shows "Hello World" UI
- [ ] Environment detection works (shows "Trusted")
- [ ] Direct API call via `call3DSpace()` succeeds
- [ ] No backend deployment needed for production
- [ ] Local development still works with backend proxy
- [ ] Architecture validates for full feature rollout

## Risk Mitigation
**Risk**: `call3DSpace()` doesn't work as expected in 3DDashboard
**Mitigation**: Fallback to backend proxy is automatic and transparent

**Risk**: Widget deployment requires additional approvals
**Mitigation**: Start with staging environment, minimal widget

**Risk**: SSO authentication fails
**Mitigation**: Clear error messages, fallback logic in place

## Timeline
- Step 1-2: 2 hours (build minimal widget + manifest)
- Step 3-4: 30 minutes (build + package)
- Step 5: 1 hour (deploy + troubleshoot)
- Step 6: 30 minutes (validate all scenarios)

**Total**: ~4 hours for Phase 1 validation

## Next Steps
1. Implement optional backend architecture in `apiService.js`
2. Simplify `App.vue` to minimal "Hello World" UI
3. Create `widget.json` manifest
4. Build and test locally
5. Deploy to staging 3DDashboard
6. Validate architecture works end-to-end
