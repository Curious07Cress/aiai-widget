# Internal Git Hosting for V1 Release

**Date**: February 25, 2026
**Purpose**: Document migration from GitHub Pages to internal git hosting for production widget deployment

---

## Internal Git Server

**Host**: `itgit.dsone.3ds.com`
**Type**: GitLab (3DS internal instance)
**Access**: Requires 3DS credentials and SSH key setup

### URL Patterns

**SSH** (recommended for development):
```
git@itgit.dsone.3ds.com:group/project.git
```

**HTTPS** (for widget hosting):
```
https://itgit.dsone.3ds.com/group/project/-/raw/branch/file.html
```

---

## Current GitHub Setup (Phase 1)

**Repository**: https://github.com/Curious07Cress/aiai-widget
**Deployment**: GitHub Pages (public, external)
**Widget URL**: https://curious07cress.github.io/aiai-widget/index.html

**Limitations**:
- ❌ Public repository (security concern for production)
- ❌ External service (not controlled by 3DS)
- ❌ Requires GitHub account

---

## Migration Plan to Internal Git (V1)

### Step 1: Repository Setup

**Target Location**: `itgit.dsone.3ds.com:widget-lab/aiai-health-dashboard`
**Alternative**: `itgit.dsone.3ds.com:ai-assistant/dashboard-widget`

#### Create Repository

1. **Option A: Via GitLab Web UI**
   - Navigate to: https://itgit.dsone.3ds.com
   - Log in with 3DS credentials
   - Click "New Project"
   - Name: `aiai-health-dashboard`
   - Group: `widget-lab` or `ai-assistant` (check permissions)
   - Visibility: **Internal** (accessible to all 3DS employees)

2. **Option B: Request from Widget Lab Team**
   - Contact widget-lab team to create repository
   - Provide project name and description
   - Request appropriate permissions

#### Configure Repository

```bash
# Add internal git remote
cd E:/repo/ai-assistant-assem-struct/dashboard/health-widget
git remote add internal git@itgit.dsone.3ds.com:widget-lab/aiai-health-dashboard.git

# Push gh-pages branch to internal
git push internal gh-pages

# Set internal as default for gh-pages
git checkout gh-pages
git branch --set-upstream-to=internal/gh-pages
```

### Step 2: GitLab Pages Setup

**GitLab Pages** (equivalent to GitHub Pages):
- Automatic HTTPS hosting for git repositories
- URL pattern: `https://widget-lab.itgit.pages.dsone.3ds.com/aiai-health-dashboard/`
- Requires `.gitlab-ci.yml` for build/deployment

#### Create .gitlab-ci.yml

```yaml
# File: .gitlab-ci.yml (in repository root)
pages:
  stage: deploy
  script:
    - mkdir .public
    - cp -r * .public
    - mv .public public
  artifacts:
    paths:
      - public
  only:
    - gh-pages  # Deploy from gh-pages branch
```

**Alternative: Static Hosting without CI**

If GitLab Pages is complex, use direct raw file access:
```
https://itgit.dsone.3ds.com/widget-lab/aiai-health-dashboard/-/raw/gh-pages/index.html
```

### Step 3: Update Widget Configuration

Once internal hosting is active:

1. **Update Additional App in 3DDashboard**:
   - Go to: Compass → Additional Apps
   - Find "AI Assistant Health Dashboard"
   - Click Edit
   - Update Source Code File URL:
     - **Old**: `https://curious07cress.github.io/aiai-widget/index.html`
     - **New**: `https://widget-lab.itgit.pages.dsone.3ds.com/aiai-health-dashboard/index.html`
   - Click Save

2. **Test deployment**:
   - Refresh widget in 3DDashboard
   - Verify loads from internal git
   - Check browser console for errors

### Step 4: Access Control

**Internal Git Benefits**:
- ✅ Controlled by 3DS IT
- ✅ Integrated with 3DPassport SSO
- ✅ Access control via groups/projects
- ✅ Internal network (more secure)

**Recommended Settings**:
- Project Visibility: **Internal** (all 3DS employees)
- Master/Main branch: Protected
- Deployment branch (gh-pages): Protected, maintainers only
- Merge requests: Required for changes

---

## Deployment Workflow (V1)

### Local Development

```bash
cd dashboard/health-widget

# Develop with backend proxy
npm run dev  # localhost:3000

# Build for production
npm run build  # Output: dist/
```

### Deploy to Internal Git

```bash
# Switch to deployment branch
git checkout gh-pages

# Update with latest build
cp -r dist/* .
git add .
git commit -m "Release v1.0.x"

# Push to internal git
git push internal gh-pages

# Deployment:
# - GitLab Pages: Automatic rebuild (~1-2 min)
# - Direct raw files: Immediate availability
```

