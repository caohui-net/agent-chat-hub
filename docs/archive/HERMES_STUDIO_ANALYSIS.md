# Hermes-Studio 项目分析与借鉴

## 项目对比

### Hermes-Studio（参考项目）
- **语言**：TypeScript/React
- **类型**：Web UI 仪表板（自托管）
- **主要功能**：Multi-agent crews、Cron job scheduler、Knowledge graph、Workflow orchestration
- **创建日期**：2026-04-10
- **Stars**：345 | **Forks**：71
- **最后更新**：2026-07-03

### Agent Chat Hub（本项目）
- **语言**：Python 3.14+
- **类型**：TUI 终端应用
- **主要功能**：Multi-model agent chat、Message validation、Session management、Plugin system
- **架构**：ADR-0001 决策采用 TUI（而非 Web）
- **创建日期**：约 2026-06
- **阶段**：Phase 3（插件系统）

---

## 核心借鉴点

### 1. **多Agent协作架构** ⭐⭐⭐

**Hermes-Studio 实现：**
- `Crews`：命名的Agent组，支持并行任务分发
- 每个Agent成员独立的会话（Session）管理
- Profile-scoped workspaces：按profile隔离文件系统
- 实时 SSE streaming 活动反馈

**本项目当前状态：**
- ✅ Phase 2 已实现 MessageBus 和并发API调用
- ✅ Agent执行器异步化完成
- ⚠️ 缺少类似 Crews 的命名Agent组概念

**建议应用：**
```python
# src/core/crew_manager.py - 类似 Hermes 的 Crews 概念
class CrewConfig:
    name: str
    description: str
    members: List[AgentConfig]
    profile_root: str  # 隔离工作目录
    
class CrewSession:
    crew_id: str
    member_sessions: Dict[str, SessionConfig]  # 每个成员独立会话
    activity_feed: List[CrewEvent]  # 活动日志
```

---

### 2. **Cron Job 定时任务管理** ⭐⭐⭐

**Hermes-Studio 特色：**
- 自然语言提示词 + Cron 表达式
- 支持预设（每15分钟、每小时、每天、每周）
- 交付渠道（Telegram、Discord、Slack、Signal）
- 即时触发 + 实时 SSE 流
- 暂停/恢复/编辑/监控

**本项目可借鉴：**
```python
# src/core/job_scheduler.py
from datetime import datetime
from croniter import croniter

class CronJob(BaseModel):
    job_id: str
    prompt: str
    schedule: str  # Cron 表达式
    enabled: bool
    agent_id: str
    tags: List[str]
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    delivery_channels: List[str]  # ["telegram", "discord"]
    
class JobExecutor:
    async def trigger_now(self, job: CronJob) -> JobRun:
        """立即触发，支持实时 SSE 流"""
        pass
    
    async def get_schedule_info(self, job: CronJob) -> ScheduleInfo:
        """获取下次执行时间"""
        pass
```

**使用场景：**
- 定时汇总 Agent 输出
- 定期代码分析
- 定时数据监控

---

### 3. **权限与执行批准（Approval）** ⭐⭐

**Hermes-Studio 实现：**
- 执行前批准机制（Approve/Deny/Always-Allow）
- 命令白名单（Command Allowlist）
- 工具集限制（Toolsets）
- 代码执行限制

**本项目应用场景：**
```python
# src/core/approval_manager.py
class ExecutionApproval(BaseModel):
    action_id: str
    action_type: Literal["shell", "api_call", "file_write"]
    details: Dict[str, Any]
    approval_mode: Literal["auto", "require_approval", "always_allow"]
    created_at: datetime
    approved_by: Optional[str]
    
class ApprovalPolicy(BaseModel):
    dangerous_commands: List[str]  # ["rm", "docker rm"]
    api_allowlist: Dict[str, List[str]]
    code_execution_limit: int  # 字节数
    require_approval_for: List[str]
```

---

### 4. **实时流式响应（SSE Streaming）** ⭐⭐⭐

**Hermes-Studio 做法：**
- 直接网关连接，实时 SSE 流
- 工具调用渲染
- 实时状态更新

**本项目优化建议：**
```python
# src/core/sse_manager.py
class SSEStream:
    """实时流式事件"""
    async def stream_agent_response(
        self, 
        session_id: str,
        stream: AsyncIterator[str]
    ) -> AsyncIterator[str]:
        """流式传输 Agent 响应"""
        async for chunk in stream:
            yield f"data: {json.dumps({
                'type': 'response_chunk',
                'data': chunk,
                'timestamp': datetime.now().isoformat()
            })}\n\n"
            
    async def stream_tool_call(
        self, 
        tool_name: str, 
        args: Dict
    ) -> AsyncIterator[str]:
        """流式传输工具调用事件"""
        yield f"data: {json.dumps({
            'type': 'tool_call',
            'tool': tool_name,
            'args': args
        })}\n\n"
```

