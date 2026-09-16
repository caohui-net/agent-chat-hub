# 工作流引擎关键组件实现指南
## Agent Chat Hub Phase 4 技术蓝图

**文档版本**: 1.0  
**日期**: 2026-09-05  
**目标**: 从 ResponseCoordinator（规则级）升级到 Task/DAG（工程级）

---

## 一、快速参考：三层架构

```
┌─────────────────────────────────────────┐
│  Layer 3: Workflow Orchestration        │  ← DAG、可视化、高级调度
│  (Phase 4d: Optional Web Editor)        │
├─────────────────────────────────────────┤
│  Layer 2: Task Execution & Scheduling   │  ← 并发、资源管理、状态追踪
│  (Phase 4a-c: Core Enhancement)        │
├─────────────────────────────────────────┤
│  Layer 1: Agent Response Coordination   │  ← 现有 ResponseCoordinator
│  (Phase 1-3: Current Foundation)       │
└─────────────────────────────────────────┘
```

---

## 二、实现顺序与依赖

### 2.1 模块加载顺序（按执行先后）

```
1. src/core/task.py                     # Task 数据模型
   ├─ TaskStatus enum
   ├─ Task class
   ├─ TaskResult class
   └─ RetryPolicy class

2. src/core/workflow.py                 # 工作流数据模型
   ├─ WorkflowNode class
   ├─ WorkflowEdge class
   ├─ Workflow class
   └─ Validators

3. src/core/dependency_resolver.py      # 依赖解析
   ├─ DependencyResolver class
   ├─ topological_sort()
   ├─ cycle_detection()
   └─ graph_analysis()

4. src/agents/task_executor.py          # Task 执行器
   ├─ TaskExecutor class
   ├─ retry_with_backoff()
   └─ timeout_handling()

5. src/agents/workflow_executor.py      # 工作流执行引擎
   ├─ WorkflowExecutor class
   ├─ execute_workflow()
   ├─ _find_ready_nodes()
   └─ concurrent_execution()

6. src/agents/concurrency_scheduler.py  # 并发调度器
   ├─ ConcurrencyScheduler class
   ├─ schedule_workflow()
   └─ resource_aware_scheduling()

7. src/core/resource_manager.py         # 资源管理器
   ├─ HierarchicalResourceManager
   ├─ allocate_resources()
   └─ enforce_limits()

8. src/ui/workflow_editor.py            # TUI 工作流编辑器
   ├─ WorkflowEditor widget
   ├─ auto_layout()
   └─ interactive_editing()
```

### 2.2 实现代码框架（可直接复制）

#### 步骤 1: Task 数据模型

```python
# src/core/task.py
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    """任务状态机"""
    PENDING = "pending"           # 等待前置完成
    QUEUED = "queued"             # 等待资源
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 成功完成
    FAILED = "failed"             # 执行失败
    RETRYING = "retrying"         # 重试中
    CANCELLED = "cancelled"       # 已取消
    TIMEOUT = "timeout"           # 超时

class RetryPolicy(BaseModel):
    """重试策略"""
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    
    def get_delay(self, attempt: int) -> float:
        """指数退避计算"""
        delay = self.initial_delay_seconds * (self.backoff_multiplier ** attempt)
        return min(delay, self.max_delay_seconds)

class Task(BaseModel):
    """可执行任务 — 工作流的基本单位"""
    
    # 标识
    task_id: str
    name: str
    description: Optional[str] = None
    
    # 执行配置
    agent_id: str                          # 负责执行的 Agent
    prompt: str                             # 任务提示词
    
    # 输入输出
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    
    # 依赖
    depends_on: List[str] = Field(default_factory=list)  # 前置 Task IDs
    
    # 执行策略
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout_seconds: int = 3600
    
    # 资源需求
    estimated_memory_mb: int = 512
    estimated_disk_mb: int = 100
    estimated_duration_seconds: int = 60
    
    # 状态追踪
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    
    # 时间戳
    created_at: datetime
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 元数据
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskResult(BaseModel):
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    output: Dict[str, Any]
    error: Optional[str] = None
    execution_time_seconds: float
    tokens_used: int = 0
    attempt_number: int
    retry_delay_seconds: Optional[float] = None
```

