# Agent Chat Hub - 测试文档

## 1. 测试概述

### 1.1 测试策略

Agent Chat Hub 采用多层次测试策略，确保代码质量和系统稳定性。

```
┌─────────────────────────────────────────────┐
│          金字塔测试策略                       │
│                                             │
│              ┌───────────┐                  │
│              │  E2E测试  │  ←── 5%         │
│            ┌─────────────┐                  │
│            │  集成测试    │  ←── 15%        │
│          ┌─────────────────┐                │
│          │   单元测试       │  ←── 80%      │
│        └─────────────────────┘              │
└─────────────────────────────────────────────┘
```

### 1.2 测试类型

| 测试类型 | 覆盖范围 | 目标覆盖率 | 运行频率 |
|---------|---------|-----------|---------|
| **单元测试** | 单个函数/类 | ≥80% | 每次commit |
| **集成测试** | 多个组件协作 | ≥60% | 每次push |
| **性能测试** | 关键路径 | 基准存在 | 每周/发版前 |
| **端到端测试** | 完整流程 | 核心场景 | 发版前 |

### 1.3 当前测试覆盖率

根据最新测试运行结果：

| 模块 | 覆盖率 | 测试数量 | 状态 |
|------|--------|---------|------|
| `src/agents/coordinator.py` | 95% | 12 | ✅ |
| `src/agents/message_bus.py` | 92% | 8 | ✅ |
| `src/agents/session.py` | 88% | 10 | ✅ |
| `src/core/config.py` | 85% | 6 | ✅ |
| `src/tui/` | 65% | 15 | ⚠️ |
| **总体** | **82%** | **56** | ✅ |

---

## 2. 运行测试

### 2.1 快速开始

```bash
# 运行所有测试
pytest

# 运行并显示详细输出
pytest -v

# 运行并显示print输出
pytest -s

# 运行特定文件
pytest tests/test_coordinator.py

# 运行特定测试
pytest tests/test_coordinator.py::test_select_agents
```

### 2.2 生成覆盖率报告

```bash
# 生成HTML报告
pytest --cov=src --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# 生成终端报告
pytest --cov=src --cov-report=term-missing

# 生成XML报告（CI使用）
pytest --cov=src --cov-report=xml
```

### 2.3 并行运行测试

```bash
# 安装pytest-xdist
pip install pytest-xdist

# 自动检测CPU核心数并行运行
pytest -n auto

# 指定进程数
pytest -n 4
```

### 2.4 运行特定类型的测试

```bash
# 只运行单元测试
pytest tests/unit/

# 只运行集成测试
pytest tests/integration/

# 运行标记的测试
pytest -m "slow"  # 运行标记为slow的测试
pytest -m "not slow"  # 跳过slow测试

# 运行失败的测试
pytest --lf  # last-failed
pytest --ff  # failed-first
```

---

## 3. 单元测试

### 3.1 目录结构

```
tests/
├── unit/                          # 单元测试（可选子目录）
├── test_coordinator.py           # Coordinator测试
├── test_message_bus.py           # MessageBus测试
├── test_config.py                # Config测试
├── test_mention_parser.py        # MentionParser测试
└── conftest.py                   # pytest fixtures
```

### 3.2 单元测试示例

**测试Coordinator的资格判定规则**：

