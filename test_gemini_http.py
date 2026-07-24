#!/usr/bin/env python3
"""
测试Gemini HTTP API改进效果
重点验证：多轮对话记忆保持
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import ConfigManager
from src.agents.executor import AgentExecutor
from src.core.models import Message


async def test_gemini_multiturn():
    """测试Gemini多轮对话（关键测试）"""
    print("\n" + "="*60)
    print("测试2：多轮对话（验证对话记忆）")
    print("="*60)

    # 指定项目配置目录
    config_dir = project_root / "config"
    config_manager = ConfigManager(config_dir=config_dir)
    print(f"配置目录: {config_manager.config_dir}")
    config_manager.load_configs()
    print(f"已加载的agents: {list(config_manager.agents.keys())}")

    executor = AgentExecutor(config_manager)

    # 获取配置
    agent_config = config_manager.get_agent("agent_gemini")
    if not agent_config:
        print("❌ 未找到agent_gemini配置")
        return False

    # 第一轮：建立上下文
    messages_round1 = [
        Message(
            role="user",
            content="我的名字叫小明，请记住这个信息。"
        )
    ]

    try:
        print("\n第1轮对话：")
        print(f"用户: {messages_round1[0].content}")

        response1 = await executor.execute(agent_config, messages_round1)
        print(f"Gemini: {response1}")

        # 第二轮：测试记忆
        messages_round2 = [
            Message(role="user", content="我的名字叫小明，请记住这个信息。"),
            Message(role="assistant", content=response1),
            Message(role="user", content="请问我的名字是什么？")
        ]

        print("\n第2轮对话：")
        print(f"用户: {messages_round2[2].content}")

        response2 = await executor.execute(agent_config, messages_round2)
        print(f"Gemini: {response2}")

        # 验证：响应中是否包含"小明"
        if "小明" in response2:
            print("\n✅ 测试通过：Gemini成功记住了对话历史")
            return True
        else:
            print("\n❌ 测试失败：Gemini未能记住对话历史")
            print(f"   期望响应包含：小明")
            print(f"   实际响应：{response2}")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_basic():
    """测试Gemini基本响应"""
    print("\n" + "="*60)
    print("测试1：基本响应")
    print("="*60)

    # 指定项目配置目录
    config_dir = project_root / "config"
    config_manager = ConfigManager(config_dir=config_dir)
    config_manager.load_configs()

    executor = AgentExecutor(config_manager)

    agent_config = config_manager.get_agent("agent_gemini")
    if not agent_config:
        print("❌ 未找到agent_gemini配置")
        return False

    messages = [
        Message(role="user", content="你好，请简单介绍一下你自己。")
    ]

    try:
        print(f"\n用户: {messages[0].content}")
        response = await executor.execute(agent_config, messages)
        print(f"Gemini: {response}")

        if response and len(response) > 10:
            print(f"\n✅ 测试通过（响应长度：{len(response)}字符）")
            return True
        else:
            print("\n❌ 测试失败：响应为空或过短")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("开始测试Gemini HTTP API改进...")

    results = []

    # 测试1：基本响应
    result1 = await test_gemini_basic()
    results.append(("基本响应", result1))

    # 测试2：多轮对话（关键）
    result2 = await test_gemini_multiturn()
    results.append(("多轮对话", result2))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\n通过率: {passed_count}/{total_count} ({passed_count*100//total_count}%)")

    if all(p for _, p in results):
        print("\n🎉 所有测试通过！Gemini HTTP改进成功！")
        return 0
    else:
        print("\n⚠️  部分测试失败，需要进一步调试")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
