# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**agent-chat-hub** is a multi-model AI agent chat system that allows users to interact with multiple AI models (Claude, Codex, Gemini) through a unified TUI (Terminal User Interface). The system features multi-agent coordination through a response coordinator, session management, and a plugin architecture.

**Tech Stack**: Python 3.14+, Textual (TUI), Pydantic v2, LangGraph, structlog, httpx, keyring

## Core Architecture

### Three-Layer Design

**1. Core Layer (src/core/)**
- **ConfigManager**: Loads/manages model configs, agent configs, and API keys (stored securely via keyring)
- **MessageValidator**: Auto-repairs malformed JSON responses from agents
- **Message/SessionConfig/ModelConfig/AgentConfig**: Pydantic data models for type safety

**2. Agent Layer (src/agents/)**
- **ResponseCoordinator**: 6 coordination rules for multi-agent orchestration:
  1. **Qualification**: Route based on @mentions or coordinator role
  2. **Ordering**: Sort by priority (ascending) then agent_id (alphabetic)
  3. **Deduplication**: Prevent duplicate calls within same round (session, round_num, agent_id)
  4. **Cancellation**: Block new calls after user cancellation
  5. **Budget**: Enforce MVP limits (3 agents, 3 calls/round, 12k tokens, 120s timeout)
  6. **Stop**: Six stopping conditions (timeout, max calls, max tokens, cancellation, no agents, round complete)
- **AgentExecutor**: Async API calls to Anthropic/OpenAI, handles streaming responses
- **SessionManager**: Conversation history, session persistence, orchestrates coordinator + executor
- **MessageBus**: Event-driven communication between agents (pub/sub)

**3. UI Layer (src/tui/)**
- **TUI Application** (Textual-based):
  - Agent panels showing response streams in real-time
  - Input screen with @mention support (coordinator can @other agents to trigger collaboration)
  - Status bar showing token/budget usage and model info
  - Config management screens
  - Plugin management interface

### Key Design Decisions

- **TUI over Web**: Chosen for lower latency and better terminal integration (see `docs/adr/0001-采用TUI替代React-Web界面.md`)
- **Pydantic v2**: Strong type validation for configs and messages
- **LangGraph**: Stateful multi-turn conversations with checkpoint persistence
- **keyring**: Secure API key storage (system credential store, not file-based)

## Development Workflow

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Common Commands

```bash
# Run the application
python main.py
# or use the entrypoint: agent-chat-hub

# Run all tests (58 tests: 45 unit + 13 integration, 100% pass rate)
pytest tests/ -v

# Run specific test file
pytest tests/test_coordinator.py -v

# Run a single test
pytest tests/test_coordinator.py::test_qualification_with_mentions -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Lint with black and ruff
black src tests
ruff check src tests --fix
```

### Configuration

Configuration stored in `~/.agent-chat-hub/`:
- **models.json**: Model provider configs (Anthropic, OpenAI)
- **agents.json**: Agent definitions with priority, role_type (coordinator/worker), capabilities
- **sessions/**: Conversation history (persisted to SQLite via LangGraph checkpoint)

First run will prompt for model setup. API keys are stored securely in system keyring.

## Testing

**Test Structure**:
- **Unit tests** (45): Core coordinator logic (6 rules), MessageBus, MessageValidator
- **Integration tests** (13): Full coordination flows, concurrent agent calls, response handling

**Test Files**:
- `tests/test_coordinator.py`: ResponseCoordinator (all 6 rules)
- `tests/test_message_bus.py`: Event-driven messaging
- `tests/integration/test_role_system_integration.py`: Full multi-agent flows

Before committing, ensure `pytest tests/ -v` passes.

## Code Style

- **Black**: Line length 100, Python 3.14
- **Ruff**: Linting with same config
- **Type hints**: Required for all functions (Pydantic validation enforces this)
- **Async/await**: All agent executor calls are async for concurrency
- **Logging**: Use structlog (configured in logger setup, avoid print statements)

## Recent Features

### Phase 3: Plugin System
- Plugin registry and loader (`src/core/plugin_system.py`)
- Plugin API: Agent, Config, Message, TUI hooks
- Example: Hello plugin in `src/plugins/hello/`
- TUI interface for plugin management

### Phase 2.1: @mention Coordination
- Coordinator can @mention other agents to trigger collaboration
- Supports partial matching (case-insensitive)
- Routes messages via MessageBus to mentioned agents
- Enhanced role display in TUI (role_type, coordinator indicator)

### File Operations
- New: `src/core/file_storage.py` (added)
- New: `src/tui/input_screen.py` (added for message input)

## Important Constraints

**MVP Budget Limits** (enforced by ResponseCoordinator):
- Max concurrent agents: 3
- Max calls per round: 3
- Max tokens per round: 12,000
- Timeout: 120 seconds

**Agent Role Types**:
- **coordinator**: Can initiate collaboration, receive user input, delegate to workers
- **worker**: Responds only to coordinator or @mentions

## Files to Know

| Path | Purpose |
|------|---------|
| `main.py` | App entry point, initializes coordinator/executor/session_manager |
| `src/agents/coordinator.py` | 6 coordination rules (most critical logic) |
| `src/agents/executor.py` | Async API calls, streaming responses |
| `src/agents/session.py` | Session lifecycle, message history |
| `src/core/config.py` | Config loading, model/agent management |
| `src/tui/app.py` | TUI entry point (Textual app) |
| `tests/test_coordinator.py` | Rule validation (18 unit tests) |
| `tests/integration/` | End-to-end coordination tests |

## Debugging Tips

- **ResponseCoordinator rules**: Check `qualify_agents()`, `sort_agents()`, `is_duplicate_call()`, `check_budget()`, `should_stop()`
- **Agent execution failures**: Look at `src/agents/executor.py` for API error handling
- **TUI glitches**: Check `src/tui/app.py` for event loop and rendering issues
- **Session persistence**: LangGraph checkpoint stored in `~/.agent-chat-hub/sessions/` (SQLite)
- **Logging**: Enable with `LOGLEVEL=DEBUG` env var if configured
