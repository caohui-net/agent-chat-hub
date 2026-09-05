# Hermes-Studio Agent 交互分析 — 本项目改善方案

## 执行摘要

Hermes-Studio 采用 **Web UI + 多Agent协作** 架构，其 Agent 交互设计比本项目更成熟。通过对标分析，本项目在以下 5 个维度存在改善机会，可通过逐步优化显著提升 Agent 协作体验。

---

## 第一部分：本项目当前 Agent 交互架构评估

### ✅ 已有的优势

| 功能 | 实现状态 | 评分 |
|------|--------|------|
| 基础 MessageBus | Phase 2 ✅ | ⭐⭐⭐ |
| 异步并发执行 | Phase 2 ✅ | ⭐⭐⭐ |
| @mention 协作路由 | Phase 3 ✅ | ⭐⭐⭐ |
| ResponseCoordinator (6 规则) | Phase 1 ✅ | ⭐⭐⭐ |
| 会话管理与持久化 | Phase 2 ✅ | ⭐⭐⭐ |
| 插件系统 (基础) | Phase 3 ✅ | ⭐⭐ |

### ⚠️ 当前限制

1. **Agent 响应可见性差** — 无实时流，响应到达后一次性显示
2. **Agent 状态追踪不足** — 无单个 Agent 的执行状态展示
3. **交互反馈机制缺失** — Agent 间通信结果无完整审计
4. **协作深度有限** — @mention 协作限 2 轮，无灵活的工作流编排
5. **调试困难** — 无清晰的 Agent 执行日志和问题定位机制

---

## 第二部分：Hermes-Studio 关键设计模式

### 1. **多Agent Crews 模式** ⭐⭐⭐

**Hermes-Studio 实现：**
```
Crew 组织方式
├─ crew_name: "Research Team"
├─ members: 
│  ├─ analyst (role)
│  ├─ writer (role)
│  └─ reviewer (role)
├─ profile_root: ~/.hermes/profiles/research-team/
└─ session_scoping: 每个成员独立会话
```

**本项目现状：**
```python
# src/core/models.py - SessionConfig
messages: List[Message]  # 全局共享消息
active_agent_ids: List[str]  # 简单 ID 列表
# 缺少：Crew 概念、Profile 隔离、成员会话管理
```

**改进建议：** 从 `active_agent_ids` 升级到 `Crew` 对象，支持：
- 命名的 Agent 组（如 "Research Crew"）
- 成员级别的会话隔离
- 工作空间隔离（profile_root）

---

### 2. **实时 SSE Streaming 反馈** ⭐⭐⭐

**Hermes-Studio 特色：**
- 逐字符流式响应
- 工具调用实时渲染
- 网络状态感知

**本项目现状：**
```python
# src/agents/executor.py - execute()
# 同步返回完整 response
return await self._call_anthropic(...)  # 一次性返回
```

**改进建议：**
```python
# 支持流式返回
async def execute_streaming(
    self,
    agent_config: AgentConfig,
    messages: List[Message]
) -> AsyncIterator[str]:
    """流式返回响应"""
    async for chunk in stream_response:
        yield chunk
```

---

### 3. **Agent 执行状态可视化** ⭐⭐

**Hermes-Studio 做法：**
- Operations Dashboard（全局 Agent 状态）
- 每个 Crew 的 Operations 标签
- 实时状态过滤（Running/Completed/Error）

**本项目现状：**
```python
# session.py - process_user_input()
results = await asyncio.gather(...)
# 返回时才知道结果，中途无反馈
```

**改进建议：**
```python
class AgentExecutionState(Enum):
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    STREAMING = "streaming"  # 响应流中
    COMPLETED = "completed"  # 已完成
    ERROR = "error"          # 出错

@dataclass
class AgentStatus:
    agent_id: str
    state: AgentExecutionState
    progress: float  # 0-100
    tokens_used: int
    error: Optional[str]
```

TUI 可动态展示各 Agent 的实时状态。

---

### 4. **Agent 协作深度提升** ⭐⭐⭐

**Hermes-Studio：**
- DAG 工作流编辑器
- 可视化任务管道
- 按拓扑顺序执行

**本项目现状（session.py:197-256）：**
```python
# 固定 2 轮协作循环
max_collab_rounds = 2
while collab_round < max_collab_rounds:
    # 1. 解析所有响应中的 @mentions
    # 2. 触发被 @mention 的 agents
    # 硬编码上限，不灵活
```

