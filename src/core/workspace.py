"""
工作空间管理 - 扩展会话概念，支持文件/任务/artifacts管理

提供完整的工作空间功能：
- 文件引用和追踪
- 任务管理和追踪
- Artifacts（生成物）管理
"""

from __future__ import annotations

import time
import uuid
import hashlib
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import structlog

from src.core.database import Database

logger = structlog.get_logger()


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"      # 待处理
    RUNNING = "running"      # 进行中
    DONE = "done"           # 完成
    FAILED = "failed"       # 失败
    CANCELED = "canceled"   # 取消


class ArtifactType(str, Enum):
    """生成物类型"""
    CODE = "code"                # 代码文件
    DOCUMENT = "document"        # 文档
    IMAGE = "image"              # 图片
    DIAGRAM = "diagram"          # 图表
    DATA = "data"                # 数据文件
    OTHER = "other"              # 其他


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


@dataclass
class Workspace:
    """工作空间"""

    workspace_id: str
    session_id: str
    title: str
    description: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkspaceManager:
    """工作空间管理器

    提供工作空间、文件、任务、生成物的完整管理功能。
    """

    def __init__(self, db: Database):
        """初始化工作空间管理器

        Args:
            db: 数据库实例
        """
        self.db = db
        self._init_workspace_schema()
        logger.info("workspace_manager_initialized")

    def _init_workspace_schema(self) -> None:
        """初始化工作空间相关的数据库schema"""

        # 创建 workspaces 表
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                workspace_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                metadata TEXT
            )
        """)

        # 创建 file_references 表
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS file_references (
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
                related_tasks TEXT,
                related_messages TEXT,
                is_uploaded INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id)
            )
        """)

        # 创建索引
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspace_files
            ON file_references(workspace_id)
        """)

        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path
            ON file_references(file_path)
        """)

        # 创建 tasks 表
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_to TEXT,
                created_by TEXT NOT NULL,
                parent_task_id TEXT,
                subtasks TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                started_at REAL,
                completed_at REAL,
                related_files TEXT,
                related_messages TEXT,
                result TEXT,
                error TEXT,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
                FOREIGN KEY (parent_task_id) REFERENCES tasks(task_id)
            )
        """)

        # 创建索引
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspace_tasks
            ON tasks(workspace_id)
        """)

        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_status
            ON tasks(workspace_id, status)
        """)

        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_assigned
            ON tasks(assigned_to)
        """)

        # 创建 artifacts 表
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at REAL NOT NULL,
                metadata TEXT,
                source_task_id TEXT,
                source_message_id TEXT,
                version INTEGER DEFAULT 1,
                previous_version TEXT,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
                FOREIGN KEY (source_task_id) REFERENCES tasks(task_id),
                FOREIGN KEY (previous_version) REFERENCES artifacts(artifact_id)
            )
        """)

        # 创建索引
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_workspace_artifacts
            ON artifacts(workspace_id)
        """)

        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_artifact_type
            ON artifacts(workspace_id, artifact_type)
        """)

        logger.info("workspace_schema_initialized")

    # === 工作空间管理 ===

    def create_workspace(
        self,
        session_id: str,
        title: str = "新工作空间",
        description: Optional[str] = None
    ) -> Workspace:
        """创建工作空间

        Args:
            session_id: 会话ID
            title: 工作空间标题
            description: 工作空间描述

        Returns:
            创建的工作空间
        """
        workspace_id = str(uuid.uuid4())
        now = time.time()

        workspace = Workspace(
            workspace_id=workspace_id,
            session_id=session_id,
            title=title,
            description=description,
            created_at=now,
            updated_at=now
        )

        self.db.execute(
            """
            INSERT INTO workspaces
            (workspace_id, session_id, title, description, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workspace_id,
                session_id,
                title,
                description,
                now,
                now,
                json.dumps(workspace.metadata)
            )
        )

        logger.info("workspace_created", workspace_id=workspace_id, session_id=session_id)
        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """获取工作空间

        Args:
            workspace_id: 工作空间ID

        Returns:
            工作空间对象，如果不存在则返回None
        """
        row = self.db.fetchone(
            "SELECT * FROM workspaces WHERE workspace_id = ?",
            (workspace_id,)
        )

        if not row:
            return None

        return Workspace(
            workspace_id=row['workspace_id'],
            session_id=row['session_id'],
            title=row['title'],
            description=row['description'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )

    def list_workspaces(self, limit: int = 100) -> List[Workspace]:
        """列出工作空间

        Args:
            limit: 最大返回数量

        Returns:
            工作空间列表
        """
        rows = self.db.fetchall(
            "SELECT * FROM workspaces ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )

        return [
            Workspace(
                workspace_id=row['workspace_id'],
                session_id=row['session_id'],
                title=row['title'],
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {}
            )
            for row in rows
        ]

    # === 文件管理 ===

    def add_file_reference(
        self,
        workspace_id: str,
        file_path: str,
        created_by: str = "user"
    ) -> FileReference:
        """添加文件引用

        Args:
            workspace_id: 工作空间ID
            file_path: 文件路径
            created_by: 创建者

        Returns:
            文件引用对象
        """
        path = Path(file_path)

        # 计算文件哈希
        file_hash = self._calculate_file_hash(path)

        file_id = str(uuid.uuid4())
        now = time.time()

        file_ref = FileReference(
            file_id=file_id,
            workspace_id=workspace_id,
            file_path=str(path.absolute()),
            file_name=path.name,
            file_type=path.suffix[1:] if path.suffix else "",
            file_size=path.stat().st_size if path.exists() else 0,
            file_hash=file_hash,
            created_by=created_by,
            created_at=now,
            last_accessed=now
        )

        self.db.execute(
            """
            INSERT INTO file_references
            (file_id, workspace_id, file_path, file_name, file_type, file_size,
             file_hash, created_by, created_at, last_accessed, access_count,
             related_tasks, related_messages, is_uploaded, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_id, workspace_id, file_ref.file_path, file_ref.file_name,
                file_ref.file_type, file_ref.file_size, file_ref.file_hash,
                created_by, now, now, 0,
                json.dumps(file_ref.related_tasks),
                json.dumps(file_ref.related_messages),
                1, 0
            )
        )

        logger.info("file_reference_added", file_id=file_id, file_name=path.name)
        return file_ref

    def get_file_reference(self, file_id: str) -> Optional[FileReference]:
        """获取文件引用

        Args:
            file_id: 文件ID

        Returns:
            文件引用对象，如果不存在则返回None
        """
        row = self.db.fetchone(
            "SELECT * FROM file_references WHERE file_id = ?",
            (file_id,)
        )

        if not row:
            return None

        return self._row_to_file_reference(row)

    def list_files(
        self,
        workspace_id: str,
        file_type: Optional[str] = None
    ) -> List[FileReference]:
        """列出工作空间文件

        Args:
            workspace_id: 工作空间ID
            file_type: 文件类型过滤（可选）

        Returns:
            文件引用列表
        """
        if file_type:
            rows = self.db.fetchall(
                """
                SELECT * FROM file_references
                WHERE workspace_id = ? AND file_type = ? AND is_deleted = 0
                ORDER BY created_at DESC
                """,
                (workspace_id, file_type)
            )
        else:
            rows = self.db.fetchall(
                """
                SELECT * FROM file_references
                WHERE workspace_id = ? AND is_deleted = 0
                ORDER BY created_at DESC
                """,
                (workspace_id,)
            )

        return [self._row_to_file_reference(row) for row in rows]

    def update_file_access(self, file_id: str) -> None:
        """更新文件访问统计

        Args:
            file_id: 文件ID
        """
        now = time.time()
        self.db.execute(
            """
            UPDATE file_references
            SET last_accessed = ?, access_count = access_count + 1
            WHERE file_id = ?
            """,
            (now, file_id)
        )

    def delete_file_reference(self, file_id: str) -> None:
        """删除文件引用（软删除）

        Args:
            file_id: 文件ID
        """
        self.db.execute(
            "UPDATE file_references SET is_deleted = 1 WHERE file_id = ?",
            (file_id,)
        )
        logger.info("file_reference_deleted", file_id=file_id)

    # === 任务管理 ===

    def create_task(
        self,
        workspace_id: str,
        title: str,
        description: str,
        assigned_to: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        created_by: str = "user"
    ) -> Task:
        """创建任务

        Args:
            workspace_id: 工作空间ID
            title: 任务标题
            description: 任务描述
            assigned_to: 分配给（agent_id）
            parent_task_id: 父任务ID
            created_by: 创建者

        Returns:
            创建的任务
        """
        task_id = str(uuid.uuid4())
        now = time.time()

        task = Task(
            task_id=task_id,
            workspace_id=workspace_id,
            title=title,
            description=description,
            status=TaskStatus.PENDING,
            assigned_to=assigned_to,
            created_by=created_by,
            parent_task_id=parent_task_id,
            created_at=now,
            updated_at=now
        )

        self.db.execute(
            """
            INSERT INTO tasks
            (task_id, workspace_id, title, description, status, assigned_to,
             created_by, parent_task_id, subtasks, created_at, updated_at,
             started_at, completed_at, related_files, related_messages, result, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id, workspace_id, title, description, TaskStatus.PENDING.value,
                assigned_to, created_by, parent_task_id, json.dumps(task.subtasks),
                now, now, None, None,
                json.dumps(task.related_files), json.dumps(task.related_messages),
                None, None
            )
        )

        # 如果有父任务，更新父任务的subtasks列表
        if parent_task_id:
            self.add_subtask(parent_task_id, task_id)

        logger.info("task_created", task_id=task_id, title=title)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象，如果不存在则返回None
        """
        row = self.db.fetchone(
            "SELECT * FROM tasks WHERE task_id = ?",
            (task_id,)
        )

        if not row:
            return None

        return self._row_to_task(row)

    def list_tasks(
        self,
        workspace_id: str,
        status: Optional[TaskStatus] = None,
        assigned_to: Optional[str] = None
    ) -> List[Task]:
        """列出任务

        Args:
            workspace_id: 工作空间ID
            status: 状态过滤（可选）
            assigned_to: 分配者过滤（可选）

        Returns:
            任务列表
        """
        query = "SELECT * FROM tasks WHERE workspace_id = ?"
        params = [workspace_id]

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)

        query += " ORDER BY created_at DESC"

        rows = self.db.fetchall(query, tuple(params))
        return [self._row_to_task(row) for row in rows]

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[str] = None,
        error: Optional[str] = None
    ) -> Task:
        """更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            result: 任务结果（可选）
            error: 错误信息（可选）

        Returns:
            更新后的任务
        """
        now = time.time()

        # 根据状态设置时间字段
        started_at = None
        completed_at = None

        if status == TaskStatus.RUNNING:
            # 获取当前任务，检查是否已经设置started_at
            task = self.get_task(task_id)
            if task and not task.started_at:
                started_at = now

        if status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELED):
            completed_at = now

        # 构建更新语句
        update_fields = ["status = ?", "updated_at = ?"]
        params = [status.value, now]

        if started_at:
            update_fields.append("started_at = ?")
            params.append(started_at)

        if completed_at:
            update_fields.append("completed_at = ?")
            params.append(completed_at)

        if result is not None:
            update_fields.append("result = ?")
            params.append(result)

        if error is not None:
            update_fields.append("error = ?")
            params.append(error)

        params.append(task_id)

        query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE task_id = ?"
        self.db.execute(query, tuple(params))

        logger.info("task_status_updated", task_id=task_id, status=status.value)

        # 返回更新后的任务
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        return task

    def assign_task(self, task_id: str, agent_id: str) -> Task:
        """分配任务

        Args:
            task_id: 任务ID
            agent_id: Agent ID

        Returns:
            更新后的任务
        """
        now = time.time()
        self.db.execute(
            "UPDATE tasks SET assigned_to = ?, updated_at = ? WHERE task_id = ?",
            (agent_id, now, task_id)
        )

        logger.info("task_assigned", task_id=task_id, agent_id=agent_id)

        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        return task

    def add_subtask(self, parent_task_id: str, subtask_id: str) -> None:
        """添加子任务

        Args:
            parent_task_id: 父任务ID
            subtask_id: 子任务ID
        """
        parent = self.get_task(parent_task_id)
        if not parent:
            raise ValueError(f"Parent task not found: {parent_task_id}")

        if subtask_id not in parent.subtasks:
            parent.subtasks.append(subtask_id)
            now = time.time()
            self.db.execute(
                "UPDATE tasks SET subtasks = ?, updated_at = ? WHERE task_id = ?",
                (json.dumps(parent.subtasks), now, parent_task_id)
            )
            logger.info("subtask_added", parent_task_id=parent_task_id, subtask_id=subtask_id)

    # === 生成物管理 ===

    def create_artifact(
        self,
        workspace_id: str,
        artifact_type: ArtifactType,
        file_path: str,
        created_by: str,
        source_task_id: Optional[str] = None,
        source_message_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Artifact:
        """创建生成物

        Args:
            workspace_id: 工作空间ID
            artifact_type: 生成物类型
            file_path: 文件路径
            created_by: 创建者（agent_id）
            source_task_id: 来源任务ID
            source_message_id: 来源消息ID
            metadata: 元数据

        Returns:
            创建的生成物
        """
        artifact_id = str(uuid.uuid4())
        now = time.time()
        path = Path(file_path)

        artifact = Artifact(
            artifact_id=artifact_id,
            workspace_id=workspace_id,
            artifact_type=artifact_type,
            file_path=str(path.absolute()),
            file_name=path.name,
            created_by=created_by,
            created_at=now,
            metadata=metadata or {},
            source_task_id=source_task_id,
            source_message_id=source_message_id
        )

        self.db.execute(
            """
            INSERT INTO artifacts
            (artifact_id, workspace_id, artifact_type, file_path, file_name,
             created_by, created_at, metadata, source_task_id, source_message_id,
             version, previous_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id, workspace_id, artifact_type.value, artifact.file_path,
                artifact.file_name, created_by, now, json.dumps(artifact.metadata),
                source_task_id, source_message_id, 1, None
            )
        )

        logger.info("artifact_created", artifact_id=artifact_id, artifact_type=artifact_type.value)
        return artifact

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """获取生成物

        Args:
            artifact_id: 生成物ID

        Returns:
            生成物对象，如果不存在则返回None
        """
        row = self.db.fetchone(
            "SELECT * FROM artifacts WHERE artifact_id = ?",
            (artifact_id,)
        )

        if not row:
            return None

        return self._row_to_artifact(row)

    def list_artifacts(
        self,
        workspace_id: str,
        artifact_type: Optional[ArtifactType] = None
    ) -> List[Artifact]:
        """列出生成物

        Args:
            workspace_id: 工作空间ID
            artifact_type: 生成物类型过滤（可选）

        Returns:
            生成物列表
        """
        if artifact_type:
            rows = self.db.fetchall(
                """
                SELECT * FROM artifacts
                WHERE workspace_id = ? AND artifact_type = ?
                ORDER BY created_at DESC
                """,
                (workspace_id, artifact_type.value)
            )
        else:
            rows = self.db.fetchall(
                """
                SELECT * FROM artifacts
                WHERE workspace_id = ?
                ORDER BY created_at DESC
                """,
                (workspace_id,)
            )

        return [self._row_to_artifact(row) for row in rows]

    def create_artifact_version(
        self,
        previous_artifact_id: str,
        file_path: str
    ) -> Artifact:
        """创建生成物新版本

        Args:
            previous_artifact_id: 上一版本生成物ID
            file_path: 新文件路径

        Returns:
            新版本生成物
        """
        previous = self.get_artifact(previous_artifact_id)
        if not previous:
            raise ValueError(f"Previous artifact not found: {previous_artifact_id}")

        artifact_id = str(uuid.uuid4())
        now = time.time()
        path = Path(file_path)

        artifact = Artifact(
            artifact_id=artifact_id,
            workspace_id=previous.workspace_id,
            artifact_type=previous.artifact_type,
            file_path=str(path.absolute()),
            file_name=path.name,
            created_by=previous.created_by,
            created_at=now,
            metadata=previous.metadata.copy(),
            source_task_id=previous.source_task_id,
            source_message_id=previous.source_message_id,
            version=previous.version + 1,
            previous_version=previous_artifact_id
        )

        self.db.execute(
            """
            INSERT INTO artifacts
            (artifact_id, workspace_id, artifact_type, file_path, file_name,
             created_by, created_at, metadata, source_task_id, source_message_id,
             version, previous_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id, artifact.workspace_id, artifact.artifact_type.value,
                artifact.file_path, artifact.file_name, artifact.created_by,
                now, json.dumps(artifact.metadata), artifact.source_task_id,
                artifact.source_message_id, artifact.version, previous_artifact_id
            )
        )

        logger.info("artifact_version_created", artifact_id=artifact_id, version=artifact.version)
        return artifact

    # === 辅助方法 ===

    def _calculate_file_hash(self, path: Path) -> str:
        """计算文件SHA256哈希

        Args:
            path: 文件路径

        Returns:
            SHA256哈希值
        """
        if not path.exists():
            return ""

        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _row_to_file_reference(self, row: Dict[str, Any]) -> FileReference:
        """数据库行转FileReference对象"""
        return FileReference(
            file_id=row['file_id'],
            workspace_id=row['workspace_id'],
            file_path=row['file_path'],
            file_name=row['file_name'],
            file_type=row['file_type'],
            file_size=row['file_size'],
            file_hash=row['file_hash'],
            created_by=row['created_by'],
            created_at=row['created_at'],
            last_accessed=row['last_accessed'],
            access_count=row['access_count'],
            related_tasks=json.loads(row['related_tasks']) if row['related_tasks'] else [],
            related_messages=json.loads(row['related_messages']) if row['related_messages'] else [],
            is_uploaded=bool(row['is_uploaded']),
            is_deleted=bool(row['is_deleted'])
        )

    def _row_to_task(self, row: Dict[str, Any]) -> Task:
        """数据库行转Task对象"""
        return Task(
            task_id=row['task_id'],
            workspace_id=row['workspace_id'],
            title=row['title'],
            description=row['description'],
            status=TaskStatus(row['status']),
            assigned_to=row['assigned_to'],
            created_by=row['created_by'],
            parent_task_id=row['parent_task_id'],
            subtasks=json.loads(row['subtasks']) if row['subtasks'] else [],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at'],
            related_files=json.loads(row['related_files']) if row['related_files'] else [],
            related_messages=json.loads(row['related_messages']) if row['related_messages'] else [],
            result=row['result'],
            error=row['error']
        )

    def _row_to_artifact(self, row: Dict[str, Any]) -> Artifact:
        """数据库行转Artifact对象"""
        return Artifact(
            artifact_id=row['artifact_id'],
            workspace_id=row['workspace_id'],
            artifact_type=ArtifactType(row['artifact_type']),
            file_path=row['file_path'],
            file_name=row['file_name'],
            created_by=row['created_by'],
            created_at=row['created_at'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            source_task_id=row['source_task_id'],
            source_message_id=row['source_message_id'],
            version=row['version'],
            previous_version=row['previous_version']
        )
