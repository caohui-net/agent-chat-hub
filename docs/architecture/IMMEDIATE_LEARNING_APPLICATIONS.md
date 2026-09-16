# 多Agent交互 — 从Hermes-Studio可立即学习应用的技术

**生成日期**: 2026-09-05  
**目标**: 在MVP基础上快速应用（不需要等P4阶段）  
**工作量**: 1-2周（小优化，快速赢）

---

## 🎯 即学即用的5项技术

### 1️⃣ Agent隔离与状态管理

**从Hermes学到**：
- Crews概念：命名Agent组，每个成员独立会话
- Profile隔离：工作空间按Agent隔离
- 状态追踪：每个Agent的独立上下文

**本项目当前状态**：
```python
# src/agents/session.py
class SessionManager:
    current_session: Optional[SessionConfig]  # 全局会话
    messages: list[Message]  # 所有Agent共享消息
    # ❌ 无Agent隔离，无独立会话
```

**可立即应用**：
```python
# src/core/agent_context.py (新建，100行)

class AgentContext:
    """Agent独立上下文 - 隔离状态"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.session_messages = []  # 该Agent的私有消息
        self.state = {}             # Agent的私有状态
        self.created_at = time.time()

class ContextManager:
    """管理所有Agent的上下文"""
    def __init__(self):
        self.contexts: Dict[str, AgentContext] = {}
    
    def get_agent_context(self, agent_id: str) -> AgentContext:
        """获取Agent的独立上下文"""
        if agent_id not in self.contexts:
            self.contexts[agent_id] = AgentContext(agent_id)
        return self.contexts[agent_id]
    
    def get_shared_context(self) -> List[Message]:
        """获取共享的全局消息（用于Agent对话）"""
        # 只返回用户消息 + coordinator消息
        pass

# 在SessionManager中使用
class SessionManager:
    def __init__(self):
        self.context_manager = ContextManager()
    
    async def process_user_input(self, user_input: str):
        # 为每个被选中的Agent创建独立上下文
        selected_agents = self.coordinator.select_agents(...)
        
        for agent in selected_agents:
            agent_ctx = self.context_manager.get_agent_context(agent.agent_id)
            # 在Agent的上下文中执行
            response = await self.executor.execute(
                agent,
                messages=self.get_messages_for_agent(agent.agent_id)
            )
            # 保存到Agent独立上下文
            agent_ctx.session_messages.append(Message(role="assistant", content=response))
```

**收益**：
- ✅ Agent不会互相污染状态
- ✅ 支持多并发会话
- ✅ 为后续多用户隔离打下基础
- ✅ 代码: 100行，集成: 1小时

---

### 2️⃣ 实时状态反馈（轻量级）

**从Hermes学到**：
- Operations Dashboard：显示每个Agent的实时状态
- 状态机：PENDING → RUNNING → COMPLETED/ERROR
- 进度指示：百分比 + 动画

**本项目当前状态**：
```python
# 黑屏等待3-5秒，无中间反馈
responses = await asyncio.gather(*executor_tasks)  # 一次性等待
```

**可立即应用**（不需要完整流式改造）：
```python
# src/core/agent_status.py (新建，80行)

from enum import Enum
from dataclasses import dataclass

class AgentStatus(Enum):
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    ERROR = "error"          # 出错

@dataclass
class AgentState:
    agent_id: str
    status: AgentStatus
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    tokens: int = 0
    error: Optional[str] = None

class AgentStatusManager:
    """追踪所有Agent的实时状态"""
    def __init__(self):
        self.states: Dict[str, AgentState] = {}
    
    def mark_running(self, agent_id: str):
        self.states[agent_id] = AgentState(
            agent_id=agent_id,
            status=AgentStatus.RUNNING,
            start_time=time.time()
        )
    
    def mark_completed(self, agent_id: str, tokens: int = 0):
        state = self.states.get(agent_id)
        if state:
            state.status = AgentStatus.COMPLETED
            state.end_time = time.time()
            state.tokens = tokens
    
    def get_all_statuses(self) -> Dict[str, AgentState]:
        return dict(self.states)

# 在SessionManager中集成
class SessionManager:
    def __init__(self):
        self.status_manager = AgentStatusManager()
    
    async def process_user_input(self, user_input: str):
        selected_agents = self.coordinator.select_agents(...)
        
        # 1. 标记所有Agent为RUNNING
        for agent in selected_agents:
            self.status_manager.mark_running(agent.agent_id)
        
        # 2. 执行并监听状态
        async def execute_with_tracking(agent):
            try:
                self.status_manager.mark_running(agent.agent_id)
                response = await self.executor.execute(agent, messages)
                self.status_manager.mark_completed(agent.agent_id, len(response))
                return response
            except Exception as e:
                self.status_manager.mark_error(agent.agent_id, str(e))
                raise
        
        results = await asyncio.gather(
            *[execute_with_tracking(a) for a in selected_agents],
            return_exceptions=True
        )

# 在TUI中显示状态
class ChatApp(App):
    def update_agent_status_display(self):
        """实时更新Agent状态显示"""
        statuses = self.session_manager.status_manager.get_all_statuses()
        
        status_text = ""
        for agent_id, state in statuses.items():
            icon = {
                AgentStatus.PENDING: "⏳",
                AgentStatus.RUNNING: "⚙️",
                AgentStatus.COMPLETED: "✅",
                AgentStatus.ERROR: "❌",
            }[state.status]
            
            duration = ""
            if state.end_time:
                duration = f" ({state.end_time - state.start_time:.1f}s)"
            
            status_text += f"{icon} {agent_id}: {state.status.value}{duration}\n"
        
        self.agent_status_panel.update(status_text)
```

