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


def test_multiple_agents_concurrent_response(config_manager, coordinator):
    """测试多Agent并发响应场景 - Phase 2.1"""
    # 创建3个不同优先级的agents
    agent1 = AgentConfig(
        agent_id="concurrent_agent_1",
        name="Concurrent Agent 1",
        role="助手1",
        model_id="test-model",
        priority=100,
        active=True
    )
    agent2 = AgentConfig(
        agent_id="concurrent_agent_2",
        name="Concurrent Agent 2",
        role="助手2",
        model_id="test-model",
        priority=150,
        active=True
    )
    agent3 = AgentConfig(
        agent_id="concurrent_agent_3",
        name="Concurrent Agent 3",
        role="助手3",
        model_id="test-model",
        priority=200,
        active=True
    )

    # 添加agents到配置
    config_manager.add_agent(agent1)
    config_manager.add_agent(agent2)
    config_manager.add_agent(agent3)

    # 启动新轮次
    coordinator.start_round(session_id="concurrent_test", round_num=1)

    # 获取所有活跃agents
    agents = [agent1, agent2, agent3]

    # 筛选合格agents
    qualified = coordinator.qualify_agents(agents)
    assert len(qualified) == 3, "应该有3个合格的agents"

    # 选择agents进行响应
    selected, stop_reason = coordinator.select_agents(qualified)
    assert len(selected) == 3, "应该选择全部3个agents"

    # 验证排序：按priority升序
    assert selected[0].priority == 100, "第一个agent应该是priority=100"
    assert selected[1].priority == 150, "第二个agent应该是priority=150"
    assert selected[2].priority == 200, "第三个agent应该是priority=200"

    # 验证agent_id顺序正确
    assert selected[0].agent_id == "concurrent_agent_1"
    assert selected[1].agent_id == "concurrent_agent_2"
    assert selected[2].agent_id == "concurrent_agent_3"


def test_budget_max_agents_with_multiple():
    """测试max_agents边界限制 - Phase 2.1"""
    from src.agents.coordinator import ResponseCoordinator, BudgetLimits

    # 创建协调器，限制max_agents=3
    coordinator = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=3,
            max_calls_per_round=10,
            max_tokens=50000,
            timeout_seconds=120.0
        )
    )

    # 创建5个agents（优先级递增）
    agents = [
        AgentConfig(
            agent_id=f"budget_agent_{i}",
            name=f"Budget Agent {i}",
            role=f"助手{i}",
            model_id="test-model",
            priority=100 + i * 50,
            active=True
        )
        for i in range(5)
    ]

    # 启动轮次
    coordinator.start_round(session_id="budget_test", round_num=1)

    # qualify_agents已经应用max_agents限制，应只返回3个
    qualified = coordinator.qualify_agents(agents)
    assert len(qualified) == 3, "qualify_agents应用max_agents=3限制，只返回3个agents"

    # 验证返回的是优先级最高的3个（priority最小）
    assert qualified[0].priority == 100
    assert qualified[1].priority == 150
    assert qualified[2].priority == 200

    # select_agents进一步处理
    selected, stop_reason = coordinator.select_agents(qualified)
    assert len(selected) == 3, "应返回3个agents"


def test_deduplication_prevents_message_bombing():
    """测试去重规则防止消息轰炸 - Phase 2.1"""
    from src.agents.coordinator import ResponseCoordinator, BudgetLimits

    coordinator = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=3,
            max_calls_per_round=10,
            max_tokens=50000,
            timeout_seconds=120.0
        )
    )

    # 创建单个agent
    agent = AgentConfig(
        agent_id="dedup_agent",
        name="Dedup Agent",
        role="测试助手",
        model_id="test-model",
        priority=100,
        active=True
    )

    # 启动轮次
    session_id = "dedup_test"
    round_num = 1
    coordinator.start_round(session_id=session_id, round_num=round_num)

    # 第一次调用：应该成功（不是重复）
    is_dup1 = coordinator.is_duplicate_call(agent.agent_id)
    assert not is_dup1, "第一次调用不应是重复"

    # 记录第一次调用
    coordinator.record_call(agent.agent_id, tokens_used=1000)

    # 第二次调用：应该被识别为重复（相同session、round、agent）
    is_dup2 = coordinator.is_duplicate_call(agent.agent_id)
    assert is_dup2, "第二次调用应被识别为重复"

    # 验证：不同session允许
    coordinator.start_round(session_id="different_session", round_num=round_num)
    is_dup3 = coordinator.is_duplicate_call(agent.agent_id)
    assert not is_dup3, "不同session应允许"

    # 验证：不同round允许
    coordinator.start_round(session_id=session_id, round_num=2)
    is_dup4 = coordinator.is_duplicate_call(agent.agent_id)
    assert not is_dup4, "不同round应允许"

    # 验证：不同agent允许
    coordinator.start_round(session_id=session_id, round_num=round_num)
    is_dup5 = coordinator.is_duplicate_call("different_agent")
    assert not is_dup5, "不同agent应允许"


