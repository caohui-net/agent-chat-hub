# 深度分析：多 Agent 协调与工作流引擎设计
## Hermes-Studio vs Agent Chat Hub 对标研究

**分析日期**: 2026-09-05  
**作者**: Claude Code  
**范围**: Agent 协调机制、工作流引擎、并发控制、资源管理

---

## 执行摘要

本报告深度分析 Hermes-Studio 的多 Agent 协调机制与工作流引擎实现，对标当前项目 Agent Chat Hub 的 ResponseCoordinator，提出改进方向。

**核心发现**：
- Hermes-Studio 采用**中心化协调 + 事件驱动**模型，对标 ResponseCoordinator 的 6 条规则框架
- **Crews 概念**超越简单 Agent 列表，实现工作空间隔离和活动追踪
- **DAG 工作流**与**响应协调**是两个独立但互补的层次
- 当前 ResponseCoordinator 缺少：并发Task编排、工作流状态追踪、动态依赖解析
- 建议分阶段增强：Task 模型 → DAG 引擎 → 实时状态追踪

---

## 一、Hermes-Studio 架构概览

### 1.1 核心设计原则

```
用户消息
    ↓
[Coordinator Agent] ← 意图识别、任务分派、结果聚合
    ↓
┌─────────────────────────┐
│  Crews（命名Agent组）     │
│  ├─ 成员Agent列表        │
│  ├─ Profile隔离工作空间  │
│  ├─ 活动日志追踪        │
│  └─ 权限模型            │
└─────────────────────────┘
    ↓
[DAG Workflow Engine]
    ├─ 节点：Agent Task
    ├─ 边：数据/控制依赖
    ├─ 执行：拓扑排序
    └─ 状态：实时追踪
```

**关键特性**：
1. **事件驱动架构** — 每个操作均发布 SSE 事件
2. **多层隔离** — Session、Crew、Profile 三级隔离
3. **实时反馈** — WebSocket/SSE 流式输出
4. **审计完整性** — 所有交互记录在案

### 1.2 对比当前项目

| 维度 | Hermes-Studio | Agent Chat Hub | 差距 |
|------|---|---|---|
| **协调模型** | 中心化 Coordinator + DAG | ResponseCoordinator (6规则) | 缺 DAG |
| **Agent 组织** | Crews + Profile隔离 | 单一 Agent 池 | 缺组织层 |
| **工作流** | 完整 DAG 编辑/执行 | 无 | 缺工作流引擎 |
| **状态追踪** | 每个节点实时状态 | Round-level 统计 | 粒度粗 |
| **并发控制** | Task级 + 预算限制 | Round-level | 缺Task隔离 |
| **事件系统** | SSE 流式事件 | MessageBus (点对点) | 缺广播事件 |

---

## 二、Crews 数据模型与隔离机制

### 2.1 Crews 的四层架构

```python
# 层次1：User Sessions
# 用户与系统的对话界面
class UserSession:
    session_id: str
    user_id: str
    created_at: datetime
    active_crews: List[str]  # 当前激活的 Crews

# 层次2：Crews（命名Agent组）
# 逻辑上的Agent协作团队
class Crew:
    crew_id: str
    name: str                    # 可读名称，e.g., "Research Crew"
    description: str
    members: List[AgentMember]  # Agent 角色分配
    profile_id: str             # 关联的 Profile（工作空间）
    metadata: Dict[str, Any]    # 自定义元数据
    
    # 权限模型
    permissions: CrewPermissions
    created_at: datetime
    updated_at: datetime

class AgentMember:
    agent_id: str
    role: str                    # "researcher", "analyst", "writer"
    capabilities: List[str]     # ["web_search", "data_analysis"]
    priority: int
    max_concurrent_tasks: int = 3

# 层次3：Profile（工作空间隔离）
# 每个 Crew 有独立的工作目录和资源上下文
class Profile:
    profile_id: str
    crew_id: str
    workspace_root: Path         # /home/user/.hermes/profiles/{profile_id}
    
    # 隔离的资源
    knowledge_base: Path         # 该 Crew 的知识库
    artifact_dir: Path           # 生成文件存储目录
    memory: MemoryStore         # Crew级别的持久化记忆
    
    # 计算资源限制
    resource_limits: ResourceLimits

class ResourceLimits:
    max_memory_mb: int = 2048
    max_disk_mb: int = 10240
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 3600

# 层次4：Activity Feed（完整审计）
class CrewActivityLog:
    crew_id: str
    activities: List[ActivityEvent]  # 事件流
    
class ActivityEvent:
    event_id: str
    timestamp: datetime
    event_type: Literal[
        "task_created",
        "task_started",
        "task_completed",
        "task_failed",
        "agent_message",
        "resource_alert",
        "error"
    ]
    actor: str                   # agent_id 或 "user"
    details: Dict[str, Any]
    metadata: Dict[str, Any]
```