---

### 5. **会话持久化与恢复** ⭐⭐

**Hermes-Studio 特色：**
- Redis 后端存储
- 优雅的文件存储回退
- 会话在服务重启后恢复

**本项目对标实现：**
```python
# src/core/session_persistence.py
class SessionStore(ABC):
    @abstractmethod
    async def save_session(self, session: SessionConfig) -> None:
        pass
    
    @abstractmethod
    async def load_session(self, session_id: str) -> SessionConfig:
        pass

class RedisSessionStore(SessionStore):
    """Redis 优先"""
    async def save_session(self, session: SessionConfig) -> None:
        await self.redis.set(
            f"session:{session.id}",
            session.model_dump_json(),
            ex=86400 * 30  # 30天过期
        )

class SQLiteSessionStore(SessionStore):
    """SQLite 后备"""
    # 当前已支持 via aiosqlite
```

---

### 6. **知识图谱可视化** ⭐⭐

**Hermes-Studio 方案：**
- 力导向图（Force-directed graph）
- 缩放、平移、拖拽节点
- 悬停高亮连接
- 按度数调整节点大小

**本项目可选扩展：**
```python
# src/ui/knowledge_graph.py
class KnowledgeNode:
    id: str
    label: str
    degree: int  # 连接数
    category: str
    
class KnowledgeEdge:
    source: str
    target: str
    relation_type: str
    
class KnowledgeGraphRenderer:
    """用于 Web 扩展或可视化输出"""
    def export_to_d3(self, nodes, edges) -> Dict:
        """导出 D3.js 格式用于前端渲染"""
        pass
```

---

### 7. **模板系统与预设** ⭐

**Hermes-Studio 实现：**
- 7 个内置 Crew 模板
- 4 个 Conductor 模板（Research、Build、Review、Deploy）
- 用户可保存自己的模板
- 统一的模板系统（`templateType` 字段）

**本项目应用：**
```python
# src/core/template_manager.py
class AgentTemplate(BaseModel):
    name: str
    description: str
    system_prompt: str
    recommended_skills: List[str]
    category: str  # "research", "coding", "analysis"
    
class SessionTemplate(BaseModel):
    name: str
    description: str
    agents: List[str]  # Agent ID 列表
    initial_prompt: str
    settings: Dict[str, Any]
```

---

### 8. **成本追踪** ⭐⭐

**Hermes-Studio 做法：**
- 每个 Crew 级别的 token 统计
- 按 Agent 的输入/输出分离
- 基于模型价格表估算成本
- 会话级别成本合计

**本项目实现建议：**
```python
# src/core/cost_tracker.py
class TokenUsage(BaseModel):
    session_id: str
    agent_id: str
    model: str
    input_tokens: int
    output_tokens: int
    timestamp: datetime

class CostCalculator:
    PRICE_TABLE = {
        "claude-opus-4-8": {"input": 0.015, "output": 0.075},
        "claude-sonnet-5": {"input": 0.003, "output": 0.015},
        "gpt-4": {"input": 0.03, "output": 0.06},
    }
    
    def calculate_cost(self, usage: TokenUsage) -> float:
        prices = self.PRICE_TABLE.get(usage.model, {})
        return (
            usage.input_tokens * prices.get("input", 0) / 1000 +
            usage.output_tokens * prices.get("output", 0) / 1000
        )
```

---

### 9. **审计日志（Audit Trail）** ⭐

**Hermes-Studio 特色：**
- 跨会话的时间线视图
- 工具调用 + 用户消息 + 批准请求
- 按会话、事件类型、日期范围过滤
- 50 条分页

**本项目集成建议：**
```python
# src/core/audit_log.py
class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime
    event_type: Literal["tool_call", "user_message", "approval", "error"]
    session_id: str
    agent_id: Optional[str]
    details: Dict[str, Any]
    
class AuditStore:
    """已有 SQLite 基础，可扩展"""
    async def query_events(
        self,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 50
    ) -> List[AuditEvent]:
        pass
```

---

### 10. **工作流编排（DAG 编辑器）** ⭐

**Hermes-Studio 实现：**
- DAG（有向无环图）可视化编辑
- 节点、贝塞尔曲线连接
- 自动布局
- 实时执行状态更新（SSE）

