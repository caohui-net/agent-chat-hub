"""
Phase 2集成测试 - 测试多Agent协作核心功能
"""
import pytest
import asyncio
from pathlib import Path
from src.core.config import ConfigManager
from src.core.models import ModelConfig, AgentConfig
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager
from src.agents.message_bus import MessageBus


@pytest.fixture
def temp_config_dir(tmp_path):
    """创建临时配置目录"""
    return tmp_path / "config"


@pytest.fixture
def config_manager(temp_config_dir):
    """创建配置管理器"""
    cm = ConfigManager(temp_config_dir)

    # 添加测试模型
    model = ModelConfig(
        model_id="test-model",
        provider="anthropic",
        display_name="Test Model",
        base_url="https://api.example.com/v1/messages",
        api_key_name="test_api_key"
    )
    cm.add_model(model)

    # 添加测试Agent
    agent1 = AgentConfig(
        agent_id="agent_1",
        name="Agent 1",
        role="测试助手1",
        model_id="test-model",
        priority=100,
        active=True
    )
    agent2 = AgentConfig(
        agent_id="agent_2",
        name="Agent 2",
        role="测试助手2",
        model_id="test-model",
        priority=90,
        active=True
    )
    cm.add_agent(agent1)
    cm.add_agent(agent2)

    return cm


@pytest.fixture
def coordinator():
    """创建响应协调器"""
    return ResponseCoordinator()


@pytest.fixture
def executor(config_manager):
    """创建Agent执行器"""
    return AgentExecutor(config_manager)


@pytest.fixture
def session_manager(config_manager, coordinator, executor):
    """创建会话管理器"""
    return SessionManager(config_manager, coordinator, executor)


def test_session_creation(session_manager):
    """测试会话创建"""
    session = session_manager.create_session("集成测试会话")

    assert session is not None
    assert session.title == "集成测试会话"
    assert session_manager.current_session == session


def test_message_bus_integration(session_manager):
    """测试消息总线集成"""
    session = session_manager.create_session("消息总线测试")

    # 验证MessageBus已初始化
    assert session_manager.message_bus is not None

    # 验证agents已注册
    agents = session_manager.config_manager.list_agents(active_only=True)
    for agent in agents:
        assert agent.agent_id in session_manager.message_bus._queues


def test_agent_message_sending():
    """测试Agent间消息发送"""
    async def run_test():
        # 创建测试环境
        config_dir = Path("/tmp/test_agent_message_sending")
        cm = ConfigManager(config_dir)

        # 添加测试模型和agents
        model = ModelConfig(
            model_id="test-model",
            provider="anthropic",
            display_name="Test Model",
            base_url="https://api.example.com",
            api_key_name="test_key"
        )
        cm.add_model(model)

        agent1 = AgentConfig(
            agent_id="agent_1",
            name="Agent 1",
            role="测试",
            model_id="test-model"
        )
        agent2 = AgentConfig(
            agent_id="agent_2",
            name="Agent 2",
            role="测试",
            model_id="test-model"
        )
        cm.add_agent(agent1)
        cm.add_agent(agent2)

        # 创建session manager
        coord = ResponseCoordinator()
        executor = AgentExecutor(cm)
        sm = SessionManager(cm, coord, executor)
        sm.create_session("测试")

        # 发送消息
        await sm.send_agent_message("agent_1", "Hello from agent_1", to_agent_id="agent_2")

        # 验证消息历史
        history = sm.get_agent_message_history(limit=10)
        assert len(history) > 0
        assert "agent_1" in history[0] or "Agent 1" in history[0]

        # 清理
        await executor.aclose()
        import shutil
        if config_dir.exists():
            shutil.rmtree(config_dir)

    asyncio.run(run_test())


def test_coordinator_with_multiple_agents(config_manager, coordinator):
    """测试协调器处理多Agent场景"""
    # 启动新轮次
    coordinator.start_round(session_id="test_session", round_num=1)

    # 获取所有活跃agents
    agents = config_manager.list_agents(active_only=True)
    assert len(agents) >= 2

    # 协调器应该能筛选agents
    qualified = coordinator.qualify_agents(agents)
    assert len(qualified) > 0

    # 选择agents（按优先级排序）
    selected, stop_reason = coordinator.select_agents(qualified)
    assert len(selected) > 0
    # 优先级升序排列（数值越小越优先）
    assert selected[0].priority <= selected[-1].priority


def test_session_message_history(session_manager):
    """测试会话消息历史"""
    session = session_manager.create_session("历史测试")

    # 添加用户消息
    session_manager.add_message("user", "测试消息1")
    session_manager.add_message("assistant", "回复消息1", agent_id="agent_1")
    session_manager.add_message("user", "测试消息2")

    # 获取历史
    history = session_manager.get_message_history()

    assert len(history) == 3
    assert "用户" in history[0]
    assert "测试消息1" in history[0]
    assert "Agent 1" in history[1] or "agent_1" in history[1]


def test_config_persistence(temp_config_dir):
    """测试配置持久化"""

    # 创建配置管理器并添加模型
    cm1 = ConfigManager(temp_config_dir)
    model = ModelConfig(
        model_id="persist-model",
        provider="openai",
        display_name="Persist Test",
        base_url="https://api.openai.com/v1",
        api_key_name="persist_key"
    )
    cm1.add_model(model)
    cm1.save_configs()  # 显式保存到文件

    # 创建新的配置管理器读取同一目录
    cm2 = ConfigManager(temp_config_dir)
    cm2.load_configs()  # 显式从文件加载
    models = cm2.list_models()

    assert len(models) > 0
    assert any(m.model_id == "persist-model" for m in models)