def test_budget_max_calls_concurrent():
    """测试max_calls_per_round边界限制 - Phase 2.1"""
    from src.agents.coordinator import ResponseCoordinator, BudgetLimits

    # 限制每轮最多3次调用
    coordinator = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=5,
            max_calls_per_round=3,
            max_tokens=50000,
            timeout_seconds=120.0
        )
    )

    # 创建3个agents
    agents = [
        AgentConfig(
            agent_id=f"calls_agent_{i}",
            name=f"Calls Agent {i}",
            role=f"助手{i}",
            model_id="test-model",
            priority=100 + i * 50,
            active=True
        )
        for i in range(3)
    ]

    # 启动轮次
    coordinator.start_round(session_id="calls_test", round_num=1)

    # 前3次调用应该成功
    for i, agent in enumerate(agents):
        should_stop_before, _ = coordinator.should_stop()
        assert not should_stop_before, f"第{i+1}次调用前不应停止"

        coordinator.record_call(agent.agent_id, tokens_used=1000)

    # 第4次调用前应该停止（超出max_calls限制）
    should_stop_after, reason = coordinator.should_stop()
    assert should_stop_after, "第4次调用前应该停止（max_calls=3）"

    # 验证统计信息
    stats = coordinator.get_round_stats()
    assert stats["total_calls"] == 3, "应记录3次调用"


def test_budget_max_tokens_concurrent():
    """测试max_tokens边界限制 - Phase 2.1"""
    from src.agents.coordinator import ResponseCoordinator, BudgetLimits

    # 限制每轮最多12000 tokens
    coordinator = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=5,
            max_calls_per_round=10,
            max_tokens=12000,
            timeout_seconds=120.0
        )
    )

    # 启动轮次
    coordinator.start_round(session_id="tokens_test", round_num=1)

    # 第1次调用：5000 tokens
    coordinator.record_call("agent_1", tokens_used=5000)
    should_stop_1, _ = coordinator.should_stop()
    assert not should_stop_1, "5000 tokens后不应停止"

    # 第2次调用：6000 tokens，累计11000
    coordinator.record_call("agent_2", tokens_used=6000)
    should_stop_2, _ = coordinator.should_stop()
    assert not should_stop_2, "11000 tokens后不应停止"

    # 第3次调用尝试：需要2000 tokens，会超出12000限制
    # 在record_call之前，should_stop应该考虑是否还有预算
    # 但实际上should_stop是在已记录调用后判断，所以这里先记录
    coordinator.record_call("agent_3", tokens_used=2000)

    # 现在累计13000 tokens，超出限制
    should_stop_3, reason = coordinator.should_stop()
    assert should_stop_3, "13000 tokens后应该停止（超出12000限制）"

    # 验证统计信息
    stats = coordinator.get_round_stats()
    assert stats["total_tokens"] == 13000, "应记录13000 tokens"


def test_cancellation_concurrent_agents():
    """测试并发取消场景 - Phase 2.1"""
    from src.agents.coordinator import ResponseCoordinator, BudgetLimits

    coordinator = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=5,
            max_calls_per_round=10,
            max_tokens=50000,
            timeout_seconds=120.0
        )
    )

    # 创建3个agents
    agents = [
        AgentConfig(
            agent_id=f"cancel_agent_{i}",
            name=f"Cancel Agent {i}",
            role=f"助手{i}",
            model_id="test-model",
            priority=100 + i * 50,
            active=True
        )
        for i in range(3)
    ]

    # 启动轮次
    session_id = "cancel_test"
    round_num = 1
    coordinator.start_round(session_id=session_id, round_num=round_num)

    # 第1个agent开始响应
    coordinator.record_call(agents[0].agent_id, tokens_used=1000)

    # 用户发起取消
    coordinator.cancel_round()

    # 验证round已被标记为取消
    assert coordinator.current_round.cancelled, "round应该被标记为已取消"

    # 第2、3个agent尝试响应应该被阻止
    should_stop, reason = coordinator.should_stop()
    assert should_stop, "取消后should_stop应返回True"


def test_agent_priority_sorting_concurrent():
    """测试多Agent场景下的排序规则 - Phase 2.1"""
    from src.agents.coordinator import ResponseCoordinator, BudgetLimits

    coordinator = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=3,
            max_calls_per_round=10,
            max_tokens=50000,
            timeout_seconds=120.0
        )
    )

    # 创建5个agents，故意打乱priority和agent_id顺序
    agents = [
        AgentConfig(agent_id="agent_c", name="Agent C", role="助手C",
                   model_id="test-model", priority=100, active=True),
        AgentConfig(agent_id="agent_a", name="Agent A", role="助手A",
                   model_id="test-model", priority=100, active=True),
        AgentConfig(agent_id="agent_d", name="Agent D", role="助手D",
                   model_id="test-model", priority=150, active=True),
        AgentConfig(agent_id="agent_b", name="Agent B", role="助手B",
                   model_id="test-model", priority=150, active=True),
        AgentConfig(agent_id="agent_e", name="Agent E", role="助手E",
                   model_id="test-model", priority=200, active=True),
    ]

    # 启动轮次
    coordinator.start_round(session_id="sort_test", round_num=1)

    # 筛选和选择
    qualified = coordinator.qualify_agents(agents)
    selected, stop_reason = coordinator.select_agents(qualified)

    # 验证：由于max_agents=3，应返回3个
    assert len(selected) == 3, "应返回3个agents"

    # 验证排序规则：
    # 1. 按priority升序（100 < 150 < 200）
    # 2. 相同priority按agent_id字典序（a < c, b < d）
    # 期望顺序：agent_a(100), agent_c(100), agent_b(150)
    assert selected[0].agent_id == "agent_a", "第1个应是agent_a (priority=100, 字典序最小)"
    assert selected[1].agent_id == "agent_c", "第2个应是agent_c (priority=100)"
    assert selected[2].agent_id == "agent_b", "第3个应是agent_b (priority=150, 字典序最小)"
