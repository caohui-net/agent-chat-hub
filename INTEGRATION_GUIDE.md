# 5项Agent交互增强 - 集成指南

**创建日期**: 2026-09-05  
**状态**: ✅ 核心模块已完成，等待集成

---

## ✅ 已完成的模块

| 模块 | 文件 | 行数 | 状态 |
|------|------|------|------|
| Agent隔离 | `src/core/agent_context.py` | 150 | ✅ 完成 |
| @mention增强 | `src/core/mention_matcher.py` | 130 | ✅ 完成 |
| 状态追踪 | `src/core/agent_status.py` | 175 | ✅ 完成 |
| 重试策略 | `src/core/retry_policy.py` | 150 | ✅ 完成 |
| Token追踪 | `src/core/token_tracker.py` | 200 | ✅ 完成 |

**总计**: 805行代码，commit: `cc5fe11`

---

## 📋 集成步骤

### Step 1: 修改 SessionManager (2小时)

**文件**: `src/agents/session.py`

**修改1: 初始化新组件**
```python
# 在 SessionManager.__init__ 中添加
from ..core.agent_context import ContextManager
from ..core.agent_status import AgentStatusManager
from ..core.token_tracker import TokenTracker

class SessionManager:
    def __init__(self, ...):
        # 现有代码
        self.config = config
        self.executor = AgentExecutor(config)
        self.coordinator = ResponseCoordinator(config)
        
        # 新增组件
        self.context_manager = ContextManager()
        self.status_manager = AgentStatusManager()
        self.token_tracker = TokenTracker()
```

**修改2: 在执行中追踪状态和Token**
```python
async def process_user_input(self, user_input: str):
    # 1. 选择Agent（使用增强的@mention匹配）
    selected_agents = self.coordinator.select_agents(...)
    
    # 2. 标记所有Agent为PENDING
    for agent in selected_agents:
        self.status_manager.mark_pending(agent.agent_id)
    
    # 3. 并发执行，带状态追踪
    async def execute_with_tracking(agent):
        try:
            # 标记为RUNNING
            self.status_manager.mark_running(agent.agent_id)
            
            # 获取Agent的独立上下文
            agent_ctx = self.context_manager.get_agent_context(agent.agent_id)
            
            # 执行（在Step 2中添加重试）
            response = await self.executor.execute(agent, messages)
            
            # 记录Token使用
            if hasattr(response, 'usage'):
                from ..core.token_tracker import AgentTokenUsage
                self.token_tracker.record_usage(AgentTokenUsage(
                    agent_id=agent.agent_id,
                    model=agent.model_id,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                ))
                
                # 标记为COMPLETED
                self.status_manager.mark_completed(
                    agent.agent_id,
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )
            
            # 保存到Agent上下文
            agent_ctx.add_message(Message(role="assistant", content=response.content))
            
            return response
            
        except Exception as e:
            self.status_manager.mark_error(agent.agent_id, str(e))
            raise
    
    # 4. 执行所有Agent
    results = await asyncio.gather(
        *[execute_with_tracking(a) for a in selected_agents],
        return_exceptions=True
    )
    
    return results
```

---

### Step 2: 修改 AgentExecutor (1小时)

**文件**: `src/agents/executor.py`

**添加重试支持**
```python
from ..core.retry_policy import RetryPolicy

class AgentExecutor:
    def __init__(self, config):
        self.config = config
        # 新增：重试策略
        self.retry_policy = RetryPolicy(max_retries=3, base_delay=1.0)
    
    async def execute(self, agent, messages):
        """执行Agent，自动重试"""
        return await self.retry_policy.execute_with_retry(
            self._execute_internal,
            agent,
            messages
        )
    
    async def _execute_internal(self, agent, messages):
        """原有的execute逻辑，重命名为_execute_internal"""
        # 原来的 self.execute() 代码移到这里
        return await self._call_anthropic(...)
```

---

### Step 3: 修改 ResponseCoordinator (1小时)

**文件**: `src/agents/coordinator.py`

