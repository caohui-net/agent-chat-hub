#!/usr/bin/env python3
"""测试已实现的5项技术集成 - 使用mock避免API调用"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator, BudgetLimits
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager

async def main():
    print("=" * 60)
    print("🧪 测试5项技术集成（Mock模式）")
    print("=" * 60)

    # 1. 初始化
    config_dir = Path.home() / ".agent-chat-hub"
    config_manager = ConfigManager(config_dir=config_dir)
    config_manager.load_configs()

    print(f"\n✅ 已加载 {len(config_manager.agents)} 个agents")
    print(f"✅ 已加载 {len(config_manager.models)} 个models")

    # 2. 创建组件
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

    print(f"\n✅ 所有组件创建成功")

    # 3. 检查集成的5项技术
    print("\n" + "=" * 60)
    print("📋 检查已集成的技术")
    print("=" * 60)

    # ✅ 1. Agent隔离与上下文管理
    print("\n1️⃣ Agent隔离与上下文管理")
    print(f"   ContextManager: {session_manager.context_manager is not None}")
    print(f"   当前上下文数: {len(session_manager.context_manager.contexts)}")

    # ✅ 2. Agent状态追踪
    print("\n2️⃣ Agent状态追踪")
    print(f"   AgentStatusManager: {session_manager.status_manager is not None}")

    # ✅ 3. Token追踪
    print("\n3️⃣ Token追踪")
    print(f"   TokenTracker (SessionManager): {session_manager.token_tracker is not None}")
    print(f"   TokenTracker (Executor): {executor.token_tracker is not None}")

    # ✅ 4. 重试机制
    print("\n4️⃣ 重试机制")
    print(f"   RetryPolicy: {executor.retry_policy is not None}")
    print(f"   最大重试次数: {executor.retry_policy.max_retries}")
    print(f"   基础延迟: {executor.retry_policy.base_delay}s")

    # ✅ 5. @mention增强匹配
    print("\n5️⃣ @mention增强匹配")
    from src.core.mention_matcher import MentionMatcher
    from src.core.mention_parser import parse_mentions

    test_mentions = ["gemini", "claud", "cod"]
    agents_list = list(config_manager.agents.values())

    for mention in test_mentions:
        matched = MentionMatcher.match_agent(agents_list, mention, threshold=0.6)
        if matched:
            print(f"   '@{mention}' -> ✅ {matched.agent_id}")
        else:
            print(f"   '@{mention}' -> ❌ 未匹配")

    # 4. 模拟用户输入（使用mock）
    print("\n" + "=" * 60)
    print("🎭 模拟Agent执行（Mock模式）")
    print("=" * 60)

    session_id = session_manager.create_session("Mock测试会话")
    print(f"\n✅ 会话创建: {session_id}")

    user_input = "@gemini 你好"
    print(f"\n📥 用户输入: {user_input}")

    # Mock executor.execute to avoid real API call
    mock_response = "你好！我是Gemini助手，很高兴为你服务。"

    with patch.object(executor, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = mock_response

        # 处理输入
        print("\n⚙️  处理中...")
        responses = await session_manager.process_user_input(user_input)

        # 显示结果
        print(f"\n✅ 收到 {len(responses)} 个响应")
        for resp in responses:
            print(f"   {resp[:100]}...")

    # 5. 显示统计
    print("\n" + "=" * 60)
    print("📊 统计信息")
    print("=" * 60)

    # Token统计
    stats = session_manager.token_tracker.get_session_stats()
    print(f"\nToken统计:")
    print(f"   总输入: {stats['total_input_tokens']}")
    print(f"   总输出: {stats['total_output_tokens']}")
    print(f"   总计: {stats['total_tokens']}")
    print(f"   估算成本: ${stats['total_cost_usd']:.4f}")

    # Agent状态
    print(f"\nAgent状态:")
    all_statuses = session_manager.status_manager.get_all_statuses()
    for agent_id, status in all_statuses.items():
        print(f"   {agent_id}: {status.status.value}")
        if status.end_time and status.start_time:
            elapsed = status.end_time - status.start_time
            print(f"      耗时: {elapsed:.2f}s")

    print("\n" + "=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