**本项目可选 Phase 4 功能：**
```python
# src/core/workflow_dag.py
class WorkflowNode:
    id: str
    task: str  # Agent task
    dependencies: List[str]  # 前置任务 ID
    position: Tuple[int, int]  # 用于可视化
    
class WorkflowDAG:
    nodes: Dict[str, WorkflowNode]
    
    async def execute_topological(self) -> Dict[str, Any]:
        """按拓扑排序执行节点"""
        pass
```

---

## 架构设计模式可参考

### 事件驱动架构
```python
# Hermes-Studio 广泛使用事件系统
# 本项目已有 MessageBus，可扩展：
class EventBus:
    async def publish(self, event: Event):
        """发布事件"""
        pass
    
    async def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        pass
```

### 实时通知系统
```python
# WebSocket / SSE 集成
class RealtimeNotifier:
    async def notify_agent_status(self, agent_id: str, status: str):
        pass
    
    async def notify_job_completion(self, job_id: str, result: Dict):
        pass
```

---

## 技术栈对比

| 功能 | Hermes-Studio | Agent Chat Hub | 建议 |
|------|---|---|---|
| 前端 | React + TypeScript | Textual (TUI) | TUI 保持，可考虑 Web 扩展 |
| 后端 | Node.js | Python | 保持 Python |
| 数据库 | SQLite + Redis | SQLite | 考虑 Redis 用于会话持久化 |
| 消息流 | SSE (HTTP) | 基于 HTTP | SSE 已有基础 |
| 定时任务 | Cron scheduler | 无 | 建议引入 `APScheduler` 或 `croniter` |
| 认证 | Auth middleware | 基本 keyring | 强化安全检查 |

---

## 直接可用代码片段

### 1. Cron 表达式工具函数
```python
from croniter import croniter

def get_next_run(cron_expr: str) -> datetime:
    """获取下次执行时间"""
    cron = croniter(cron_expr)
    return cron.get_next(datetime)

def is_due(cron_expr: str, last_run: datetime) -> bool:
    """检查是否应该执行"""
    cron = croniter(cron_expr, last_run)
    return cron.get_prev(datetime) == last_run
```

### 2. SSE 事件序列化
```python
def format_sse_event(event_type: str, data: Dict) -> str:
    """格式化 SSE 事件"""
    return (
        f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"
    )
```

### 3. 会话恢复模式
```python
async def restore_session(session_id: str):
    """从存储恢复会话"""
    try:
        # 尝试 Redis
        session = await redis_store.load(session_id)
    except Exception:
        # 回退到 SQLite
        session = await sqlite_store.load(session_id)
    return session
```

---

## 实施优先级

| 优先级 | 功能 | 工作量 | 影响 |
|---|---|---|---|
| P0 | Cron Job Manager | 中 | 高 — 独特价值 |
| P1 | Execution Approvals | 小 | 高 — 安全性 |
| P1 | 成本追踪 | 小 | 中 — 可观性 |
| P2 | Crews 命名 Agent 组 | 中 | 中 — 组织性 |
| P2 | 审计日志完善 | 小 | 中 — 追踪 |
| P3 | 知识图谱可视化 | 中 | 低 — 可选 |
| P3 | DAG 工作流编辑 | 大 | 低 — Phase 4+ |

---

## 安全性建议

✅ **来自 Hermes-Studio：**
1. CSP 头部设置（如扩展到 Web）
2. 路径遍历防护（Profile-scoped workspaces）
3. Exec 批准提示（不让 Agent 无条件执行）
4. 命令白名单机制
5. 所有 API 路由上的认证中间件

---

## 总结

**Hermes-Studio 最有价值的借鉴：**

1. **Cron Job Manager** — 可直接移植为 Phase 3.1 或 Phase 4 功能
2. **Execution Approvals** — 增强安全性，值得优先实现
3. **多Agent协作 (Crews)** — 完善现有的 Agent 协调机制
4. **SSE 实时流** — 已有基础，可优化
5. **成本追踪** — 快速赢（quick win）

**不直接适用的：**
- Web UI（本项目采用 TUI 是正确决策）
- React 组件（不同技术栈）

**建议后续行动：**
- 在 Phase 3 完成后，优先考虑 Cron Job Manager（P0）
- 同步实现 Execution Approvals（P1）
- 为未来的 Web 扩展留下 API 空间

---

**分析日期**：2026-09-04  
**参考项目**：https://github.com/JPeetz/Hermes-Studio  
**本项目**：Agent Chat Hub (v0.1.0)