**使用增强的@mention匹配**
```python
from ..core.mention_matcher import MentionMatcher

class ResponseCoordinator:
    def parse_mentions(self, text: str, available_agents: List[AgentConfig]) -> List[str]:
        """解析@mention并返回匹配的agent_ids"""
        import re
        mentions = re.findall(r'@(\w+)', text)
        matched_agent_ids = []
        
        for mention in mentions:
            agent = MentionMatcher.match_agent(available_agents, mention)
            if agent:
                matched_agent_ids.append(agent.agent_id)
                logger.info(
                    "mention_matched",
                    mention=mention,
                    agent_id=agent.agent_id,
                    agent_name=agent.name
                )
            else:
                logger.warning("mention_no_match", mention=mention)
        
        return matched_agent_ids
```

---

### Step 4: 修改 TUI (2-3小时)

**文件**: `src/tui/app.py`

**添加状态显示面板**
```python
from textual.widgets import Static
from ..core.agent_status import AgentStatus

class AgentStatusPanel(Static):
    """Agent状态显示面板"""
    
    def __init__(self, session_manager):
        super().__init__()
        self.session_manager = session_manager
    
    def render(self) -> str:
        """渲染Agent状态"""
        statuses = self.session_manager.status_manager.get_all_statuses()
        
        if not statuses:
            return "暂无Agent运行"
        
        lines = ["🤖 Agent状态:"]
        
        for agent_id, state in statuses.items():
            icon = {
                AgentStatus.PENDING: "⏳",
                AgentStatus.RUNNING: "⚙️",
                AgentStatus.COMPLETED: "✅",
                AgentStatus.ERROR: "❌",
            }[state.status]
            
            duration = ""
            if state.end_time:
                duration = f" ({state.elapsed_seconds:.1f}s)"
            elif state.start_time:
                duration = f" (进行中...)"
            
            tokens = ""
            if state.total_tokens > 0:
                tokens = f" [{state.total_tokens} tokens]"
            
            lines.append(f"{icon} {agent_id}: {state.status.value}{duration}{tokens}")
        
        return "\n".join(lines)

class ChatApp(App):
    def compose(self) -> ComposeResult:
        # 现有组件
        yield Header()
        yield Horizontal(
            agent_list_panel,
            chat_display,
            file_panel,
            # 新增：状态面板
            AgentStatusPanel(self.session_manager)
        )
    
    async def on_mount(self) -> None:
        # 定时刷新状态面板
        self.set_interval(0.5, self.refresh_agent_status)
    
    def refresh_agent_status(self) -> None:
        """刷新Agent状态显示"""
        status_panel = self.query_one(AgentStatusPanel)
        status_panel.refresh()
```

**添加Token统计显示**
```python
class TokenStatsPanel(Static):
    """Token统计显示"""
    
    def __init__(self, session_manager):
        super().__init__()
        self.session_manager = session_manager
    
    def render(self) -> str:
        return self.session_manager.token_tracker.format_summary()
```

---

## 🧪 测试步骤

### 1. 单元测试 (创建测试文件)

```bash
# 创建测试目录
mkdir -p tests/core

# 测试文件
touch tests/core/test_agent_context.py
touch tests/core/test_mention_matcher.py
touch tests/core/test_agent_status.py
touch tests/core/test_retry_policy.py
touch tests/core/test_token_tracker.py
```

### 2. 集成测试

**测试1: Agent隔离**
```python
# 验证不同Agent的上下文互不干扰
ctx_manager = ContextManager()
ctx1 = ctx_manager.get_agent_context("researcher")
ctx2 = ctx_manager.get_agent_context("coder")

ctx1.set_state("key", "value1")
assert ctx2.get_state("key") is None  # 隔离验证
```

**测试2: @mention匹配**
```python
# 验证模糊匹配
matcher = MentionMatcher()
matched = matcher.match_agent(agents, "research")  # 应匹配"researcher"
assert matched.agent_id == "researcher"
```