**收益**：
- ✅ 用户能看到进度（⏳ RUNNING → ✅ COMPLETED）
- ✅ 性能数据可见（执行时间、Token数）
- ✅ 错误明确提示
- ✅ 代码: 80行，集成: 2小时

---

### 3️⃣ 智能重试机制

**从Hermes学到**：
- 重试策略：指数退避
- 最大重试次数：防止无限重试
- 错误分类：哪些错误可重试，哪些不可

**本项目当前状态**：
```python
# src/agents/executor.py
# 无重试机制，API调用失败直接抛异常
response = await self._call_anthropic(...)  # 可能超时或网络错误
```

**可立即应用**：
```python
# src/core/retry_policy.py (新建，60行)

from enum import Enum
import asyncio

class RetryPolicy:
    """重试策略"""
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """执行函数，自动重试"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                # 可重试的错误
                if self._is_retryable(e):
                    # 指数退避
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"Retrying {func.__name__} after {delay}s (attempt {attempt+1}/{self.max_retries})",
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                else:
                    # 不可重试的错误，直接抛出
                    raise
        
        # 所有重试都失败
        raise last_error
    
    def _is_retryable(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        # 可重试：网络超时、临时服务不可用
        retryable_errors = (
            asyncio.TimeoutError,
            ConnectionError,
            TimeoutError,
        )
        
        # 检查错误类型和消息
        if isinstance(error, retryable_errors):
            return True
        
        # 检查API响应码（429 Too Many Requests, 503 Service Unavailable）
        if hasattr(error, 'status_code'):
            return error.status_code in (429, 503, 504)
        
        return False

# 在Executor中使用
class AgentExecutor:
    def __init__(self):
        self.retry_policy = RetryPolicy(max_retries=3, base_delay=1.0)
    
    async def execute(self, agent, messages):
        """执行Agent，自动重试"""
        return await self.retry_policy.execute_with_retry(
            self._execute_internal,
            agent,
            messages
        )
    
    async def _execute_internal(self, agent, messages):
        # 原来的execute逻辑
        return await self._call_anthropic(...)
```

**收益**：
- ✅ 网络抖动自动恢复
- ✅ API限流自动重试
- ✅ 减少用户等待
- ✅ 代码: 60行，集成: 1小时

---

### 4️⃣ Token计数与成本追踪

**从Hermes学到**：
- 每个Agent的Token统计
- 累积成本计算
- 用户配额限制

**本项目当前状态**：
```python
# src/agents/executor.py
# 返回response，但Token数据没有收集
response = await self._call_anthropic(...)
# TokenUsage数据存在但未被使用
```

