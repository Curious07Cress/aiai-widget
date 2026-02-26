# MCP Proxy Local Development Architecture

## Overview

This document describes the local development architecture for the AI Assembly Structure project, enabling development and testing without the 3DEXPERIENCE cloud.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LOCAL DEVELOPMENT FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Terminal Chat   │  User interface (replaces AURA UI for chat)
│  (chat_client.py)│
└────────┬─────────┘
         │ HTTP POST /api/v1/agents/{agent_id}/submit
         ▼
┌──────────────────┐
│ ai-assembly-     │  AI Agent Backend (Python)
│ structure        │  - Processes user requests
│ (port 5210)      │  - Calls MCP tools via WebSocket
└────────┬─────────┘
         │ WebSocket (JSON-RPC 2.0)
         ▼
┌──────────────────┐
│ AIAI Proxy Mock  │  MCP Protocol Bridge (Python)
│ (port 8289)      │  - Handles tools/context, tools/initialize,
│                  │    tools/list, tools/call
└────────┬─────────┘
         │ WebSocket (JSON-RPC 2.0)
         ▼
┌──────────────────┐
│ CEF Browser      │  Embedded Chromium in SolidWorks
│ (JS Injection)   │  - MockAIAIEventsManager.js
│                  │  - localDevPromise.js
└────────┬─────────┘
         │ dscef.sendString(JSON)
         ▼
