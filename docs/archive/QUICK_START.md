# 🚀 快速开始 - 使用新集成的功能

## 1️⃣ 立即使用（无需配置）

所有5项新功能已自动集成到 `SessionManager`，**完全透明**：

```python
from src.agents.session import SessionManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.core.config import ConfigManager

# 初始化（所有新功能自动启用）
config_manager = ConfigManager()
coordinator = ResponseCoordinator()
executor = AgentExecutor(config_manager)
session_manager = SessionManager(config_manager, coordinator, executor)

# 创建会话
session_manager.create_session("我的会话")

# 使用 - 就这么简单！
responses = await session_manager.process_user_input("@gemini 你好")
```

## 2️⃣ 查看Agent状态

```python
# 获取所有Agent的实时状态
statuses = session_manager.status_manager.get_all_statuses()

for agent_id, state in statuses.items():
    print(f"{agent_id}: {state.status.value}")
    print(f"  耗时: {state.elapsed_seconds:.1f}s")
    print(f"  Token: {state.total_tokens}")
    if state.error:
        print(f"  错误: {state.error}")
```

## 3️⃣ 查看Token统计

```python
# 获取会话统计
stats = session_manager.token_tracker.get_session_stats()

print(f"总输入: {stats['total_input_tokens']:,} tokens")
print(f"总输出: {stats['total_output_tokens']:,} tokens")
print(f"总计: {stats['total_tokens']:,} tokens")
print(f"成本: ${stats['total_cost_usd']:.4f}")

# 按Agent查看
for agent_id, agent_stats in stats['by_agent'].items():
    total = agent_stats['input'] + agent_stats['output']
    print(f"{agent_id}: {total} tokens (${agent_stats['cost']:.4f})")
```

## 4️⃣ 使用@mention（支持模糊匹配）

```python
# 所有这些都能匹配到 agent_gemini
await session_manager.process_user_input("@gemini 你好")   # 精确匹配
await session_manager.process_user_input("@gem 你好")     # 前缀匹配
await session_manager.process_user_input("@mini 你好")    # 包含匹配
await session_manager.process_user_input("@genini 你好")  # 模糊匹配
```

## 5️⃣ 在TUI中显示状态面板

```python
from src.tui.agent_status_panel import AgentStatusPanel, TokenStatsPanel

# 在TUI的compose()方法中添加
def compose(self) -> ComposeResult:
    # ... 其他组件 ...
    
    # 添加状态面板
    yield AgentStatusPanel(self.session_manager.status_manager)
    
    # 添加Token统计面板
    yield TokenStatsPanel(self.session_manager.token_tracker)
```

面板会自动刷新显示：
- **AgentStatusPanel**: 每0.5秒更新一次
- **TokenStatsPanel**: 每1秒更新一次

## 6️⃣ 自动重试（完全透明）

重试机制已集成到 `AgentExecutor`，无需任何配置：

```python
# 这些错误会自动重试3次（指数退避：1s → 2s → 4s）
- TimeoutError
- ConnectionError
- asyncio.TimeoutError
- HTTP 429 (Too Many Requests)
- HTTP 503 (Service Unavailable)
- HTTP 504 (Gateway Timeout)

# 其他错误直接抛出，不重试
```

## 7️⃣ Agent上下文隔离

```python
# 每个Agent有独立的上下文
context = session_manager.context_manager.get_agent_context("agent_gemini")

# 访问Agent的私有消息
for msg in context.session_messages:
    print(msg)

# 访问Agent的私有状态
print(context.state)
```

## 🧪 运行测试

```bash
# 单元测试（5项技术独立验证）
python3 -m pytest test_verification.py -v

# TUI面板测试
python3 test_tui_status_panel.py

# 诊断测试（验证@mention和消息显示）
python3 diagnose_issues.py

# TUI集成测试（完整工作流程）
python3 test_tui_integration.py
```

## 📊 功能展示

运行任意测试脚本，你会看到：

```
📊 Agent执行状态
⚙️ gemini-pro: running (0.2s...)
✅ claude-sonnet: completed (0.1s) | 450 tokens
❌ codex: error (0.1s) | ⚠️ API超时

💰 Token统计
📥 输入: 250 tokens
📤 输出: 650 tokens
📊 总计: 900 tokens
💵 成本: $0.0072

按Agent统计:
  • gemini-pro: 300 tokens ($0.0000)
  • claude-sonnet: 600 tokens ($0.0072)
```

## 📚 更多信息

- **INTEGRATION_SUMMARY.md** - 完整的集成总结
- **INTEGRATION_COMPLETE.md** - 详细的技术文档
- **IMMEDIATE_LEARNING_APPLICATIONS.md** - 原始技术说明

---

**生成日期**: 2026-09-06  
**版本**: v1.0
