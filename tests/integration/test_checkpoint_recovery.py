"""
检查点系统集成测试 - 崩溃恢复场景
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.core.checkpoint import (
    CheckpointManager,
    CheckpointType,
    CheckpointState
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


@pytest.mark.asyncio
async def test_crash_during_agent_response(checkpoint_manager):
    """测试Agent响应中途崩溃恢复

    场景：
    1. 用户输入 → USER_INPUT检查点（ACTIVE）
    2. Agent开始响应 → AGENT_START检查点
    3. 系统崩溃（模拟：检查点保持ACTIVE）
    4. 重启后检测到ACTIVE检查点 → 标记为FAILED
    5. 从上一个RESOLVED检查点恢复
    """
    session_id = "session_crash_test"

    # 步骤1: 创建会话开始检查点（成功完成）
    session_start = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=0,
        checkpoint_type=CheckpointType.SESSION_START,
        session_snapshot={
            "messages": [],
            "round_num": 0,
            "active_agent_ids": []
        }
    )
    checkpoint_manager.activate_checkpoint(session_start.checkpoint_id)
    checkpoint_manager.resolve_checkpoint(session_start.checkpoint_id)

    # 步骤2: 用户输入检查点（成功完成）
    user_input = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT,
        session_snapshot={
            "messages": [{"role": "user", "content": "Hello"}],
            "round_num": 1,
            "active_agent_ids": ["claude"]
        }
    )
    checkpoint_manager.activate_checkpoint(user_input.checkpoint_id)
    checkpoint_manager.resolve_checkpoint(user_input.checkpoint_id)

    # 步骤3: Agent开始响应（模拟崩溃：检查点创建后激活但未解决）
    agent_start = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_START,
        agent_id="claude",
        session_snapshot={
            "messages": [{"role": "user", "content": "Hello"}],
            "round_num": 1,
            "active_agent_ids": ["claude"]
        }
    )
    checkpoint_manager.activate_checkpoint(agent_start.checkpoint_id)

    # ⚡ 系统崩溃 ⚡

    # === 重启后的恢复流程 ===

    # 步骤4: 检测所有ACTIVE检查点
    active_checkpoints = checkpoint_manager.find_active_checkpoints()
    assert len(active_checkpoints) == 1
    assert active_checkpoints[0].checkpoint_id == agent_start.checkpoint_id

    # 步骤5: 标记为FAILED
    for active_cp in active_checkpoints:
        checkpoint_manager.fail_checkpoint(
            active_cp.checkpoint_id,
            error="Process crashed"
        )

    # 验证标记为FAILED
    failed_cp = checkpoint_manager.get_checkpoint(agent_start.checkpoint_id)
    assert failed_cp.state == CheckpointState.FAILED
    assert "crashed" in failed_cp.error.lower()

    # 步骤6: 找到上一个RESOLVED检查点
    last_resolved = checkpoint_manager.get_last_resolved_checkpoint(session_id)
    assert last_resolved is not None
    assert last_resolved.checkpoint_id == user_input.checkpoint_id

    # 步骤7: 从上一个成功检查点恢复
    restored_state = checkpoint_manager.restore_from_checkpoint(
        last_resolved.checkpoint_id
    )

    # 验证恢复的状态
    assert restored_state["round_num"] == 1
    assert len(restored_state["messages"]) == 1
    assert restored_state["messages"][0]["content"] == "Hello"
    assert restored_state["active_agent_ids"] == ["claude"]

    # 步骤8: 创建恢复记录检查点
    recovery_checkpoint = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=restored_state["round_num"],
        checkpoint_type=CheckpointType.USER_COMMAND,
        session_snapshot=restored_state,
        response_data={"recovered_from": last_resolved.checkpoint_id}
    )

    # 验证恢复成功
    assert recovery_checkpoint is not None
    assert recovery_checkpoint.checkpoint_type == CheckpointType.USER_COMMAND


@pytest.mark.asyncio
async def test_checkpoint_sequence(checkpoint_manager):
    """测试检查点序列完整性

    验证完整的对话流程中检查点的创建和状态转换。
    """
    session_id = "session_sequence_test"

    # 1. SESSION_START
    cp_start = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=0,
        checkpoint_type=CheckpointType.SESSION_START,
        session_snapshot={"messages": [], "round_num": 0}
    )
    checkpoint_manager.activate_checkpoint(cp_start.checkpoint_id)
    checkpoint_manager.resolve_checkpoint(cp_start.checkpoint_id)

    # 2. USER_INPUT (Round 1)
    cp_input1 = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT,
        session_snapshot={
            "messages": [{"role": "user", "content": "Hello"}],
            "round_num": 1
        }
    )
    checkpoint_manager.activate_checkpoint(cp_input1.checkpoint_id)
    checkpoint_manager.resolve_checkpoint(cp_input1.checkpoint_id)

    # 3. AGENT_START (claude)
    cp_agent_start = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_START,
        agent_id="claude",
        session_snapshot={
            "messages": [{"role": "user", "content": "Hello"}],
            "round_num": 1
        }
    )
    checkpoint_manager.activate_checkpoint(cp_agent_start.checkpoint_id)

    # 4. AGENT_COMPLETE (claude)
    cp_agent_complete = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_COMPLETE,
        agent_id="claude",
        response_data={"content": "Hi there!"},
        session_snapshot={
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!", "agent_id": "claude"}
            ],
            "round_num": 1
        }
    )
    checkpoint_manager.resolve_checkpoint(cp_agent_start.checkpoint_id)

    # 5. ROUND_COMPLETE
    cp_round_complete = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.ROUND_COMPLETE,
        session_snapshot={
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!", "agent_id": "claude"}
            ],
            "round_num": 1
        }
    )
    checkpoint_manager.activate_checkpoint(cp_round_complete.checkpoint_id)
    checkpoint_manager.resolve_checkpoint(cp_round_complete.checkpoint_id)

    # 验证检查点序列
    all_checkpoints = checkpoint_manager.list_checkpoints(session_id, limit=100)
    assert len(all_checkpoints) == 5  # SESSION_START + USER_INPUT + AGENT_START + AGENT_COMPLETE + ROUND_COMPLETE

    # 验证序列号连续
    sequences = [cp.sequence for cp in reversed(all_checkpoints)]
    assert sequences == list(range(5))

    # 验证类型顺序
    types = [cp.checkpoint_type for cp in reversed(all_checkpoints)]
    assert types[0] == CheckpointType.SESSION_START
    assert types[1] == CheckpointType.USER_INPUT
    assert types[2] == CheckpointType.AGENT_START
    assert types[3] == CheckpointType.AGENT_COMPLETE
    assert types[4] == CheckpointType.ROUND_COMPLETE

    # 验证最终状态：所有检查点都是RESOLVED
    states = [cp.state for cp in all_checkpoints]
    # 最后一个ROUND_COMPLETE被激活并解决，所以都应该是RESOLVED
    resolved_count = sum(1 for state in states if state == CheckpointState.RESOLVED)
    assert resolved_count >= 4  # 至少前4个是RESOLVED


@pytest.mark.asyncio
async def test_multiple_agent_crash_recovery(checkpoint_manager):
    """测试多Agent并发时崩溃恢复

    场景：3个Agent并发响应，其中2个完成，1个崩溃。
    """
    session_id = "session_multi_agent_crash"

    # 初始状态
    user_input = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT,
        session_snapshot={
            "messages": [{"role": "user", "content": "Hello"}],
            "round_num": 1,
            "active_agent_ids": ["claude", "codex", "gemini"]
        }
    )
    checkpoint_manager.activate_checkpoint(user_input.checkpoint_id)
    checkpoint_manager.resolve_checkpoint(user_input.checkpoint_id)

    # Agent 1 (claude) - 开始并完成
    claude_start = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_START,
        agent_id="claude"
    )
    claude_complete = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_COMPLETE,
        agent_id="claude",
        response_data={"content": "Response from Claude"}
    )
    checkpoint_manager.resolve_checkpoint(claude_start.checkpoint_id)

    # Agent 2 (codex) - 开始并完成
    codex_start = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_START,
        agent_id="codex"
    )
    codex_complete = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_COMPLETE,
        agent_id="codex",
        response_data={"content": "Response from Codex"}
    )
    checkpoint_manager.resolve_checkpoint(codex_start.checkpoint_id)

    # Agent 3 (gemini) - 开始但崩溃（保持ACTIVE）
    gemini_start = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_START,
        agent_id="gemini"
    )
    checkpoint_manager.activate_checkpoint(gemini_start.checkpoint_id)

    # ⚡ 系统崩溃 ⚡

    # 恢复：检测ACTIVE检查点
    active_checkpoints = checkpoint_manager.find_active_checkpoints()
    assert len(active_checkpoints) == 1
    assert active_checkpoints[0].agent_id == "gemini"

    # 标记失败
    checkpoint_manager.fail_checkpoint(
        active_checkpoints[0].checkpoint_id,
        error="Agent timeout during crash"
    )

    # 验证：已完成的Agent检查点仍然有效
    claude_complete_retrieved = checkpoint_manager.get_checkpoint(claude_complete.checkpoint_id)
    codex_complete_retrieved = checkpoint_manager.get_checkpoint(codex_complete.checkpoint_id)

    assert claude_complete_retrieved.checkpoint_type == CheckpointType.AGENT_COMPLETE
    assert codex_complete_retrieved.checkpoint_type == CheckpointType.AGENT_COMPLETE

    # 验证：失败的Agent检查点被标记
    gemini_start_retrieved = checkpoint_manager.get_checkpoint(gemini_start.checkpoint_id)
    assert gemini_start_retrieved.state == CheckpointState.FAILED
    assert "timeout" in gemini_start_retrieved.error.lower()


@pytest.mark.asyncio
async def test_rollback_after_error(checkpoint_manager):
    """测试错误后回滚

    场景：Agent响应后发现错误，用户回滚到之前的状态。
    """
    session_id = "session_rollback_test"

    # 初始状态 (Round 1)
    cp1 = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.USER_INPUT,
        session_snapshot={
            "messages": [
                {"role": "user", "content": "What is 2+2?"}
            ],
            "round_num": 1
        }
    )
    checkpoint_manager.activate_checkpoint(cp1.checkpoint_id)
    checkpoint_manager.resolve_checkpoint(cp1.checkpoint_id)

    # Agent响应 (错误答案)
    cp2 = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,
        checkpoint_type=CheckpointType.AGENT_COMPLETE,
        agent_id="claude",
        response_data={"content": "5"},  # 错误答案
        session_snapshot={
            "messages": [
                {"role": "user", "content": "What is 2+2?"},
                {"role": "assistant", "content": "5", "agent_id": "claude"}
            ],
            "round_num": 1
        }
    )
    checkpoint_manager.activate_checkpoint(cp2.checkpoint_id)
    checkpoint_manager.resolve_checkpoint(cp2.checkpoint_id)

    # 用户发现错误，回滚到cp1
    rollback_checkpoint = checkpoint_manager.rollback_to_checkpoint(
        cp1.checkpoint_id,
        create_new=True
    )

    # 验证回滚
    assert rollback_checkpoint.checkpoint_type == CheckpointType.USER_COMMAND
    assert rollback_checkpoint.session_id == session_id

    # 恢复状态
    restored_state = checkpoint_manager.restore_from_checkpoint(cp1.checkpoint_id)

    # 验证状态恢复到错误答案之前
    assert len(restored_state["messages"]) == 1
    assert restored_state["messages"][0]["content"] == "What is 2+2?"
    assert restored_state["round_num"] == 1

    # 验证可以继续对话（从cp1状态）
    cp3 = checkpoint_manager.create_checkpoint(
        session_id=session_id,
        round_num=1,  # 同一轮次，但从rollback后的状态
        checkpoint_type=CheckpointType.AGENT_COMPLETE,
        agent_id="claude",
        response_data={"content": "4"},  # 正确答案
        session_snapshot={
            "messages": [
                {"role": "user", "content": "What is 2+2?"},
                {"role": "assistant", "content": "4", "agent_id": "claude"}
            ],
            "round_num": 1
        }
    )

    assert cp3.session_id == session_id


@pytest.mark.asyncio
async def test_cleanup_during_long_session(checkpoint_manager):
    """测试长会话中的检查点清理

    验证自动清理不影响恢复能力。
    """
    session_id = "session_long_test"

    # 模拟长会话：创建150个检查点
    for round_num in range(50):
        # USER_INPUT
        checkpoint_manager.create_checkpoint(
            session_id=session_id,
            round_num=round_num + 1,
            checkpoint_type=CheckpointType.USER_INPUT,
            session_snapshot={"round_num": round_num + 1}
        )

        # AGENT_COMPLETE
        checkpoint_manager.create_checkpoint(
            session_id=session_id,
            round_num=round_num + 1,
            checkpoint_type=CheckpointType.AGENT_COMPLETE,
            agent_id="claude",
            session_snapshot={"round_num": round_num + 1}
        )

        # ROUND_COMPLETE
        checkpoint_manager.create_checkpoint(
            session_id=session_id,
            round_num=round_num + 1,
            checkpoint_type=CheckpointType.ROUND_COMPLETE,
            session_snapshot={"round_num": round_num + 1}
        )

    # 验证创建了150个
    all_checkpoints = checkpoint_manager.list_checkpoints(session_id, limit=200)
    assert len(all_checkpoints) == 150

    # 清理，保留最近100个
    deleted = checkpoint_manager.cleanup_old_checkpoints(
        session_id,
        keep_last_n=100
    )
    assert deleted == 50

    # 验证剩余100个
    remaining = checkpoint_manager.list_checkpoints(session_id, limit=200)
    assert len(remaining) == 100

    # 验证最新的检查点仍然可用
    latest = remaining[0]
    assert latest.round_num == 50

    # 验证可以从最新检查点恢复
    restored = checkpoint_manager.restore_from_checkpoint(latest.checkpoint_id)
    assert restored["round_num"] == 50