### Update in 3DDashboard

**With GitLab Pages**: Automatic, widget fetches latest on next load
**With raw file URLs**: May require cache invalidation (Ctrl+F5)

---

## Comparison: GitHub vs Internal Git

| Feature | GitHub Pages | Internal Git (GitLab Pages) |
|---------|--------------|----------------------------|
| **Access Control** | Public/Private (paid) | Internal to 3DS |
| **Authentication** | GitHub account | 3DPassport SSO |
| **HTTPS** | ✅ Free | ✅ Automatic |
| **CDN** | ✅ Global | 🟡 Regional (EU) |
| **Deployment Speed** | 1-2 min | 1-2 min (Pages) / Instant (raw) |
| **Security** | ❌ External | ✅ Internal |
| **Cost** | Free (public) | Free (internal) |
| **Control** | ❌ GitHub Inc. | ✅ 3DS IT |
| **Approval Needed** | No | IT approval may be required |

---

## Alternative Hosting Methods (If GitLab Pages Unavailable)

### Option 1: Direct Raw File Access

**URL Pattern**:
```
https://itgit.dsone.3ds.com/widget-lab/aiai-health-dashboard/-/raw/gh-pages/index.html
```

**Pros**:
- ✅ No CI/CD setup needed
- ✅ Immediate availability
- ✅ Simple

**Cons**:
- ❌ No automatic HTTPS for custom domains
- ❌ URL structure exposes git branch
- ❌ Possible CORS issues

### Option 2: Internal Web Server

**Setup**: Host on internal Apache/Nginx server
**URL**: `https://internal-widgets.3ds.com/aiai-health-dashboard/`

**Requirements**:
- Request server space from IT
- Configure DNS and SSL
- Set up deployment pipeline
- More complex than git hosting

### Option 3: S3-Compatible Object Storage

**Setup**: Use 3DS internal object storage
**URL**: `https://storage.3ds.com/widgets/aiai-health-dashboard/index.html`

**Requirements**:
- Access to internal S3/MinIO
- Configure bucket permissions
- Set up deployment automation

---

## Recommended Approach for V1

### Short-term (Current)
- ✅ Keep using GitHub Pages for testing and development
- ✅ Validates architecture and deployment workflow
- ✅ No internal approvals needed yet

### V1 Release
1. **Request internal git repository** from widget-lab team
2. **Set up GitLab Pages** with `.gitlab-ci.yml`
3. **Migrate widget** to internal hosting
4. **Update 3DDashboard** with new URL
5. **Test thoroughly** before production announcement

### Production
- **Remove GitHub repository** or make it a mirror
- **All updates** go through internal git
- **Access control** via GitLab groups
- **Audit trail** via git commits and merge requests

---

## SSH Key Setup (If Needed)

To push to internal git via SSH:

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your.email@3ds.com"

# Add to ssh-agent
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitLab:
# 1. Log in to https://itgit.dsone.3ds.com
# 2. Profile → Settings → SSH Keys
# 3. Paste public key
# 4. Click "Add key"

# Test connection
ssh -T git@itgit.dsone.3ds.com
# Should see: "Welcome to GitLab, @username!"
```

---

## Next Steps

### Immediate
- [ ] Verify access to itgit.dsone.3ds.com with your credentials
- [ ] Check if widget-lab or ai-assistant group exists
- [ ] Request repository creation (if needed)
- [ ] Test SSH or HTTPS access

### V1 Preparation
- [ ] Create internal git repository
- [ ] Set up GitLab Pages or raw file hosting
- [ ] Test deployment workflow
- [ ] Document any IT approval requirements
- [ ] Update deployment scripts

### Migration
- [ ] Push widget to internal git
- [ ] Verify hosting works
- [ ] Update 3DDashboard URL
- [ ] Test in production environment
- [ ] Archive/remove GitHub repository

---

## References

**chartjs Widget Example**:
- Repository: `git@itgit.dsone.3ds.com:widget-lab/widget-examples/chartjs.git`
- Web: https://itgit.dsone.3ds.com/widget-lab/widget-examples/chartjs
- Package.json: `E:\repo\ai-assistant-assem-struct\dashboard\chartjs\package.json`

**Internal Git Documentation**:
- GitLab: https://itgit.dsone.3ds.com
- Widget Lab: https://itgit.dsone.3ds.com/widget-lab

**Contact**:
- Widget Lab Team: For repository creation and GitLab Pages setup
- IT Support: For SSH access or internal hosting issues

---

**Created**: February 25, 2026
**Last Updated**: February 25, 2026
**Status**: Ready for V1 migration planning
