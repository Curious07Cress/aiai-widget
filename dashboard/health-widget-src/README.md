# AI Assistant Health Dashboard Widget

A 3DDashboard widget for monitoring AI Assistant infrastructure health with optional backend architecture.

## Features

- ✅ **UWA-compliant widget** - Works in 3DDashboard with proper initialization
- ✅ **Dynamic trusted mode detection** - Automatically uses direct API calls in 3DDashboard
- ✅ **Optional backend** - Falls back to backend proxy for local development
- ✅ **Real-time health monitoring** - Auto-refresh health status
- ✅ **Responsive UI** - Built with Vue 2 + Vuetify 2

## Architecture

### Trusted Mode (3DDashboard)
- Uses `call3DSpace()` from `@widget-lab/platform-connectors`
- Direct API calls via user's SSO session
- No backend deployment required

### Standalone Mode (Local Development)
- Falls back to backend proxy (`localhost:8080`)
- Backend handles 3DPassport authentication
- Full functionality for developers

## Project Structure

```
src/
├── components/
│   ├── HealthDashboard.vue  # Main dashboard component
│   ├── StatusCard.vue        # Health status card
│   └── ServiceInfo.vue       # Service information table
├── services/
│   └── apiService.js         # API client with dynamic mode detection
├── lib/
│   ├── widget.js             # UWA initialization (from chartjs template)
│   └── widget-starter.js     # Entry point wrapper
├── plugins/
│   └── vuetify.js            # Vuetify configuration
├── store/
│   └── index.js              # Vuex store (minimal)
├── static/
│   ├── widget.json           # 3DDashboard widget manifest
│   ├── version.json          # Version tracking
│   └── lib/require.js        # RequireJS for AMD modules
├── main.js                   # Application initialization
└── index.html                # HTML entry point
```

## Development

### Prerequisites

- Node.js >= 14
- npm >= 6

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm start
```

Opens widget at `http://localhost:8080` in standalone mode.

### Build for Production

```bash
npm run build
```

Output: `dist/` directory

## Deployment

### GitHub Pages

1. Build the widget:
   ```bash
   npm run build
   ```

2. Deploy `dist/` to gh-pages branch:
   ```bash
   cd dist
   git init
   git checkout -b gh-pages
   git add .
   git commit -m "Deploy widget"
   git push origin gh-pages --force
   ```

3. Configure GitHub Pages: Settings → Pages → gh-pages branch

### 3DDashboard Additional App

1. Go to: Compass → Additional Apps → Create
2. **Storage**: External
3. **Source**: `https://your-github-pages-url/index.html`
4. Click **Create**

## Configuration

Widget preferences (configurable in 3DDashboard):

- **aiaiUrl**: AIAI API base URL
- **refreshInterval**: Auto-refresh interval in seconds

## Key Components

### `apiService.js` - Critical Component

**Dynamic Trusted Mode Detection:**
```javascript
function isWidgetTrusted() {
    // Checks at RUNTIME, not module load time
    return window.widget &&
           typeof call3DSpace === 'function' &&
           window.widget.uwaUrl;
}
```

**Automatic Mode Selection:**
- Tries `call3DSpace()` if in trusted mode
- Falls back to backend proxy if direct call fails
- Clear error messages for debugging

### `widget.js` - UWA Initialization

Based on proven chartjs widget pattern:
- Polling for widget object with retry logic
- Mock widget for standalone mode
- Handles three environments: widget exists, UWA exists, standalone

## Testing

### Test in 3DDashboard

1. Deploy to GitHub Pages
2. Create Additional App
3. Verify console logs:
   ```
   [Widget] Widget object ready
   [ApiService] Running in trusted mode (3DDashboard)
   [ApiService] Direct call succeeded
   ```

### Test Standalone

1. Start backend proxy:
   ```bash
   cd ../backend
   python -m app.main
   ```

2. Start widget dev server:
   ```bash
   npm start
   ```

3. Verify console logs:
   ```
   [ApiService] Not in trusted mode
   [ApiService] Using backend proxy
   ```

## Troubleshooting

### Widget shows blank page in 3DDashboard

- Check browser console for errors
- Verify UWA initialization: look for `[Widget] Widget object ready`
- Ensure widget.json is in dist/

### "Backend proxy not configured" error

- Expected in 3DDashboard (should use direct API calls)
- In standalone mode: start backend server

### Fonts don't load

- GitHub Pages CORS issue (cosmetic only)
- Icons still work via MDI font

## Built With

- **Vue 2.6.12** - Progressive JavaScript framework
- **Vuetify 2.3.17** - Material Design component framework
- **Vuex 3.5.1** - State management
- **Webpack 4** - Module bundler
- **@widget-lab/platform-connectors** - 3DDashboard integration

## License

MIT

## Authors

AI Assistant Team
