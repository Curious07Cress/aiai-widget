# AIAI Assistant Component Architecture

This document describes how AIAI assistants interface with external system components. It provides the specifications needed to create stubs for local automation testing without requiring the full AIAI framework.

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Interfaces](#component-interfaces)
3. [Data Structures](#data-structures)
4. [Request Lifecycle](#request-lifecycle)
5. [Stub Implementation Guide](#stub-implementation-guide)

---

## System Overview

```
+------------------+     +-------------------+     +------------------+
|   AIAI Framework |     |  Assistant Factory|     |   LangGraph      |
|                  |---->|  (factory.py)     |---->|   StateGraph     |
|  - HTTP/Lifecycle|     |  - Loads resources|     |  - Executes flow |
|  - Plugin system |     |  - Creates graph  |     |  - State machine |
+------------------+     +-------------------+     +------------------+
        |                        |                        |
        v                        v                        v
+------------------+     +-------------------+     +------------------+
|  ConnectionManager|    |  PromptFactory    |     |  MCP Tools       |
|  - Service config |    |  - Template lookup|     |  - CAD integration|
+------------------+     +-------------------+     +------------------+
        |                        |                        |
        v                        v                        v
+------------------+     +-------------------+     +------------------+
|  LLM Factory     |     |  Checkpointer     |     |  StreamingIterator|
|  - Model creation|     |  - State persist  |     |  - Real-time UI  |
+------------------+     +-------------------+     +------------------+
```

### Components to Stub

| Component | Import Path | Purpose |
|-----------|-------------|---------|
| `AIAIAgent` | `i3dx_aiassistant.core.agents.agent` | Base class for factory |
| `RequestContext` | `i3dx_aiassistant.core.common.schemas` | Request metadata |
| `ConnectionManager` | `i3dx_aiassistant.core.connections.connection_manager` | Service connectivity |
| `PromptFactory` | `i3dx_aiassistant.core.templates.prompt` | Template retrieval |
| `StreamingIterator` | `i3dx_aiassistant.core.agents.streaming_iterator` | Response streaming |
| `ParamsSchema` | `i3dx_aiassistant.core.common.schemas` | Parameter base class |
| `LLMParams` | `i3dx_aiassistant.core.common.schemas` | LLM configuration |
| `IAgentPlugin` | `i3dx_aiassistant.core.common.plugins` | Plugin registration |
| `ResponseHandler` | `i3dx_aiassistant.core.response.handler` | Output formatting |

---

## Component Interfaces

### 1. AIAIAgent (Base Class)

The factory class extends `AIAIAgent` which provides resource loading capabilities.

```python
class AIAIAgent:
    """Base class for AIAI agent factories."""

    def __init__(self, config: Dict[str, Any], *args, **kwargs) -> None:
        """
        Initialize with AIAI configuration.

        Args:
            config: Dictionary containing AIAI configuration including
                    LLM settings, MCP tool configs, prompt paths, etc.
        """
        self.config = config

    @property
    def llm_factory(self) -> "LLMFactory":
        """Returns the LLM factory for creating language models."""
        pass

    @property
    def tool_loader(self) -> "ToolLoader":
        """Returns the tool loader for loading MCP tools and checkpointers."""
        pass

    async def acreate(
        self,
        params: "ParamsSchema",
        context: "RequestContext",
        connection_manager: "ConnectionManager",
        streaming_iterator: "StreamingIterator",
        agent_name: str,
        agent_version: str,
        *args,
        **kwargs
    ) -> "StateGraph":
        """
        Create and return the LangGraph workflow.

        This method is called by the AIAI framework to obtain
        the compiled graph for request execution.

        Args:
            params: Agent parameters from request
            context: Request context with metadata
            connection_manager: Service connectivity manager
            streaming_iterator: For real-time UI updates
            agent_name: Registered agent name
            agent_version: Agent version string

        Returns:
            Compiled LangGraph StateGraph ready for execution
        """
        raise NotImplementedError
```

### 2. LLMFactory

Creates LLM instances from configuration.

```python
class LLMFactory:
    """Factory for creating LLM instances."""

    def create(
        self,
        params: "LLMParams",
        context: "RequestContext",
        connection_manager: "ConnectionManager"
    ) -> "BaseChatModel":
        """
        Create an LLM instance.

        Args:
            params: LLM configuration parameters
            context: Request context
            connection_manager: Service connectivity

        Returns:
            LLM instance (LangChain BaseChatModel compatible)
            with .model_name attribute

        Raises:
            RuntimeError: If LLM creation fails
        """
        pass
```

### 3. ToolLoader

Loads MCP tools and checkpointers from AIAI.

```python
class ToolLoader:
    """Loader for MCP tools and other AIAI tools."""

    async def arun(
        self,
        tool_name: str,
        context: "RequestContext",
        connection_manager: "ConnectionManager",
        input_values: Dict[str, Any] = None,
        remote: bool = False
    ) -> Tuple[List[Any], Any, Any]:
        """
        Asynchronously load tools.

        Args:
            tool_name: Name of tool loader (e.g., "mcp_tool_loader")
            context: Request context
            connection_manager: Service connectivity
            input_values: Optional input parameters (e.g., {"args": ""})
            remote: Whether to load from remote service

        Returns:
            Tuple of (tools_list, metadata, extra)
            tools_list contains tool objects with .name attribute
        """
        pass

    def run(
        self,
        tool_name: str,
        context: "RequestContext",
        connection_manager: "ConnectionManager",
        input_values: Dict[str, Any] = None,
        remote: bool = False
    ) -> Tuple[Any, Any, Any]:
        """
        Synchronously load tools (used for checkpointer).

        Args:
            tool_name: Name of tool (e.g., "checkpointer_tool")
            context: Request context
            connection_manager: Service connectivity
            input_values: Optional input parameters
            remote: Whether to load from remote service

        Returns:
            Tuple of (tool_instance, metadata, extra)
        """
        pass
```

### 4. RequestContext

Carries request metadata through the system.

```python
@dataclass
class RequestContext:
    """Request context passed through the entire request lifecycle."""

    request_id: str  # UUID for request tracing
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Used for logging: logger.info(f"[{context.request_id}] message")
```

### 5. ConnectionManager

Manages connections to external services.

```python
class ConnectionManager:
    """Manages service connections and configuration."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with connection configuration.

        Args:
            config: Dictionary with service endpoints, credentials, etc.
        """
        self.config = config

    def get_connection(self, service_name: str) -> Any:
        """Get connection for a specific service."""
        pass

    def get_config(self, key: str) -> Any:
        """Get configuration value."""
        pass
```

### 6. PromptFactory

Retrieves prompt templates from AIAI template storage.

```python
class PromptFactory:
    """Factory for retrieving prompt templates."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with configuration.

        Args:
            config: AIAI configuration dictionary
        """
        self.config = config

    def get_prompt(
        self,
        context: "RequestContext",
        template_name: str,
        template_version: str,
        lang: str
    ) -> Optional["PromptTemplate"]:
        """
        Retrieve a prompt template.

        Args:
            context: Request context
            template_name: Name of template (e.g., "asmstruct_generator")
            template_version: Version string (e.g., "1.0.0")
            lang: Language code (e.g., "en", "ja")

        Returns:
            PromptTemplate object with .template attribute containing
            the prompt string with placeholders like {design_request}

            Returns None if template not found
        """
        pass


class PromptTemplate:
    """Prompt template from AIAI."""

    def __init__(self, template: str):
        """
        Args:
            template: Prompt string with variable placeholders
        """
        self.template = template
```

### 7. StreamingIterator

Streams responses to UI in real-time.

```python
class StreamingIterator:
    """Iterator for streaming responses to UI."""

    async def send(self, chunk: str) -> None:
        """
        Send a text chunk to the UI.

        Args:
            chunk: Text to stream to user
        """
        pass

    async def send_json(self, data: Dict[str, Any]) -> None:
        """
        Send structured data to the UI.

        Args:
            data: JSON-serializable dictionary
        """
        pass

    def is_closed(self) -> bool:
        """Check if the stream is closed."""
        pass
```

### 8. ParamsSchema and LLMParams

Parameter schemas for agent configuration.

```python
@dataclass
class LLMParams:
    """LLM configuration parameters."""

    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30

    def model_copy(self) -> "LLMParams":
        """Create a copy of the parameters."""
        return LLMParams(
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout
        )


@dataclass
class ParamsSchema:
    """Base schema for agent parameters."""

    llm: LLMParams
    prompt_language: str = "en"
    chat_history: List[Dict[str, str]] = field(default_factory=list)
```

### 9. MCP Tool Interface

MCP tools for CAD integration.

```python
class MCPTool:
    """MCP tool for CAD operations."""

    name: str  # Tool identifier (e.g., "solidworks_assembly_structure_tool")

    async def ainvoke(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the MCP tool asynchronously.

        Args:
            input: Dictionary with "input" key containing JSON string
                   Example: {"input": '{"name": "Part", "components": [...]}'}

        Returns:
            Result dictionary from CAD system

        Raises:
            Exception: If MCP invocation fails
        """
        pass

    def invoke(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous version of ainvoke."""
        pass
```

### 10. IAgentPlugin

Plugin registration interface.

```python
class IAgentPlugin:
    """Interface for registering agents with AIAI framework."""

    # Class attributes to be set by implementation
    factory: Type["AIAIAgent"]  # Factory class
    params_schema: Type["ParamsSchema"]  # Parameter schema class
    response_handler: Type["ResponseHandler"]  # Response handler class
    state_schema: Type  # LangGraph state TypedDict
```

### 11. ResponseHandler

Formats responses for AIAI framework.

```python
class ResponseHandler:
    """Handles response formatting for AIAI framework."""

    # Constants for extracting data from state
    MESSAGES_KEY: str = "messages"
    FINAL_OUTPUT_KEY: str = "final_output"

    def get_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract response from final state.

        Args:
            state: Final LangGraph state after execution

        Returns:
            Formatted response dictionary for AIAI
        """
        pass

    def get_stream_response(
        self,
        state: Dict[str, Any],
        chunk: str
    ) -> Dict[str, Any]:
        """
        Format streaming response chunk.

        Args:
            state: Current state
            chunk: Text chunk being streamed

        Returns:
            Formatted chunk for streaming
        """
        pass
```

---

## Data Structures

### AgentState (LangGraph State)

```python
from typing import TypedDict, Annotated, Sequence, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """State passed through LangGraph workflow."""

    # Chat messages with reducer for appending
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Router state for conditional edges
    # Contains: {"question_type": "handle_generate_question", ...}
    router_state: Annotated[Dict[str, str], ...]

    # Memory of generated/modified structures
    # List of versioned snapshots
    state_memory: Annotated[List[Dict[str, Any]], ...]
```

### State Memory Entry

```python
{
    "version": "1.0",
    "timestamp": "2024-01-15T10:30:00Z",
    "operation": "generate",  # or "modify"
    "structure": {
        "name": "ProductName",
        "components": [
            {
                "name": "Component1",
                "quantity": 1,
                "children": []
            }
        ]
    },
    "summary": "Created product structure with 3 components"
}
```

### Classifier Response

```python
{
    "question_type": "handle_generate_question",  # or handle_crud_operation, etc.
    "confidence": 0.95,
    "reasoning": "User wants to create a new structure"
}
```

### Generator/Modifier Response

```python
{
    "summary": "Created laptop structure with screen, keyboard, and battery",
    "structure": {
        "name": "Laptop",
        "components": [
            {"name": "Screen", "quantity": 1},
            {"name": "Keyboard", "quantity": 1},
            {"name": "Battery", "quantity": 1}
        ]
    }
}
```

### MCP Tool Input Format

```python
# Structure is passed as JSON string in "input" key
{
    "input": '{"name": "Laptop", "components": [...]}'
}
```

---

## Request Lifecycle

### Phase 1: Factory Initialization

```
AIAI Framework
    |
    v
Factory.__init__(config)
    |
    +-- Create PromptAdapter (wraps PromptFactory)
    |
    v
Factory ready for requests
```

### Phase 2: Workflow Creation (per request)

```
AIAI Framework calls factory.acreate()
    |
    v
Load LLM
    |-- llm_factory.create(params, context, connection_manager)
    |-- Returns: LLM instance with .model_name
    |
    v
Load MCP Tools
    |-- tool_loader.arun("mcp_tool_loader", context, connection_manager, {"args": ""})
    |-- Returns: List of tools, filter by tool.name
    |
    v
Load Checkpointer (optional)
    |-- tool_loader.run("checkpointer_tool", context, connection_manager)
    |-- Returns: Checkpointer instance or None
    |
    v
Create WorkflowConfig
    |-- Bundles all resources
    |
    v
Build LangGraph via WorkflowOrchestrator
    |-- .set_classifier(handler, routing_map, router_fn)
    |-- .add_agent("generator", handler, needs_mcp=True)
    |-- .add_agent("advisor", handler, needs_mcp=False)
    |-- .compile()
    |
    v
Return compiled StateGraph
```

### Phase 3: Request Execution

```
User message arrives
    |
    v
StateGraph.invoke({"messages": [HumanMessage(content=user_input)]})
    |
    v
Classifier Node
    |-- Validates state
    |-- Gets prompt via prompt_getter
    |-- Invokes LLM
    |-- Parses classification JSON
    |-- Updates router_state
    |
    v
Conditional Edge (based on router_state.question_type)
    |-- "handle_generate_question" -> Generator
    |-- "handle_crud_operation" -> Modifier
    |-- "handle_general_question" -> Advisor
    |-- "handle_unknown_question" -> Fallback
    |
    v
Agent Node (e.g., Generator)
    |-- Validates state and input
    |-- Gets system prompt via prompt_getter
    |-- Invokes LLM with streaming
    |   |-- stream_json_field() streams "summary" to UI
    |-- Parses response JSON
    |-- If needs_mcp:
    |   |-- Calls mcp_tool.ainvoke({"input": json.dumps(structure)})
    |-- Updates state_memory
    |-- Appends AIMessage to messages
    |
    v
END node
    |
    v
ResponseHandler.get_response(state)
    |
    v
Return to AIAI Framework -> User
```

---

## Stub Implementation Guide

### Directory Structure for Stubs

```
tests/
  stubs/
    __init__.py
    aiai_framework/
      __init__.py
      agent.py           # AIAIAgent stub
      schemas.py         # RequestContext, ParamsSchema, LLMParams
      connection.py      # ConnectionManager stub
      prompt.py          # PromptFactory stub
      streaming.py       # StreamingIterator stub
      plugins.py         # IAgentPlugin stub
      response.py        # ResponseHandler stub
    tools/
      __init__.py
      llm.py             # Mock LLM
      mcp.py             # Mock MCP tools
      checkpointer.py    # Mock checkpointer
    fixtures/
      prompts/           # Test prompt files
      responses/         # Mock LLM responses
```

### Stub: AIAIAgent

```python
# tests/stubs/aiai_framework/agent.py

from typing import Dict, Any, Tuple, List
from .schemas import RequestContext, ParamsSchema, LLMParams
from .connection import ConnectionManager
from .streaming import StreamingIterator


class MockLLMFactory:
    """Mock LLM factory for testing."""

    def __init__(self, mock_llm=None):
        self._mock_llm = mock_llm

    def create(
        self,
        params: LLMParams,
        context: RequestContext,
        connection_manager: ConnectionManager
    ):
        if self._mock_llm:
            return self._mock_llm
        return MockLLM(model_name=params.model_name)


class MockToolLoader:
    """Mock tool loader for testing."""

    def __init__(self, tools: Dict[str, Any] = None, checkpointer=None):
        self._tools = tools or {}
        self._checkpointer = checkpointer

    async def arun(
        self,
        tool_name: str,
        context: RequestContext,
        connection_manager: ConnectionManager,
        input_values: Dict[str, Any] = None,
        remote: bool = False
    ) -> Tuple[List[Any], None, None]:
        if tool_name == "mcp_tool_loader":
            return list(self._tools.values()), None, None
        return [], None, None

    def run(
        self,
        tool_name: str,
        context: RequestContext,
        connection_manager: ConnectionManager,
        input_values: Dict[str, Any] = None,
        remote: bool = False
    ) -> Tuple[Any, None, None]:
        if tool_name == "checkpointer_tool":
            return self._checkpointer, None, None
        return None, None, None


class AIAIAgent:
    """Stub base class for AIAI agents."""

    def __init__(self, config: Dict[str, Any], *args, **kwargs):
        self.config = config
        self._llm_factory = MockLLMFactory()
        self._tool_loader = MockToolLoader()

    @property
    def llm_factory(self) -> MockLLMFactory:
        return self._llm_factory

    @property
    def tool_loader(self) -> MockToolLoader:
        return self._tool_loader

    def set_mock_llm(self, llm):
        """Set mock LLM for testing."""
        self._llm_factory = MockLLMFactory(mock_llm=llm)

    def set_mock_tools(self, tools: Dict[str, Any]):
        """Set mock MCP tools for testing."""
        self._tool_loader._tools = tools

    def set_mock_checkpointer(self, checkpointer):
        """Set mock checkpointer for testing."""
        self._tool_loader._checkpointer = checkpointer
```

### Stub: Mock LLM

```python
# tests/stubs/tools/llm.py

from typing import List, Dict, Any, AsyncIterator
from dataclasses import dataclass
import json


@dataclass
class MockAIMessage:
    content: str

    @property
    def type(self):
        return "ai"


class MockLLM:
    """Mock LLM for testing."""

    def __init__(
        self,
        model_name: str = "mock-model",
        responses: Dict[str, str] = None
    ):
        self.model_name = model_name
        self._responses = responses or {}
        self._default_response = json.dumps({
            "summary": "Mock response",
            "structure": {"name": "MockPart", "components": []}
        })
        self._call_count = 0
        self._last_messages = None

    def set_response(self, pattern: str, response: str):
        """Set response for messages containing pattern."""
        self._responses[pattern] = response

    def set_default_response(self, response: str):
        """Set default response when no pattern matches."""
        self._default_response = response

    def _get_response(self, messages: List) -> str:
        """Get response based on message content."""
        last_msg = messages[-1].content if messages else ""

        for pattern, response in self._responses.items():
            if pattern.lower() in last_msg.lower():
                return response

        return self._default_response

    async def ainvoke(self, messages: List) -> MockAIMessage:
        """Async invoke the mock LLM."""
        self._call_count += 1
        self._last_messages = messages
        response = self._get_response(messages)
        return MockAIMessage(content=response)

    def invoke(self, messages: List) -> MockAIMessage:
        """Sync invoke the mock LLM."""
        self._call_count += 1
        self._last_messages = messages
        response = self._get_response(messages)
        return MockAIMessage(content=response)

    async def astream(self, messages: List) -> AsyncIterator[str]:
        """Async stream response chunks."""
        response = self._get_response(messages)
        # Simulate streaming by yielding chunks
        chunk_size = 50
        for i in range(0, len(response), chunk_size):
            yield response[i:i + chunk_size]
```

### Stub: Mock MCP Tool

```python
# tests/stubs/tools/mcp.py

from typing import Dict, Any
import json


class MockMCPTool:
    """Mock MCP tool for testing."""

    def __init__(self, name: str, responses: Dict[str, Any] = None):
        self.name = name
        self._responses = responses or {}
        self._default_response = {"status": "success", "message": "Operation completed"}
        self._invocations = []

    def set_response(self, input_pattern: str, response: Dict[str, Any]):
        """Set response for inputs containing pattern."""
        self._responses[input_pattern] = response

    def set_default_response(self, response: Dict[str, Any]):
        """Set default response."""
        self._default_response = response

    def _get_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get response based on input."""
        input_str = input_data.get("input", "")

        for pattern, response in self._responses.items():
            if pattern.lower() in input_str.lower():
                return response

        return self._default_response

    async def ainvoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Async invoke the mock MCP tool."""
        self._invocations.append(input_data)
        return self._get_response(input_data)

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync invoke the mock MCP tool."""
        self._invocations.append(input_data)
        return self._get_response(input_data)

    def get_invocations(self) -> list:
        """Get all invocations for assertions."""
        return self._invocations

    def get_last_invocation(self) -> Dict[str, Any]:
        """Get the last invocation."""
        return self._invocations[-1] if self._invocations else None

    def clear_invocations(self):
        """Clear invocation history."""
        self._invocations = []
```

### Stub: PromptFactory

```python
# tests/stubs/aiai_framework/prompt.py

from typing import Dict, Any, Optional
from dataclasses import dataclass
import os


@dataclass
class PromptTemplate:
    """Prompt template stub."""
    template: str


class PromptFactory:
    """Mock PromptFactory for testing."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._templates: Dict[str, str] = {}
        self._prompts_dir: Optional[str] = None

    def set_template(self, name: str, lang: str, template: str):
        """Register a template for testing."""
        key = f"{name}_{lang}"
        self._templates[key] = template

    def set_prompts_directory(self, path: str):
        """Set directory to load prompts from files."""
        self._prompts_dir = path

    def get_prompt(
        self,
        context: Any,
        template_name: str,
        template_version: str,
        lang: str
    ) -> Optional[PromptTemplate]:
        """Get a prompt template."""
        key = f"{template_name}_{lang}"

        # Check in-memory templates first
        if key in self._templates:
            return PromptTemplate(template=self._templates[key])

        # Try loading from file
        if self._prompts_dir:
            filepath = os.path.join(self._prompts_dir, f"{key}.txt")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    return PromptTemplate(template=f.read())

        # Return a default template for testing
        return PromptTemplate(
            template=f"Mock template for {template_name} in {lang}"
        )
```

### Stub: StreamingIterator

```python
# tests/stubs/aiai_framework/streaming.py

from typing import List, Dict, Any


class StreamingIterator:
    """Mock StreamingIterator for testing."""

    def __init__(self):
        self._chunks: List[str] = []
        self._json_data: List[Dict[str, Any]] = []
        self._closed = False

    async def send(self, chunk: str) -> None:
        """Record a text chunk."""
        if not self._closed:
            self._chunks.append(chunk)

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Record JSON data."""
        if not self._closed:
            self._json_data.append(data)

    def is_closed(self) -> bool:
        """Check if closed."""
        return self._closed

    def close(self):
        """Close the iterator."""
        self._closed = True

    # Test helper methods
    def get_chunks(self) -> List[str]:
        """Get all recorded chunks."""
        return self._chunks

    def get_full_response(self) -> str:
        """Get concatenated response."""
        return "".join(self._chunks)

    def get_json_data(self) -> List[Dict[str, Any]]:
        """Get all JSON data sent."""
        return self._json_data

    def clear(self):
        """Clear recorded data."""
        self._chunks = []
        self._json_data = []
        self._closed = False
```

### Stub: RequestContext and Schemas

```python
# tests/stubs/aiai_framework/schemas.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import uuid


@dataclass
class RequestContext:
    """Mock RequestContext for testing."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMParams:
    """LLM configuration parameters."""

    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30

    def model_copy(self) -> "LLMParams":
        """Create a copy."""
        return LLMParams(
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout
        )


@dataclass
class ParamsSchema:
    """Base schema for agent parameters."""

    llm: LLMParams = field(default_factory=LLMParams)
    prompt_language: str = "en"
    chat_history: List[Dict[str, str]] = field(default_factory=list)
```

### Stub: ConnectionManager

```python
# tests/stubs/aiai_framework/connection.py

from typing import Dict, Any


class ConnectionManager:
    """Mock ConnectionManager for testing."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._connections: Dict[str, Any] = {}

    def set_connection(self, name: str, connection: Any):
        """Register a mock connection."""
        self._connections[name] = connection

    def get_connection(self, service_name: str) -> Any:
        """Get a connection."""
        return self._connections.get(service_name)

    def get_config(self, key: str) -> Any:
        """Get configuration value."""
        return self.config.get(key)
```

### Example Test Usage

```python
# tests/test_generator_workflow.py

import pytest
import json
from tests.stubs.aiai_framework import (
    AIAIAgent,
    RequestContext,
    ConnectionManager,
    StreamingIterator,
    PromptFactory,
    LLMParams,
)
from tests.stubs.tools import MockLLM, MockMCPTool

from i3dx_aiassistant_asmstruct.asmstruct.aiai.factory import AssemblyStructureAgentFactory
from i3dx_aiassistant_asmstruct.asmstruct.aiai.schemas import AssemblyStructureAgentParams


@pytest.fixture
def mock_llm():
    """Create mock LLM with test responses."""
    llm = MockLLM()

    # Set classifier response
    llm.set_response("classify", json.dumps({
        "question_type": "handle_generate_question",
        "confidence": 0.95
    }))

    # Set generator response
    llm.set_response("design", json.dumps({
        "summary": "Created laptop structure",
        "structure": {
            "name": "Laptop",
            "components": [
                {"name": "Screen", "quantity": 1}
            ]
        }
    }))

    return llm


@pytest.fixture
def mock_mcp_tool():
    """Create mock MCP tool."""
    tool = MockMCPTool(name="solidworks_assembly_structure_tool")
    tool.set_default_response({"status": "success"})
    return tool


@pytest.fixture
def factory(mock_llm, mock_mcp_tool):
    """Create factory with mocked dependencies."""
    factory = AssemblyStructureAgentFactory(config={})
    factory.set_mock_llm(mock_llm)
    factory.set_mock_tools({"solidworks_assembly_structure_tool": mock_mcp_tool})
    return factory


@pytest.mark.asyncio
async def test_generator_creates_structure(factory, mock_mcp_tool):
    """Test that generator creates structure and sends to MCP."""
    # Arrange
    context = RequestContext()
    connection_manager = ConnectionManager()
    streaming_iterator = StreamingIterator()
    params = AssemblyStructureAgentParams(
        llm=LLMParams(),
        prompt_language="en"
    )

    # Act
    graph = await factory.acreate(
        params=params,
        context=context,
        connection_manager=connection_manager,
        streaming_iterator=streaming_iterator,
        agent_name="asmstruct",
        agent_version="1.0.0"
    )

    result = await graph.ainvoke({
        "messages": [{"role": "user", "content": "Design a laptop"}]
    })

    # Assert
    assert mock_mcp_tool.get_invocations()
    last_invocation = mock_mcp_tool.get_last_invocation()
    structure = json.loads(last_invocation["input"])
    assert structure["name"] == "Laptop"
```

---

## Summary

This document provides the complete interface specifications for creating stubs of all AIAI framework components. The key points are:

1. **AIAIAgent** is the base class that factories extend
2. **LLM, MCP tools, and checkpointer** are loaded via factory methods
3. **PromptFactory** provides template retrieval with language support
4. **StreamingIterator** enables real-time UI updates
5. **RequestContext** carries tracing metadata through the system
6. **AgentState** is the LangGraph state structure

Use the stub implementations as a starting point, customizing the mock behaviors for your specific test scenarios.