**改进建议：**
```python
# 支持配置的协作策略
class CollaborationPolicy(BaseModel):
    max_rounds: int = 2        # 最大协作轮数
    max_chain_depth: int = 3   # 最大调用深度
    mode: Literal["sequential", "parallel", "dag"]
    
# DAG 模式示例
class CollaborationDAG:
    nodes: Dict[str, AgentTask]
    edges: List[Tuple[str, str]]  # (from, to) 依赖
    
    async def execute_topological(self) -> Dict[str, str]:
        """按拓扑排序执行"""
        pass
```

---

### 5. **完整的审计与可观性** ⭐⭐

**Hermes-Studio 审计日志（/audit）：**
- 跨会话时间线
- 工具调用 + 用户消息 + 批准请求
- 按事件类型过滤

**本项目现状：**
```python
# 仅有基础的 structlog 日志
logger.info("agent_responded", agent_id=..., response_length=...)
# 无完整的事件审计系统
```

**改进建议：**
```python
class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime
    event_type: Literal["agent_call", "user_input", "collab", "error"]
    session_id: str
    agent_id: Optional[str]
    details: Dict[str, Any]
    
class AuditLogger:
    async def log_event(self, event: AuditEvent) -> None:
        """记录审计事件到数据库"""
        pass
    
    async def query_events(
        self,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[AuditEvent]:
        """查询审计事件"""
        pass
```

---

## 第三部分：实施路线图

### Phase 3.1（当前 + 1 周）：可观性增强

**目标**：提升 Agent 交互的可见性和调试能力

**任务**：
1. **扩展审计日志系统**
   ```python
   # src/core/audit_log.py (新建)
   class AuditLogger:
       async def log_agent_start(self, agent_id, session_id)
       async def log_agent_complete(self, agent_id, response, tokens)
       async def log_collab_mention(self, from_agent, to_agents)
   ```

2. **改进 TUI 状态展示**
   ```python
   # src/tui/app.py - 新增 Agent 面板
   class AgentStatusPanel:
       def render_status(self) -> RenderableType:
           # 实时展示各 Agent 的：
           # - 执行状态（PENDING/RUNNING/COMPLETED/ERROR）
           # - Token 用量
           # - 执行时间
   ```

3. **添加调试命令**
   ```
   /audit session_id        # 查看会话审计日志
   /agent-status agent_id   # 查看单个 Agent 状态
   /collab-history          # 查看协作历史
   ```

**工作量**：2-3 天  
**收益**：快速定位问题，改善调试体验

---

### Phase 3.2（1-2 周）：Agent 执行状态管理

**目标**：支持实时状态反馈，为 Agent 交互提供中途反馈

**任务**：
1. **实现执行状态枚举** (见第二部分)
2. **refactor SessionManager**
   ```python
   class SessionManager:
       async def process_user_input_with_status(
           self,
           user_input: str
       ) -> AsyncIterator[AgentStatusUpdate]:
           """流式返回 Agent 状态更新"""
           # yield AgentStatusUpdate(agent_id, "RUNNING", ...)
           # yield AgentStatusUpdate(agent_id, "COMPLETED", ...)
   ```

3. **TUI 实时状态面板**
   - 显示当前执行中的 Agents
   - 进度条和 Token 统计
   - 实时更新

**工作量**：3-4 天  
**收益**：用户能看到中途反馈，大幅改善交互体验

---

### Phase 4.0（2-3 周）：Crews 和工作流编排

**目标**：支持更高级的 Agent 协作模式（可选）

**任务**：
1. **Crew 数据模型**
   ```python
   # src/core/crew.py
   class Crew(BaseModel):
       crew_id: str
       name: str
       description: str
       members: List[AgentConfig]
       profile_root: str
       session_map: Dict[str, str]  # agent_id -> session_id
   ```

2. **DAG 工作流支持**
   ```python
   # src/core/workflow.py
   class WorkflowDAG:
       async def execute(self) -> Dict[str, str]:
           """按拓扑排序执行"""
   ```

3. **CollaborationPolicy 配置**
   - 替代硬编码的 `max_collab_rounds = 2`
   - 支持 sequential/parallel/dag 模式

