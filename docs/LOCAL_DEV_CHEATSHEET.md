# Local Development Cheatsheet

## Quick Start (5 Steps)

```
1. Start Python servers     → python start_local_dev.py --start
2. Start SolidWorks         → Launch SolidWorks application
3. Open Assembly Structure  → Click "Assembly Structure" button in AI Lab tab
4. Wait for connection      → Look for "SOLIDWORKS CONNECTED" in proxy console
5. Send chat message        → Use terminal chat client
```

## Detailed Steps

### Step 1: Start Python Servers
```powershell
cd E:\repo\ai-assistant-assem-struct\scripts
python start_local_dev.py --start
```

This opens two terminal windows:
- **AI Assembly Structure Server** (port 5210) - AI backend
- **AIAI Proxy Mock** (port 8289) - WebSocket bridge to SolidWorks

Wait for both to show they're running.

### Step 2: Start SolidWorks
- Launch SolidWorks normally
- Ensure `LocalDev=1` registry key is set (one-time setup)

### Step 3: Open Assembly Structure Panel
- In SolidWorks, find the **AI Lab** tab in the right pane
- Click **"Assembly Structure"** button
- This triggers JavaScript injection into the CEF browser

### Step 4: Verify Connection
In the **AIAI Proxy Mock** terminal, look for:
```
============================================================
  SOLIDWORKS CONNECTED (Bidirectional Mode)
  Interceptor version: 1.0.0
============================================================
```

If you don't see this, the connection failed. Check:
- Registry key `LocalDev=1` is set
- SolidWorks C# logs at `%LocalAppData%\SldAura\Logs\`

### Step 5: Send Chat Message
```powershell
cd E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src
python -m i3dx_aiassistant_asmstruct.mcp_mock_server.chat_client
```

Or use VS Code debug configuration: **"Chat Client - Interactive"**

---

## Registry Setup (One-Time)

Enable local development mode:
```
Key:   HKCU\Software\Dassault Systemes\SolidWorksPDM\Servers\3DEXPERIENCE
Value: LocalDev (DWORD)
Data:  1
```

Optional - custom WebSocket URL:
```
Value: LocalDevWebSocketUrl (String)
Data:  ws://localhost:8289/ws
```

Optional - show debug console:
```
Value: ShowDevConsole (DWORD)
Data:  1
```

---

## Startup Script Options

```powershell
# Show instructions and status
python start_local_dev.py

# Check if servers are running
python start_local_dev.py --status

# Start all servers (recommended)
python start_local_dev.py --start

# Start only AI server
python start_local_dev.py --start-server

# Start only proxy
python start_local_dev.py --start-proxy

# Show manual commands
python start_local_dev.py --commands
```

---

## Troubleshooting

### No "SOLIDWORKS CONNECTED" message
1. Check `LocalDev=1` registry key
2. Close and reopen Assembly Structure panel
3. Check C# logs: `%LocalAppData%\SldAura\Logs\mcp-server-*.log`

### Tool calls fail with "going away"
- SolidWorks disconnected. Reopen Assembly Structure panel.

### Port already in use
```powershell
# Check what's using the port
netstat -ano | findstr :5210
netstat -ano | findstr :8289

# Kill process if needed
taskkill /PID <pid> /F
```

### Server won't start
```powershell
# Try manual startup to see errors
cd E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src
$env:CONFIG_FILE="E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai_agent\src\config\config.json"
python -m uvicorn i3dx_aiassistant_asmstruct.main:app --host localhost --port 5210
```

---

## Architecture Flow

```
Terminal Chat → HTTP → ai-assembly-structure (5210)
                              ↓
                       WebSocket (MCP)
                              ↓
                     AIAI Proxy Mock (8289)
                              ↓
                       WebSocket (JSON-RPC)
                              ↓
                    CEF Browser (JS Interceptor)
                              ↓
                       dscef.sendString()
                              ↓
                    C# SWEventListener
                              ↓
                    AssyStructAssistant
                              ↓
                       SolidWorks API
```

---

## Log Locations

| Component | Location |
|-----------|----------|
| AI Server | Terminal window (console output) |
| Proxy Mock | Terminal window (console output) |
| SolidWorks C# | `%LocalAppData%\SldAura\Logs\mcp-server-*.log` |
| JavaScript | CEF browser console (if `ShowDevConsole=1`) |

---

*Last Updated: January 2026*
