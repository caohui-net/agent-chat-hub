"""
检查点系统 - 细粒度状态快照与恢复

支持Agent响应级别的检查点，用于崩溃恢复和回滚。
"""

import uuid
import time
import json
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
import structlog

from src.core.database import Database

logger = structlog.get_logger()


class CheckpointType(str, Enum):
    """检查点类型"""
    SESSION_START = "session_start"      # 会话开始
    USER_INPUT = "user_input"            # 用户输入
    AGENT_START = "agent_start"          # Agent开始响应
    AGENT_COMPLETE = "agent_complete"    # Agent完成响应
    AGENT_ERROR = "agent_error"          # Agent错误
    TIMEOUT = "timeout"                  # 超时
    USER_COMMAND = "user_command"        # 用户显式命令
    ROUND_COMPLETE = "round_complete"    # 轮次完成


class CheckpointState(str, Enum):
    """检查点状态"""
    PENDING = "pending"      # 待激活
    ACTIVE = "active"        # 当前激活（每个会话只有一个）
    RESOLVED = "resolved"    # 已解决
    FAILED = "failed"        # 失败


@dataclass
class ResponseCheckpoint:
    """响应检查点

    记录系统在特定时刻的完整状态快照。
    """

    # 标识
    checkpoint_id: str                  # UUID
    session_id: str                     # 会话ID
    round_num: int                      # 轮次编号

    # 类型和状态
    checkpoint_type: CheckpointType
    state: CheckpointState

    # Agent信息
    agent_id: Optional[str] = None      # 关联的Agent ID

    # 快照数据
    response_data: Optional[str] = None # Agent响应内容（JSON）
    session_snapshot: Optional[str] = None  # 会话状态快照（JSON）

    # 错误信息
    error: Optional[str] = None

    # 时间戳
    timestamp: float = field(default_factory=time.time)

    # 序列号（单调递增）
    sequence: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "round_num": self.round_num,
            "checkpoint_type": self.checkpoint_type.value,
            "state": self.state.value,
            "agent_id": self.agent_id,
            "response_data": self.response_data,
            "session_snapshot": self.session_snapshot,
            "error": self.error,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponseCheckpoint":
        """从字典创建"""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            session_id=data["session_id"],
            round_num=data["round_num"],
            checkpoint_type=CheckpointType(data["checkpoint_type"]),
            state=CheckpointState(data["state"]),
            agent_id=data.get("agent_id"),
            response_data=data.get("response_data"),
            session_snapshot=data.get("session_snapshot"),
            error=data.get("error"),
            timestamp=data["timestamp"],
            sequence=data["sequence"],
        )