**工作量**：1-2 周  
**收益**：支持更复杂的 Agent 协作场景

---

## 第四部分：代码改进清单

### 立即可做的改动

#### 1. 增强审计日志（2-3 小时）

**文件**：`src/core/audit_log.py` (新建)

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class AuditEventType(Enum):
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    COLLAB_MENTION = "collab_mention"
    USER_INPUT = "user_input"

@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    session_id: str
    agent_id: Optional[str]
    details: Dict[str, Any]

class AuditLogger:
    def __init__(self, db_path: Optional[str] = None):
        # 使用 SQLite 存储审计事件
        pass
    
    async def log_event(self, event: AuditEvent) -> None:
        """记录事件"""
        pass
    
    async def query_by_session(self, session_id: str) -> List[AuditEvent]:
        """按会话查询"""
        pass
```

**集成到 SessionManager**：
```python
# src/agents/session.py
class SessionManager:
    def __init__(self, ..., audit_logger: AuditLogger = None):
        self.audit_logger = audit_logger or AuditLogger()
    
    async def process_user_input(self, user_input: str):
        # ... 现有逻辑 ...
        
        # 记录用户输入
        await self.audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.USER_INPUT,
            session_id=self.current_session.session_id,
            details={"content": user_input}
        ))
        
        # 记录 Agent 调用
        for agent in selected_agents:
            await self.audit_logger.log_event(AuditEvent(
                event_type=AuditEventType.AGENT_START,
                session_id=self.current_session.session_id,
                agent_id=agent.agent_id,
                details={"timestamp": time.time()}
            ))
```

---

#### 2. Agent 执行状态跟踪（3-4 小时）

**文件**：`src/core/execution_state.py` (新建)

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

class ExecutionState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class AgentExecutionStatus:
    agent_id: str
    state: ExecutionState
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_tokens: int = 0
    output_tokens: int = 0
    error: Optional[str] = None
    
    @property
    def elapsed_seconds(self) -> float:
        if not self.start_time:
            return 0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

class ExecutionStateManager:
    def __init__(self):
        self.states: Dict[str, AgentExecutionStatus] = {}
    
    def mark_running(self, agent_id: str) -> None:
        self.states[agent_id] = AgentExecutionStatus(
            agent_id=agent_id,
            state=ExecutionState.RUNNING,
            start_time=datetime.now()
        )
    
    def mark_completed(self, agent_id: str, output_tokens: int = 0) -> None:
        if agent_id in self.states:
            self.states[agent_id].state = ExecutionState.COMPLETED
            self.states[agent_id].end_time = datetime.now()
            self.states[agent_id].output_tokens = output_tokens
    
    def mark_error(self, agent_id: str, error: str) -> None:
        if agent_id in self.states:
            self.states[agent_id].state = ExecutionState.ERROR
            self.states[agent_id].error = error
            self.states[agent_id].end_time = datetime.now()
    
    def get_status(self, agent_id: str) -> Optional[AgentExecutionStatus]:
        return self.states.get(agent_id)
    
    def get_all_statuses(self) -> Dict[str, AgentExecutionStatus]:
        return self.states.copy()
```

**集成到 SessionManager**：
```python
# src/agents/session.py
class SessionManager:
    def __init__(self, ...):
        self.exec_state_manager = ExecutionStateManager()
    
    async def process_user_input(self, user_input: str):
        # ...
        for agent in selected_agents:
            self.exec_state_manager.mark_running(agent.agent_id)
        
        results = await asyncio.gather(...)
        
        for agent_config, response, error in results:
            if error:
                self.exec_state_manager.mark_error(
                    agent_config.agent_id,
                    str(error)
                )
            else:
                tokens = len(response)
                self.exec_state_manager.mark_completed(
                    agent_config.agent_id,
                    tokens
                )
```

---

#### 3. 调试命令集（2-3 小时）

**文件**：`src/tui/debug_commands.py` (新建)