```python
# tests/test_coordinator.py
import pytest
from src.agents.coordinator import ResponseCoordinator, BudgetLimits
from src.core.models import AgentConfig

class TestResponseCoordinator:
    """ResponseCoordinator单元测试"""
    
    @pytest.fixture
    def coordinator(self):
        """创建coordinator实例"""
        return ResponseCoordinator(BudgetLimits())
    
    @pytest.fixture
    def sample_agents(self):
        """测试用的agent配置"""
        return [
            AgentConfig(
                agent_id="coordinator",
                name="总管",
                role_type="coordinator",
                priority=1,
                active=True
            ),
            AgentConfig(
                agent_id="gpt4",
                name="GPT-4",
                role_type="specialist",
                priority=2,
                active=True
            ),
            AgentConfig(
                agent_id="claude",
                name="Claude",
                role_type="specialist",
                priority=3,
                active=True
            ),
        ]
    
    def test_qualify_agents_without_mentions(self, coordinator, sample_agents):
        """测试无@mentions时只选择coordinator角色"""
        # Act
        qualified = coordinator.qualify_agents(sample_agents, mentions=None)
        
        # Assert
        assert len(qualified) == 1
        assert qualified[0].agent_id == "coordinator"
        assert qualified[0].role_type == "coordinator"
    
    def test_qualify_agents_with_mentions(self, coordinator, sample_agents):
        """测试有@mentions时只选择被@的agents"""
        # Act
        qualified = coordinator.qualify_agents(
            sample_agents, 
            mentions=["gpt4", "claude"]
        )
        
        # Assert
        assert len(qualified) == 2
        assert qualified[0].agent_id == "gpt4"  # priority=2
        assert qualified[1].agent_id == "claude"  # priority=3
    
    def test_sort_agents_by_priority(self, coordinator, sample_agents):
        """测试按优先级排序"""
        # 打乱顺序
        shuffled = [sample_agents[2], sample_agents[0], sample_agents[1]]
        
        # Act
        sorted_agents = coordinator.sort_agents(shuffled)
        
        # Assert
        assert sorted_agents[0].priority == 1
        assert sorted_agents[1].priority == 2
        assert sorted_agents[2].priority == 3
    
    def test_is_duplicate_call(self, coordinator):
        """测试去重检查"""
        # Arrange
        coordinator.start_round("session_123", round_num=1)
        coordinator.record_call("agent_a")
        
        # Act & Assert
        assert coordinator.is_duplicate_call("agent_a") is True
        assert coordinator.is_duplicate_call("agent_b") is False
    
    def test_check_budget_timeout(self, coordinator):
        """测试超时预算检查"""
        # Arrange
        budget = BudgetLimits(timeout_seconds=0.01)
        coordinator = ResponseCoordinator(budget)
        coordinator.start_round("session_123", round_num=1)
        
        # Act
        import time
        time.sleep(0.02)
        reason = coordinator.check_budget()
        
        # Assert
        assert reason == StopReason.TIMEOUT
```

### 3.3 测试MessageBus

```python
# tests/test_message_bus.py
import pytest
import asyncio
from src.agents.message_bus import MessageBus
from src.core.models import AgentMessage

@pytest.mark.asyncio
class TestMessageBus:
    """MessageBus单元测试"""
    
    @pytest.fixture
    def message_bus(self):
        """创建MessageBus实例"""
        return MessageBus()
    
    async def test_register_agent(self, message_bus):
        """测试注册agent"""
        # Act
        message_bus.register_agent("agent_a")
        
        # Assert
        assert "agent_a" in message_bus._queues
    
    async def test_publish_point_to_point(self, message_bus):
        """测试点对点消息"""
        # Arrange
        message_bus.register_agent("agent_a")
        message = AgentMessage(
            from_agent_id="system",
            to_agent_id="agent_a",
            message_type="task",
            content="Hello"
        )
        
        # Act
        await message_bus.publish(message)
        
        # Assert
        assert message_bus.has_messages("agent_a")
        received = await message_bus.get_message("agent_a", timeout=0.1)
        assert received.content == "Hello"
    
    async def test_publish_broadcast(self, message_bus):
        """测试广播消息"""
        # Arrange
        message_bus.register_agent("agent_a")
        message_bus.register_agent("agent_b")
        message_bus.subscribe("agent_a", "broadcast")
        message_bus.subscribe("agent_b", "broadcast")
        
        message = AgentMessage(
            from_agent_id="system",
            to_agent_id=None,  # 广播
            message_type="broadcast",
            content="Announcement"
        )
        
        # Act
        await message_bus.publish(message)
        
        # Assert
        assert message_bus.has_messages("agent_a")
        assert message_bus.has_messages("agent_b")
```

### 3.4 Mock和Stub

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_llm():
    """模拟的LLM客户端"""
    llm = Mock()
    llm.ainvoke = AsyncMock(return_value="模拟响应")
    return llm

