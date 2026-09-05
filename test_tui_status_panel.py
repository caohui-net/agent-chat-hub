#!/usr/bin/env python3
"""测试TUI状态面板显示"""

import asyncio
import time
from pathlib import Path

from src.core.agent_status import AgentStatus, AgentStatusManager
from src.core.token_tracker import TokenTracker, AgentTokenUsage


def test_status_display():
    """测试状态显示逻辑"""
    print("=" * 60)
    print("🧪 测试Agent状态面板显示逻辑")
    print("=" * 60)

    # 1. 创建状态管理器
    status_manager = AgentStatusManager()
    print("\n✅ 创建AgentStatusManager")

    # 2. 模拟3个Agent的不同状态
    print("\n📝 模拟Agent状态:")

    # Agent 1: RUNNING
    status_manager.mark_running("gemini-pro")
    print("   • gemini-pro: RUNNING")

    # Agent 2: COMPLETED
    status_manager.mark_running("claude-sonnet")
    time.sleep(0.1)
    status_manager.mark_completed("claude-sonnet", output_tokens=450)
    print("   • claude-sonnet: COMPLETED (450 tokens)")

    # Agent 3: ERROR
    status_manager.mark_running("codex")
    time.sleep(0.05)
    status_manager.mark_error("codex", "API超时")
    print("   • codex: ERROR (API超时)")

    # 3. 获取所有状态并格式化显示
    print("\n" + "=" * 60)
    print("📊 状态面板显示预览")
    print("=" * 60)

    statuses = status_manager.get_all_statuses()

    for agent_id, state in statuses.items():
        # 状态图标
        icon = {
            AgentStatus.PENDING: "⏳",
            AgentStatus.RUNNING: "⚙️",
            AgentStatus.COMPLETED: "✅",
            AgentStatus.ERROR: "❌",
        }.get(state.status, "❓")

        # 计算耗时
        duration = ""
        if state.end_time and state.start_time:
            elapsed = state.end_time - state.start_time
            duration = f" ({elapsed:.1f}s)"
        elif state.start_time and state.status == AgentStatus.RUNNING:
            elapsed = time.time() - state.start_time
            duration = f" ({elapsed:.1f}s...)"

        # Token信息
        token_info = ""
        if state.total_tokens > 0:
            token_info = f" | {state.total_tokens} tokens"

        # 错误信息
        error_info = ""
        if state.error:
            error_info = f" | ⚠️ {state.error[:50]}"

        # 显示
        print(f"{icon} {agent_id}: {state.status.value}{duration}{token_info}{error_info}")

    print()


def test_token_stats_display():
    """测试Token统计显示逻辑"""
    print("=" * 60)
    print("🧪 测试Token统计面板显示逻辑")
    print("=" * 60)

    # 1. 创建Token追踪器
    tracker = TokenTracker()
    print("\n✅ 创建TokenTracker")

    # 2. 模拟Token使用
    print("\n📝 模拟Token使用:")

    tracker.record_usage(AgentTokenUsage(
        agent_id="gemini-pro",
        model="gemini-pro",
        input_tokens=100,
        output_tokens=200
    ))
    print("   • gemini-pro: 100 + 200 = 300 tokens")

    tracker.record_usage(AgentTokenUsage(
        agent_id="claude-sonnet",
        model="claude-sonnet-5",
        input_tokens=150,
        output_tokens=450
    ))
    print("   • claude-sonnet: 150 + 450 = 600 tokens")

    # 3. 获取统计并格式化显示
    print("\n" + "=" * 60)
    print("💰 Token统计面板显示预览")
    print("=" * 60)

    stats = tracker.get_session_stats()

    print(f"\n📥 输入: {stats['total_input_tokens']:,} tokens")
    print(f"📤 输出: {stats['total_output_tokens']:,} tokens")
    print(f"📊 总计: {stats['total_tokens']:,} tokens")
    print(f"💵 成本: ${stats['total_cost_usd']:.4f}")

    if stats['by_agent']:
        print("\n按Agent统计:")
        for agent_id, agent_stats in stats['by_agent'].items():
            print(
                f"  • {agent_id}: "
                f"{agent_stats['input']} + {agent_stats['output']} = "
                f"{agent_stats['input'] + agent_stats['output']} tokens "
                f"(${agent_stats['cost']:.4f})"
            )

    print()


if __name__ == "__main__":
    test_status_display()
    print("\n")
    test_token_stats_display()

    print("=" * 60)
    print("✅ 所有测试完成")
    print("=" * 60)