```python
class DebugCommands:
    def __init__(self, session_manager: SessionManager, audit_logger: AuditLogger):
        self.session_manager = session_manager
        self.audit_logger = audit_logger
    
    async def cmd_audit(self, session_id: str) -> str:
        """查看会话审计日志"""
        events = await self.audit_logger.query_by_session(session_id)
        return self._format_events(events)
    
    async def cmd_agent_status(self, agent_id: str) -> str:
        """查看 Agent 执行状态"""
        status = self.session_manager.exec_state_manager.get_status(agent_id)
        if not status:
            return f"No status for agent {agent_id}"
        
        return f"""
Agent: {agent_id}
State: {status.state.value}
Duration: {status.elapsed_seconds:.1f}s
Tokens: input={status.input_tokens}, output={status.output_tokens}
Error: {status.error or "None"}
        """
    
    async def cmd_collab_history(self) -> str:
        """查看协作历史"""
        events = await self.audit_logger.query_by_type(AuditEventType.COLLAB_MENTION)
        return self._format_collaboration_events(events)
    
    def _format_events(self, events: List[AuditEvent]) -> str:
        lines = ["Audit Events:"]
        for event in events:
            lines.append(
                f"  [{event.timestamp.isoformat()}] "
                f"{event.event_type.value} - {event.agent_id}"
            )
        return "\n".join(lines)
```

---

### 中期改动（Phase 3.2）

#### 4. 实时状态流（流式返回）

**改进 SessionManager**：
```python
async def process_user_input_with_stream(
    self,
    user_input: str
) -> AsyncIterator[Dict[str, Any]]:
    """流式返回 Agent 状态更新"""
    # 1. 发送 user_input 事件
    yield {
        "type": "user_input",
        "content": user_input
    }
    
    # 2. Agent 执行前，标记为 RUNNING
    for agent in selected_agents:
        self.exec_state_manager.mark_running(agent.agent_id)
        yield {
            "type": "agent_status",
            "agent_id": agent.agent_id,
            "state": "running"
        }
    
    # 3. 并发执行，逐个返回完成状态
    for agent_config, response, error in results:
        if error:
            self.exec_state_manager.mark_error(agent_config.agent_id, str(error))
            yield {
                "type": "agent_error",
                "agent_id": agent_config.agent_id,
                "error": str(error)
            }
        else:
            self.exec_state_manager.mark_completed(agent_config.agent_id, len(response))
            yield {
                "type": "agent_response",
                "agent_id": agent_config.agent_id,
                "response": response,
                "tokens": len(response)
            }
```

---

## 第五部分：快速检查清单

| 功能 | 优先级 | 工作量 | 完成条件 |
|------|-------|-------|---------|
| 审计日志系统 | P0 | 2-3h | ✅ 可查询会话/Agent 事件 |
| 执行状态管理 | P0 | 3-4h | ✅ 追踪 PENDING/RUNNING/COMPLETED/ERROR |
| 调试命令集 | P1 | 2-3h | ✅ /audit /agent-status /collab-history 可用 |
| TUI 状态面板 | P1 | 4-6h | ✅ 实时显示各 Agent 状态 |
| **小计** | | **11-16h** | **核心改进** |
| 流式状态返回 | P2 | 4-5h | ✅ 支持 AsyncIterator 输出 |
| Crew 模型 | P3 | 1-2w | ✅ 支持命名 Agent 组 |
| DAG 工作流 | P3 | 1-2w | ✅ 支持拓扑排序执行 |

---

## 总结

**Hermes-Studio 启示：**
1. ✅ Agent 状态可视化极其重要（Operations Dashboard）
2. ✅ 审计日志是调试的关键
3. ✅ 实时反馈（SSE）大幅改善 UX
4. ✅ 灵活的协作策略（Crews、DAG）支持复杂场景

**本项目立即可做：**
1. **Phase 3.1**（1-2 天）：审计日志 + 执行状态管理 + 调试命令
2. **Phase 3.2**（3-4 天）：TUI 状态面板 + 流式返回
3. **Phase 4.0**（可选，1-2 周）：Crews + DAG 工作流

**不需要重构的地方：**
- ✅ MessageBus 架构合理
- ✅ ResponseCoordinator 6 规则完善
- ✅ @mention 协作机制有效
- ✅ TUI 选型正确（vs Web）

**建议优先顺序：**
1. 审计日志（最快获益）
2. 执行状态面板（用户可观性）
3. 调试命令（开发者体验）
4. 后续：流式返回、Crews、DAG（按需求）

---

**分析日期**：2026-09-05  
**参考**：Hermes-Studio v1.20.0 + 本项目 Phase 3  
**下一步**：选择立即可做的任务（建议从审计日志开始）
