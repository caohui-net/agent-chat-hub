"""
测试响应协调器 - 验证6条响应控制规则
"""
import pytest
from time import sleep

from src.agents.coordinator import (
    ResponseCoordinator,
    BudgetLimits,
    StopReason,
)
from src.core.models import AgentConfig


@pytest.fixture
def coordinator():
    """创建测试用的协调器"""
    return ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=3,
            max_calls_per_round=3,
            max_tokens=12000,
            timeout_seconds=5.0  # 测试用较短超时
        )
    )


@pytest.fixture
def sample_agents():
    """创建测试用的agents"""
    return [
        AgentConfig(
            agent_id="agent_c",
            name="Agent C",
            role="assistant",
            model_id="model1",
            priority=200,
            active=True
        ),
        AgentConfig(
            agent_id="agent_a",
            name="Agent A",
            role="assistant",
            model_id="model1",
            priority=100,
            active=True
        ),
        AgentConfig(
            agent_id="agent_b",
            name="Agent B",
            role="assistant",
            model_id="model1",
            priority=100,
            active=True
        ),
        AgentConfig(
            agent_id="agent_d",
            name="Agent D (Inactive)",
            role="assistant",
            model_id="model1",
            priority=50,
            active=False  # 不活跃
        ),
    ]


# ==================== Rule 1: Qualification ====================

def test_qualify_agents_filters_active_only(coordinator, sample_agents):
    """Rule 1: 资格判定 - 仅选择active=True的agents"""
    qualified = coordinator.qualify_agents(sample_agents)

    # 应该过滤掉agent_d（active=False）
    assert len(qualified) == 3
    agent_ids = [a.agent_id for a in qualified]
    assert "agent_d" not in agent_ids
    assert "agent_a" in agent_ids
    assert "agent_b" in agent_ids
    assert "agent_c" in agent_ids


def test_qualify_agents_respects_max_limit(coordinator, sample_agents):
    """Rule 1: 资格判定 - 遵守最大agent数限制"""
    # 只允许2个agents
    qualified = coordinator.qualify_agents(sample_agents, max_agents=2)
    assert len(qualified) == 2


# ==================== Rule 2: Ordering ====================

def test_sort_agents_by_priority_then_id(coordinator, sample_agents):
    """Rule 2: 排序 - 优先级升序 + agent_id字典序"""
    active_agents = [a for a in sample_agents if a.active]
    sorted_agents = coordinator.sort_agents(active_agents)

    # 预期顺序：
    # 1. agent_a (priority=100, id='agent_a')
    # 2. agent_b (priority=100, id='agent_b')
    # 3. agent_c (priority=200, id='agent_c')
    assert sorted_agents[0].agent_id == "agent_a"
    assert sorted_agents[1].agent_id == "agent_b"
    assert sorted_agents[2].agent_id == "agent_c"


def test_sort_agents_priority_order(coordinator):
    """Rule 2: 排序 - 验证优先级升序"""
    agents = [
        AgentConfig(agent_id="high", name="High", role="a", model_id="m", priority=300, active=True),
        AgentConfig(agent_id="low", name="Low", role="a", model_id="m", priority=100, active=True),
        AgentConfig(agent_id="mid", name="Mid", role="a", model_id="m", priority=200, active=True),
    ]
    sorted_agents = coordinator.sort_agents(agents)

    # 应该按priority升序
    assert sorted_agents[0].agent_id == "low"
    assert sorted_agents[1].agent_id == "mid"
    assert sorted_agents[2].agent_id == "high"


# ==================== Rule 3: Deduplication ====================

def test_deduplication_prevents_duplicate_calls(coordinator, sample_agents):
    """Rule 3: 去重 - (session, round, agent) 三元组唯一"""
    coordinator.start_round(session_id="session1", round_num=1)

    # 首次调用agent_a
    assert not coordinator.is_duplicate_call("agent_a")
    coordinator.record_call("agent_a", tokens_used=100)

    # 再次调用agent_a应该被识别为重复
    assert coordinator.is_duplicate_call("agent_a")

    # 调用agent_b不应该重复
    assert not coordinator.is_duplicate_call("agent_b")


def test_deduplication_across_rounds(coordinator):
    """Rule 3: 去重 - 不同轮次的相同agent不算重复"""
    # Round 1
    coordinator.start_round(session_id="session1", round_num=1)
    coordinator.record_call("agent_a", tokens_used=100)
    assert coordinator.is_duplicate_call("agent_a")

    # Round 2 - 应该可以再次调用agent_a
    coordinator.start_round(session_id="session1", round_num=2)
    assert not coordinator.is_duplicate_call("agent_a")


def test_deduplication_across_sessions(coordinator):
    """Rule 3: 去重 - 不同session的相同agent不算重复"""
    # Session 1
    coordinator.start_round(session_id="session1", round_num=1)
    coordinator.record_call("agent_a", tokens_used=100)

    # Session 2 - 应该可以再次调用agent_a
    coordinator.start_round(session_id="session2", round_num=1)
    assert not coordinator.is_duplicate_call("agent_a")


# ==================== Rule 4: Cancellation ====================

def test_cancellation_marks_round_cancelled(coordinator):
    """Rule 4: 取消 - 取消后标记cancelled=True"""
    coordinator.start_round(session_id="session1", round_num=1)
    assert not coordinator.current_round.cancelled

    coordinator.cancel_round()
    assert coordinator.current_round.cancelled
    assert coordinator.current_round.stop_reason == StopReason.USER_CANCEL