**可立即应用**：
```python
# src/core/token_tracker.py (新建，100行)

@dataclass
class AgentTokenUsage:
    agent_id: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    timestamp: float = field(default_factory=time.time)
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
    
    def estimate_cost(self, price_table: Dict) -> float:
        """估算成本"""
        prices = price_table.get(self.model, {})
        input_cost = self.input_tokens * prices.get("input", 0) / 1_000_000
        output_cost = self.output_tokens * prices.get("output", 0) / 1_000_000
        return input_cost + output_cost

class TokenTracker:
    """追踪Token使用情况"""
    
    PRICE_TABLE = {
        "claude-opus-4": {"input": 15, "output": 75},      # per 1M
        "claude-sonnet-5": {"input": 3, "output": 15},
        "gpt-4": {"input": 30, "output": 60},
    }
    
    def __init__(self):
        self.usage_history: List[AgentTokenUsage] = []
    
    def record_usage(self, usage: AgentTokenUsage):
        """记录Token使用"""
        self.usage_history.append(usage)
    
    def get_session_stats(self) -> Dict:
        """获取会话统计"""
        total_input = sum(u.input_tokens for u in self.usage_history)
        total_output = sum(u.output_tokens for u in self.usage_history)
        total_cost = sum(u.estimate_cost(self.PRICE_TABLE) for u in self.usage_history)
        
        by_agent = {}
        for usage in self.usage_history:
            if usage.agent_id not in by_agent:
                by_agent[usage.agent_id] = {"input": 0, "output": 0, "cost": 0}
            by_agent[usage.agent_id]["input"] += usage.input_tokens
            by_agent[usage.agent_id]["output"] += usage.output_tokens
            by_agent[usage.agent_id]["cost"] += usage.estimate_cost(self.PRICE_TABLE)
        
        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": total_cost,
            "by_agent": by_agent,
        }
    
    def get_daily_cost(self) -> float:
        """获取今日成本"""
        today = datetime.now().date()
        today_usage = [
            u for u in self.usage_history
            if datetime.fromtimestamp(u.timestamp).date() == today
        ]
        return sum(u.estimate_cost(self.PRICE_TABLE) for u in today_usage)

# 在Executor中集成
class AgentExecutor:
    def __init__(self):
        self.token_tracker = TokenTracker()
    
    async def execute(self, agent, messages):
        response = await self._call_anthropic(...)
        
        # 记录Token使用
        self.token_tracker.record_usage(AgentTokenUsage(
            agent_id=agent.agent_id,
            model=agent.model_id,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        ))
        
        return response

# 在TUI中显示
class ChatApp(App):
    def render_token_stats(self):
        """显示Token统计"""
        stats = self.executor.token_tracker.get_session_stats()
        
        return f"""
        📊 本会话Token统计:
        ├─ 输入: {stats['total_input_tokens']} tokens
        ├─ 输出: {stats['total_output_tokens']} tokens
        ├─ 总计: {stats['total_tokens']} tokens
        └─ 成本: ${stats['total_cost_usd']:.4f}
        
        💰 今日成本: ${self.executor.token_tracker.get_daily_cost():.2f}
        """
```

**收益**：
- ✅ 用户知道每个Agent花了多少Token
- ✅ 成本透明化
- ✅ 为配额限制打下基础
- ✅ 代码: 100行，集成: 2小时

---

### 5️⃣ @mention增强 - 部分匹配 + 模糊搜索

**从Hermes学到**：
- 支持部分匹配（"research" 可匹配 "researcher"）
- 支持模糊查找
- 支持别名

**本项目当前状态**：
```python
# src/agents/coordinator.py 第223-231行
# 已支持部分匹配，但可以做得更好

def matches_mention(agent: AgentConfig, mention: str) -> bool:
    mention_lower = mention.lower()
    if agent.agent_id == mention or agent.name == mention:
        return True
    if mention_lower in agent.agent_id.lower() or mention_lower in agent.name.lower():
        return True
    return False
```

**可立即应用**（增强版）：
```python
# src/core/mention_matcher.py (新建，80行)

from difflib import SequenceMatcher

class MentionMatcher:
    """智能@mention匹配"""
    
    @staticmethod
    def similarity_ratio(a: str, b: str) -> float:
        """计算相似度比例（0-1）"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    @staticmethod
    def match_agent(agents: List[AgentConfig], mention: str, threshold: float = 0.6):
        """
        匹配Agent，支持多种策略：
        1. 精确匹配 (agent_id或name完全相同)
        2. 前缀匹配 ("res" 匹配 "researcher")
        3. 包含匹配 ("search" 在 "researcher" 中)
        4. 模糊匹配 (相似度 > threshold)
        """
        mention_lower = mention.lower()
        candidates = []
        
        # 1. 精确匹配 - 最高优先级
        for agent in agents:
            if agent.agent_id.lower() == mention_lower or agent.name.lower() == mention_lower:
                return agent
        
        # 2. 前缀匹配
        for agent in agents:
            if agent.agent_id.lower().startswith(mention_lower) or agent.name.lower().startswith(mention_lower):
                candidates.append((agent, 1.0))
        
        if candidates:
            return candidates[0][0]  # 返回第一个前缀匹配
        
        # 3. 包含匹配
        for agent in agents:
            if mention_lower in agent.agent_id.lower() or mention_lower in agent.name.lower():
                candidates.append((agent, 0.9))
        
        if candidates:
            return candidates[0][0]
        
        # 4. 模糊匹配
        for agent in agents:
            ratio1 = MentionMatcher.similarity_ratio(mention, agent.agent_id)
            ratio2 = MentionMatcher.similarity_ratio(mention, agent.name)
            max_ratio = max(ratio1, ratio2)
            
            if max_ratio > threshold:
                candidates.append((agent, max_ratio))
        
        if candidates:
            # 返回相似度最高的
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        return None  # 未找到匹配

# 在Coordinator中使用
class ResponseCoordinator:
    def parse_mentions(self, text: str, available_agents: List[AgentConfig]) -> List[str]:
        """解析@mention并返回匹配的agent_ids"""
        
        import re
        mentions = re.findall(r'@(\w+)', text)
        matched_agents = set()
        
        for mention in mentions:
            agent = MentionMatcher.match_agent(available_agents, mention)
            if agent:
                matched_agents.add(agent.agent_id)
                logger.info(f"Matched @{mention} to {agent.agent_id} ({agent.name})")
            else:
                logger.warning(f"No agent matched for @{mention}")
        
        return list(matched_agents)
```