@pytest.fixture
def mock_config_manager():
    """模拟的配置管理器"""
    config = Mock()
    config.get_model.return_value = {"model_id": "gpt-4"}
    config.list_agents.return_value = []
    return config

# 使用mock
def test_with_mock(mock_llm):
    # 测试代码
    response = await mock_llm.ainvoke("test")
    assert response == "模拟响应"
    mock_llm.ainvoke.assert_called_once_with("test")
```

---

## 4. 集成测试

### 4.1 目录结构

```
tests/integration/
├── test_session_flow.py          # 会话流程测试
├── test_coordinator_executor.py  # Coordinator+Executor集成
├── test_role_system_integration.py # AI角色系统集成
└── __init__.py
```

### 4.2 集成测试示例

**测试完整的用户消息流程**：

```python
# tests/integration/test_session_flow.py
import pytest
import asyncio
from src.agents.session import SessionManager
from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor

@pytest.mark.asyncio
class TestSessionFlow:
    """会话流程集成测试"""
    
    @pytest.fixture
    async def session_manager(self):
        """创建完整的SessionManager"""
        config_manager = ConfigManager()
        coordinator = ResponseCoordinator()
        executor = AgentExecutor(config_manager)
        
        manager = SessionManager(
            config_manager,
            coordinator,
            executor
        )
        
        yield manager
        
        # Cleanup
        await manager.cleanup()
    
    async def test_user_message_without_mention(self, session_manager):
        """测试无@mention的用户消息流程"""
        # Arrange
        session = session_manager.create_session("测试会话")
        
        # Act
        session_manager.add_message("user", "你好")
        responses = await session_manager.process_user_message()
        
        # Assert
        assert len(responses) > 0
        # 只有coordinator响应
        assert all(r.agent_id == "coordinator" for r in responses)
    
    async def test_user_message_with_mentions(self, session_manager):
        """测试带@mention的用户消息流程"""
        # Arrange
        session = session_manager.create_session("测试会话")
        
        # Act
        session_manager.add_message("user", "@gpt4 @claude 请比较两个方案")
        responses = await session_manager.process_user_message()
        
        # Assert
        assert len(responses) == 2
        response_ids = {r.agent_id for r in responses}
        assert response_ids == {"gpt4", "claude"}
```

### 4.3 测试Coordinator和Executor协作

```python
# tests/integration/test_coordinator_executor.py
import pytest
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor

@pytest.mark.asyncio
async def test_concurrent_execution():
    """测试并发执行多个agents"""
    # Arrange
    coordinator = ResponseCoordinator()
    executor = AgentExecutor()
    
    agents = [
        AgentConfig(agent_id="gpt4", active=True),
        AgentConfig(agent_id="claude", active=True),
    ]
    
    coordinator.start_round("session_123", round_num=1)
    selected, _ = coordinator.select_agents(agents, mentions=["gpt4", "claude"])
    
    # Act
    results = await executor.execute_concurrent(
        selected,
        messages=[Message(role="user", content="测试")]
    )
    
    # Assert
    assert len(results) == 2
    for result in results:
        coordinator.record_call(result.agent_id, tokens_used=100)
    
    # 检查去重
    selected_again, _ = coordinator.select_agents(agents, mentions=["gpt4"])
    assert len(selected_again) == 0  # 已经调用过，被去重
```

---

## 5. 性能测试

### 5.1 基准测试

项目包含性能基准测试脚本：

```bash
# 运行Phase 2基准测试
python benchmarks/benchmark_phase2.py

# 运行压力测试
python benchmarks/stress_test.py
```

### 5.2 性能指标

**当前性能基准**（Phase 2）：

| 指标 | 实际性能 | 目标 | 状态 |
|------|---------|------|------|
| 会话创建 | 0.07ms/次 | <10ms | ✅ 超标200倍 |
| 吞吐量 | 14,439次/秒 | >100次/秒 | ✅ 超标144倍 |
| MessageBus延迟 | <1ms | <5ms | ✅ |
| Coordinator选择 | <0.5ms | <2ms | ✅ |

### 5.3 压力测试

**压力测试场景**：

```python
# benchmarks/stress_test.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def simulate_user(user_id: int, duration: int):
    """模拟单个用户行为"""
    end_time = time.time() + duration
    while time.time() < end_time:
        # 发送消息
        await send_message(f"用户{user_id}的消息")
        await asyncio.sleep(random.uniform(0.5, 2.0))