#### 步骤 2: Workflow 数据模型

```python
# src/core/workflow.py
from typing import Dict, List, Set
from datetime import datetime

class WorkflowNode(BaseModel):
    """工作流节点 — 表示一个任务"""
    
    node_id: str
    task: Task
    
    # 可视化位置（用于编辑器）
    position_x: int = 0
    position_y: int = 0
    
    # 执行约束
    max_retries: int = 3
    timeout_seconds: int = 3600
    
    # 执行条件
    condition: Optional[str] = None  # 条件表达式，e.g., "${task_prev.output.success}"

class WorkflowEdge(BaseModel):
    """工作流边 — 节点间的依赖"""
    
    edge_id: str
    from_node_id: str
    to_node_id: str
    
    # 数据映射
    data_mapping: Dict[str, str] = Field(default_factory=dict)
    # e.g., {"previous_output": "current_input"}
    
    # 条件边
    condition: Optional[str] = None
    # e.g., "status == 'success'"

class Workflow(BaseModel):
    """有向无环图工作流"""
    
    workflow_id: str
    name: str
    description: Optional[str] = None
    
    # 图结构
    nodes: Dict[str, WorkflowNode] = Field(default_factory=dict)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    
    # 执行配置
    max_parallelism: int = 5              # 最多同时执行的节点
    timeout_seconds: int = 7200           # 整体超时
    
    # 关联
    crew_id: Optional[str] = None
    profile_id: Optional[str] = None
    
    # 元数据
    created_at: datetime
    updated_at: datetime
    created_by: str
    tags: List[str] = Field(default_factory=list)
    
    def add_node(self, node: WorkflowNode) -> None:
        """添加节点"""
        self.nodes[node.node_id] = node
    
    def add_edge(self, edge: WorkflowEdge) -> None:
        """添加边"""
        self.edges.append(edge)
    
    def validate(self) -> List[str]:
        """验证工作流有效性"""
        errors = []
        
        # 检查节点存在性
        for edge in self.edges:
            if edge.from_node_id not in self.nodes:
                errors.append(f"Missing node: {edge.from_node_id}")
            if edge.to_node_id not in self.nodes:
                errors.append(f"Missing node: {edge.to_node_id}")
        
        # 检查循环（在 DependencyResolver 中）
        
        return errors
```

#### 步骤 3: 依赖解析器

```python
# src/core/dependency_resolver.py
from typing import List, Set, Tuple, Dict
from collections import defaultdict

class CycleDetectedError(Exception):
    """检测到工作流循环"""
    pass

class DependencyResolver:
    """依赖解析与拓扑排序"""
    
    @staticmethod
    def topological_sort(workflow: Workflow) -> List[str]:
        """
        Kahn 算法 — O(V+E) 时间复杂度
        
        Returns:
            节点执行顺序
            
        Raises:
            CycleDetectedError: 工作流包含循环
        """
        nodes = set(workflow.nodes.keys())
        edges = workflow.edges
        
        # 计算入度
        in_degree = {node_id: 0 for node_id in nodes}
        adjacency = defaultdict(list)
        
        for edge in edges:
            in_degree[edge.to_node_id] += 1
            adjacency[edge.from_node_id].append(edge.to_node_id)
        
        # 入度为 0 的节点队列
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            # 移除出边，更新入度
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否所有节点都被处理
        if len(result) != len(nodes):
            cycle = DependencyResolver._find_cycle(workflow)
            raise CycleDetectedError(f"Cycle: {' -> '.join(cycle)}")
        
        return result
    
    @staticmethod
    def _find_cycle(workflow: Workflow) -> List[str]:
        """DFS 找出第一条循环"""
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            # 找出所有出边
            neighbors = [
                edge.to_node_id for edge in workflow.edges
                if edge.from_node_id == node_id
            ]
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # 找到循环
                    idx = path.index(neighbor)
                    return path[idx:] + [neighbor]
            
            path.pop()
            rec_stack.remove(node_id)
            return None
        
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
    ) -> Set[str]:
        """获取指定节点的所有下游节点"""
        downstream = set()
        visited = set()
        
        def dfs(current_id):
            visited.add(current_id)
            neighbors = [
                edge.to_node_id for edge in workflow.edges
                if edge.from_node_id == current_id
            ]
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    downstream.add(neighbor)
                    dfs(neighbor)
        
        dfs(node_id)
        return downstream
    
    @staticmethod
    def get_upstream_nodes(
        workflow: Workflow,
        node_id: str
    ) -> Set[str]:
        """获取指定节点的所有上游节点"""
        upstream = set()
        visited = set()
        
        def dfs(current_id):
            visited.add(current_id)
            predecessors = [
                edge.from_node_id for edge in workflow.edges
                if edge.to_node_id == current_id
            ]
            
            for predecessor in predecessors:
                if predecessor not in visited:
                    upstream.add(predecessor)
                    dfs(predecessor)
        
        dfs(node_id)
        return upstream
```

