#!/usr/bin/env python3
"""完整流程调试：模拟用户输入 @gemini 在不在？"""

import asyncio
import json
from pathlib import Path
from src.core.models import AgentConfig, SessionConfig
from src.agents.session import SessionManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor

async def main():
    print("=" * 60)
    print("🔍 完整流程调试：@gemini 在不在？")
    print("=" * 60)

    # 1. 配置目录
    config_dir = Path.home() / ".agent-chat-hub"

    print("\n步骤1 - 初始化ConfigManager")
    from src.core.config import ConfigManager
    from src.agents.coordinator import BudgetLimits

    config_manager = ConfigManager(config_dir=config_dir)
    config_manager.load_configs()
    print(f"  已加载 {len(config_manager.agents)} 个agents")
    print(f"  已加载 {len(config_manager.models)} 个models")

    # 2. 显示agents
    active_agents = [a for a in config_manager.agents.values() if a.active]
    print(f"\n步骤2 - {len(active_agents)} 个active agents:")
    for agent in active_agents:
        print(f"  - {agent.agent_id} ({agent.name})")

    # 3. 创建组件
    print("\n步骤3 - 创建组件")

    coordinator = ResponseCoordinator(
        budget_limits=BudgetLimits(
            max_agents=3,
            max_calls_per_round=3,
            max_tokens=12000,
            timeout_seconds=120.0
        )
    )
    print(f"  ✅ ResponseCoordinator创建成功")

    executor = AgentExecutor(config_manager)
    print(f"  ✅ AgentExecutor创建成功")

    session_manager = SessionManager(
        config_manager=config_manager,
        coordinator=coordinator,
        executor=executor,
        session_dir=config_dir / "sessions"
    )
    print(f"  ✅ SessionManager创建成功")

    # 4. 创建会话
    print("\n步骤4 - 创建新会话")
    session_id = session_manager.create_session("测试会话")
    print(f"  会话ID: {session_id}")

    # 5. 模拟用户输入
    user_input = "@gemini 在不在？"
    print(f"\n步骤5 - 用户输入: {user_input}")

    try:
        # 6. 处理输入
        print("\n步骤6 - 处理输入...")
        responses = await session_manager.process_user_input(user_input)

        # 7. 显示结果
        print("\n步骤7 - 响应结果:")
        if responses:
            print(f"  收到 {len(responses)} 个响应:")
            for i, response_text in enumerate(responses, 1):
                print(f"\n  响应 {i}:")
                print(f"    {response_text[:200]}...")
        else:
            print("  ⚠️ 没有收到任何响应")

        # 8. 显示消息历史
        print("\n步骤8 - 消息历史:")
        history = session_manager.get_message_history()
        for msg in history:
            print(f"  {msg}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