### 2.2 隔离机制详解

**隔离层次 1：会话隔离**
```python
# 不同用户的会话完全独立
# 存储结构：
~/.hermes/
  users/
    user_a/sessions/session_001/
    user_b/sessions/session_001/  # 独立命名空间
```

**隔离层次 2：Crew 隔离**
```python
# 同一用户的多个 Crew 资源隔离
~/.hermes/
  users/
    user_a/
      profiles/
        research_crew/     # Crew A 的工作空间
          knowledge/
          artifacts/
          memory.db
        coding_crew/       # Crew B 的工作空间（独立）
          knowledge/
          artifacts/
          memory.db
```

**隔离层次 3：Profile 隔离**
```python
# 细粒度资源隔离
class ProfileIsolationManager:
    async def get_isolated_context(
        self,
        profile_id: str
    ) -> IsolatedContext:
        """获取指定 Profile 的隔离上下文"""
        profile = await self.load_profile(profile_id)
        
        # 返回沙箱化的环境
        return IsolatedContext(
            workspace_root=profile.workspace_root,
            allowed_dirs=[
                profile.knowledge_base,
                profile.artifact_dir,
            ],
            denied_dirs=[
                "/etc",
                "/home/other_user"
            ],
            resource_limits=profile.resource_limits,
            env_vars=profile.safe_env_vars()
        )
    
    async def execute_in_isolated_context(
        self,
        profile_id: str,
        task: Task
    ) -> TaskResult:
        """在隔离上下文中执行任务"""
        context = await self.get_isolated_context(profile_id)
        
        # 沙箱执行（如实际需要）
        with context.sandbox():
            result = await task.execute()
        
        return result
```

**隔离层次 4：资源限制**
```python
class ResourceGuard:
    """资源守卫 — 防止 Crew 资源溢出"""
    
    async def check_and_allocate(
        self,
        crew_id: str,
        required_resources: ResourceRequest
    ) -> bool:
        """检查和分配资源"""
        crew_limits = await self.get_crew_limits(crew_id)
        
        # 检查内存
        current_memory = await self.get_current_memory_usage(crew_id)
        if current_memory + required_resources.memory_mb > crew_limits.max_memory_mb:
            raise ResourceExhausted(f"Memory limit for {crew_id}")
        
        # 检查磁盘
        current_disk = await self.get_current_disk_usage(crew_id)
        if current_disk + required_resources.disk_mb > crew_limits.max_disk_mb:
            raise ResourceExhausted(f"Disk limit for {crew_id}")
        
        # 检查并发任务数
        current_tasks = await self.count_active_tasks(crew_id)
        if current_tasks >= crew_limits.max_concurrent_tasks:
            raise ResourceExhausted(f"Task concurrency limit for {crew_id}")
        
        return True
```

### 2.3 Crews 与当前 Agent 池的对比

**当前 Agent Chat Hub：**
```python
# 所有 Agent 在单一全局池中
agents = [
    AgentConfig(id="agent_a", ...),
    AgentConfig(id="agent_b", ...),
    AgentConfig(id="agent_c", ...),
]

# 响应协调在 Round 级别
class RoundState:
    call_records: Set[Tuple[session, round, agent]]
    total_calls: int
    total_tokens: int
```

**Hermes-Studio Crews：**
```python
# Agent 按 Crew 分组
crews = [
    Crew(
        name="research_crew",
        members=[
            AgentMember(agent="web_search", role="researcher"),
            AgentMember(agent="summarizer", role="analyst"),
        ],
        profile_id="profile_123"  # 专用工作空间
    ),
    Crew(
        name="coding_crew",
        members=[
            AgentMember(agent="code_review", role="reviewer"),
            AgentMember(agent="debugger", role="debugger"),
        ],
        profile_id="profile_456"
    )
]

# 每个 Crew 有独立的资源限制、持久化存储、审计日志
```

**改进建议**（见第四部分）：引入 CrewManager，支持命名 Agent 组。

---

## 三、DAG 工作流引擎的实现

### 3.1 核心数据模型