#### 步骤 4: Task 执行器

```python
# src/agents/task_executor.py
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TaskExecutor:
    """Task 执行器 — 带重试和超时"""
    
    def __init__(self, agent_executor: "AgentExecutor"):
        self.agent_executor = agent_executor
    
    async def execute_task(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> TaskResult:
        """执行单个任务"""
        
        attempt = 0
        last_error = None
        
        while attempt <= task.retry_policy.max_retries:
            try:
                task.status = TaskStatus.RUNNING
                task.attempts = attempt + 1
                task.started_at = datetime.now()
                
                logger.info(
                    f"Executing task {task.task_id} "
                    f"(attempt {attempt + 1}/{task.retry_policy.max_retries + 1})"
                )
                
                # 执行任务（带超时）
                output = await asyncio.wait_for(
                    self._run_task(task, context),
                    timeout=task.timeout_seconds
                )
                
                task.status = TaskStatus.COMPLETED
                task.output_data = output
                task.completed_at = datetime.now()
                
                return TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.COMPLETED,
                    output=output,
                    execution_time_seconds=(
                        task.completed_at - task.started_at
                    ).total_seconds(),
                    attempt_number=attempt + 1
                )
            
            except asyncio.TimeoutError:
                last_error = f"Timeout after {task.timeout_seconds}s"
                task.status = TaskStatus.TIMEOUT
                logger.warning(f"Task {task.task_id} timed out")
            
            except Exception as e:
                last_error = str(e)
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task.task_id} failed: {e}")
            
            # 重试处理
            if attempt < task.retry_policy.max_retries:
                delay = task.retry_policy.get_delay(attempt)
                logger.info(f"Retrying task {task.task_id} in {delay}s")
                task.status = TaskStatus.RETRYING
                await asyncio.sleep(delay)
            
            attempt += 1
        
        # 所有重试都失败
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()
        
        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            output={},
            error=last_error,
            execution_time_seconds=(
                task.completed_at - task.started_at
            ).total_seconds(),
            attempt_number=attempt
        )
    
    async def _run_task(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """实际执行任务（调用 Agent）"""
        
        # 整合输入数据
        full_input = {**context, **task.input_data}
        
        # 调用 Agent
        response = await self.agent_executor.call_agent(
            agent_id=task.agent_id,
            prompt=task.prompt,
            inputs=full_input
        )
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
```

#### 步骤 5: 工作流执行引擎

