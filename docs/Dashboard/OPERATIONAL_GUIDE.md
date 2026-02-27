# Dashboard Widget - Operational Guide

**Last Updated**: February 27, 2026
**Current Status**: Phase 1 (MVP) with Compact Status Bar deployed

---

## Quick Reference

| Item | Value |
|------|-------|
| **Widget URL** | https://curious07cress.github.io/aiai-widget/index.html |
| **GitHub Repo** | https://github.com/Curious07Cress/aiai-widget |
| **Widget Directory** | `E:\repo\ai-assistant-assem-struct\dashboard\health-widget-src` |
| **Backend Directory** | `E:\repo\ai-assistant-assem-struct\dashboard\backend` |
| **Build System** | Webpack 4 |
| **Framework** | Vue 2.6.12 + Vuetify 2.3.17 |

---

## Routine Tasks

### Task 1: Build Widget After Code Changes

**When to do this**: After modifying any `.vue`, `.js`, or `.css` files in `src/`

```bash
cd E:\repo\ai-assistant-assem-struct\dashboard\health-widget-src
npm run build
```

**Expected output**:
```
Hash: <12-digit-hash>
Built at: <timestamp>
bundle.js
1.<hash>.bundle.js
2.<hash>.bundle.js
index.html
static/
```

**Build artifacts**: Located in `dist/` folder

---

### Task 2: Deploy Widget to GitHub Pages

**When to do this**: After building widget with changes you want to deploy

**Steps**:

1. **Ensure you're on gh-pages branch and have latest build**:
```bash
cd E:\repo\ai-assistant-assem-struct
git checkout main
git pull origin main
```

2. **Build the widget** (if not already done):
```bash
cd dashboard/health-widget-src
npm run build
```

3. **Switch to gh-pages and copy dist files**:
```bash
cd E:\repo\ai-assistant-assem-struct
git checkout gh-pages
git pull origin gh-pages
```

4. **Copy built files** (using git worktree method):
```bash
# Create a temporary worktree for main branch
git worktree add C:\temp\main-build main

# Build in the worktree
cd C:\temp\main-build\dashboard\health-widget-src
npm run build

# Copy dist files to gh-pages root
cd E:\repo\ai-assistant-assem-struct
cp -r C:\temp\main-build\dashboard\health-widget-src\dist/* .

# Clean up worktree
git worktree remove C:\temp\main-build
```

5. **Commit and push**:
```bash
# Remove old bundle files (if they exist with different hash)
git rm 1.*.bundle.js 2.*.bundle.js 2>/dev/null || true

# Add new files
git add *.js index.html static/

# Commit
git commit -m "Deploy: <description of changes>

Build hash: <hash-from-build-output>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to GitHub Pages
git push origin gh-pages
```

6. **Get updated URL**:
The URL remains the same: https://curious07cress.github.io/aiai-widget/index.html

Wait 1-2 minutes for GitHub Pages to update, then refresh widget in 3DDashboard.

---

### Task 3: Update Widget in 3DDashboard

**When to do this**: After deploying to GitHub Pages

**Steps**:

1. **Open 3DDashboard**: Navigate to your 3DDashboard instance
2. **Refresh the widget page**: Hard refresh (Ctrl+F5 or Cmd+Shift+R)
3. **Verify changes**: Check that your updates are visible

**Note**: The widget URL never changes - it's always the same GitHub Pages link.

---

### Task 4: Commit Source Code Changes

**When to do this**: After making changes to widget or backend code

```bash
cd E:\repo\ai-assistant-assem-struct

# Check what changed
git status

# Stage changes
git add <files>

# Commit
git commit -m "<description>

Details:
- <change 1>
- <change 2>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to main branch
git push origin main
```

---

## Current Architecture

### Frontend (Widget)
- **Location**: `dashboard/health-widget-src/`
- **Deployment**: GitHub Pages (External storage)
- **URL**: https://curious07cress.github.io/aiai-widget/index.html
- **Branch**: Source on `main`, deployed files on `gh-pages`

### Backend (FastAPI)
- **Location**: `dashboard/backend/`
- **Deployment**: **TBD** - Where is production backend hosted?
- **Local Dev**: `localhost:8080`
- **API Endpoint**: `/api/health/all`

### Data Flow
```
3DDashboard Widget
       ↓
  GitHub Pages
  (index.html)
       ↓
  Backend API
  (health data)
       ↓
   AIAI Service
  (health check)
```

---

## Phase 1 Implementation Status

### ✅ Completed
- [x] Compact status bar design (replacing 3 large cards)
- [x] Color-coded health indicators (green/yellow/red/gray)
- [x] AIAI service status display
- [x] Response time display (when backend returns correct format)
- [x] Last updated timestamp
- [x] Manual refresh button
- [x] Auto-refresh (30s interval, configurable)
- [x] MCP service hidden (per specification)
- [x] Widget deployed to GitHub Pages
- [x] Backend health endpoint transformation (committed, not deployed)

### ⏳ Pending
- [ ] Deploy backend fix to production
- [ ] Verify status bar shows actual metrics (not "Down" and "N/A")
- [ ] Backend deployment location/process documentation

---

## Known Issues

### Issue 1: Status Bar Shows "Down" and "N/A"
**Status**: Fixed in code, pending backend deployment

**Root Cause**: Backend returns `aiai_api` and `latency_ms`, frontend expects `aiai` and `response_time_ms`

**Fix**: Updated `dashboard/backend/app/routers/health.py` to transform data format

**Commit**: `8c28fcb6` on main branch

**Next Steps**: Deploy backend with this fix

---

## Deployment Checklist

Use this checklist when deploying changes:

### Widget Changes
- [ ] Code changes made and tested locally
- [ ] `npm run build` completed successfully
- [ ] Dist files copied to gh-pages branch
- [ ] Old bundle files removed (if hash changed)
- [ ] New files committed and pushed to gh-pages
- [ ] GitHub Pages updated (wait 1-2 min)
- [ ] Widget refreshed in 3DDashboard
- [ ] Changes verified working

### Backend Changes
- [ ] Code changes made and tested locally
- [ ] Changes committed to main branch
- [ ] Backend deployed to production (process TBD)
- [ ] Health endpoint tested
- [ ] Widget verified receiving correct data

---

## Troubleshooting

### Widget shows "Down" and "N/A"
**Cause**: Backend not returning data in expected format
**Solution**: Deploy backend fix from commit `8c28fcb6`

### Widget shows blank page
**Cause**: Build error or UWA initialization issue
**Solution**: Check browser console, verify dist/ has index.html

### GitHub Pages not updating
**Cause**: GitHub caching
**Solution**: Wait 2 minutes, hard refresh browser (Ctrl+F5)

### Backend connection error
**Cause**: Backend not deployed or URL wrong
**Solution**: Verify backend URL in widget settings

---

## Contact

**Questions about**:
- Widget deployment → GitHub Pages process documented above
- Backend deployment → **NEEDS DOCUMENTATION** - Where is production backend?
- Specification → See `DASHBOARD_SPECIFICATION.md`
