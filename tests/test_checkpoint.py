"""
检查点系统单元测试
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.core.checkpoint import (
    CheckpointManager,
    CheckpointType,
    CheckpointState,
    ResponseCheckpoint
)


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_checkpoints.db"
        yield str(db_path)


@pytest.fixture
def checkpoint_manager(temp_db):
    """创建检查点管理器实例"""
    return CheckpointManager(temp_db)


def test_create_checkpoint(checkpoint_manager):
    """测试创建检查点"""
    checkpoint = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT,
        session_snapshot={"messages": [], "round_num": 1}
    )

    assert checkpoint.checkpoint_id is not None
    assert checkpoint.session_id == "session_1"
    assert checkpoint.round_num == 1
    assert checkpoint.checkpoint_type == CheckpointType.USER_INPUT
    assert checkpoint.state == CheckpointState.PENDING
    assert checkpoint.sequence == 0
    assert checkpoint.session_snapshot is not None

    # 验证数据库持久化
    retrieved = checkpoint_manager.get_checkpoint(checkpoint.checkpoint_id)
    assert retrieved is not None
    assert retrieved.checkpoint_id == checkpoint.checkpoint_id
    assert retrieved.session_id == checkpoint.session_id


def test_activate_checkpoint(checkpoint_manager):
    """测试激活检查点（自动解决上一个ACTIVE）"""
    # 创建第一个检查点并激活
    checkpoint1 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT
    )
    checkpoint_manager.activate_checkpoint(checkpoint1.checkpoint_id)

    # 验证第一个检查点是ACTIVE
    retrieved1 = checkpoint_manager.get_checkpoint(checkpoint1.checkpoint_id)
    assert retrieved1.state == CheckpointState.ACTIVE

    # 创建第二个检查点并激活
    checkpoint2 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=2,
        checkpoint_type=CheckpointType.USER_INPUT
    )
    checkpoint_manager.activate_checkpoint(checkpoint2.checkpoint_id)

    # 验证第一个检查点变为RESOLVED
    retrieved1_after = checkpoint_manager.get_checkpoint(checkpoint1.checkpoint_id)
    assert retrieved1_after.state == CheckpointState.RESOLVED

    # 验证第二个检查点是ACTIVE
    retrieved2 = checkpoint_manager.get_checkpoint(checkpoint2.checkpoint_id)
    assert retrieved2.state == CheckpointState.ACTIVE

    # 验证只有一个ACTIVE检查点
    active = checkpoint_manager.get_active_checkpoint("session_1")
    assert active.checkpoint_id == checkpoint2.checkpoint_id


def test_resolve_checkpoint(checkpoint_manager):
    """测试解决检查点"""
    checkpoint = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_START,
        agent_id="agent_1"
    )

    # 解决检查点
    checkpoint_manager.resolve_checkpoint(checkpoint.checkpoint_id)

    # 验证状态变更
    retrieved = checkpoint_manager.get_checkpoint(checkpoint.checkpoint_id)
    assert retrieved.state == CheckpointState.RESOLVED


def test_fail_checkpoint(checkpoint_manager):
    """测试失败检查点"""
    checkpoint = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_START,
        agent_id="agent_1"
    )

    # 标记失败
    error_msg = "API timeout"
    checkpoint_manager.fail_checkpoint(checkpoint.checkpoint_id, error_msg)

    # 验证状态和错误信息
    retrieved = checkpoint_manager.get_checkpoint(checkpoint.checkpoint_id)
    assert retrieved.state == CheckpointState.FAILED
    assert retrieved.error == error_msg


def test_restore_from_checkpoint(checkpoint_manager):
    """测试从检查点恢复"""
    session_snapshot = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ],
        "round_num": 2,
        "active_agent_ids": ["agent_1"],
        "token_usage": {"input_tokens": 10, "output_tokens": 20}
    }

    checkpoint = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=2,
        checkpoint_type=CheckpointType.ROUND_COMPLETE,
        session_snapshot=session_snapshot
    )

    # 恢复状态
    restored_state = checkpoint_manager.restore_from_checkpoint(checkpoint.checkpoint_id)

    # 验证恢复的数据
    assert restored_state["round_num"] == 2
    assert len(restored_state["messages"]) == 2
    assert restored_state["messages"][0]["role"] == "user"
    assert restored_state["active_agent_ids"] == ["agent_1"]
    assert restored_state["token_usage"]["input_tokens"] == 10


def test_restore_from_checkpoint_no_snapshot(checkpoint_manager):
    """测试从没有快照的检查点恢复（应抛出异常）"""
    checkpoint = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_START,
        agent_id="agent_1"
        # 没有session_snapshot
    )

    # 应该抛出ValueError
    with pytest.raises(ValueError, match="has no session snapshot"):
        checkpoint_manager.restore_from_checkpoint(checkpoint.checkpoint_id)


def test_rollback_to_checkpoint(checkpoint_manager):
    """测试回滚到检查点"""
    session_snapshot = {
        "messages": [{"role": "user", "content": "Hello"}],
        "round_num": 1
    }

    checkpoint = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT,
        session_snapshot=session_snapshot
    )

    # 回滚（创建新检查点）
    rollback_checkpoint = checkpoint_manager.rollback_to_checkpoint(
        checkpoint.checkpoint_id,
        create_new=True
    )

    # 验证新检查点
    assert rollback_checkpoint.checkpoint_id != checkpoint.checkpoint_id
    assert rollback_checkpoint.session_id == checkpoint.session_id
    assert rollback_checkpoint.checkpoint_type == CheckpointType.USER_COMMAND
    assert rollback_checkpoint.sequence > checkpoint.sequence

    # 验证response_data包含回滚信息
    response_data = json.loads(rollback_checkpoint.response_data)
    assert response_data["rollback_to"] == checkpoint.checkpoint_id


def test_cleanup_old_checkpoints(checkpoint_manager):
    """测试清理旧检查点"""
    # 创建10个检查点
    for i in range(10):
        checkpoint_manager.create_checkpoint(
            session_id="session_1",
            round_num=i + 1,
            checkpoint_type=CheckpointType.USER_INPUT
        )

    # 验证创建了10个
    all_checkpoints = checkpoint_manager.list_checkpoints("session_1", limit=100)
    assert len(all_checkpoints) == 10

    # 清理，只保留最近5个
    deleted_count = checkpoint_manager.cleanup_old_checkpoints(
        session_id="session_1",
        keep_last_n=5
    )

    # 验证删除了5个
    assert deleted_count == 5

    # 验证剩余5个
    remaining = checkpoint_manager.list_checkpoints("session_1", limit=100)
    assert len(remaining) == 5

    # 验证保留的是最新的5个（sequence 5-9）
    sequences = [cp.sequence for cp in remaining]
    assert min(sequences) == 5
    assert max(sequences) == 9


def test_list_checkpoints(checkpoint_manager):
    """测试列出检查点"""
    # 创建多个检查点
    for i in range(5):
        checkpoint_manager.create_checkpoint(
            session_id="session_1",
            round_num=i + 1,
            checkpoint_type=CheckpointType.USER_INPUT
        )

    # 列出检查点
    checkpoints = checkpoint_manager.list_checkpoints("session_1", limit=10)

    # 验证数量和顺序（倒序）
    assert len(checkpoints) == 5
    assert checkpoints[0].sequence == 4  # 最新的
    assert checkpoints[4].sequence == 0  # 最旧的


def test_find_active_checkpoints(checkpoint_manager):
    """测试查找ACTIVE检查点"""
    # 创建并激活检查点
    checkpoint1 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT
    )
    checkpoint_manager.activate_checkpoint(checkpoint1.checkpoint_id)

    checkpoint2 = checkpoint_manager.create_checkpoint(
        session_id="session_2",
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT
    )
    checkpoint_manager.activate_checkpoint(checkpoint2.checkpoint_id)

    # 查找所有ACTIVE
    active_checkpoints = checkpoint_manager.find_active_checkpoints()

    # 验证找到2个
    assert len(active_checkpoints) == 2
    active_ids = {cp.checkpoint_id for cp in active_checkpoints}
    assert checkpoint1.checkpoint_id in active_ids
    assert checkpoint2.checkpoint_id in active_ids


def test_get_last_resolved_checkpoint(checkpoint_manager):
    """测试获取最后一个RESOLVED检查点"""
    # 创建并解决多个检查点
    checkpoint1 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT
    )
    checkpoint_manager.resolve_checkpoint(checkpoint1.checkpoint_id)

    checkpoint2 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=2,
        checkpoint_type=CheckpointType.USER_INPUT
    )
    checkpoint_manager.resolve_checkpoint(checkpoint2.checkpoint_id)

    # 创建一个ACTIVE（不解决）
    checkpoint3 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=3,
        checkpoint_type=CheckpointType.USER_INPUT
    )
    checkpoint_manager.activate_checkpoint(checkpoint3.checkpoint_id)

    # 获取最后一个RESOLVED
    last_resolved = checkpoint_manager.get_last_resolved_checkpoint("session_1")

    # 验证是checkpoint2
    assert last_resolved.checkpoint_id == checkpoint2.checkpoint_id


def test_sequence_generation(checkpoint_manager):
    """测试序列号生成"""
    # 创建3个检查点
    cp1 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT
    )
    cp2 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=2,
        checkpoint_type=CheckpointType.USER_INPUT
    )
    cp3 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=3,
        checkpoint_type=CheckpointType.USER_INPUT
    )

    # 验证序列号单调递增
    assert cp1.sequence == 0
    assert cp2.sequence == 1
    assert cp3.sequence == 2


def test_multiple_sessions(checkpoint_manager):
    """测试多会话隔离"""
    # 会话1创建检查点
    cp1_s1 = checkpoint_manager.create_checkpoint(
        session_id="session_1",
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT
    )

    # 会话2创建检查点
    cp1_s2 = checkpoint_manager.create_checkpoint(
        session_id="session_2",
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT
    )

    # 验证序列号独立
    assert cp1_s1.sequence == 0
    assert cp1_s2.sequence == 0

    # 验证列出检查点只返回对应会话
    checkpoints_s1 = checkpoint_manager.list_checkpoints("session_1")
    assert len(checkpoints_s1) == 1
    assert checkpoints_s1[0].session_id == "session_1"

    checkpoints_s2 = checkpoint_manager.list_checkpoints("session_2")
    assert len(checkpoints_s2) == 1
    assert checkpoints_s2[0].session_id == "session_2"
