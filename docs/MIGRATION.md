# API Migration Guide

This guide helps you migrate your code to work with the latest breaking changes introduced in the Evidence Matrix v3 updates.

## Overview

Three breaking changes were introduced to improve API consistency and predictability:

1. `ResponseCoordinator.select_agents()` return value changed
2. `ResponseCoordinator.start_round()` signature changed
3. `ConfigManager` persistence behavior changed

---

## 1. ResponseCoordinator.select_agents() Return Value

### What Changed

**Before**: Returns a list of agents
```python
agents = coordinator.select_agents(qualified_agents)
```

**After**: Returns a tuple `(agents, stop_reason)`
```python
agents, stop_reason = coordinator.select_agents(qualified_agents)
```

### Why

The new return value provides stop reason information, enabling better control flow and debugging.

### Migration Steps

**Option A: Unpack the tuple (recommended)**
```python
# Old code
agents = coordinator.select_agents(qualified_agents)
for agent in agents:
    # process agent
```

**New code**
```python
# New code
agents, stop_reason = coordinator.select_agents(qualified_agents)
for agent in agents:
    # process agent
# Optionally use stop_reason for logging/debugging
```

**Option B: Use only the first element (if you don't need stop_reason)**
```python
agents = coordinator.select_agents(qualified_agents)[0]
```

### Test Coverage

- `tests/test_integration_phase2.py::test_coordinator_with_multiple_agents:170`

---

## 2. ResponseCoordinator.start_round() Signature

### What Changed

**Before**: No required parameters
```python
coordinator.start_round()
```

**After**: Requires `session_id` and `round_num`
```python
coordinator.start_round(session_id="my-session", round_num=1)
```

### Why

Explicit session and round tracking improves state management and debugging capabilities.

### Migration Steps

Update all `start_round()` calls to include required parameters:

```python
# Old code
coordinator.start_round()

# New code
session_id = "your-session-id"  # Get from your session management
round_num = 1  # Track round number in your application
coordinator.start_round(session_id=session_id, round_num=round_num)
```

### Test Coverage

- `tests/test_integration_phase2.py::test_coordinator_with_multiple_agents:154`

---

## 3. ConfigManager Persistence Behavior

### What Changed

**Before**: Automatic persistence (assumed)
```python
config_manager.add_model(model)
# Changes automatically saved
```

**After**: Explicit save/load required
```python
config_manager.add_model(model)
config_manager.save_configs()  # Must call explicitly
```

### Why

Explicit save/load provides better control over when I/O operations occur and reduces unexpected disk writes.

### Migration Steps

**Add explicit save calls after modifications:**

```python
# Old code
config_manager.add_model(model)
config_manager.add_agent(agent)

# New code
config_manager.add_model(model)
config_manager.add_agent(agent)
config_manager.save_configs()  # Explicit save
```

**Add explicit load calls when reading:**

```python
# New code
config_manager = ConfigManager(config_dir)
config_manager.load_configs()  # Explicit load
models = config_manager.list_models()
```

### Rollback Option

If you need automatic persistence for backward compatibility, you can wrap ConfigManager:

```python
class AutoSaveConfigManager(ConfigManager):
    def add_model(self, model):
        super().add_model(model)
        self.save_configs()
    
    def add_agent(self, agent):
        super().add_agent(agent)
        self.save_configs()
```

### Test Coverage

- `tests/test_integration_phase2.py::test_config_persistence:192-212`

---

## Complete Migration Checklist

- [ ] Search codebase for `select_agents(` calls
- [ ] Update all to unpack tuple: `agents, stop_reason = select_agents(...)`
- [ ] Search codebase for `start_round(` calls
- [ ] Update all to include `session_id` and `round_num` parameters
- [ ] Search codebase for `ConfigManager` usage
- [ ] Add `save_configs()` after modifications
- [ ] Add `load_configs()` after initialization
- [ ] Run full test suite to verify: `pytest tests/ -v`
- [ ] Check for deprecation warnings in logs

---

## Verification Commands

```bash
# Search for old API usage patterns
grep -r "select_agents(" src/
grep -r "start_round()" src/
grep -r "ConfigManager(" src/

# Run tests to verify migration
pytest tests/ -v

# Check test coverage
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Support

If you encounter issues during migration:

1. Check test examples in `tests/test_integration_phase2.py`
2. Review complete evidence at `.collab/artifacts/pr-evidence-complete.md`
3. Open an issue on GitHub with your use case

---

**Last Updated**: 2026-07-20  
**Applies To**: PR #1 (Evidence Matrix v3)
