#!/usr/bin/env python3
"""
集成测试 - 验证5项Agent交互增强功能
"""
import asyncio
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.agent_context import ContextManager
from src.core.agent_status import AgentStatusManager, AgentStatus
from src.core.token_tracker import TokenTracker, AgentTokenUsage
from src.core.retry_policy import RetryPolicy
from src.core.mention_matcher import MentionMatcher
from src.core.models import AgentConfig


async def test_agent_context():
    """测试Agent上下文隔离"""
    print("\n🧪 测试1: Agent上下文隔离")

    context_manager = ContextManager()

    # 为两个Agent创建独立上下文
    ctx1 = context_manager.get_agent_context("agent1")
    ctx2 = context_manager.get_agent_context("agent2")

    # 验证隔离
    ctx1.state["key"] = "value1"
    ctx2.state["key"] = "value2"

    assert ctx1.state["key"] == "value1"
    assert ctx2.state["key"] == "value2"
    assert ctx1.agent_id == "agent1"
    assert ctx2.agent_id == "agent2"

    print("✅ Agent上下文隔离成功")


async def test_agent_status():
    """测试Agent状态追踪"""
    print("\n🧪 测试2: Agent状态追踪")

    status_manager = AgentStatusManager()

    # 标记运行
    status_manager.mark_running("agent1")
    status = status_manager.get_status("agent1")
    assert status.status == AgentStatus.RUNNING
    assert status.start_time is not None

    # 标记完成
    await asyncio.sleep(0.1)  # 模拟执行时间
    status_manager.mark_completed("agent1", output_tokens=500)
    status = status_manager.get_status("agent1")
    assert status.status == AgentStatus.COMPLETED
    assert status.output_tokens == 500
    assert status.elapsed_seconds > 0

    print(f"✅ Agent状态追踪成功 (执行时间: {status.elapsed_seconds:.3f}s)")


async def test_token_tracker():
    """测试Token追踪"""
    print("\n🧪 测试3: Token追踪与成本计算")

    tracker = TokenTracker()

    # 记录使用
    usage1 = AgentTokenUsage(
        agent_id="agent1",
        model="claude-sonnet-5",
        input_tokens=100,
        output_tokens=500
    )
    tracker.record_usage(usage1)

    usage2 = AgentTokenUsage(
        agent_id="agent2",
        model="claude-opus-4",
        input_tokens=200,
        output_tokens=800
    )
    tracker.record_usage(usage2)

    # 获取统计
    stats = tracker.get_session_stats()
    assert stats["total_input_tokens"] == 300
    assert stats["total_output_tokens"] == 1300
    assert stats["total_tokens"] == 1600
    assert stats["total_cost_usd"] > 0

    print(f"✅ Token追踪成功 (总成本: ${stats['total_cost_usd']:.4f})")


async def test_retry_policy():
    """测试重试策略"""
    print("\n🧪 测试4: 智能重试策略")

    retry_policy = RetryPolicy(max_retries=3, base_delay=0.1)

    # 模拟可重试的失败
    attempts = 0

    async def flaky_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Network timeout")
        return "success"

    result = await retry_policy.execute_with_retry(flaky_operation)
    assert result == "success"
    assert attempts == 3

    print(f"✅ 重试策略成功 (重试{attempts-1}次后成功)")


def test_mention_matcher():
    """测试@mention智能匹配"""
    print("\n🧪 测试5: @mention智能匹配")

    # 创建测试agents
    agents = [
        AgentConfig(
            agent_id="researcher",
            name="研究员",
            model_id="claude-sonnet-5",
            role="researcher",
            active=True
        ),
        AgentConfig(
            agent_id="code_reviewer",
            name="代码审查员",
            model_id="claude-sonnet-5",
            role="reviewer",
            active=True
        ),
        AgentConfig(
            agent_id="writer",
            name="文档编写员",
            model_id="claude-sonnet-5",
            role="writer",
            active=True
        ),
    ]

    # 测试各种匹配
    tests = [
        ("research", "researcher"),      # 前缀匹配
        ("reviewer", "code_reviewer"),   # 包含匹配
        ("write", "writer"),             # 前缀匹配
        ("研究", "researcher"),          # 模糊匹配name
    ]

    for mention, expected in tests:
        matched = MentionMatcher.match_agent(agents, mention)
        assert matched is not None, f"未能匹配 '{mention}'"
        assert matched.agent_id == expected, f"匹配错误: 期望{expected}, 实际{matched.agent_id}"
        print(f"  ✓ '@{mention}' → {matched.agent_id} ({matched.name})")

    print("✅ @mention智能匹配成功")


async def main():
    """运行所有集成测试"""
    print("=" * 60)
    print("🚀 开始集成测试 - 5项Agent交互增强")
    print("=" * 60)

    try:
        # 运行所有测试
        await test_agent_context()
        await test_agent_status()
        await test_token_tracker()
        await test_retry_policy()
        test_mention_matcher()

        print("\n" + "=" * 60)
        print("🎉 所有集成测试通过！")
        print("=" * 60)
        print("\n✅ 5项功能已验证:")
        print("  1. Agent上下文隔离")
        print("  2. 实时状态追踪")
        print("  3. Token追踪与成本计算")
        print("  4. 智能重试策略")
        print("  5. @mention智能匹配")
        print("\n🚀 可以开始使用新功能！")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