**测试3: 状态追踪**
```python
# 验证状态转换
status_mgr = AgentStatusManager()
status_mgr.mark_running("agent1")
assert status_mgr.get_status("agent1").status == AgentStatus.RUNNING
```

**测试4: 重试机制**
```python
# 验证重试逻辑
retry_policy = RetryPolicy(max_retries=3)
call_count = 0

async def flaky_func():
    nonlocal call_count
    call_count += 1
    if call_count < 3:
        raise ConnectionError("网络错误")
    return "成功"

result = await retry_policy.execute_with_retry(flaky_func)
assert call_count == 3  # 重试2次后成功
assert result == "成功"
```

**测试5: Token追踪**
```python
# 验证成本计算
tracker = TokenTracker()
tracker.record_usage(AgentTokenUsage(
    agent_id="researcher",
    model="claude-sonnet-5",
    input_tokens=1000,
    output_tokens=2000
))

stats = tracker.get_session_stats()
assert stats["total_tokens"] == 3000
assert stats["total_cost_usd"] > 0
```

---

## 📊 验收标准

### 功能验收

- [ ] Agent上下文隔离：不同Agent的状态互不影响
- [ ] @mention支持模糊匹配：`@research` 可匹配 `researcher`
- [ ] 实时状态显示：TUI显示⏳→⚙️→✅状态变化
- [ ] 网络错误自动重试：API超时后自动重试3次
- [ ] Token统计准确：显示每个Agent的token使用和成本

### 性能验收

- [ ] 状态更新延迟 <100ms
- [ ] Token统计开销 <1ms/记录
- [ ] 上下文查询性能 <10ms
- [ ] 重试不影响正常响应时间

### 用户体验验收

**之前**:
```
用户: "@researcher 分析代码"
└─ 黑屏等待3-5秒
└─ 返回结果
```

**之后**:
```
用户: "@research 分析代码"  (模糊匹配)
└─ ⏳ researcher: pending
└─ ⚙️ researcher: running (0.5s)
└─ ✅ researcher: completed (2.3s, 450 tokens, $0.012)
└─ 返回结果
```

---

## 🚀 部署计划

### Week 1: 核心集成 (已完成模块开发)
- [x] Day 1: 创建5个核心模块 ✅
- [ ] Day 2: SessionManager集成
- [ ] Day 3: Executor集成 + Coordinator集成
- [ ] Day 4: TUI集成
- [ ] Day 5: 测试和调试

### Week 2: 测试和优化
- [ ] Day 1-2: 单元测试
- [ ] Day 3: 集成测试
- [ ] Day 4: 性能测试
- [ ] Day 5: 文档完善

---

## 📝 集成检查清单

### 代码集成
- [ ] `session.py`: 添加3个管理器初始化
- [ ] `session.py`: 修改`process_user_input()`添加状态追踪
- [ ] `executor.py`: 添加重试策略
- [ ] `coordinator.py`: 使用`MentionMatcher`
- [ ] `app.py`: 添加`AgentStatusPanel`
- [ ] `app.py`: 添加`TokenStatsPanel`

### 测试
- [ ] 5个单元测试文件创建
- [ ] 集成测试通过
- [ ] 手动测试验收

### 文档
- [ ] README更新（新特性说明）
- [ ] CHANGELOG添加条目
- [ ] 用户指南更新

---

## 💡 下一步行动

**立即开始**:
```bash
# 1. 查看已完成的模块
ls -la src/core/

# 2. 开始集成SessionManager
vim src/agents/session.py

# 3. 运行项目测试
pytest tests/

# 4. 启动TUI查看效果
python -m src.main
```

**遇到问题参考**:
- 设计文档: `IMMEDIATE_LEARNING_APPLICATIONS.md`
- 技术参考: `TECHNOLOGY_REFERENCE_GUIDE.md`
- 代码框架: 各模块已完成，可直接导入使用

---

**状态**: 🎯 核心模块已完成，等待集成到现有系统  
**下一步**: 修改SessionManager集成3个管理器
