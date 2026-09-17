# 工作空间增强设计文档

**创建日期**: 2026-09-17  
**版本**: v1.0  
**状态**: 设计阶段

---

## 1. 概述

### 1.1 目标

将 Agent Chat Hub 从单纯的对话系统扩展为完整的工作空间，支持：
- 文件引用和追踪
- 任务管理和追踪
- Artifacts（生成物）管理
- Agent-to-Agent 自动委托

### 1.2 灵感来源

参考 Tutti 的工作空间概念，但简化为单用户场景。

---

## 2. 核心概念

### 2.1 从 Session 到 Workspace

**当前架构**:
```python
class SessionConfig:
    session_id: str
    messages: List[Message]  # 只有对话
```

**新架构**:
```python
class Workspace:
    workspace_id: str
    session_id: str              # 关联的会话
    messages: List[Message]      # 对话历史
    files: List[FileReference]   # 文件引用
    tasks: List[Task]            # 任务列表
    artifacts: List[Artifact]    # 生成物
    checkpoints: List[Checkpoint] # 检查点
    metadata: Dict[str, Any]     # 元数据
```

---

## 3. 数据模型

### 3.1 FileReference（文件引用）

```python
@dataclass
class FileReference:
    """文件引用"""
    
    # 标识
    file_id: str                    # UUID
    workspace_id: str               # 所属工作空间
    
    # 文件信息
    file_path: str                  # 文件路径（绝对路径）
    file_name: str                  # 文件名
    file_type: str                  # 文件类型（扩展名）
    file_size: int                  # 文件大小（字节）
    file_hash: str                  # 文件哈希（SHA256）
    
    # 元数据
    created_by: str                 # 创建者（user 或 agent_id）
    created_at: float               # 创建时间
    last_accessed: float            # 最后访问时间
    access_count: int = 0           # 访问次数
    
    # 关联
    related_tasks: List[str] = field(default_factory=list)  # 关联任务 IDs
    related_messages: List[str] = field(default_factory=list)  # 关联消息 IDs
    
    # 状态
    is_uploaded: bool = True        # 是否已上传
    is_deleted: bool = False        # 是否已删除
```

### 3.2 Task（任务）

```python
class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"      # 待处理
    RUNNING = "running"      # 进行中
    DONE = "done"           # 完成
    FAILED = "failed"       # 失败
    CANCELED = "canceled"   # 取消

@dataclass
class Task:
    """任务"""
    
    # 标识
    task_id: str                    # UUID
    workspace_id: str               # 所属工作空间
    
    # 任务信息
    title: str                      # 任务标题
    description: str                # 任务描述
    status: TaskStatus              # 任务状态
    
    # 分配
    assigned_to: Optional[str] = None   # 分配给谁（agent_id）
    created_by: str = "user"            # 创建者
    
    # 层次结构
    parent_task_id: Optional[str] = None  # 父任务 ID
    subtasks: List[str] = field(default_factory=list)  # 子任务 IDs
    
    # 时间
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # 关联
    related_files: List[str] = field(default_factory=list)  # 关联文件 IDs
    related_messages: List[str] = field(default_factory=list)  # 关联消息 IDs
    
    # 结果
    result: Optional[str] = None    # 任务结果
    error: Optional[str] = None     # 错误信息
```

### 3.3 Artifact（生成物）

```python
class ArtifactType(str, Enum):
    """生成物类型"""
    CODE = "code"                # 代码文件
    DOCUMENT = "document"        # 文档
    IMAGE = "image"              # 图片
    DIAGRAM = "diagram"          # 图表
    DATA = "data"                # 数据文件
    OTHER = "other"              # 其他

@dataclass
class Artifact:
    """生成物"""
    
    # 标识
    artifact_id: str                # UUID
    workspace_id: str               # 所属工作空间
    
    # 类型和路径
    artifact_type: ArtifactType     # 生成物类型
    file_path: str                  # 文件路径
    file_name: str                  # 文件名
    
    # 创建者
    created_by: str                 # 创建者（agent_id）
    created_at: float = field(default_factory=time.time)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    # 关联
    source_task_id: Optional[str] = None     # 来源任务
    source_message_id: Optional[str] = None  # 来源消息
    
    # 版本
    version: int = 1                # 版本号
    previous_version: Optional[str] = None  # 上一版本 artifact_id
```

