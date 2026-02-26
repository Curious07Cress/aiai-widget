# Coding Guidelines for AI Assembly Structure Project

## General Principles

### Code Style
- **No Emojis**: NEVER include emojis in code, comments, docstrings, or log messages
- **Clean Code**: Write readable, maintainable code following Python best practices
- **Consistent Formatting**: Use 4 spaces for indentation, follow PEP 8 style guide

### Logging
- Use centralized logging configuration from `logging_config.py`
- Always include `request_id` in log messages when available: `logger.info(f"[{request_id}] message")`
- Use appropriate log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: Confirmation that things are working as expected
  - `WARNING`: Something unexpected but recoverable happened
  - `ERROR`: A serious problem occurred
  - `CRITICAL`: A very serious error that may prevent the program from continuing
- Never use `print()` statements - always use `logger`
- Never call `logging.basicConfig()` - use centralized configuration

### Error Handling
- Use specific exception types (ValueError, TypeError, RuntimeError, etc.)
- Always include descriptive error messages
- Use `throw_error()` from errors.py for HTTP exceptions with proper error codes
- Log exceptions with `logger.exception()` to capture stack traces
- Implement retry logic with max attempts and exponential backoff where appropriate

### Async Operations
- Use `async/await` for all LLM invocations
- Always wrap async operations with `asyncio.wait_for()` and timeout protection (default 30 seconds)
- Handle `asyncio.TimeoutError` explicitly in exception handlers

### Validation
- Validate all function inputs at the start of functions
- Check for None, empty strings, invalid types
- Raise appropriate exceptions with clear messages
- Document validation requirements in docstrings

### Documentation
- Include comprehensive docstrings for all functions and classes
- Use Google-style docstring format with Args, Returns, Raises sections
- Document expected input/output formats for complex data structures
- Keep inline comments concise and meaningful

### File Operations
- Use atomic write patterns (temp file + rename) for critical file operations
- Always specify encoding explicitly: `encoding="utf-8"`
- Use `Path` objects from pathlib for path operations
- Implement automatic backup for corrupted files
- Handle file-specific exceptions: FileNotFoundError, PermissionError, OSError

### State Management
- Use immutable data structures where possible
- Avoid global mutable state
- Thread-safe operations for shared state
- Version and timestamp all state snapshots

### Testing
- Write unit tests for all new functionality
- Test error paths and edge cases
- Mock external dependencies (LLM, MCP tools, file I/O)

## Project-Specific Guidelines

### LLM Response Handling
- Parse JSON responses from LLM carefully with try-except for JSONDecodeError
- Split LLM responses into summary and structure components
- Return full response (summary + structure) to user
- Send only structure to MCP tool
- Validate response schema before processing

### MCP Tool Integration
- Always pass structure as JSON string to MCP tool: `{"input": structure_str}`
- Never pass raw strings or list indices
- Handle MCP tool errors gracefully with proper logging

### Agent Pattern
- All agent handlers should be async functions
- All agents should accept: state, factory, llm, context, prompt_language, request_id
- All agents should return result from `build_agent_state()`
- Validate factory type at start of handler

### Request Tracking
- Generate unique `request_id` for each request (UUID)
- Pass `request_id` through all function calls
- Include in all log messages for traceability

## Anti-Patterns to Avoid

- ❌ Using emojis in code or logs
- ❌ Using `print()` instead of logging
- ❌ Calling `logging.basicConfig()`
- ❌ Synchronous LLM calls without timeouts
- ❌ Generic exception handlers without logging
- ❌ Magic numbers and hardcoded strings
- ❌ Duplicate code across multiple files
- ❌ Missing input validation
- ❌ Unclear variable names
- ❌ Functions longer than 50 lines without good reason