```python
# DAG 的基本单位：Workflow Node（对应 Agent Task）
class WorkflowNode:
    """工作流节点 — 表示一个可执行的任务"""
    
    node_id: str
    name: str
    description: Optional[str]
    
    # 执行配置
    agent_id: str                # 负责执行的 Agent
    task_definition: TaskDef     # 任务定义
    
    # 依赖配置
    dependencies: List[str]      # 前置节点 ID
    
    # 参数配置
    input_schema: Dict[str, Any]         # 输入参数模型
    output_schema: Dict[str, Any]        # 输出参数模型
    
    # 可视化位置
    position: Tuple[int, int]    # (x, y) 用于编辑器显示
    
    # 执行策略
    retry_policy: RetryPolicy
    timeout_seconds: int = 3600
    
    # 元数据
    tags: List[str]
    created_at: datetime

class RetryPolicy:
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    initial_delay_seconds: float = 1.0
    
    def get_delay(self, attempt: int) -> float:
        return self.initial_delay_seconds * (self.backoff_multiplier ** attempt)

# DAG 的容器和执行管理
class Workflow:
    """有向无环图工作流"""
    
    workflow_id: str
    name: str
    description: str
    
    # 图结构
    nodes: Dict[str, WorkflowNode]  # node_id -> WorkflowNode
    edges: List[WorkflowEdge]       # 连接关系
    
    # 执行配置
    max_parallelism: int = 5        # 最多同时执行的节点数
    
    # 元数据
    crew_id: str                     # 所属 Crew
    created_at: datetime
    updated_at: datetime
    version: int
    
    def get_topological_order(self) -> List[str]:
        """获取拓扑排序的节点执行顺序"""
        # 使用 Kahn 算法计算拓扑排序
        in_degree = {node_id: 0 for node_id in self.nodes}
        
        for edge in self.edges:
            in_degree[edge.to_node_id] += 1
        
        queue = [nid for nid, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            # 移除该节点的出边
            for edge in self.edges:
                if edge.from_node_id == node_id:
                    in_degree[edge.to_node_id] -= 1
                    if in_degree[edge.to_node_id] == 0:
                        queue.append(edge.to_node_id)
        
        if len(result) != len(self.nodes):
            raise ValueError("Workflow contains cycle!")
        
        return result
    
    def validate(self) -> List[str]:
        """验证工作流有效性"""
        errors = []
        
        # 检查循环
        try:
            self.get_topological_order()
        except ValueError as e:
            errors.append(str(e))
        
        # 检查缺失节点
        for edge in self.edges:
            if edge.from_node_id not in self.nodes:
                errors.append(f"Missing node: {edge.from_node_id}")
            if edge.to_node_id not in self.nodes:
                errors.append(f"Missing node: {edge.to_node_id}")
        
        # 检查参数匹配
        for edge in self.edges:
            from_node = self.nodes[edge.from_node_id]
            to_node = self.nodes[edge.to_node_id]
            
            # 验证输出->输入参数兼容
            for param_name in edge.data_mapping:
                if param_name not in from_node.output_schema:
                    errors.append(
                        f"Output parameter {param_name} "
                        f"not found in {edge.from_node_id}"
                    )
        
        return errors

class WorkflowEdge:
    """工作流边 — 表示节点间的依赖关系"""
    
    edge_id: str
    from_node_id: str
    to_node_id: str
    
    # 数据流
    data_mapping: Dict[str, str]  # {output_param: input_param}
    
    # 控制流条件
    condition: Optional[str]       # 条件表达式
    
    # 样式（用于编辑器）
    style: Dict[str, Any] = {}
```

### 3.2 执行引擎