def test_cancellation_stops_agent_selection(coordinator, sample_agents):
    """Rule 4: 取消 - 取消后禁止新的agent调用"""
    coordinator.start_round(session_id="session1", round_num=1)
    coordinator.cancel_round()

    selected, stop_reason = coordinator.select_agents(sample_agents)

    # 应该返回空列表和USER_CANCEL原因
    assert len(selected) == 0
    assert stop_reason == StopReason.USER_CANCEL


# ==================== Rule 5: Budget ====================

def test_budget_max_calls_limit(coordinator, sample_agents):
    """Rule 5: 预算 - 最大调用次数限制"""
    coordinator.start_round(session_id="session1", round_num=1)

    # 记录3次调用（达到max_calls_per_round=3）
    coordinator.record_call("agent_a", tokens_used=100)
    coordinator.record_call("agent_b", tokens_used=100)
    coordinator.record_call("agent_c", tokens_used=100)

    # 检查预算应该返回MAX_CALLS
    stop_reason = coordinator.check_budget()
    assert stop_reason == StopReason.MAX_CALLS


def test_budget_max_tokens_limit(coordinator, sample_agents):
    """Rule 5: 预算 - 最大token数限制"""
    coordinator.start_round(session_id="session1", round_num=1)

    # 记录12000 tokens（达到max_tokens=12000）
    coordinator.record_call("agent_a", tokens_used=12000)

    # 检查预算应该返回BUDGET_EXCEEDED
    stop_reason = coordinator.check_budget()
    assert stop_reason == StopReason.BUDGET_EXCEEDED


def test_budget_timeout_limit(coordinator):
    """Rule 5: 预算 - 超时限制"""
    # 使用较短的超时时间（0.1秒）
    coordinator.budget_limits.timeout_seconds = 0.1
    coordinator.start_round(session_id="session1", round_num=1)

    # 等待超过超时时间
    sleep(0.15)

    # 检查预算应该返回TIMEOUT
    stop_reason = coordinator.check_budget()
    assert stop_reason == StopReason.TIMEOUT


def test_budget_within_limits(coordinator):
    """Rule 5: 预算 - 在限制范围内返回None"""
    coordinator.start_round(session_id="session1", round_num=1)

    # 记录少量调用
    coordinator.record_call("agent_a", tokens_used=100)

    # 检查预算应该返回None（未超限）
    stop_reason = coordinator.check_budget()
    assert stop_reason is None


# ==================== Rule 6: Stop ====================

def test_stop_on_no_agents(coordinator):
    """Rule 6: 停止 - 无可用agents时停止"""
    coordinator.start_round(session_id="session1", round_num=1)

    # 选择空列表
    selected, stop_reason = coordinator.select_agents([])
    assert len(selected) == 0
    assert stop_reason == StopReason.NO_AGENTS


def test_stop_on_all_duplicates(sample_agents):
    """Rule 6: 停止 - 所有agents都已调用时停止"""
    # 使用更大的max_calls避免触发预算限制
    coord = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=3,
            max_calls_per_round=10,  # 足够大，不会先触发
            max_tokens=12000,
            timeout_seconds=5.0
        )
    )
    coord.start_round(session_id="session1", round_num=1)

    # 记录所有active agents的调用
    coord.record_call("agent_a", tokens_used=100)
    coord.record_call("agent_b", tokens_used=100)
    coord.record_call("agent_c", tokens_used=100)

    # 再次选择应该返回ROUND_COMPLETE
    selected, stop_reason = coord.select_agents(sample_agents)
    assert len(selected) == 0
    assert stop_reason == StopReason.ROUND_COMPLETE


def test_should_stop_checks_all_conditions(coordinator):
    """Rule 6: 停止 - should_stop检查所有停止条件"""
    # 无轮次时应该停止
    should_stop, reason = coordinator.should_stop()
    assert should_stop is True
    assert reason == StopReason.NO_AGENTS

    # 正常运行时不应停止
    coordinator.start_round(session_id="session1", round_num=1)
    should_stop, reason = coordinator.should_stop()
    assert should_stop is False
    assert reason is None

    # 取消后应该停止
    coordinator.cancel_round()
    should_stop, reason = coordinator.should_stop()
    assert should_stop is True
    assert reason == StopReason.USER_CANCEL


# ==================== 集成测试 ====================

def test_select_agents_integration(coordinator, sample_agents):
    """集成测试：select_agents整合所有规则"""
    coordinator.start_round(session_id="session1", round_num=1)

    # 首次选择
    selected, stop_reason = coordinator.select_agents(sample_agents)

    # 应该选出3个active agents，按排序规则
    assert len(selected) == 3
    assert stop_reason is None
    assert selected[0].agent_id == "agent_a"  # priority=100, id='agent_a'
    assert selected[1].agent_id == "agent_b"  # priority=100, id='agent_b'
    assert selected[2].agent_id == "agent_c"  # priority=200, id='agent_c'

    # 记录agent_a的调用
    coordinator.record_call("agent_a", tokens_used=1000)

    # 再次选择，agent_a应该被去重
    selected, stop_reason = coordinator.select_agents(sample_agents)
    assert len(selected) == 2
    assert selected[0].agent_id == "agent_b"
    assert selected[1].agent_id == "agent_c"


def test_get_round_stats(coordinator):
    """测试轮次统计信息"""
    coordinator.start_round(session_id="session1", round_num=1)
    coordinator.record_call("agent_a", tokens_used=1000)
    coordinator.record_call("agent_b", tokens_used=2000)

    stats = coordinator.get_round_stats()

    assert stats["round_num"] == 1
    assert stats["session_id"] == "session1"
    assert stats["total_calls"] == 2
    assert stats["total_tokens"] == 3000
    assert stats["cancelled"] is False
    assert "budget_usage" in stats