┌──────────────────┐
│ C# SWEventListener│  Event Router
│                  │  - Routes MCP events to appropriate Assistant
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ AssyStructAssistant│  MCP Tool Implementation
│ (C#)             │  - HandleContextEvent()
│                  │  - HandleInitializeEvent()
│                  │  - HandleListToolsEvent()
│                  │  - HandleCallToolEvent()
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ SolidWorks API   │  CAD Operations
│                  │  - Assembly structure generation
│                  │  - Feature manipulation
└──────────────────┘
```

## Components

### 1. Terminal Chat Client (`chat_client.py`)
- **Location:** `E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src\i3dx_aiassistant_asmstruct\mcp_mock_server\chat_client.py`
- **Purpose:** Interactive terminal UI for sending chat messages
- **Replaces:** AURA chat UI (we do NOT use AURA UI for chat)
- **Protocol:** HTTP POST to ai-assembly-structure

### 2. AI Assembly Structure Server (port 5210)
- **Location:** `E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src\i3dx_aiassistant_asmstruct\main.py`
- **Purpose:** AI agent backend that processes user requests
- **Config:** `E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai_agent\src\config\config.json`
- **Protocol:** HTTP API + WebSocket to MCP proxy

### 3. AIAI Proxy Mock (port 8289)
- **Location:** `E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src\i3dx_aiassistant_asmstruct\mcp_mock_server\aiai_proxy_mock.py`
- **Purpose:** Bridges ai-assembly-structure to SolidWorks via MCP protocol
- **Protocol:** WebSocket JSON-RPC 2.0
- **MCP Events Handled:**
  - `tools/context` - Context/capability exchange
  - `tools/initialize` - Server initialization
  - `tools/list` - List available MCP tools
  - `tools/call` - Execute MCP tool

### 4. CEF Browser (JavaScript Injection)
- **Files:**
  - `E:\SW_AICollab\sldAura\MockAIAIEventsManager.js` - WebSocket client, routes MCP events
  - `E:\SW_AICollab\sldAura\localDevPromise.js` - Bridges JS to C# via dscef.sendString()
- **Purpose:** Connects to AIAI Proxy Mock, forwards events to C#
- **Injection Trigger:** When `LocalDev=1` registry key is set

### 5. C# SWEventListener
- **Location:** `E:\SW_AICollab\sldAura\SWEventListener.cs`
- **Purpose:** Receives events from JavaScript, routes to appropriate Assistant
- **Key Methods:**
  - `OnViewReady()` - Injects JavaScript when browser loads
  - Event handlers for MCP events

### 6. AssyStructAssistant (C#)
- **Location:** `E:\SW_AICollab\sldAura\Competencies\AssyStructAssistant.cs`
- **Purpose:** Implements MCP tool handlers for assembly structure operations
- **Key Methods:**
  - `HandleContextEvent()` - Sends context/capabilities
  - `HandleInitializeEvent()` - Returns server info
  - `HandleListToolsEvent()` - Returns available tools
  - `HandleCallToolEvent()` - Executes tool and returns result
- **Uses:** `window._sendContext()`, `window._sendInitResult()`, `window._sendListToolsResult()`, `window._sendCallToolResult()`
- **Does NOT use:** `dsGenUXAIAIEventsManager` (refactored out)

## JavaScript Injection Flow

### Injection Trigger Point

The earliest possible injection happens at **CEF browser LoadEndNotify**:

```
SolidWorks starts
    ↓
sldAura.dll loads (add-in)
    ↓
Tab inserted in right pane manager ("AI Lab")
    ↓
User clicks "Assembly Structure" button  ← EARLIEST USER ACTION
    ↓
CEF browser created and loads URL
    ↓
LoadEndNotify() called (httpStatus received)  ← INJECTION TRIGGER
    ↓
Check IsLocalDevModeEnabled()
    ↓
If LocalDev=1: Call OnViewReady() immediately
    ↓
OnViewReady() calls ReadEmbeddedJavaScript()
    ↓
Inject: window.__localDevWsUrl + MockAIAIEventsManager.js + localDevPromise.js
    ↓
MockAIAIWidgetEventsManager connects to ws://localhost:8289/ws
    ↓
Sends "solidworks/ready" notification
    ↓
Ready to receive MCP events
```

### Key Code Locations

**LoadEndNotify (Trigger):**
```csharp
// E:\SW_AICollab\sldAura\cefbrowserhandler.cs:101-133
public void LoadEndNotify(int httpStatus)
{
    bool isLocalDev = SldAuraUtils.IsLocalDevModeEnabled();

    if (isLocalDev && m_jsEventListener != null)
    {
        m_jsEventListener.OnViewReady();  // Triggers injection
    }
}
```

**OnViewReady (Injection):**
```csharp
// E:\SW_AICollab\sldAura\SWEventListener.cs:427-484
public async void OnViewReady()
{
    string jsStr = SldAuraUtils.ReadEmbeddedJavaScript();
    mCEFBrowser.ExecuteJS(jsStr);  // Injects JS into browser
    m_auraInitedAndReady = true;
}
```

**ReadEmbeddedJavaScript (Script Assembly):**
```csharp
// E:\SW_AICollab\sldAura\Utils\SldAuraUtils.cs:223-291
public static string ReadEmbeddedJavaScript()
{
    if (IsLocalDevModeEnabled())
    {
        // Local dev: MockAIAIEventsManager + localDevPromise
        string wsUrl = GetLocalDevWebSocketUrl();
        sb.AppendLine($"window.__localDevWsUrl = '{wsUrl}';");
        sb.AppendLine(ReadEmbeddedResource("MockAIAIEventsManager.js"));
        sb.AppendLine(ReadEmbeddedResource("localDevPromise.js"));
        return sb.ToString();
    }
    else
    {
        // Cloud: newPromise.js (uses real AIAIWidgetEventsManager)
        return ReadEmbeddedResource("newPromise.js");
    }
}
```

## Registry Configuration

### Enable Local Development Mode
```
Key:   HKCU\Software\Dassault Systemes\SolidWorksPDM\Servers\3DEXPERIENCE
Value: LocalDev (DWORD)
Data:  1
```

### Custom WebSocket URL (Optional)
```
Key:   HKCU\Software\Dassault Systemes\SolidWorksPDM\Servers\3DEXPERIENCE
Value: LocalDevWebSocketUrl (String)
Data:  ws://localhost:8289/ws  (default if not set)
```

### Enable Debug Console (Optional)
```
Key:   HKCU\Software\Dassault Systemes\SolidWorksPDM\Servers\3DEXPERIENCE
Value: ShowDevConsole (DWORD)
Data:  1
```

## Startup Sequence

### Step 1: Start Python Servers
```bash
# Option A: Use startup script
python E:\repo\ai-assistant-assem-struct\scripts\start_local_dev.py --start

# Option B: Manual startup
# Terminal 1: ai-assembly-structure
cd E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src
$env:CONFIG_FILE="E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai_agent\src\config\config.json"
python -m uvicorn i3dx_aiassistant_asmstruct.main:app --host localhost --port 5210

# Terminal 2: AIAI Proxy Mock
cd E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src
python -m i3dx_aiassistant_asmstruct.mcp_mock_server.aiai_proxy_mock --port 8289
```

### Step 2: Start SolidWorks
1. Ensure `LocalDev=1` registry key is set
2. Launch SolidWorks
3. Click "Assembly Structure" button in AI Lab tab
4. Watch AIAI Proxy Mock console for "SOLIDWORKS CONNECTED" message

### Step 3: Start Chat Client
```bash
cd E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src
python -m i3dx_aiassistant_asmstruct.mcp_mock_server.chat_client
```

## Logging

### C# Logs (SldAura)
- **Location:** `%LocalAppData%\SldAura\Logs\mcp-server-YYYYMMDD-HHmmss.log`
- **Also:** Visual Studio Debug Output window

### Python Logs
- **ai-assembly-structure:** Console output
- **AIAI Proxy Mock:** Console output with `[AIAI-Proxy-Mock]` prefix

### JavaScript Logs
- **Browser Console:** `[MockMCP]` and `[LocalDev]` prefixed messages
- **Visible if:** CEF remote debugging enabled or `ShowDevConsole=1`

## MCP Protocol Messages

### From AIAI Proxy Mock → SolidWorks

**tools/context:**
```json
{
  "jsonrpc": "2.0",
  "id": "sw_1_abc12345",
  "method": "tools/context",
  "params": {}
}
```

**tools/initialize:**
```json
{
  "jsonrpc": "2.0",
  "id": "sw_2_def67890",
  "method": "tools/initialize",
  "params": {}
}
```

**tools/list:**
```json
{
  "jsonrpc": "2.0",
  "id": "sw_3_ghi11111",
  "method": "tools/list",
  "params": {}
}
```

**tools/call:**
```json
{
  "jsonrpc": "2.0",
  "id": "sw_4_jkl22222",
  "method": "tools/call",
  "params": {
    "name": "solidworks_assembly_structure_tool",
    "arguments": {
      "input": "{\"action\": \"generate\", \"structure\": {...}}"
    }
  }
}
```

### From SolidWorks → AIAI Proxy Mock

**Response (success):**
```json
{
  "jsonrpc": "2.0",
  "id": "sw_4_jkl22222",
  "result": {
    "content": [{"type": "text", "text": "Assembly Structure Generated"}]
  }
}
```

**Response (error):**
```json
{
  "jsonrpc": "2.0",
  "id": "sw_4_jkl22222",
  "error": {
    "code": -32603,
    "message": "Error executing tool: ..."
  }
}
```

## Troubleshooting

### WebSocket Not Connecting
1. Check AIAI Proxy Mock is running on port 8289
2. Verify `LocalDev=1` registry key
3. Check C# logs for `OnViewReady` execution
4. Check browser console for `[MockMCP]` messages

### MCP Events Not Received
1. Verify `solidworks/ready` message received in AIAI Proxy Mock console
2. Check C# logs for `HandleContextEvent`, `HandleInitializeEvent`, etc.
3. Verify JavaScript injection succeeded (check log for script length)

### Tool Execution Fails
1. Check `HandleCallToolEvent` in C# logs
2. Verify tool name matches (`solidworks_assembly_structure_tool`)
3. Check SolidWorks API errors in logs

## Files Reference

| Component | File Location |
|-----------|---------------|
| Startup Script | `E:\repo\ai-assistant-assem-struct\scripts\start_local_dev.py` |
| AI Server | `E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src\i3dx_aiassistant_asmstruct\main.py` |
| AI Server Config | `E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai_agent\src\config\config.json` |
| AIAI Proxy Mock | `E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src\i3dx_aiassistant_asmstruct\mcp_mock_server\aiai_proxy_mock.py` |
| Chat Client | `E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai-assembly-structure\src\i3dx_aiassistant_asmstruct\mcp_mock_server\chat_client.py` |
| MockAIAIEventsManager.js | `E:\SW_AICollab\sldAura\MockAIAIEventsManager.js` |
| localDevPromise.js | `E:\SW_AICollab\sldAura\localDevPromise.js` |
| SWEventListener | `E:\SW_AICollab\sldAura\SWEventListener.cs` |
| AssyStructAssistant | `E:\SW_AICollab\sldAura\Competencies\AssyStructAssistant.cs` |
| CEFBrowserHandler | `E:\SW_AICollab\sldAura\cefbrowserhandler.cs` |
| SldAuraUtils | `E:\SW_AICollab\sldAura\Utils\SldAuraUtils.cs` |
| Logger | `E:\SW_AICollab\sldAura\Utils\Logger.cs` |
| MCP Tool Registry | `E:\repo\ai-assistant-assem-struct\ai-assembly-structure\ai_agent\src\resources\registry\tools\mcp_tool_loader_1.0.0\tools.json` |

---

*Last Updated: January 2026*