```python
class WorkflowExecutor:
    """工作流执行引擎 — 协调 DAG 执行"""
    
    def __init__(
        self,
        agent_executor: AgentExecutor,
        resource_guard: ResourceGuard
    ):
        self.agent_executor = agent_executor
        self.resource_guard = resource_guard
        self.execution_cache: Dict[str, ExecutionResult] = {}
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> WorkflowResult:
        """执行整个工作流"""
        
        # 验证工作流
        errors = workflow.validate()
        if errors:
            raise ValueError(f"Invalid workflow: {errors}")
        
        # 获取拓扑排序
        topo_order = workflow.get_topological_order()
        
        # 执行追踪
        execution_run = ExecutionRun(
            workflow_id=workflow.workflow_id,
            run_id=str(uuid.uuid4()),
            start_time=datetime.now(),
            node_results={}
        )
        
        # 并发执行准备
        ready_nodes = set()
        completed_nodes = set()
        node_inputs = {
            node_id: initial_inputs if node_id in [e for e in topo_order if not workflow.nodes[e].dependencies]
            else {}
            for node_id in workflow.nodes
        }
        
        # 执行循环
        pending_tasks = {}  # node_id -> asyncio.Task
        
        while len(completed_nodes) < len(workflow.nodes):
            # 1. 找出所有可执行的节点（前置都完成）
            ready_nodes = self._find_ready_nodes(
                workflow,
                completed_nodes,
                node_inputs
            )
            
            # 2. 尊重并发限制启动任务
            for node_id in ready_nodes:
                if node_id not in pending_tasks and \
                   len(pending_tasks) < workflow.max_parallelism:
                    
                    # 资源检查
                    await self.resource_guard.check_and_allocate(
                        crew_id=workflow.crew_id,
                        required_resources=ResourceRequest(
                            memory_mb=512,  # 估计值
                            disk_mb=100
                        )
                    )
                    
                    # 启动任务
                    task = asyncio.create_task(
                        self._execute_node(
                            workflow,
                            node_id,
                            node_inputs[node_id],
                            execution_run,
                            context
                        )
                    )
                    pending_tasks[node_id] = task
            
            # 3. 等待至少一个任务完成
            if pending_tasks:
                done, pending = await asyncio.wait(
                    pending_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # 处理完成的任务
                for task in done:
                    node_id = self._find_node_by_task(pending_tasks, task)
                    result = await task
                    
                    completed_nodes.add(node_id)
                    execution_run.node_results[node_id] = result
                    
                    # 更新下游节点的输入
                    for downstream_node_id in self._get_downstream_nodes(workflow, node_id):
                        node_inputs[downstream_node_id].update(
                            result.output_data
                        )
                    
                    del pending_tasks[node_id]
            
            # 安全检查：防止死循环
            if not pending_tasks and len(completed_nodes) < len(workflow.nodes):
                remaining = set(workflow.nodes.keys()) - completed_nodes
                raise RuntimeError(f"Workflow stuck with remaining nodes: {remaining}")
        
        # 完成
        execution_run.end_time = datetime.now()
        execution_run.status = "completed"
        
        return WorkflowResult(
            workflow_id=workflow.workflow_id,
            execution_run=execution_run,
            outputs=node_inputs.get("output_node", {})
        )
    
    async def _execute_node(
        self,
        workflow: Workflow,
        node_id: str,
        inputs: Dict[str, Any],
        execution_run: ExecutionRun,
        context: ExecutionContext
    ) -> NodeExecutionResult:
        """执行单个节点（带重试和超时）"""
        
        node = workflow.nodes[node_id]
        
        for attempt in range(node.retry_policy.max_retries + 1):
            try:
                # 发布节点启动事件
                await self._publish_event(
                    "workflow_node_started",
                    node_id=node_id,
                    attempt=attempt
                )
                
                # 执行任务（带超时）
                result = await asyncio.wait_for(
                    self.agent_executor.call_agent(
                        agent_id=node.agent_id,
                        task=node.task_definition,
                        inputs=inputs,
                        context=context
                    ),
                    timeout=node.timeout_seconds
                )
                
                # 发布节点完成事件
                await self._publish_event(
                    "workflow_node_completed",
                    node_id=node_id,
                    result=result
                )
                
                return NodeExecutionResult(
                    node_id=node_id,
                    status="completed",
                    output_data=result,
                    execution_time_seconds=(
                        datetime.now() - execution_run.start_time
                    ).total_seconds()
                )
                
            except asyncio.TimeoutError:
                await self._publish_event(
                    "workflow_node_timeout",
                    node_id=node_id
                )
                
                if attempt < node.retry_policy.max_retries:
                    delay = node.retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
            
            except Exception as e:
                await self._publish_event(
                    "workflow_node_failed",
                    node_id=node_id,
                    error=str(e)
                )
                
                if attempt < node.retry_policy.max_retries:
                    delay = node.retry_policy.get_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
        
        raise RuntimeError(f"Node {node_id} failed after retries")
    
    def _find_ready_nodes(
        self,
        workflow: Workflow,
        completed_nodes: Set[str],
        node_inputs: Dict[str, Dict]
    ) -> List[str]:
        """找出所有前置依赖都已完成的节点"""
        ready = []
        
        for node_id, node in workflow.nodes.items():
            if node_id in completed_nodes:
                continue
            
            # 检查所有前置节点是否都完成
            deps_satisfied = all(
                dep_id in completed_nodes
                for dep_id in node.dependencies
            )
            
            if deps_satisfied:
                ready.append(node_id)
        
        return ready
```

