#!/usr/bin/env python3
"""
测试chat功能是否正常工作
"""
import asyncio
from pathlib import Path

from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator, BudgetLimits
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager


async def test_chat_basic():
    """测试基本的chat功能"""
    print("=" * 60)
    print("测试 1: 基本chat功能")
    print("=" * 60)

    # 配置目录
    config_dir = Path.home() / ".agent-chat-hub"
    config_dir.mkdir(parents=True, exist_ok=True)

    # 初始化
    config_manager = ConfigManager(config_dir=config_dir)
    config_manager.load_configs()

    coordinator = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=3,
            max_calls_per_round=3,
            max_tokens=12000,
            timeout_seconds=120.0
        )
    )

    executor = AgentExecutor(config_manager)

    session_manager = SessionManager(
        config_manager=config_manager,
        coordinator=coordinator,
        executor=executor,
        session_dir=config_dir / "sessions"
    )

    # 创建会话
    session_manager.create_session("测试会话")
    print("✅ 会话创建成功")

    # 列出可用的agents
    agents = config_manager.list_agents()
    print(f"\n📋 可用的Agents ({len(agents)}个):")
    for agent in agents:
        status = "✓ 活跃" if agent.active else "✗ 禁用"
        print(f"  • {agent.name} ({agent.role}) - {status}")

    print("\n" + "=" * 60)
    print("测试 2: 发送消息并获取响应")
    print("=" * 60)

    # 测试发送消息
    test_message = "你好！请简单介绍一下自己"
    print(f"\n📤 发送消息: {test_message}")

    try:
        # 处理消息
        responses = await session_manager.process_user_input(test_message)

        print(f"\n✅ 收到 {len(responses)} 个响应:")
        for i, (agent_config, response, error) in enumerate(responses, 1):
            print(f"\n--- 响应 {i} (来自 {agent_config.name}) ---")
            if error:
                print(f"❌ 错误: {error}")
            else:
                print(f"✅ {response[:200]}..." if len(response) > 200 else f"✅ {response}")

        # 显示消息历史
        print("\n" + "=" * 60)
        print("测试 3: 消息历史")
        print("=" * 60)

        history = session_manager.get_message_history()
        print(f"\n📝 消息历史 ({len(history)}条):")
        for msg in history:
            print(f"  {msg[:100]}..." if len(msg) > 100 else f"  {msg}")

        # 显示状态
        print("\n" + "=" * 60)
        print("测试 4: Agent状态")
        print("=" * 60)

        statuses = session_manager.status_manager.get_all_statuses()
        print(f"\n📊 Agent状态 ({len(statuses)}个):")
        for agent_id, state in statuses.items():
            print(f"  • {agent_id}: {state.status.value}")
            print(f"    - 耗时: {state.elapsed_seconds:.2f}s")
            print(f"    - Token: 输入={state.input_tokens}, 输出={state.output_tokens}")
            if state.error:
                print(f"    - ⚠️ 错误: {state.error}")

        # Token统计
        print("\n" + "=" * 60)
        print("测试 5: Token统计")
        print("=" * 60)

        stats = session_manager.token_tracker.get_session_stats()
        print(f"\n💰 Token统计:")
        print(f"  📥 输入: {stats['total_input_tokens']:,} tokens")
        print(f"  📤 输出: {stats['total_output_tokens']:,} tokens")
        print(f"  📊 总计: {stats['total_tokens']:,} tokens")
        print(f"  💵 成本: ${stats['total_cost_usd']:.4f}")

        if stats['by_agent']:
            print(f"\n按Agent统计:")
            for agent_id, agent_stats in stats['by_agent'].items():
                total = agent_stats['input'] + agent_stats['output']
                print(f"  • {agent_id}: {total} tokens (${agent_stats['cost']:.4f})")

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理
        await executor.aclose()


async def test_mention_functionality():
    """测试@mention功能"""
    print("\n" + "=" * 60)
    print("测试 6: @mention功能")
    print("=" * 60)

    config_dir = Path.home() / ".agent-chat-hub"
    config_manager = ConfigManager(config_dir=config_dir)
    config_manager.load_configs()

    coordinator = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=3,
            max_calls_per_round=3,
            max_tokens=12000,
            timeout_seconds=120.0
        )
    )

    executor = AgentExecutor(config_manager)

    session_manager = SessionManager(
        config_manager=config_manager,
        coordinator=coordinator,
        executor=executor,
        session_dir=config_dir / "sessions"
    )

    session_manager.create_session("测试@mention")

    # 测试不同的@mention格式
    test_cases = [
        "@gemini 你好",
        "@gem 你好",  # 前缀匹配
        "@claude 你好",
        "@clau 你好",  # 前缀匹配
    ]

    print("\n测试不同的@mention格式:")
    for test_msg in test_cases:
        print(f"\n📤 测试: {test_msg}")

        # 解析mentions
        import re
        mentions = re.findall(r'@(\w+)', test_msg)

        agents = config_manager.list_agents()
        from src.core.mention_matcher import MentionMatcher

        for mention in mentions:
            matched_agent = MentionMatcher.match_agent(agents, mention)
            if matched_agent:
                print(f"  ✅ @{mention} → {matched_agent.agent_id} ({matched_agent.name})")
            else:
                print(f"  ❌ @{mention} → 未匹配到Agent")

    await executor.aclose()

    print("\n✅ @mention测试完成")


async def main():
    """运行所有测试"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          Agent Chat Hub - Chat功能测试                       ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # 运行基本功能测试
    success = await test_chat_basic()

    if success:
        # 运行@mention测试
        await test_mention_functionality()

        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║  🎉 所有测试完成！Chat功能工作正常！                         ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print("\n💡 你现在可以运行 'python3 main.py' 启动完整的TUI界面")
        print("   或者继续使用命令行方式与agents交互")
    else:
        print("\n❌ 测试失败，请检查错误信息")


if __name__ == "__main__":
    asyncio.run(main())