**收益**：
- ✅ 用户不需要精确输入Agent名字
- ✅ 支持多种匹配方式
- ✅ 用户体验更友好
- ✅ 代码: 80行，集成: 1小时

---

## 🔧 快速集成清单

### 这周可做的（5项，共400行代码）

| 技术 | 文件 | 行数 | 工作量 | 收益 |
|------|------|------|--------|------|
| 1. Agent隔离 | agent_context.py | 100 | 1小时 | 状态隔离 |
| 2. 状态显示 | agent_status.py | 80 | 2小时 | 实时反馈 |
| 3. 重试机制 | retry_policy.py | 60 | 1小时 | 自动恢复 |
| 4. Token追踪 | token_tracker.py | 100 | 2小时 | 成本透明 |
| 5. @mention增强 | mention_matcher.py | 80 | 1小时 | UX改善 |
| **总计** | — | **420** | **7小时** | **5项快赢** |

---

## 📋 集成步骤

### Day 1: Agent隔离 + @mention增强
```bash
# 1. 创建两个新文件
touch src/core/agent_context.py
touch src/core/mention_matcher.py

# 2. 复制上面的代码
# 3. 在SessionManager中集成
# 4. 在Coordinator中使用mention_matcher
# 5. 测试@mention功能

# 工作量: 2-3小时
```

### Day 2: 状态追踪 + TUI显示
```bash
# 1. 创建新文件
touch src/core/agent_status.py

# 2. 在Executor中集成状态追踪
# 3. 在TUI中添加状态面板
# 4. 测试状态显示

# 工作量: 3-4小时
```

### Day 3: 重试机制 + Token追踪
```bash
# 1. 创建两个新文件
touch src/core/retry_policy.py
touch src/core/token_tracker.py

# 2. 在Executor中集成重试
# 3. 在Executor中集成Token追踪
# 4. 在TUI中显示统计
# 5. 测试

# 工作量: 3-4小时
```

---

## 🎯 预期效果

**之前**（当前状态）：
```
用户: "@researcher 分析这个代码"
└─ 黑屏3-5秒等待
   ⏳ (无进度反馈，无法重试，不知道Token消耗)
└─ 返回结果
```

**之后**（应用后）：
```
用户: "@research 分析这个代码"  (注: 不用精确拼写)
└─ ⏳ researcher: pending → running → completed (1.2s, 450 tokens)
   ✅ 实时显示状态变化
   (如果超时，自动重试)
   (成本追踪显示: $0.012)
└─ 返回结果 + 统计显示
```

---

## 📚 代码质量

所有代码都：
- ✅ 遵循项目现有风格
- ✅ 包含类型提示 (Pydantic/Python)
- ✅ 添加日志记录 (structlog)
- ✅ 包含错误处理
- ✅ 向后兼容（不破坏现有API）

---

## 💡 后续可做的

等这5项完成后，可以继续：
1. 会话持久化（保存状态）
2. Agent权限检查（这个Agent能否执行这个操作）
3. 消息验证增强
4. 并发限制

---

## ✨ 总结

**从Hermes-Studio学到，可立即应用到本项目的5项技术**：

1. **Agent隔离** — 每个Agent有独立上下文
2. **实时状态** — 用户看到执行进度
3. **智能重试** — 网络抖动自动恢复
4. **Token追踪** — 成本透明化
5. **@mention增强** — 模糊匹配提升UX

**投入**: 1周 (7小时代码 + 集成测试)  
**收益**: MVP体验显著提升，为P4阶段打好基础

---

**建议**: 这周利用碎片时间，逐项集成这5个技术。不需要等P4，现在就能快速赢！

**下周**: 启动P4a (DAG工作流)开发