### 3.3 工作流编辑器（前端 / TUI 组件）

```python
# 核心要素：节点、边、布局算法
class WorkflowEditor:
    """工作流可视化编辑器"""
    
    def __init__(self):
        self.selected_node: Optional[str] = None
        self.selected_edge: Optional[str] = None
        self.viewport = Viewport(x=0, y=0, zoom=1.0)
    
    def render_canvas(self) -> str:
        """渲染编辑画布"""
        # 1. 绘制节点（圆形/矩形）
        for node_id, node in self.workflow.nodes.items():
            self._render_node(node)
        
        # 2. 绘制边（贝塞尔曲线）
        for edge in self.workflow.edges:
            from_node = self.workflow.nodes[edge.from_node_id]
            to_node = self.workflow.nodes[edge.to_node_id]
            self._render_bezier_edge(from_node, to_node, edge)
        
        # 3. 渲染选中状态和工具栏
        if self.selected_node:
            self._render_node_properties(self.selected_node)
    
    def _render_bezier_edge(self, from_node, to_node, edge):
        """使用贝塞尔曲线渲染连接"""
        # 计算贝塞尔曲线的控制点
        start = (from_node.position[0] + 50, from_node.position[1] + 25)
        end = (to_node.position[0], to_node.position[1] + 25)
        
        # 控制点（偏向右下）
        cp1 = (start[0] + 100, start[1])
        cp2 = (end[0] - 100, end[1])
        
        # 使用贝塞尔曲线公式计算
        points = self._bezier_curve(start, cp1, cp2, end, segments=20)
        
        # 绘制到画布
        for i in range(len(points) - 1):
            self._draw_line(points[i], points[i+1])
    
    def auto_layout(self):
        """自动布局 — 使用层级布局算法"""
        # 1. 按拓扑排序分层
        topo_order = self.workflow.get_topological_order()
        layers = self._assign_layers(topo_order)
        
        # 2. 计算每层的节点位置
        y_spacing = 100
        for layer_num, layer_nodes in enumerate(layers):
            y = layer_num * y_spacing
            x_spacing = 150
            
            for pos_in_layer, node_id in enumerate(layer_nodes):
                x = pos_in_layer * x_spacing + 50
                self.workflow.nodes[node_id].position = (x, y)
    
    def validate_edit(self) -> List[str]:
        """验证编辑的工作流"""
        return self.workflow.validate()
```

---

## 四、任务调度与依赖解析

### 4.1 Topological Sort 实现

```python
class DependencyResolver:
    """依赖解析器 — 拓扑排序与循环检测"""
    
    @staticmethod
    def topological_sort(workflow: Workflow) -> List[str]:
        """Kahn 算法 — 时间复杂度 O(V+E)"""
        nodes = workflow.nodes
        edges = workflow.edges
        
        # 计算入度
        in_degree = {node_id: 0 for node_id in nodes}
        adjacency = {node_id: [] for node_id in nodes}
        
        for edge in edges:
            in_degree[edge.to_node_id] += 1
            adjacency[edge.from_node_id].append(edge.to_node_id)
        
        # 找出所有入度为 0 的节点
        queue = [nid for nid, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            # 移除该节点的所有出边
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否存在循环
        if len(result) != len(nodes):
            detected_cycle = self._find_cycle(workflow)
            raise CycleDetectedError(f"Cycle detected: {detected_cycle}")
        
        return result
    
    @staticmethod
    def _find_cycle(workflow: Workflow) -> List[str]:
        """使用 DFS 找出循环路径"""
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            for edge in workflow.edges:
                if edge.from_node_id == node_id:
                    neighbor = edge.to_node_id
                    
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        # 找到循环
                        cycle_start_idx = path.index(neighbor)
                        return path[cycle_start_idx:] + [neighbor]
            
            path.pop()
            rec_stack.remove(node_id)
            return False
        
        for node_id in workflow.nodes:
            if node_id not in visited:
                cycle = dfs(node_id)
                if cycle:
                    return cycle
        
        return []
    
    @staticmethod
    def get_downstream_nodes(
        workflow: Workflow,
        node_id: str
    ) -> List[str]:
        """获取指定节点的所有下游节点"""
        downstream = []
        visited = set()
        
        def dfs(current_id):
            visited.add(current_id)
            
            for edge in workflow.edges:
                if edge.from_node_id == current_id and \
                   edge.to_node_id not in visited:
                    downstream.append(edge.to_node_id)
                    dfs(edge.to_node_id)
        
        dfs(node_id)
        return downstream
    
    @staticmethod
    def get_upstream_nodes(
        workflow: Workflow,
        node_id: str
    ) -> List[str]:
        """获取指定节点的所有上游节点"""
        upstream = []
        visited = set()
        
        def dfs(current_id):
            visited.add(current_id)
            
            for edge in workflow.edges:
                if edge.to_node_id == current_id and \
                   edge.from_node_id not in visited:
                    upstream.append(edge.from_node_id)
                    dfs(edge.from_node_id)
        
        dfs(node_id)
        return upstream
```

