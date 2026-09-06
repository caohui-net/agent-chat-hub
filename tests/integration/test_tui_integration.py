"""TUI应用测试 - 简化版本，不依赖textual运行时"""
import pytest
from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager


@pytest.fixture
def config_manager(tmp_path):
    """创建临时配置管理器"""
    config_file = tmp_path / "config.json"
    return ConfigManager(str(config_file))


@pytest.fixture
def session_manager(config_manager):
    """创建会话管理器"""
    coordinator = ResponseCoordinator()
    executor = AgentExecutor(config_manager)
    return SessionManager(config_manager, coordinator, executor)


def test_tui_app_can_import():
    """测试TUI应用模块可以导入"""
    try:
        from src.tui.app import ChatApp
        assert ChatApp is not None
    except ImportError as e:
        pytest.skip(f"Textual not installed: {e}")


def test_session_manager_integration(session_manager):
    """测试会话管理器集成（TUI依赖的核心功能）"""
    # 创建会话
    session_manager.create_session("Test Session")
    assert session_manager.current_session is not None
    assert session_manager.current_session.title == "Test Session"

    # 验证消息历史功能
    history = session_manager.get_message_history()
    assert isinstance(history, list)
