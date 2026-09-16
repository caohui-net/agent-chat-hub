#!/usr/bin/env python3
"""
测试CLI集成功能
验证CLI适配器能否正确调用claude/codex/gemini命令行工具
"""
import asyncio
import sys
from src.core.cli_adapter import get_cli_adapter


async def test_cli_availability():
    """测试CLI工具可用性"""
    print("=== 测试CLI工具可用性 ===\n")

    adapter = get_cli_adapter()

    # 检查可用性
    print("CLI工具检查结果:")
    print(f"  claude CLI: {'✅ 可用' if adapter.available_clis['claude'] else '❌ 不可用'}")
    print(f"  codex CLI:  {'✅ 可用' if adapter.available_clis['codex'] else '❌ 不可用'}")
    print(f"  gemini CLI: {'✅ 可用' if adapter.available_clis['gemini'] else '❌ 不可用'}")

    print("\nProvider检查结果:")
    print(f"  anthropic: {'✅' if adapter.is_available('anthropic') else '❌'}")
    print(f"  openai:    {'✅' if adapter.is_available('openai') else '❌'}")
    print(f"  gemini:    {'✅' if adapter.is_available('gemini') else '❌'}")

    return adapter


async def test_claude_cli_call():
    """测试Claude CLI调用"""
    print("\n=== 测试Claude CLI调用 ===\n")

    adapter = get_cli_adapter()

    if not adapter.is_available("anthropic"):
        print("❌ Claude CLI不可用，跳过测试")
        return False

    try:
        messages = [
            {"role": "user", "content": "请用一句话介绍Python语言"}
        ]

        print("正在调用Claude CLI...")
        response, token_usage = await adapter.call_claude(
            messages=messages,
            system_prompt="你是一个专业的编程助手",
            model="claude-opus-4-8",
            max_tokens=100,
            temperature=1.0
        )

        print("\n✅ 调用成功!")
        print(f"\n响应内容:\n{response}\n")
        print(f"Token使用: {token_usage}")

        return True

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")
        return False


async def test_codex_cli_call():
    """测试Codex CLI调用"""
    print("\n=== 测试Codex CLI调用 ===\n")

    adapter = get_cli_adapter()

    if not adapter.is_available("openai"):
        print("❌ Codex CLI不可用，跳过测试")
        return False

    try:
        messages = [
            {"role": "user", "content": "请用一句话介绍JavaScript语言"}
        ]

        print("正在调用Codex CLI...")
        response, token_usage = await adapter.call_codex(
            messages=messages,
            system_prompt="你是一个专业的编程助手",
            model="gpt-4o",
            max_tokens=100,
            temperature=1.0
        )

        print("\n✅ 调用成功!")
        print(f"\n响应内容:\n{response}\n")
        print(f"Token使用: {token_usage}")

        return True

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")
        return False


async def test_gemini_cli_call():
    """测试Gemini CLI调用"""
    print("\n=== 测试Gemini CLI调用 ===\n")

    adapter = get_cli_adapter()

    if not adapter.is_available("gemini"):
        print("❌ Gemini CLI不可用，跳过测试")
        return False

    try:
        messages = [
            {"role": "user", "content": "请用一句话介绍Go语言"}
        ]

        print("正在调用Gemini CLI...")
        response, token_usage = await adapter.call_gemini(
            messages=messages,
            system_prompt="你是一个专业的编程助手",
            model="gemini-3.1-pro-preview",
            max_tokens=100,
            temperature=1.0
        )

        print("\n✅ 调用成功!")
        print(f"\n响应内容:\n{response}\n")
        print(f"Token使用: {token_usage}")

        return True

    except Exception as e:
        print(f"\n❌ 调用失败: {e}")
        return False


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("CLI集成测试")
    print("=" * 60)

    # 1. 检查可用性
    adapter = await test_cli_availability()

    # 2. 测试各个CLI调用（仅测试可用的）
    results = []

    if adapter.is_available("anthropic"):
        results.append(("Claude", await test_claude_cli_call()))

    if adapter.is_available("openai"):
        results.append(("Codex", await test_codex_cli_call()))

    if adapter.is_available("gemini"):
        results.append(("Gemini", await test_gemini_cli_call()))

    # 3. 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    if not results:
        print("⚠️  没有可用的CLI工具，无法进行测试")
        print("\n提示:")
        print("  - Claude CLI: https://github.com/anthropics/anthropic-cli")
        print("  - Codex CLI:  https://github.com/openai/openai-cli")
        print("  - Gemini CLI: https://github.com/google/generative-ai-cli")
        return 1

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name}: {status}")

    # 返回状态码
    all_passed = all(success for _, success in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