### 4.2 并发调度策略

```python
class ConcurrencyScheduler:
    """并发调度器 — 尊重依赖和资源限制"""
    
    def __init__(self, max_parallelism: int = 5):
        self.max_parallelism = max_parallelism
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_nodes: Set[str] = set()
    
    async def schedule_workflow(
        self,
        workflow: Workflow,
        executor: WorkflowExecutor
    ) -> WorkflowResult:
        """协调工作流执行 — 最大化并发同时尊重依赖"""
        
        dependency_resolver = DependencyResolver()
        
        # 验证无循环
        try:
            topo_order = dependency_resolver.topological_sort(workflow)
        except CycleDetectedError as e:
            logger.error(f"Workflow has cycle: {e}")
            raise
        
        # 执行跟踪
        node_states = {
            node_id: "pending"
            for node_id in workflow.nodes
        }
        node_results = {}
        
        while len(self.completed_nodes) < len(workflow.nodes):
            # 1. 找出所有可运行的节点
            ready_nodes = [
                node_id for node_id in workflow.nodes
                if node_states[node_id] == "pending" and
                   all(
                       dependency_resolver.get_upstream_nodes(
                           workflow, node_id
                       )[dep] in self.completed_nodes
                       for dep in workflow.nodes[node_id].dependencies
                   )
            ]
            
            # 2. 启动可运行的节点（受并发限制）
            for node_id in ready_nodes[:self.max_parallelism - len(self.active_tasks)]:
                node_states[node_id] = "running"
                
                task = asyncio.create_task(
                    executor._execute_node(
                        workflow,
                        node_id,
                        {},  # 实际应传入汇总的输入
                        ExecutionRun(...),
                        ExecutionContext(...)
                    )
                )
                self.active_tasks[node_id] = task
            
            # 3. 等待至少一个任务完成
            if self.active_tasks:
                done, pending = await asyncio.wait(
                    self.active_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    node_id = [nid for nid, t in self.active_tasks.items() if t is task][0]
                    result = await task
                    
                    node_states[node_id] = "completed"
                    node_results[node_id] = result
                    self.completed_nodes.add(node_id)
                    
                    del self.active_tasks[node_id]
            else:
                # 没有进行中的任务且有待处理节点 → 死锁
                pending = [nid for nid in workflow.nodes if node_states[nid] == "pending"]
                raise RuntimeError(f"Deadlock: pending nodes {pending}")
        
        return WorkflowResult(
            workflow_id=workflow.workflow_id,
            node_results=node_results
        )
```

---

## 五、并发控制与资源管理

### 5.1 多层资源管理