```python
# src/agents/workflow_executor.py
from typing import Dict, Set, List
import uuid

class WorkflowExecutor:
    """工作流执行引擎 — 协调 DAG 执行"""
    
    def __init__(
        self,
        task_executor: TaskExecutor,
        resource_manager: "HierarchicalResourceManager"
    ):
        self.task_executor = task_executor
        self.resource_manager = resource_manager
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行整个工作流"""
        
        # 验证
        errors = workflow.validate()
        if errors:
            raise ValueError(f"Invalid workflow: {errors}")
        
        # 检查循环
        try:
            topo_order = DependencyResolver.topological_sort(workflow)
        except CycleDetectedError as e:
            raise ValueError(f"Workflow has cycle: {e}")
        
        logger.info(f"Executing workflow {workflow.workflow_id} with {len(workflow.nodes)} nodes")
        
        # 执行状态
        node_results = {}
        completed_nodes: Set[str] = set()
        node_status: Dict[str, TaskStatus] = {
            node_id: TaskStatus.PENDING
            for node_id in workflow.nodes
        }
        
        # 上下文累积（用于数据流）
        execution_context = {**initial_inputs}
        
        # 并发执行循环
        pending_tasks: Dict[str, asyncio.Task] = {}
        
        while len(completed_nodes) < len(workflow.nodes):
            # 1. 找出所有可运行的节点
            ready_nodes = self._find_ready_nodes(
                workflow,
                completed_nodes,
                node_status
            )
            
            if not ready_nodes and not pending_tasks:
                # 死锁检测
                remaining = set(workflow.nodes.keys()) - completed_nodes
                raise RuntimeError(f"Deadlock: remaining nodes {remaining}")
            
            # 2. 启动可运行的节点（尊重并发限制）
            for node_id in ready_nodes:
                if node_id not in pending_tasks and \
                   len(pending_tasks) < workflow.max_parallelism:
                    
                    node = workflow.nodes[node_id]
                    node_status[node_id] = TaskStatus.QUEUED
                    
                    # 资源检查
                    try:
                        await self.resource_manager.allocate_for_task(
                            task_id=node_id,
                            crew_id=workflow.crew_id or "default",
                            requested_resources=ResourceRequest(
                                memory_mb=node.task.estimated_memory_mb,
                                disk_mb=node.task.estimated_disk_mb
                            )
                        )
                    except ResourceExhausted:
                        logger.warning(f"Insufficient resources for {node_id}, waiting...")
                        continue
                    
                    # 启动执行
                    task_coro = self.task_executor.execute_task(
                        node.task,
                        context=execution_context
                    )
                    task_obj = asyncio.create_task(task_coro)
                    pending_tasks[node_id] = task_obj
                    node_status[node_id] = TaskStatus.RUNNING
            
            # 3. 等待至少一个任务完成
            if pending_tasks:
                done, pending = await asyncio.wait(
                    pending_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    # 找出完成的节点
                    node_id = None
                    for nid, t in pending_tasks.items():
                        if t is task:
                            node_id = nid
                            break
                    
                    if node_id:
                        result = await task
                        completed_nodes.add(node_id)
                        node_results[node_id] = result
                        node_status[node_id] = result.status
                        
                        # 更新上下文用于后续节点
                        if result.status == TaskStatus.COMPLETED:
                            execution_context[node_id] = result.output
                        
                        # 释放资源
                        await self.resource_manager.release_for_task(node_id)
                        
                        del pending_tasks[node_id]
        
        logger.info(f"Workflow {workflow.workflow_id} completed")
        
        return {
            "workflow_id": workflow.workflow_id,
            "status": "completed",
            "node_results": node_results,
            "final_context": execution_context
        }
    
    def _find_ready_nodes(
        self,
        workflow: Workflow,
        completed_nodes: Set[str],
        node_status: Dict[str, TaskStatus]
    ) -> List[str]:
        """找出所有前置依赖都已完成的节点"""
        ready = []
        
        for node_id, node in workflow.nodes.items():
            # 检查是否已完成或正在进行
            if node_id in completed_nodes or node_status[node_id] in (
                TaskStatus.RUNNING,
                TaskStatus.QUEUED
            ):
                continue
            
            # 检查所有前置节点
            dependencies = node.task.depends_on
            if all(dep_id in completed_nodes for dep_id in dependencies):
                ready.append(node_id)
        
        return ready
```

---

## 三、集成清单

### 3.1 修改 src/agents/session.py

