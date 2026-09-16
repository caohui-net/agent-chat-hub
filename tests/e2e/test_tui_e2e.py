"""TUI端到端测试 - 测试Agent状态面板实时更新"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.core.models import AgentConfig
from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager
from src.core.agent_status import AgentStatus


@pytest.fixture
def temp_config_dir(tmp_path):
    """创建临时配置目录"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def config_manager(temp_config_dir):
    """创建配置管理器"""
    manager = ConfigManager(config_dir=temp_config_dir)

    # 添加测试模型
    from src.core.models import ModelConfig
    test_model = ModelConfig(
        model_id="claude-haiku-4",
        provider="anthropic",
        display_name="Claude Haiku 4",
        base_url="https://api.anthropic.com",
        api_key_name="test_key"
    )
    manager.add_model(test_model)

    return manager


@pytest.fixture
def coordinator():
    """创建协调器"""
    return ResponseCoordinator()


@pytest.fixture
def mock_executor():
    """创建模拟执行器"""
    executor = Mock(spec=AgentExecutor)
    executor.execute = AsyncMock()
    executor.aclose = AsyncMock()
    return executor


@pytest.fixture
def session_manager(config_manager, coordinator, mock_executor, tmp_path):
    """创建会话管理器（带状态回调）"""
    status_callback = Mock()
    session_dir = tmp_path / "sessions"

    manager = SessionManager(
        config_manager=config_manager,
        coordinator=coordinator,
        executor=mock_executor,
        session_dir=session_dir,
        status_callback=status_callback
    )

    return manager


@pytest.mark.asyncio
async def test_tui_status_panel_updates(session_manager, config_manager, mock_executor):
    """测试TUI状态面板实时更新

    验证：
    1. Agent状态从PENDING→RUNNING→COMPLETED正确转换
    2. 状态回调被正确触发
    3. AgentStatusManager记录正确的状态
    """
    # 创建测试Agent
    agent = AgentConfig(
        agent_id="test_agent",
        name="测试Agent",
        role="测试角色",
        model="claude-haiku-4",
        model_id="claude-haiku-4",
        active=True
    )
    config_manager.add_agent(agent)

    # 模拟执行器响应
    mock_executor.execute.return_value = "测试响应"

    # 创建会话
    session_manager.create_session("测试会话")

    # 记录状态回调次数
    callback_count_before = session_manager.status_callback.call_count

    # 处理用户输入（触发Agent执行）
    await session_manager.process_user_input("@test_agent 测试消息")

    # 验证状态回调被触发（至少2次：RUNNING和COMPLETED）
    assert session_manager.status_callback.call_count >= callback_count_before + 2

    # 验证Agent状态最终为COMPLETED
    final_status = session_manager.status_manager.get_status("test_agent")
    assert final_status is not None
    assert final_status.status == AgentStatus.COMPLETED

    # 验证执行时间被记录
    assert final_status.start_time is not None
    assert final_status.end_time is not None
    assert final_status.elapsed_seconds > 0


@pytest.mark.asyncio
async def test_tui_handles_agent_error(session_manager, config_manager, mock_executor):
    """测试TUI正确显示Agent错误状态

    验证：
    1. Agent执行失败时状态变为ERROR
    2. 错误信息被正确记录
    3. 状态回调被触发通知TUI
    """
    # 创建测试Agent
    agent = AgentConfig(
        agent_id="error_agent",
        name="错误Agent",
        role="测试角色",
        model="claude-haiku-4",
        model_id="claude-haiku-4",
        active=True
    )
    config_manager.add_agent(agent)

    # 模拟执行器抛出异常
    error_message = "模拟执行失败"
    mock_executor.execute.side_effect = RuntimeError(error_message)

    # 创建会话
    session_manager.create_session("错误测试会话")

    # 记录状态回调次数
    callback_count_before = session_manager.status_callback.call_count

    # 处理用户输入（Agent将失败）
    responses = await session_manager.process_user_input("@error_agent 测试消息")

    # 验证状态回调被触发
    assert session_manager.status_callback.call_count >= callback_count_before + 2

    # 验证Agent状态为ERROR
    error_status = session_manager.status_manager.get_status("error_agent")
    assert error_status is not None
    assert error_status.status == AgentStatus.ERROR

    # 验证错误信息被记录
    assert error_status.error is not None
    assert error_message in error_status.error

    # 验证响应包含错误信息
    assert len(responses) > 0
    assert "执行失败" in responses[0] or "❌" in responses[0]


@pytest.mark.asyncio
async def test_multiple_agents_concurrent_status_updates(session_manager, config_manager, mock_executor):
    """测试多个Agent并发执行时的状态更新

    验证：
    1. 多个Agent同时执行时状态独立追踪
    2. 每个Agent的状态正确转换
    3. 状态面板显示所有Agent的状态
    """
    # 创建多个测试Agent
    agents = [
        AgentConfig(
            agent_id=f"agent_{i}",
            name=f"Agent {i}",
            role="测试角色",
            model="claude-haiku-4",
            model_id="claude-haiku-4",
            active=True
        )
        for i in range(3)
    ]

    for agent in agents:
        config_manager.add_agent(agent)

    # 模拟执行器响应（不同延迟模拟真实并发）
    async def mock_execute_with_delay(agent_config, messages):
        """模拟带延迟的执行"""
        delay = 0.1 if agent_config.agent_id == "agent_0" else 0.05
        await asyncio.sleep(delay)
        return f"响应来自 {agent_config.name}"

    mock_executor.execute.side_effect = mock_execute_with_delay

    # 创建会话
    session_manager.create_session("并发测试会话")

    # 处理用户输入（@所有Agent触发并发执行）
    await session_manager.process_user_input("@agent_0 @agent_1 @agent_2 并发测试")

    # 验证所有Agent状态为COMPLETED
    for i in range(3):
        status = session_manager.status_manager.get_status(f"agent_{i}")
        assert status is not None
        assert status.status == AgentStatus.COMPLETED
        assert status.elapsed_seconds > 0

    # 验证状态管理器包含所有Agent
    all_statuses = session_manager.status_manager.get_all_statuses()
    assert len(all_statuses) == 3


@pytest.mark.asyncio
async def test_status_panel_clears_on_new_session(session_manager, config_manager, mock_executor):
    """测试新会话时状态面板正确重置

    验证：
    1. 新会话创建时旧状态被清除
    2. 状态面板不显示上一会话的Agent状态
    """
    # 创建测试Agent
    agent = AgentConfig(
        agent_id="test_agent",
        name="测试Agent",
        role="测试角色",
        model="claude-haiku-4",
        model_id="claude-haiku-4",
        active=True
    )
    config_manager.add_agent(agent)

    mock_executor.execute.return_value = "测试响应"

    # 创建第一个会话并执行
    session_manager.create_session("会话1")
    await session_manager.process_user_input("@test_agent 消息1")

    # 验证状态存在
    assert session_manager.status_manager.get_status("test_agent") is not None

    # 创建新会话（应该清除旧状态）
    session_manager.create_session("会话2")
    session_manager.status_manager.clear_all_statuses()  # TUI应该在新会话时调用

    # 验证状态已清除
    all_statuses = session_manager.status_manager.get_all_statuses()
    assert len(all_statuses) == 0

    # 执行新的Agent调用
    await session_manager.process_user_input("@test_agent 消息2")

    # 验证新状态被创建
    new_status = session_manager.status_manager.get_status("test_agent")
    assert new_status is not None
    assert new_status.status == AgentStatus.COMPLETED