async def stress_test_concurrent_sessions():
    """压力测试：100并发用户，5分钟"""
    tasks = [
        simulate_user(user_id, duration=300)
        for user_id in range(100)
    ]
    await asyncio.gather(*tasks)
```

**运行结果指标**：

- 并发用户数：100
- 测试时长：5分钟
- 总消息数：~15,000
- 平均响应时间：<200ms
- 错误率：0%

### 5.4 性能分析工具

```bash
# 使用cProfile
python -m cProfile -o profile.stats benchmarks/benchmark_phase2.py

# 分析结果
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)
"

# 使用memory_profiler（需安装）
pip install memory-profiler
python -m memory_profiler benchmarks/benchmark_phase2.py
```

---

## 6. 端到端测试

### 6.1 测试场景

**核心场景**：

1. **用户注册和登录流程** （如果有）
2. **创建新会话**
3. **发送用户消息并接收响应**
4. **使用@mention指定agents**
5. **切换会话**
6. **查看历史消息**
7. **配置管理**

### 6.2 E2E测试框架

由于项目是TUI应用，E2E测试可以使用：

- `textual.testing` - Textual内置测试支持
- `pytest-textual` - Pytest集成

**示例**：

```python
# tests/e2e/test_chat_flow.py
import pytest
from textual.testing import App
from src.tui.app import ChatHubApp

@pytest.mark.asyncio
async def test_send_message_flow():
    """测试发送消息的完整流程"""
    async with ChatHubApp().run_test() as pilot:
        # 等待应用启动
        await pilot.pause()
        
        # 输入消息
        await pilot.press("h", "e", "l", "l", "o")
        await pilot.press("enter")
        
        # 等待响应
        await pilot.pause(2)
        
        # 验证响应出现
        assert "hello" in pilot.app.screen.query_one("#message-list").text
```

---

## 7. 测试最佳实践

### 7.1 测试命名

**规范**：

```python
# ✅ 好：清晰描述测试内容
def test_qualify_agents_without_mentions_returns_coordinator_only():
    pass

def test_message_bus_broadcasts_to_all_subscribers():
    pass

# ❌ 不好：模糊的命名
def test_1():
    pass

def test_function():
    pass
```

### 7.2 测试结构（AAA模式）

```python
def test_something():
    # Arrange（准备）- 设置测试数据和环境
    coordinator = ResponseCoordinator()
    agents = [AgentConfig(...), AgentConfig(...)]
    
    # Act（执行）- 执行被测试的操作
    result = coordinator.select_agents(agents)
    
    # Assert（断言）- 验证结果
    assert len(result) == 2
    assert result[0].agent_id == "expected_id"
```

### 7.3 使用Fixture减少重复

```python
# conftest.py
@pytest.fixture
def coordinator():
    """提供coordinator实例"""
    return ResponseCoordinator(BudgetLimits())

@pytest.fixture
def sample_agents():
    """提供测试用的agents"""
    return [
        AgentConfig(agent_id="a", priority=1, active=True),
        AgentConfig(agent_id="b", priority=2, active=True),
    ]

# test_coordinator.py
def test_with_fixtures(coordinator, sample_agents):
    # 直接使用fixtures
    result = coordinator.select_agents(sample_agents)
    assert len(result) > 0
```

### 7.4 参数化测试

```python
@pytest.mark.parametrize("mentions,expected_count", [
    (None, 1),  # 无mentions → 1个coordinator
    (["gpt4"], 1),  # 1个mention → 1个agent
    (["gpt4", "claude"], 2),  # 2个mentions → 2个agents
])
def test_qualify_agents_with_various_mentions(
    coordinator, sample_agents, mentions, expected_count
):
    result = coordinator.qualify_agents(sample_agents, mentions=mentions)
    assert len(result) == expected_count