class CheckpointManager:
    """检查点管理器

    职责：
    - 创建和管理检查点
    - 状态转换（PENDING → ACTIVE → RESOLVED/FAILED）
    - 崩溃恢复
    - 回滚功能
    """

    def __init__(self, db_path: str):
        """初始化检查点管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db = Database(db_path)
        logger.info("checkpoint_manager_initialized", db_path=db_path)

    def create_checkpoint(
        self,
        session_id: str,
        round_num: int,
        checkpoint_type: CheckpointType,
        agent_id: Optional[str] = None,
        response_data: Optional[Dict] = None,
        session_snapshot: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> ResponseCheckpoint:
        """创建检查点

        Args:
            session_id: 会话ID
            round_num: 轮次编号
            checkpoint_type: 检查点类型
            agent_id: Agent ID（可选）
            response_data: Agent响应数据（可选）
            session_snapshot: 会话状态快照（可选）
            error: 错误信息（可选）

        Returns:
            创建的检查点对象
        """
        # 生成唯一ID
        checkpoint_id = str(uuid.uuid4())

        # 获取下一个序列号
        sequence = self._get_next_sequence(session_id)

        # 创建检查点对象
        checkpoint = ResponseCheckpoint(
            checkpoint_id=checkpoint_id,
            session_id=session_id,
            round_num=round_num,
            checkpoint_type=checkpoint_type,
            state=CheckpointState.PENDING,
            agent_id=agent_id,
            response_data=json.dumps(response_data) if response_data else None,
            session_snapshot=json.dumps(session_snapshot) if session_snapshot else None,
            error=error,
            timestamp=time.time(),
            sequence=sequence,
        )

        # 保存到数据库
        self._insert_checkpoint(checkpoint)

        logger.info(
            "checkpoint_created",
            checkpoint_id=checkpoint_id,
            session_id=session_id,
            checkpoint_type=checkpoint_type.value,
            sequence=sequence
        )

        return checkpoint

    def activate_checkpoint(self, checkpoint_id: str) -> None:
        """激活检查点

        将指定检查点标记为ACTIVE，同时将当前ACTIVE检查点变为RESOLVED。

        Args:
            checkpoint_id: 检查点ID
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        # 解决当前所有ACTIVE检查点
        active_checkpoints = self.db.fetchall(
            "SELECT checkpoint_id FROM checkpoints WHERE session_id = ? AND state = ?",
            (checkpoint.session_id, CheckpointState.ACTIVE.value)
        )

        for active in active_checkpoints:
            self.db.execute(
                "UPDATE checkpoints SET state = ? WHERE checkpoint_id = ?",
                (CheckpointState.RESOLVED.value, active["checkpoint_id"])
            )

        # 激活新检查点
        self.db.execute(
            "UPDATE checkpoints SET state = ? WHERE checkpoint_id = ?",
            (CheckpointState.ACTIVE.value, checkpoint_id)
        )

        logger.info(
            "checkpoint_activated",
            checkpoint_id=checkpoint_id,
            session_id=checkpoint.session_id,
            resolved_count=len(active_checkpoints)
        )

    def resolve_checkpoint(self, checkpoint_id: str) -> None:
        """解决检查点

        将检查点标记为RESOLVED。

        Args:
            checkpoint_id: 检查点ID
        """
        self.db.execute(
            "UPDATE checkpoints SET state = ? WHERE checkpoint_id = ?",
            (CheckpointState.RESOLVED.value, checkpoint_id)
        )

        logger.info("checkpoint_resolved", checkpoint_id=checkpoint_id)

    def fail_checkpoint(self, checkpoint_id: str, error: str) -> None:
        """标记检查点失败

        Args:
            checkpoint_id: 检查点ID
            error: 错误信息
        """
        self.db.execute(
            "UPDATE checkpoints SET state = ?, error = ? WHERE checkpoint_id = ?",
            (CheckpointState.FAILED.value, error, checkpoint_id)
        )

        logger.error(
            "checkpoint_failed",
            checkpoint_id=checkpoint_id,
            error=error
        )

    def get_checkpoint(self, checkpoint_id: str) -> Optional[ResponseCheckpoint]:
        """获取检查点

        Args:
            checkpoint_id: 检查点ID

        Returns:
            检查点对象，如果不存在则返回None
        """
        row = self.db.fetchone(
            "SELECT * FROM checkpoints WHERE checkpoint_id = ?",
            (checkpoint_id,)
        )

        return ResponseCheckpoint.from_dict(row) if row else None

    def get_active_checkpoint(self, session_id: str) -> Optional[ResponseCheckpoint]:
        """获取当前激活的检查点

        Args:
            session_id: 会话ID

        Returns:
            当前ACTIVE检查点，如果没有则返回None
        """
        row = self.db.fetchone(
            "SELECT * FROM checkpoints WHERE session_id = ? AND state = ? ORDER BY sequence DESC LIMIT 1",
            (session_id, CheckpointState.ACTIVE.value)
        )

        return ResponseCheckpoint.from_dict(row) if row else None

    def list_checkpoints(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ResponseCheckpoint]:
        """列出检查点

        Args:
            session_id: 会话ID
            limit: 返回数量限制

        Returns:
            检查点列表（按序列号倒序）
        """
        rows = self.db.fetchall(
            "SELECT * FROM checkpoints WHERE session_id = ? ORDER BY sequence DESC LIMIT ?",
            (session_id, limit)
        )

        return [ResponseCheckpoint.from_dict(row) for row in rows]

    def restore_from_checkpoint(
        self,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """从检查点恢复会话状态

        Args:
            checkpoint_id: 检查点ID

        Returns:
            会话状态快照（字典）

        Raises:
            ValueError: 检查点不存在或没有快照数据
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        if not checkpoint.session_snapshot:
            raise ValueError(f"Checkpoint {checkpoint_id} has no session snapshot")

        session_state = json.loads(checkpoint.session_snapshot)

        logger.info(
            "checkpoint_restored",
            checkpoint_id=checkpoint_id,
            session_id=checkpoint.session_id,
            round_num=checkpoint.round_num
        )

        return session_state

    def rollback_to_checkpoint(
        self,
        checkpoint_id: str,
        create_new: bool = True
    ) -> ResponseCheckpoint:
        """回滚到检查点

        Args:
            checkpoint_id: 目标检查点ID
            create_new: 是否创建新检查点记录回滚操作

        Returns:
            新创建的检查点（如果create_new=True）
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        session_state = self.restore_from_checkpoint(checkpoint_id)

        # 创建回滚记录检查点
        if create_new:
            rollback_checkpoint = self.create_checkpoint(
                session_id=checkpoint.session_id,
                round_num=checkpoint.round_num,
                checkpoint_type=CheckpointType.USER_COMMAND,
                session_snapshot=session_state,
                response_data={"rollback_to": checkpoint_id}
            )

            logger.info(
                "checkpoint_rollback",
                from_checkpoint=checkpoint_id,
                to_checkpoint=rollback_checkpoint.checkpoint_id
            )

            return rollback_checkpoint

        return checkpoint

    def cleanup_old_checkpoints(
        self,
        session_id: str,
        keep_last_n: int = 100
    ) -> int:
        """清理旧检查点

        保留最近N个检查点，删除更早的。

        Args:
            session_id: 会话ID
            keep_last_n: 保留的检查点数量

        Returns:
            删除的检查点数量
        """
        # 获取需要保留的检查点的最小序列号
        row = self.db.fetchone(
            """
            SELECT sequence FROM checkpoints
            WHERE session_id = ?
            ORDER BY sequence DESC
            LIMIT 1 OFFSET ?
            """,
            (session_id, keep_last_n - 1)
        )

        if not row:
            # 检查点总数不足keep_last_n，无需清理
            return 0

        min_sequence = row["sequence"]

        # 删除旧检查点
        cursor = self.db.execute(
            "DELETE FROM checkpoints WHERE session_id = ? AND sequence < ?",
            (session_id, min_sequence)
        )

        deleted_count = cursor.rowcount

        logger.info(
            "checkpoints_cleaned",
            session_id=session_id,
            deleted_count=deleted_count,
            kept=keep_last_n
        )

        return deleted_count

    def find_active_checkpoints(self) -> List[ResponseCheckpoint]:
        """查找所有ACTIVE检查点

        用于启动时检测异常终止的会话。

        Returns:
            ACTIVE检查点列表
        """
        rows = self.db.fetchall(
            "SELECT * FROM checkpoints WHERE state = ? ORDER BY timestamp DESC",
            (CheckpointState.ACTIVE.value,)
        )

        return [ResponseCheckpoint.from_dict(row) for row in rows]

    def get_last_resolved_checkpoint(
        self,
        session_id: str
    ) -> Optional[ResponseCheckpoint]:
        """获取上一个RESOLVED检查点

        用于崩溃恢复时找到最后的成功状态。

        Args:
            session_id: 会话ID

        Returns:
            最后一个RESOLVED检查点，如果没有则返回None
        """
        row = self.db.fetchone(
            """
            SELECT * FROM checkpoints
            WHERE session_id = ? AND state = ?
            ORDER BY sequence DESC
            LIMIT 1
            """,
            (session_id, CheckpointState.RESOLVED.value)
        )

        return ResponseCheckpoint.from_dict(row) if row else None

    def _get_next_sequence(self, session_id: str) -> int:
        """获取下一个序列号

        Args:
            session_id: 会话ID

        Returns:
            下一个序列号
        """
        row = self.db.fetchone(
            "SELECT MAX(sequence) as max_seq FROM checkpoints WHERE session_id = ?",
            (session_id,)
        )

        max_seq = row["max_seq"] if row and row["max_seq"] is not None else -1
        return max_seq + 1

    def _insert_checkpoint(self, checkpoint: ResponseCheckpoint) -> None:
        """插入检查点到数据库

        Args:
            checkpoint: 检查点对象
        """
        self.db.execute(
            """
            INSERT INTO checkpoints (
                checkpoint_id, session_id, round_num, checkpoint_type, state,
                agent_id, response_data, session_snapshot, error, timestamp, sequence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                checkpoint.checkpoint_id,
                checkpoint.session_id,
                checkpoint.round_num,
                checkpoint.checkpoint_type.value,
                checkpoint.state.value,
                checkpoint.agent_id,
                checkpoint.response_data,
                checkpoint.session_snapshot,
                checkpoint.error,
                checkpoint.timestamp,
                checkpoint.sequence,
            )
        )