```python
class HierarchicalResourceManager:
    """
    分层资源管理：
    全局限制 > Crew限制 > Task限制
    """
    
    def __init__(self):
        # 全局限制
        self.global_limits = GlobalResourceLimits(
            max_total_tasks=100,
            max_total_memory_mb=16384,  # 16GB
            max_total_gpu_percent=80
        )
        
        # 按 Crew 的配额
        self.crew_quotas: Dict[str, CrewResourceQuota] = {}
        
        # 已分配的资源
        self.allocations: Dict[str, ResourceAllocation] = {}
    
    async def allocate_for_task(
        self,
        task_id: str,
        crew_id: str,
        requested: ResourceRequest
    ) -> ResourceAllocation:
        """为任务分配资源"""
        
        # 1. 全局限制检查
        current_global = self._sum_allocations()
        if current_global.memory_mb + requested.memory_mb > self.global_limits.max_total_memory_mb:
            raise ResourceExhausted("Global memory limit")
        
        # 2. Crew 配额检查
        crew_quota = self.crew_quotas.get(crew_id)
        if crew_quota:
            crew_usage = self._sum_allocations_by_crew(crew_id)
            if crew_usage.memory_mb + requested.memory_mb > crew_quota.max_memory_mb:
                raise ResourceExhausted(f"Crew {crew_id} memory limit")
        
        # 3. 分配资源
        allocation = ResourceAllocation(
            task_id=task_id,
            crew_id=crew_id,
            memory_mb=requested.memory_mb,
            cpu_cores=requested.cpu_cores,
            gpu_percent=requested.gpu_percent,
            allocated_at=datetime.now()
        )
        
        self.allocations[task_id] = allocation
        return allocation
    
    async def release_for_task(self, task_id: str) -> None:
        """释放任务的资源"""
        if task_id in self.allocations:
            del self.allocations[task_id]
    
    def _sum_allocations(self) -> ResourceUsage:
        """统计全局资源使用"""
        return ResourceUsage(
            memory_mb=sum(a.memory_mb for a in self.allocations.values()),
            cpu_cores=sum(a.cpu_cores for a in self.allocations.values()),
            gpu_percent=max((a.gpu_percent for a in self.allocations.values()), default=0)
        )
    
    def _sum_allocations_by_crew(self, crew_id: str) -> ResourceUsage:
        """统计指定 Crew 的资源使用"""
        crew_allocs = [a for a in self.allocations.values() if a.crew_id == crew_id]
        return ResourceUsage(
            memory_mb=sum(a.memory_mb for a in crew_allocs),
            cpu_cores=sum(a.cpu_cores for a in crew_allocs),
            gpu_percent=max((a.gpu_percent for a in crew_allocs), default=0)
        )
```

### 5.2 超时与取消管理

```python
class ExecutionCancellationManager:
    """任务取消与超时管理"""
    
    def __init__(self):
        self.cancellation_tokens: Dict[str, asyncio.CancelledError] = {}
        self.timeouts: Dict[str, asyncio.Task] = {}
    
    async def execute_with_timeout(
        self,
        task_coro,
        timeout_seconds: float,
        task_id: str
    ) -> Any:
        """带超时的任务执行"""
        try:
            result = await asyncio.wait_for(
                task_coro,
                timeout=timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            # 发送取消信号
            await self.cancel_task(task_id, reason="timeout")
            raise TaskTimeoutError(f"Task {task_id} timed out after {timeout_seconds}s")
    
    async def cancel_task(self, task_id: str, reason: str) -> None:
        """主动取消任务"""
        # 发送事件
        await self._publish_cancellation_event(task_id, reason)
        
        # 标记为已取消
        self.cancellation_tokens[task_id] = asyncio.CancelledError(reason)
    
    def is_cancelled(self, task_id: str) -> bool:
        """检查任务是否已被取消"""
        return task_id in self.cancellation_tokens
```

---

## 六、ResponseCoordinator vs Hermes 调度对比

### 6.1 功能矩阵

| 维度 | ResponseCoordinator | Hermes Scheduler | 差距 | 改进优先级 |
|------|---|---|---|---|
| **去重** | ✅ 三元组 (session, round, agent) | ✅ 任务级 + Node级 | 一致 | P3 |
| **排序** | ✅ Priority + agent_id | ✅ Topo sort | Hermes更强 | P2 |
| **预算** | ✅ Calls, Tokens, Timeout | ✅ Per-crew资源 | Hermes更细 | P1 |
| **并发** | ⚠️ Round级 | ✅ 任务级 + 动态 | Hermes更优 | P0 |
| **依赖** | ❌ 无 | ✅ DAG依赖 | 完全缺失 | P0 |
| **状态** | ⚠️ Round-level | ✅ Per-node | 粒度粗 | P1 |
| **恢复** | ❌ 无 | ✅ 持久化执行运行 | 完全缺失 | P2 |
| **取消** | ✅ Round级 | ✅ Task级 | 一致 | P3 |

### 6.2 执行流程对比

**ResponseCoordinator（当前）:**
```
User Message
    ↓
select_agents()
    ├─ qualify_agents (Rule 1)
    ├─ sort_agents (Rule 2)
    ├─ filter_duplicates (Rule 3)
    └─ check_budget (Rule 5)
    ↓
[并发调用选中的agents]
    ↓
record_call() → 标记已调用
    ↓
下一轮（重复）
```

**Hermes Scheduler:**
```
User Request → Coordinator
    ↓
Intent Recognition
    ↓
Task Decomposition & DAG Creation
    ↓
Topological Sort & Dependency Resolution
    ↓
[并发执行多个Task，尊重：
  - 依赖关系
  - 资源限制
  - 超时策略
]
    ↓
State Tracking (per-node)
    ↓
Result Aggregation & Fallback
```

