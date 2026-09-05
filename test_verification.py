"""快速功能验证测试 - 验证5个核心模块的基本功能"""

import sys
import asyncio
sys.path.insert(0, 'src')

from core.agent_context import AgentContext, ContextManager
from core.mention_matcher import MentionMatcher
from core.agent_status import AgentStatus, AgentState, AgentStatusManager
from core.retry_policy import RetryPolicy, RetryPolicyBuilder
from core.token_tracker import AgentTokenUsage, TokenTracker
from core.models import AgentConfig, Message


def test_agent_context():
    """测试Agent上下文管理"""
    print("\n🧪 测试1: Agent上下文管理")

    ctx_manager = ContextManager()

    # 创建两个Agent上下文
    ctx1 = ctx_manager.get_agent_context("researcher")
    ctx2 = ctx_manager.get_agent_context("coder")

    # 设置状态
    ctx1.set_state("key", "value1")
    ctx2.set_state("key", "value2")

    # 验证隔离
    assert ctx1.get_state("key") == "value1"
    assert ctx2.get_state("key") == "value2"
    assert ctx1.get_state("key") != ctx2.get_state("key")

    print("  ✅ Agent上下文隔离正常")
    print(f"  ✅ 创建了 {len(ctx_manager.get_all_contexts())} 个上下文")


def test_mention_matcher():
    """测试@mention匹配"""
    print("\n🧪 测试2: @mention智能匹配")

    agents = [
        AgentConfig(agent_id="researcher", name="Researcher", role="研究员", system_prompt="", model_id="claude-sonnet-5"),
        AgentConfig(agent_id="coder", name="Coder", role="编码员", system_prompt="", model_id="claude-sonnet-5"),
        AgentConfig(agent_id="reviewer", name="Code Reviewer", role="代码审查员", system_prompt="", model_id="claude-sonnet-5"),
    ]

    # 测试精确匹配
    result = MentionMatcher.match_agent(agents, "researcher")
    assert result is not None
    assert result.agent_id == "researcher"
    print("  ✅ 精确匹配: 'researcher' -> researcher")

    # 测试前缀匹配
    result = MentionMatcher.match_agent(agents, "res")
    assert result is not None
    assert result.agent_id == "researcher"
    print("  ✅ 前缀匹配: 'res' -> researcher")

    # 测试包含匹配
    result = MentionMatcher.match_agent(agents, "search")
    assert result is not None
    assert result.agent_id == "researcher"
    print("  ✅ 包含匹配: 'search' -> researcher")

    # 测试模糊匹配
    result = MentionMatcher.match_agent(agents, "researher")  # 拼写错误
    assert result is not None
    assert result.agent_id == "researcher"
    print("  ✅ 模糊匹配: 'researher' -> researcher")

    # 测试无匹配
    result = MentionMatcher.match_agent(agents, "xyz")
    assert result is None
    print("  ✅ 无匹配: 'xyz' -> None")


def test_agent_status():
    """测试Agent状态管理"""
    print("\n🧪 测试3: Agent状态追踪")

    status_mgr = AgentStatusManager()

    # 标记为PENDING
    status_mgr.mark_pending("agent1")
    assert status_mgr.get_status("agent1").status == AgentStatus.PENDING
    print("  ✅ 状态: PENDING")

    # 标记为RUNNING
    status_mgr.mark_running("agent1")
    assert status_mgr.get_status("agent1").status == AgentStatus.RUNNING
    print("  ✅ 状态: RUNNING")

    # 标记为COMPLETED
    status_mgr.mark_completed("agent1", input_tokens=100, output_tokens=200)
    state = status_mgr.get_status("agent1")
    assert state.status == AgentStatus.COMPLETED
    assert state.total_tokens == 300
    print("  ✅ 状态: COMPLETED (300 tokens)")

    # 测试摘要
    summary = status_mgr.get_summary()
    assert summary["completed"] == 1
    print(f"  ✅ 摘要: {summary}")


async def test_retry_policy():
    """测试重试策略"""
    print("\n🧪 测试4: 智能重试机制")

    retry_policy = RetryPolicy(max_retries=3, base_delay=0.1)

    # 测试成功情况
    call_count = [0]

    async def success_func():
        call_count[0] += 1
        return "success"

    result = await retry_policy.execute_with_retry(success_func)
    assert result == "success"
    assert call_count[0] == 1
    print("  ✅ 首次成功: 调用1次")

    # 测试重试后成功
    call_count = [0]

    async def retry_then_success():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ConnectionError("网络错误")
        return "success"

    result = await retry_policy.execute_with_retry(retry_then_success)
    assert result == "success"
    assert call_count[0] == 3
    print("  ✅ 重试成功: 调用3次（2次重试）")

    # 测试不可重试错误
    async def non_retryable_error():
        raise ValueError("参数错误")

    try:
        await retry_policy.execute_with_retry(non_retryable_error)
        assert False, "应该抛出异常"
    except ValueError:
        print("  ✅ 不可重试错误: 立即抛出")


def test_token_tracker():
    """测试Token追踪"""
    print("\n🧪 测试5: Token追踪与成本计算")

    tracker = TokenTracker()

    # 记录使用
    tracker.record_usage(AgentTokenUsage(
        agent_id="researcher",
        model="claude-sonnet-5",
        input_tokens=1000,
        output_tokens=2000
    ))

    tracker.record_usage(AgentTokenUsage(
        agent_id="coder",
        model="claude-sonnet-5",
        input_tokens=500,
        output_tokens=1500
    ))

    # 获取统计
    stats = tracker.get_session_stats()

    assert stats["total_input_tokens"] == 1500
    assert stats["total_output_tokens"] == 3500
    assert stats["total_tokens"] == 5000
    assert stats["total_cost_usd"] > 0

    print(f"  ✅ 总Token: {stats['total_tokens']}")
    print(f"  ✅ 总成本: ${stats['total_cost_usd']:.4f}")
    print(f"  ✅ Agent数: {len(stats['by_agent'])}")

    # 测试Agent成本
    researcher_cost = tracker.get_agent_cost("researcher")
    assert researcher_cost > 0
    print(f"  ✅ researcher成本: ${researcher_cost:.4f}")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 开始功能验证测试")
    print("=" * 60)

    try:
        test_agent_context()
        test_mention_matcher()
        test_agent_status()
        await test_retry_policy()
        test_token_tracker()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！5个核心模块功能正常")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
