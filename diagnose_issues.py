#!/usr/bin/env python3
"""诊断脚本 - 测试@mention和消息显示问题"""

import asyncio
from pathlib import Path

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.session import SessionManager
from src.core.config import ConfigManager


async def test_mention_and_display():
    """测试@mention响应和消息显示"""
    print("=" * 60)
    print("🧪 诊断测试：@mention响应 + 消息显示")
    print("=" * 60)

    # 1. 初始化SessionManager
    print("\n📝 步骤1: 初始化SessionManager")
    from src.agents.coordinator import ResponseCoordinator
    from src.agents.executor import AgentExecutor

    # 使用项目根目录的config文件夹
    project_root = Path(__file__).parent
    config_dir = project_root / "config"

    config_manager = ConfigManager(config_dir=config_dir)
    config_manager.load_configs()  # 显式加载配置

    coordinator = ResponseCoordinator()
    executor = AgentExecutor(config_manager)
    session_manager = SessionManager(config_manager, coordinator, executor)
    session_manager.create_session("诊断测试会话")
    print("   ✅ SessionManager初始化完成")

    # 2. 检查可用的Agents
    print("\n📝 步骤2: 检查可用Agents")
    available_agents = config_manager.list_agents(active_only=True)
    if not available_agents:
        print("   ❌ 没有可用的Agent！")
        return

    print(f"   ✅ 找到 {len(available_agents)} 个可用Agent:")
    for agent in available_agents:
        print(f"      • {agent.agent_id} ({agent.name}) - {agent.role}")

    # 3. 测试用户消息添加
    print("\n📝 步骤3: 测试用户消息是否正确添加")
    test_input = "@gemini 你好"
    print(f"   输入: {test_input}")

    # 检查消息历史（添加前）
    history_before = session_manager.get_message_history()
    print(f"   添加前消息数: {len(history_before)}")

    # 模拟添加用户消息（不调用API）
    session_manager.add_message(role="user", content=test_input)

    # 检查消息历史（添加后）
    history_after = session_manager.get_message_history()
    print(f"   添加后消息数: {len(history_after)}")

    if len(history_after) > len(history_before):
        print("   ✅ 用户消息成功添加到历史")
        print(f"   最后一条消息: {history_after[-1]}")
    else:
        print("   ❌ 用户消息未添加！")

    # 4. 测试@mention解析
    print("\n📝 步骤4: 测试@mention解析")
    from src.core.mention_parser import parse_mentions

    mentions = parse_mentions(test_input)
    print(f"   解析到的mentions: {mentions}")

    if mentions:
        print("   ✅ @mention解析成功")
    else:
        print("   ❌ @mention解析失败！")

    # 5. 测试Agent选择
    print("\n📝 步骤5: 测试Agent选择（基于@mention）")

    # 关键：必须先启动一轮对话
    session_manager.coordinator.start_round(
        session_id=session_manager.current_session.session_id,
        round_num=1
    )

    selected_agents, stop_reason = session_manager.coordinator.select_agents(
        available_agents,
        mentions=mentions
    )

    if selected_agents:
        print(f"   ✅ 选择了 {len(selected_agents)} 个Agent:")
        for agent in selected_agents:
            print(f"      • {agent.agent_id} ({agent.name})")
    else:
        print(f"   ❌ 没有选择任何Agent！")
        if stop_reason:
            print(f"      停止原因: {stop_reason.value}")

    # 6. 测试完整流程（Mock响应，不调用真实API）
    print("\n📝 步骤6: 测试完整流程（Mock模式）")
    print("   ⚠️  注意: 使用Mock响应，不调用真实API")

    # Mock executor的execute方法
    original_execute = session_manager.executor.execute

    async def mock_execute(agent_config, messages):
        """Mock的execute方法，返回固定响应"""
        await asyncio.sleep(0.1)  # 模拟延迟
        return f"这是 {agent_config.name} 的Mock响应"

    # 替换为Mock方法
    session_manager.executor.execute = mock_execute

    try:
        # 执行完整流程
        responses = await session_manager.process_user_input("@gemini 测试消息")

        print(f"   返回了 {len(responses)} 个响应:")
        for i, resp in enumerate(responses, 1):
            print(f"      {i}. {resp[:100]}...")

        # 检查消息历史
        final_history = session_manager.get_message_history()
        print(f"\n   最终消息历史 ({len(final_history)} 条):")
        for msg in final_history:
            print(f"      {msg[:100]}...")

        if len(responses) > 0:
            print("\n   ✅ 完整流程测试成功！")
        else:
            print("\n   ❌ 完整流程测试失败 - 没有响应")

    finally:
        # 恢复原始方法
        session_manager.executor.execute = original_execute

    # 7. 诊断结论
    print("\n" + "=" * 60)
    print("📊 诊断结论")
    print("=" * 60)

    issues = []

    # 检查问题1: @mention响应
    if not selected_agents:
        issues.append("❌ 问题1确认: @mention后没有Agent被选中")
    else:
        print("✅ 问题1: @mention选择Agent正常")

    # 检查问题2: 用户消息显示
    if len(history_after) > len(history_before):
        print("✅ 问题2: 用户消息正确添加到历史")
    else:
        issues.append("❌ 问题2确认: 用户消息未添加到历史")

    if issues:
        print("\n发现的问题:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ 所有功能正常工作！")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mention_and_display())