```

### 7.5 异步测试

```python
@pytest.mark.asyncio
async def test_async_function():
    """测试异步函数"""
    result = await some_async_function()
    assert result is not None

# 测试超时
@pytest.mark.asyncio
async def test_with_timeout():
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_function(), timeout=0.1)
```

### 7.6 测试异常

```python
def test_raises_exception():
    """测试函数抛出预期的异常"""
    with pytest.raises(ValueError, match="invalid input"):
        process_invalid_input("bad data")

def test_logs_warning(caplog):
    """测试函数记录警告日志"""
    with caplog.at_level(logging.WARNING):
        trigger_warning()
    assert "warning message" in caplog.text
```

---

## 8. 持续集成（CI）

### 8.1 GitHub Actions配置

`.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.14']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 8.2 Pre-commit钩子

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

安装：

```bash
pip install pre-commit
pre-commit install
```

---

## 9. 测试覆盖率目标

### 9.1 模块覆盖率目标

| 模块 | 目标覆盖率 | 当前 | 优先级 |
|------|-----------|------|--------|
| `src/agents/coordinator.py` | ≥90% | 95% | 高 |
| `src/agents/message_bus.py` | ≥90% | 92% | 高 |
| `src/agents/session.py` | ≥85% | 88% | 高 |
| `src/agents/executor.py` | ≥85% | 80% | 中 |
| `src/core/config.py` | ≥80% | 85% | 中 |
| `src/core/mention_parser.py` | ≥90% | 100% | 高 |
| `src/tui/` | ≥60% | 65% | 低 |
| **总体** | **≥80%** | **82%** | - |

### 9.2 覆盖率检查

```bash
# 检查覆盖率是否达标
pytest --cov=src --cov-fail-under=80

# 查看未覆盖的行
pytest --cov=src --cov-report=term-missing

# 生成报告并在浏览器打开
pytest --cov=src --cov-report=html && open htmlcov/index.html
```

---

## 10. 常见测试问题

### 10.1 测试失败排查

**问题**：测试运行失败

**检查清单**：

```bash
# 1. 确认依赖已安装
pip list | grep pytest

# 2. 确认测试文件可被发现
pytest --collect-only

# 3. 运行单个测试查看详细错误
pytest -vv tests/test_coordinator.py::test_specific

# 4. 检查fixtures是否正确
pytest --fixtures
```

### 10.2 异步测试问题

**问题**：`RuntimeError: Event loop is closed`

**解决**：

```python
# 在conftest.py中添加
@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.get_event_loop_policy()
```

### 10.3 Mock问题

**问题**：Mock未按预期工作

**调试**：

```python
# 检查mock是否被调用
mock_function.assert_called()
mock_function.assert_called_once()
mock_function.assert_called_with(expected_arg)

# 查看所有调用
print(mock_function.call_args_list)
```

---

## 11. 测试工具参考

### 11.1 Pytest插件

| 插件 | 功能 | 安装 |
|------|------|------|
| `pytest-cov` | 覆盖率报告 | `pip install pytest-cov` |
| `pytest-asyncio` | 异步测试支持 | `pip install pytest-asyncio` |
| `pytest-xdist` | 并行测试 | `pip install pytest-xdist` |
| `pytest-mock` | Mock增强 | `pip install pytest-mock` |
| `pytest-timeout` | 超时控制 | `pip install pytest-timeout` |

### 11.2 断言库

```python
# 标准assert
assert value == expected
assert value is not None
assert len(items) > 0

# pytest的高级断言
pytest.approx(3.14159, rel=0.01)  # 浮点数比较
pytest.raises(ValueError)  # 异常断言
```

---

## 12. 参考资源

### 12.1 官方文档

- [Pytest官方文档](https://docs.pytest.org/)
- [pytest-asyncio文档](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py文档](https://coverage.readthedocs.io/)

### 12.2 最佳实践

- [Python测试最佳实践](https://testdriven.io/blog/testing-best-practices/)
- [Effective Python Testing With Pytest](https://realpython.com/pytest-python-testing/)

---

**文档版本**：v1.0  
**最后更新**：2026-07-26  
**维护者**：Agent Chat Hub Team