```python
# 添加到 SessionManager 类

from src.agents.workflow_executor import WorkflowExecutor
from src.core.workflow import Workflow

class SessionManager:
    # ... 现有代码 ...
    
    def __init__(self, ...):
        # ... 现有初始化 ...
        self.workflow_executor = None  # 延迟初始化
    
    async def execute_workflow(
        self,
        workflow: Workflow
    ) -> Dict[str, Any]:
        """执行工作流（Phase 4）"""
        
        if not self.workflow_executor:
            from src.agents.task_executor import TaskExecutor
            from src.core.resource_manager import HierarchicalResourceManager
            
            task_executor = TaskExecutor(self.executor)
            resource_manager = HierarchicalResourceManager()
            self.workflow_executor = WorkflowExecutor(
                task_executor,
                resource_manager
            )
        
        # 使用现有会话上下文作为初始输入
        initial_inputs = {
            "session_id": self.current_session.session_id,
            "round": self.current_round,
            "messages": [m.model_dump() for m in self.current_session.messages]
        }
        
        return await self.workflow_executor.execute_workflow(
            workflow,
            initial_inputs
        )
```

### 3.2 扩展 ResponseCoordinator

```python
# src/agents/coordinator.py 添加

class ResponseCoordinator:
    # ... 现有代码 ...
    
    def create_workflow_from_selection(
        self,
        selected_agents: List[AgentConfig],
        user_prompt: str
    ) -> Workflow:
        """从 Agent 选择创建工作流（向后兼容）
        
        Phase 4 新增：允许从现有的 Agent 协调创建工作流
        """
        
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        workflow = Workflow(
            workflow_id=workflow_id,
            name=f"Auto-generated from round {self.current_round.round_num}",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="coordinator"
        )
        
        # 创建节点（每个 Agent 一个）
        for idx, agent in enumerate(selected_agents):
            task = Task(
                task_id=f"task_{idx}",
                name=f"Call {agent.name}",
                agent_id=agent.agent_id,
                prompt=user_prompt,
                created_at=datetime.now()
            )
            
            node = WorkflowNode(
                node_id=f"node_{idx}",
                task=task,
                position_x=idx * 150,
                position_y=0
            )
            
            workflow.add_node(node)
            
            # 添加前一个节点的依赖（串行执行）
            if idx > 0:
                edge = WorkflowEdge(
                    edge_id=f"edge_{idx-1}_to_{idx}",
                    from_node_id=f"node_{idx-1}",
                    to_node_id=f"node_{idx}",
                    data_mapping={}
                )
                workflow.add_edge(edge)
        
        return workflow
```

---

## 四、测试用例框架

### 4.1 单元测试

```python
# tests/test_workflow.py
import pytest
from src.core.workflow import Workflow, WorkflowNode, WorkflowEdge, Task
from src.core.dependency_resolver import DependencyResolver, CycleDetectedError
from src.agents.workflow_executor import WorkflowExecutor

@pytest.fixture
def simple_workflow():
    """创建简单的三节点工作流"""
    workflow = Workflow(
        workflow_id="test_wf_1",
        name="Test Workflow",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        created_by="test"
    )
    
    # 创建三个任务：A -> B -> C
    for i, name in enumerate(['A', 'B', 'C']):
        task = Task(
            task_id=f"task_{name}",
            name=f"Task {name}",
            agent_id="agent_test",
            prompt=f"Execute task {name}",
            created_at=datetime.now()
        )
        
        node = WorkflowNode(
            node_id=f"node_{name}",
            task=task,
            position_x=i * 100,
            position_y=0
        )
        
        workflow.add_node(node)
    
    # 添加边
    workflow.add_edge(WorkflowEdge(
        edge_id="edge_A_B",
        from_node_id="node_A",
        to_node_id="node_B"
    ))
    workflow.add_edge(WorkflowEdge(
        edge_id="edge_B_C",
        from_node_id="node_B",
        to_node_id="node_C"
    ))
    
    return workflow

def test_topological_sort(simple_workflow):
    """测试拓扑排序"""
    order = DependencyResolver.topological_sort(simple_workflow)
    assert order == ["node_A", "node_B", "node_C"]

def test_cycle_detection(simple_workflow):
    """测试循环检测"""
    # 添加循环边
    simple_workflow.add_edge(WorkflowEdge(
        edge_id="edge_C_A",
        from_node_id="node_C",
        to_node_id="node_A"
    ))
    
    with pytest.raises(CycleDetectedError):
        DependencyResolver.topological_sort(simple_workflow)

def test_downstream_nodes(simple_workflow):
    """测试下游节点查询"""
    downstream = DependencyResolver.get_downstream_nodes(simple_workflow, "node_A")
    assert downstream == {"node_B", "node_C"}

@pytest.mark.asyncio
async def test_workflow_execution(simple_workflow):
    """测试工作流执行"""
    # ... 完整的异步测试
    pass
```

