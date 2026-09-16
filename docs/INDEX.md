# Agent Chat Hub Documentation Index

Complete documentation for the Agent Chat Hub project

---

## 📚 Documentation Structure

```
docs/
├── user-guide/          # User guides and manuals
├── api-reference/       # API documentation
├── architecture/        # Architecture and design docs
├── tutorials/           # Step-by-step tutorials
├── deployment/          # Deployment guides
├── adr/                 # Architecture Decision Records
├── api/                 # API specifications
├── plugins/             # Plugin development guides
└── archive/             # Historical documents
```

---

## 🚀 Getting Started

### For Users

1. **[Quick Start Guide](user-guide/QUICKSTART.md)** - Get up and running in 5 minutes
2. **[Configuration Guide](user-guide/CONFIGURATION.md)** - Configure models and agents
3. **[Troubleshooting](user-guide/TROUBLESHOOTING.md)** - Common issues and solutions

### For Developers

1. **[API Reference](api-reference/API.md)** - Complete API documentation
2. **[First Agent Tutorial](tutorials/FIRST_AGENT.md)** - Create your first custom agent
3. **[Architecture Overview](architecture/)** - System architecture and design

---

## 📖 User Guide

### Essential Guides

| Document | Description | Audience |
|----------|-------------|----------|
| [QUICKSTART.md](user-guide/QUICKSTART.md) | 5-minute quick start guide | All users |
| [CONFIGURATION.md](user-guide/CONFIGURATION.md) | Configuration file reference | All users |
| [TROUBLESHOOTING.md](user-guide/TROUBLESHOOTING.md) | Common problems and solutions | All users |

### Topics Covered

- Installation and setup
- API key configuration
- Creating and managing agents
- Using the TUI interface
- @mention syntax and fuzzy matching
- Session management
- Token tracking and cost monitoring
- Error diagnosis and recovery

---

## 🔧 API Reference

### Core APIs