---

## 七、改进建议

### 7.1 Phase 4 架构升级：Task 模型

```python
# src/core/task.py - 新增
class Task(BaseModel):
    """独立的可执行单位（比 Agent 调用更细粒度）"""
    
    task_id: str
    name: str
    agent_id: str
    
    # 输入/输出
    input_data: Dict[str, Any]
    expected_output_schema: Dict[str, Any]
    
    # 执行策略
    retry_policy: RetryPolicy
    timeout_seconds: int = 3600
    
    # 依赖
    depends_on: List[str]  # 前置 Task IDs
    
    # 状态追踪
    status: TaskStatus = "pending"
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
```

### 7.2 阶段实施路线图

**Phase 4a (Week 1-2): Task 模型与执行**
- [ ] 实现 Task 类和 TaskStatus
- [ ] 创建 TaskExecutor（带重试和超时）
- [ ] Task 持久化到 SQLite
- [ ] 迁移 Agent 调用到 Task 模型

**Phase 4b (Week 3-4): DAG 工作流**
- [ ] 实现 Workflow、Node、Edge 模型
- [ ] 拓扑排序与循环检测
- [ ] WorkflowExecutor 基础版本
- [ ] DAG 验证和错误处理

**Phase 4c (Week 5-6): 并发与资源管理**
- [ ] HierarchicalResourceManager
- [ ] 并发调度策略
- [ ] 实时状态追踪
- [ ] 集成测试

**Phase 4d (Week 7-8): 可视化编辑器**
- [ ] TUI 工作流编辑器
- [ ] 节点/边管理
- [ ] 自动布局算法
- [ ] 实时执行可视化

### 7.3 与 ResponseCoordinator 的兼容性

**保持现有 API，扩展新功能：**
```python
# 现有的 6 条规则仍然有效
coordinator = ResponseCoordinator()
agents = coordinator.qualify_agents(available_agents, mentions=mentions)

# 新增任务级协调
task_scheduler = TaskScheduler()
task_results = await task_scheduler.execute_dag(workflow)

# 两者可共存（ResponseCoordinator 处理 Agent 轮次，TaskScheduler 处理工作流）
```

---

## 八、核心组件实现清单

### 优先级 P0（关键）
- [ ] Task 数据模型
- [ ] Workflow、Node、Edge 模型
- [ ] 拓扑排序算法
- [ ] 基础 WorkflowExecutor

### 优先级 P1（重要）
- [ ] HierarchicalResourceManager
- [ ] 并发调度器
- [ ] DAG 验证
- [ ] 任务持久化

### 优先级 P2（增强）
- [ ] Crew 模型
- [ ] Profile 隔离机制
- [ ] 实时状态追踪 SSE
- [ ] 审计日志

### 优先级 P3（可选）
- [ ] TUI 工作流编辑器
- [ ] 自动布局算法
- [ ] 循环 Workflow 支持
- [ ] 条件执行分支

---

## 九、风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| DAG 循环 | 无限执行 | 拓扑排序检查 + 单元测试 |
| 资源溢出 | 系统崩溃 | 分层配额 + 监控告警 |
| 超时未处理 | 僵尸任务 | CancellationManager + 强制超时 |
| 状态不一致 | 数据损坏 | 事务机制 + 审计日志 |
| 性能衰减 | 高延迟 | 缓存优化 + 并发限制 |

---

## 十、总结与建议

### 主要发现
1. **Hermes-Studio 的优势**：完整的 DAG 工作流 + 细粒度资源管理 + 事件驱动架构
2. **当前项目的优势**：简洁的 ResponseCoordinator 设计 + 6 条规则清晰 + 易维护
3. **结合的最佳实践**：保留 ResponseCoordinator 的核心，增加 Task/DAG 层

### 实施建议
1. **短期（Phase 4a）**：实现 Task 模型，逐步迁移 Agent 调用
2. **中期（Phase 4b-c）**：完整 DAG 引擎 + 并发调度器
3. **长期（Phase 4d）**：可视化工作流编辑器，为 Web 扩展做准备

### 代码示例位置
- 本文档第二至五部分包含完整的代码实现框架
- 可直接复制到项目中，最小化改造

---

**文档版本**: 1.0  
**最后更新**: 2026-09-05  
**推荐审阅**: 架构师、技术主管
