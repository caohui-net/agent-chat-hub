#!/usr/bin/env python3
"""TUI集成测试 - 测试完整的TUI交互流程"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.session import SessionManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.core.config import ConfigManager


async def test_tui_workflow():
    """模拟TUI的完整工作流程"""
    print("=" * 60)
    print("🧪 TUI集成测试 - 完整工作流程")
    print("=" * 60)

    # 1. 初始化（模拟TUI启动）
    print("\n📝 步骤1: 初始化（模拟TUI启动）")
    project_root = Path(__file__).parent
    config_dir = project_root / "config"

    config_manager = ConfigManager(config_dir=config_dir)
    config_manager.load_configs()

    coordinator = ResponseCoordinator()
    executor = AgentExecutor(config_manager)
    session_manager = SessionManager(config_manager, coordinator, executor)

    # 创建会话
    session_manager.create_session("TUI集成测试会话")
    print("   ✅ 初始化完成")

    # 2. 检查可用Agents
    print("\n📝 步骤2: 检查可用Agents")
    available_agents = config_manager.list_agents(active_only=True)
    print(f"   ✅ 找到 {len(available_agents)} 个可用Agent:")
    for agent in available_agents[:3]:  # 只显示前3个
        print(f"      • {agent.agent_id} ({agent.name})")

    if not available_agents:
        print("   ❌ 没有可用Agent，测试终止")
        return

    # 3. 模拟用户输入（带@mention）
    print("\n📝 步骤3: 模拟用户输入")
    test_messages = [
        "@gemini 你好",
        "@claude 帮我写个Python函数",
        "继续讨论刚才的话题",
    ]

    # Mock executor的execute方法
    original_execute = session_manager.executor.execute

    async def mock_execute(agent_config, messages):
        """Mock的execute方法"""
        await asyncio.sleep(0.1)
        return f"[{agent_config.name}] 这是对消息 '{messages[-1].content[:20]}...' 的Mock响应"

    session_manager.executor.execute = mock_execute

    try:
        for i, user_input in enumerate(test_messages, 1):
            print(f"\n--- 消息 {i} ---")
            print(f"👤 用户输入: {user_input}")

            # 调用process_user_input（这是TUI的主要入口）
            responses = await session_manager.process_user_input(user_input)

            print(f"🤖 收到 {len(responses)} 个响应:")
            for resp in responses:
                print(f"   {resp}")

            # 检查消息历史
            history = session_manager.get_message_history()
            print(f"📝 当前消息历史: {len(history)} 条")

    finally:
        session_manager.executor.execute = original_execute

    # 4. 验证最终状态
    print("\n" + "=" * 60)
    print("📊 最终状态验证")
    print("=" * 60)

    final_history = session_manager.get_message_history()
    print(f"\n消息历史 ({len(final_history)} 条):")
    for msg in final_history:
        print(f"  {msg[:80]}...")

    # 检查状态管理器
    if hasattr(session_manager, 'status_manager'):
        print("\n✅ AgentStatusManager已集成")
        statuses = session_manager.status_manager.get_all_statuses()
        print(f"   记录了 {len(statuses)} 个Agent状态")

    if hasattr(session_manager, 'token_tracker'):
        print("\n✅ TokenTracker已集成")
        stats = session_manager.token_tracker.get_session_stats()
        print(f"   总Token: {stats['total_tokens']}")

    if hasattr(session_manager, 'context_manager'):
        print("\n✅ ContextManager已集成")

    print("\n" + "=" * 60)
    print("✅ TUI集成测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tui_workflow())