| API | Description | Link |
|-----|-------------|------|
| **AgentExecutor** | Execute agents and get responses | [API.md#agentexecutor](api-reference/API.md#agentexecutor) |
| **SessionManager** | Manage conversation sessions | [API.md#sessionmanager](api-reference/API.md#sessionmanager) |
| **ConfigManager** | Manage configuration | [API.md#configmanager](api-reference/API.md#configmanager) |
| **ContextManager** | Agent context isolation | [API.md#contextmanager](api-reference/API.md#contextmanager) |
| **AgentStatusManager** | Track agent status | [API.md#agentstatusmanager](api-reference/API.md#agentstatusmanager) |
| **TokenTracker** | Track token usage and cost | [API.md#tokentracker](api-reference/API.md#tokentracker) |

### Data Models

- **Message** - Chat message object
- **AgentConfig** - Agent configuration
- **AgentMessage** - Agent response message
- **TokenUsage** - Token usage statistics
- **AgentStatus** - Agent execution status

---

## 🎓 Tutorials

### Step-by-Step Guides

| Tutorial | Level | Time | Link |
|----------|-------|------|------|
| **Create Your First Agent** | Beginner | 15 min | [FIRST_AGENT.md](tutorials/FIRST_AGENT.md) |

### Tutorial Topics

1. Understanding agent structure
2. Designing agent behavior
3. Writing effective system prompts
4. Configuring agents
5. Testing and debugging
6. Advanced configuration
7. Multi-agent collaboration

---

## 🏗️ Architecture

### Architecture Documents

| Document | Description |
|----------|-------------|
| [IMPLEMENTATION_SUMMARY.md](architecture/IMPLEMENTATION_SUMMARY.md) | Phase 3.5 implementation summary |
| [CLI_INTEGRATION_REPORT.md](architecture/CLI_INTEGRATION_REPORT.md) | CLI integration architecture |
| [TECHNOLOGY_ROADMAP_EXECUTIVE_SUMMARY.md](architecture/TECHNOLOGY_ROADMAP_EXECUTIVE_SUMMARY.md) | Technology roadmap |
| [IMMEDIATE_LEARNING_APPLICATIONS.md](architecture/IMMEDIATE_LEARNING_APPLICATIONS.md) | Learning and applications guide |

### ADR (Architecture Decision Records)

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-0001](adr/0001-采用TUI替代React-Web界面.md) | Adopt TUI instead of React Web UI | ✅ Accepted |

---

## 🚀 Deployment

### Deployment Guides

| Document | Description |
|----------|-------------|
| [INTEGRATION_GUIDE.md](deployment/INTEGRATION_GUIDE.md) | Integration and deployment guide |

---

## 🔌 Plugin Development

### Plugin Documentation

Located in `docs/plugins/`:

- Plugin system architecture
- Plugin API reference
- Creating custom plugins
- Plugin examples

---

## 📊 Feature Documentation

### Phase 3.5 Enhanced Features

All five enhanced features implemented in Phase 3.5:

#### 1. Agent Context Isolation

**Description**: Each agent maintains its own independent context

**Documentation**:
- API: [ContextManager](api-reference/API.md#contextmanager)
- Implementation: [IMPLEMENTATION_SUMMARY.md](architecture/IMPLEMENTATION_SUMMARY.md)

**Key Methods**:
- `get_agent_context(agent_id)` - Get agent's context
- `add_message_to_context(agent_id, message)` - Add message to context

#### 2. Real-time Status Tracking

**Description**: Track agent execution status in real-time

**Documentation**:
- API: [AgentStatusManager](api-reference/API.md#agentstatusmanager)
- Tutorial: [QUICKSTART.md](user-guide/QUICKSTART.md)

**Status Types**:
- `IDLE` - Agent is idle
- `PENDING` - Waiting to execute
- `RUNNING` - Currently executing
- `COMPLETED` - Execution completed
- `ERROR` - Execution failed

#### 3. Token Tracking & Cost Calculation

**Description**: Real-time token usage and cost monitoring

**Documentation**:
- API: [TokenTracker](api-reference/API.md#tokentracker)
- Configuration: [CONFIGURATION.md](user-guide/CONFIGURATION.md)

**Features**:
- Per-agent token statistics
- Session-wide token totals
- Real-time cost calculation
- Cost per model/provider

#### 4. Smart Retry Policy

**Description**: Automatic retry with exponential backoff

**Documentation**:
- API: [AgentExecutor](api-reference/API.md#agentexecutor)
- Troubleshooting: [TROUBLESHOOTING.md](user-guide/TROUBLESHOOTING.md)

**Retry Configuration**:
- Max retries: 3
- Base delay: 1s
- Exponential backoff: 2x (1s → 2s → 4s)
- Retryable errors: Timeout, Connection, Rate limit (429), Service unavailable (503/504)

#### 5. Fuzzy @mention Matching

**Description**: Smart agent name matching with fuzzy search

**Documentation**:
- User Guide: [QUICKSTART.md](user-guide/QUICKSTART.md)
- Tutorial: [FIRST_AGENT.md](tutorials/FIRST_AGENT.md)

**Matching Strategies**:
1. Exact match (highest priority)
2. Prefix match
3. Contains match
4. Fuzzy match (case-insensitive)

---

## 🗂️ Archive

Historical documents moved to `docs/archive/`:

- Old quickstart guides
- Analysis documents
- Integration reports
- PRD discussions
- Verification reports

These documents are kept for reference but are no longer actively maintained.

---

## 📝 Document Templates

### Configuration File Template

All configuration files in `.claude/rules/` and `.claude/docs/` must include:

```markdown
## Load Trigger (懒加载条件)

Read this file when:
- [Condition 1]
- [Condition 2]
- [Condition 3]
```

See [handoff.md](../.claude/rules/handoff.md) for format specification.

---

## 🔍 Quick Reference

### Common Tasks

| Task | Document | Section |
|------|----------|---------|
| Install and setup | [QUICKSTART.md](user-guide/QUICKSTART.md) | Steps 1-5 |
| Configure API key | [CONFIGURATION.md](user-guide/CONFIGURATION.md) | API Keys |
| Create new agent | [FIRST_AGENT.md](tutorials/FIRST_AGENT.md) | Full tutorial |
| Fix errors | [TROUBLESHOOTING.md](user-guide/TROUBLESHOOTING.md) | All sections |
| Use API | [API.md](api-reference/API.md) | Complete reference |
| Understand architecture | [Architecture docs](architecture/) | All files |

### Key Concepts

| Concept | Explanation | Where to Learn |
|---------|-------------|----------------|
| **Agent** | AI model instance with specific role and behavior | [FIRST_AGENT.md](tutorials/FIRST_AGENT.md) |
| **Session** | Conversation context and history | [API.md#sessionmanager](api-reference/API.md#sessionmanager) |
| **@mention** | Direct message to specific agent(s) | [QUICKSTART.md](user-guide/QUICKSTART.md) |
| **Token** | Unit of text for billing and limits | [CONFIGURATION.md](user-guide/CONFIGURATION.md) |
| **Provider** | AI model service (Anthropic, OpenAI, etc.) | [CONFIGURATION.md](user-guide/CONFIGURATION.md) |
| **System Prompt** | Instructions that define agent behavior | [FIRST_AGENT.md](tutorials/FIRST_AGENT.md) |

---

## 📖 Reading Paths

### New User Path

1. [QUICKSTART.md](user-guide/QUICKSTART.md) - Get started
2. [CONFIGURATION.md](user-guide/CONFIGURATION.md) - Configure your setup
3. [FIRST_AGENT.md](tutorials/FIRST_AGENT.md) - Create custom agent

### Developer Path

1. [API.md](api-reference/API.md) - Understand the API
2. [Architecture docs](architecture/) - Learn the architecture
3. [FIRST_AGENT.md](tutorials/FIRST_AGENT.md) - Build something

### Troubleshooting Path

1. [TROUBLESHOOTING.md](user-guide/TROUBLESHOOTING.md) - Find your error
2. [CONFIGURATION.md](user-guide/CONFIGURATION.md) - Check configuration
3. [API.md](api-reference/API.md) - Understand the behavior

---

## 🌐 External Resources

### Official Documentation

- **Anthropic Claude**: https://docs.anthropic.com
- **OpenAI GPT**: https://platform.openai.com/docs
- **Google Gemini**: https://ai.google.dev/docs
- **Textual TUI**: https://textual.textualize.io

### Community

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas

---

## 🔄 Document Updates

### Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-09-06 | Initial documentation restructure |

### Contributing to Documentation

To update documentation:

1. Edit the relevant `.md` file
2. Follow the markdown style guide
3. Update this index if adding new documents
4. Submit a pull request

### Style Guide

- Use clear, concise language
- Include code examples
- Add verification steps where applicable
- Use tables for structured data
- Include "Load Trigger" section in config files

---

## 📬 Feedback

Found an error or have a suggestion?

- **Documentation Issues**: [GitHub Issues](https://github.com/yourusername/agent-chat-hub/issues) with "docs" label
- **General Questions**: [GitHub Discussions](https://github.com/yourusername/agent-chat-hub/discussions)

---

**Last Updated**: 2026-09-06  
**Version**: 1.0  
**Maintainer**: caohui