---

## 4. 数据库 Schema

### 4.1 workspaces 表

```sql
CREATE TABLE workspaces (
    workspace_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    metadata TEXT,  -- JSON
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

### 4.2 file_references 表

```sql
CREATE TABLE file_references (
    file_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at REAL NOT NULL,
    last_accessed REAL NOT NULL,
    access_count INTEGER DEFAULT 0,
    related_tasks TEXT,      -- JSON array
    related_messages TEXT,   -- JSON array
    is_uploaded BOOLEAN DEFAULT 1,
    is_deleted BOOLEAN DEFAULT 0,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    INDEX idx_workspace_files (workspace_id),
    INDEX idx_file_path (file_path)
);
```

### 4.3 tasks 表

```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_to TEXT,
    created_by TEXT NOT NULL,
    parent_task_id TEXT,
    subtasks TEXT,           -- JSON array
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    started_at REAL,
    completed_at REAL,
    related_files TEXT,      -- JSON array
    related_messages TEXT,   -- JSON array
    result TEXT,
    error TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    FOREIGN KEY (parent_task_id) REFERENCES tasks(task_id),
    INDEX idx_workspace_tasks (workspace_id),
    INDEX idx_task_status (workspace_id, status),
    INDEX idx_task_assigned (assigned_to)
);
```

### 4.4 artifacts 表

```sql
CREATE TABLE artifacts (
    artifact_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at REAL NOT NULL,
    metadata TEXT,           -- JSON
    source_task_id TEXT,
    source_message_id TEXT,
    version INTEGER DEFAULT 1,
    previous_version TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    FOREIGN KEY (source_task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (previous_version) REFERENCES artifacts(artifact_id),
    INDEX idx_workspace_artifacts (workspace_id),
    INDEX idx_artifact_type (workspace_id, artifact_type)
);
```

---

## 5. WorkspaceManager API

### 5.1 核心方法

```python
class WorkspaceManager:
    """工作空间管理器"""
    
    def __init__(self, db_path: str):
        """初始化"""
        
    # === 工作空间管理 ===
    
    def create_workspace(
        self,
        session_id: str,
        title: str = "新工作空间"
    ) -> Workspace:
        """创建工作空间"""
        
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """获取工作空间"""
        
    def list_workspaces(self, limit: int = 100) -> List[Workspace]:
        """列出工作空间"""
        
    # === 文件管理 ===
    
    def add_file_reference(
        self,
        workspace_id: str,
        file_path: str,
        created_by: str = "user"
    ) -> FileReference:
        """添加文件引用"""
        
    def get_file_reference(self, file_id: str) -> Optional[FileReference]:
        """获取文件引用"""
        
    def list_files(
        self,
        workspace_id: str,
        file_type: Optional[str] = None
    ) -> List[FileReference]:
        """列出工作空间文件"""
        
    def update_file_access(self, file_id: str) -> None:
        """更新文件访问统计"""
        
    def delete_file_reference(self, file_id: str) -> None:
        """删除文件引用（软删除）"""
        
    # === 任务管理 ===
    
    def create_task(
        self,
        workspace_id: str,
        title: str,
        description: str,
        assigned_to: Optional[str] = None,
        parent_task_id: Optional[str] = None
    ) -> Task:
        """创建任务"""
        
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        
    def list_tasks(
        self,
        workspace_id: str,
        status: Optional[TaskStatus] = None,
        assigned_to: Optional[str] = None
    ) -> List[Task]:
        """列出任务"""
        
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> Task:
        """更新任务状态"""
        
    def assign_task(self, task_id: str, agent_id: str) -> Task:
        """分配任务"""
        
    def add_subtask(self, parent_task_id: str, subtask_id: str) -> None:
        """添加子任务"""
        
    # === 生成物管理 ===
    
    def create_artifact(
        self,
        workspace_id: str,
        artifact_type: ArtifactType,
        file_path: str,
        created_by: str,
        source_task_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Artifact:
        """创建生成物"""
        
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """获取生成物"""
        
    def list_artifacts(
        self,
        workspace_id: str,
        artifact_type: Optional[ArtifactType] = None
    ) -> List[Artifact]:
        """列出生成物"""
        
    def create_artifact_version(
        self,
        previous_artifact_id: str,
        file_path: str
    ) -> Artifact:
        """创建生成物新版本"""
```

---

## 6. Agent-to-Agent 自动委托

### 6.1 委托模型

```python
@dataclass
class DelegationRequest:
    """委托请求"""
    
    # 标识
    delegation_id: str              # UUID
    workspace_id: str               # 所属工作空间
    
    # 委托方
    from_agent_id: str              # 委托方 Agent
    from_message_id: str            # 来源消息 ID
    
    # 接收方
    to_agent_id: str                # 接收方 Agent
    
    # 任务
    task_id: str                    # 关联任务 ID
    task_description: str           # 任务描述
    
    # 上下文
    context: Dict[str, Any]         # 委托上下文
    
    # 状态
    status: str                     # PENDING, ACCEPTED, COMPLETED, REJECTED
    
    # 时间
    created_at: float = field(default_factory=time.time)
    accepted_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # 结果
    result_message_id: Optional[str] = None
    result: Optional[str] = None
```

### 6.2 委托解析器

```python
class DelegationParser:
    """委托解析器 - 从 Agent 响应中识别委托意图"""
    
    DELEGATION_PATTERNS = [
        r"@(\w+)\s+请(.*)",           # @codex 请优化代码
        r"@(\w+)\s+(.*)",              # @codex 实现 API
        r"委托给?\s*@(\w+)\s+(.*)",    # 委托给 @codex 优化
    ]
    
    def parse(self, content: str) -> Optional[DelegationRequest]:
        """解析委托意图"""
        for pattern in self.DELEGATION_PATTERNS:
            match = re.search(pattern, content)
            if match:
                to_agent = match.group(1)
                task_desc = match.group(2)
                return DelegationRequest(
                    delegation_id=str(uuid.uuid4()),
                    to_agent_id=to_agent,
                    task_description=task_desc,
                    context={}
                )
        return None
```

### 6.3 委托流程

```
1. Agent Claude 响应:
   "我已经分析了代码，发现需要优化算法。@codex 请优化 main.py 中的排序算法。"

2. DelegationParser 解析:
   → 识别到委托意图
   → 目标: codex
   → 任务: "优化 main.py 中的排序算法"

3. DelegationManager 处理:
   → 创建 Task（自动）
   → 分配给 codex
   → 创建 DelegationRequest
   → 触发 codex 执行

4. Codex 执行:
   → 接收任务上下文（包含 Claude 的分析）
   → 执行优化
   → 完成任务
   → 标记 DelegationRequest 为 COMPLETED

5. 通知 Claude:
   → 委托完成通知（可选）
```

### 6.4 防止无限循环

```python
class DelegationManager:
    MAX_DELEGATION_DEPTH = 3  # 最大委托深度
    
    def validate_delegation(
        self,
        from_agent_id: str,
        to_agent_id: str,
        workspace_id: str
    ) -> bool:
        """验证委托是否合法"""
        
        # 1. 检查委托深度
        depth = self._get_delegation_depth(from_agent_id, workspace_id)
        if depth >= self.MAX_DELEGATION_DEPTH:
            raise ValueError(
                f"委托深度超过限制 ({self.MAX_DELEGATION_DEPTH})"
            )
        
        # 2. 检查循环委托
        if self._has_circular_delegation(from_agent_id, to_agent_id, workspace_id):
            raise ValueError(
                f"检测到循环委托: {from_agent_id} -> {to_agent_id}"
            )
        
        return True
    
    def _get_delegation_depth(
        self,
        agent_id: str,
        workspace_id: str
    ) -> int:
        """获取委托深度（当前 agent 在委托链中的深度）"""
        # 递归查找父委托
        
    def _has_circular_delegation(
        self,
        from_agent: str,
        to_agent: str,
        workspace_id: str
    ) -> bool:
        """检查是否存在循环委托"""
        # 检查 to_agent 是否在 from_agent 的祖先链中
```

---

## 7. TUI 集成

### 7.1 工作空间视图

```python
class WorkspaceView(Widget):
    """工作空间视图"""
    
    def compose(self):
        yield Container(
            # 文件树
            Tree("文件", id="file-tree"),
            
            # 任务列表
            DataTable(id="task-table"),
            
            # 生成物列表
            DataTable(id="artifact-table"),
            
            id="workspace-container"
        )
    
    def on_mount(self):
        """挂载时加载数据"""
        self._load_files()
        self._load_tasks()
        self._load_artifacts()
```

### 7.2 任务面板

```python
class TaskPanel(Widget):
    """任务面板"""
    
    def compose(self):
        yield Container(
            # 任务列表
            DataTable(
                id="task-list",
                columns=["ID", "标题", "状态", "分配给", "进度"]
            ),
            
            # 任务详情
            Container(id="task-detail"),
            
            # 操作按钮
            Horizontal(
                Button("创建任务", id="create-task"),
                Button("分配任务", id="assign-task"),
                Button("完成任务", id="complete-task"),
            )
        )
    
    async def on_button_pressed(self, event):
        """按钮点击处理"""
        if event.button.id == "create-task":
            await self.show_create_task_dialog()
        elif event.button.id == "assign-task":
            await self.show_assign_dialog()
        # ...
```

---

## 8. 使用示例

### 8.1 创建工作空间并添加文件

```python
# 创建工作空间
workspace = workspace_manager.create_workspace(
    session_id="sess-123",
    title="Web 应用开发"
)

# 添加文件引用
file_ref = workspace_manager.add_file_reference(
    workspace_id=workspace.workspace_id,
    file_path="/home/user/project/main.py",
    created_by="user"
)

# 引用文件: @file:main.py
```

### 8.2 创建和分配任务

```python
# 用户创建任务
task = workspace_manager.create_task(
    workspace_id=workspace.workspace_id,
    title="优化排序算法",
    description="main.py 中的排序算法性能较差，需要优化"
)

# 用户分配给 Agent
workspace_manager.assign_task(task.task_id, agent_id="codex")

# Agent 开始执行
workspace_manager.update_task_status(
    task.task_id,
    status=TaskStatus.RUNNING
)

# Agent 完成任务
workspace_manager.update_task_status(
    task.task_id,
    status=TaskStatus.DONE,
    result="已将冒泡排序替换为快速排序，性能提升 10x"
)
```

### 8.3 Agent 自动委托

```python
# Claude 响应包含委托
claude_response = """
我已经分析了代码架构，发现以下问题：
1. 数据库查询效率低
2. 缺少缓存机制
3. API 响应时间过长

@codex 请实现 Redis 缓存层来优化 API 性能。
"""

# 系统自动解析委托
delegation = delegation_parser.parse(claude_response)

# 自动创建任务
task = workspace_manager.create_task(
    workspace_id=workspace.workspace_id,
    title="实现 Redis 缓存层",
    description=delegation.task_description,
    assigned_to="codex"
)

# 自动触发 codex 执行
await session_manager.delegate_to_agent("codex", task)
```

---

## 9. 测试策略

### 9.1 单元测试

```python
# tests/test_workspace.py
def test_create_workspace()
def test_add_file_reference()
def test_create_task()
def test_task_lifecycle()
def test_create_artifact()

# tests/test_delegation.py
def test_parse_delegation()
def test_delegation_depth_limit()
def test_circular_delegation_detection()
def test_auto_delegation_flow()
```

### 9.2 集成测试

```python
# tests/integration/test_workspace_integration.py
async def test_complete_workflow()
async def test_auto_delegation_chain()
async def test_task_with_files_and_artifacts()
```

---

## 10. 总结

### 10.1 核心价值

- ✅ 更完整的工作上下文（不只是对话）
- ✅ 任务追踪和管理（清晰的工作流）
- ✅ Agent 自动协作（减少人工干预）
- ✅ 生成物管理（版本化输出）

### 10.2 实施优先级

1. **高优先级**: Workspace 数据模型和 Manager API
2. **高优先级**: 任务管理和状态追踪
3. **中优先级**: Agent-to-Agent 自动委托
4. **中优先级**: TUI 工作空间视图
5. **低优先级**: 生成物版本管理

---

**文档版本**: v1.0  
**下一步**: 实施 WorkspaceManager