---

## 五、迁移计划（从 ResponseCoordinator）

### 5.1 渐进式迁移

**阶段 1：共存** (Week 1-2)
```python
# ResponseCoordinator 继续处理 Agent 轮次
agents = coordinator.select_agents(available_agents)
for agent in agents:
    response = await executor.call_agent(agent)
    coordinator.record_call(agent.agent_id)

# 新的 Task/DAG 仅用于显式工作流
if user_provides_workflow:
    workflow = parse_workflow_definition(user_input)
    results = await workflow_executor.execute_workflow(workflow)
```

**阶段 2：选择性迁移** (Week 3-4)
```python
# 自动创建工作流（基于 Agent 协调结果）
selected_agents = coordinator.select_agents(available_agents)
workflow = coordinator.create_workflow_from_selection(selected_agents, user_prompt)
results = await workflow_executor.execute_workflow(workflow)
```

**阶段 3：深度整合** (Week 5-6)
```python
# ResponseCoordinator 变为 WorkflowOrchestrator 的前端
class WorkflowOrchestrator(ResponseCoordinator):
    async def select_and_execute(self, available_agents, user_prompt):
        """整合选择和执行"""
        selected = self.select_agents(available_agents)
        workflow = self.create_workflow_from_selection(selected, user_prompt)
        return await self.execute_workflow(workflow)
```

### 5.2 数据库迁移（如需持久化）

```python
# 新增 SQLite 表
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    workflow_id TEXT,
    name TEXT,
    agent_id TEXT,
    status TEXT,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);

CREATE TABLE workflows (
    workflow_id TEXT PRIMARY KEY,
    name TEXT,
    crew_id TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    definition JSON
);

CREATE TABLE task_results (
    result_id TEXT PRIMARY KEY,
    task_id TEXT,
    status TEXT,
    output JSON,
    error TEXT,
    execution_time_seconds REAL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);
```

---

## 六、性能预期

### 6.1 基准测试方向

```python
# benchmarks/benchmark_phase4.py

async def benchmark_workflow_execution():
    """工作流执行性能基准"""
    
    # 测试场景 1：线性工作流 (A -> B -> C)
    linear_wf = create_linear_workflow(depth=10)
    
    # 测试场景 2：树形工作流
    tree_wf = create_tree_workflow(depth=3, width=3)
    
    # 测试场景 3：DAG 工作流
    dag_wf = create_dag_workflow(nodes=20, edges=30)
    
    # 基准指标
    # - 拓扑排序时间
    # - 首个任务到执行时间 (TTFB)
    # - 并发执行效率
    # - 资源利用率
```

### 6.2 性能目标

| 指标 | 目标 | 备注 |
|------|------|------|
| 拓扑排序 | <10ms (100 nodes) | Kahn 算法线性复杂度 |
| 并发启动 | <50ms | 创建任务和调度 |
| 任务切换开销 | <5ms | asyncio 开销 |
| 状态更新 | <1ms | 内存操作 |

---

## 七、检查清单

- [ ] Task 数据模型实现
- [ ] Workflow 数据模型实现
- [ ] DependencyResolver 实现 (含单元测试)
- [ ] TaskExecutor 实现 (含重试和超时)
- [ ] WorkflowExecutor 基础版实现
- [ ] 集成测试 (execute_workflow 端到端)
- [ ] 与 ResponseCoordinator 兼容性测试
- [ ] 性能基准测试
- [ ] 文档更新
- [ ] 用户示例

---

**下一步**: 选择 Phase 4a 开始实现，从 Task 模型开始
