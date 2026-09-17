"""演示增强的 @mention 机制使用示例

展示如何使用新的 MentionParser 和 MentionResolver
"""

import asyncio
from pathlib import Path
from src.core.mention_parser import MentionParser, MentionType
from src.core.mention_resolver import MentionResolver


async def demo_basic_parsing():
    """演示基本的引用解析"""
    print("=== 演示 1: 基本引用解析 ===\n")

    parser = MentionParser()

    # 示例消息
    text = """
    @claude 请分析 @file:~/config.json 的内容，
    并参考 @history:session-123:round-5 的讨论。
    完成后更新 @task:task-456
    """

    mentions = parser.parse(text)

    print(f"原始消息:\n{text}\n")
    print(f"解析出 {len(mentions)} 个引用:\n")

    for i, mention in enumerate(mentions, 1):
        print(f"{i}. 类型: {mention.type.value}")
        print(f"   目标: {mention.target}")
        if mention.context:
            print(f"   上下文: {mention.context}")
        print(f"   原始文本: {mention.raw_text}")
        print(f"   位置: [{mention.start_pos}:{mention.end_pos}]")
        print()


async def demo_file_resolution():
    """演示文件引用解析"""
    print("\n=== 演示 2: 文件引用解析 ===\n")

    # 创建临时测试文件
    test_file = Path("/tmp/demo_mention_test.txt")
    test_file.write_text("这是一个测试文件的内容\n包含多行数据", encoding='utf-8')

    parser = MentionParser()
    resolver = MentionResolver()

    text = f"@claude 分析 @file:{test_file} 的内容"

    mentions = parser.parse(text)
    contexts = await resolver.resolve_all(mentions)

    print(f"消息: {text}\n")

    for context in contexts:
        print(f"引用类型: {context.mention.type.value}")
        print(f"目标: {context.mention.target}")
        print(f"解析状态: {'成功' if context.resolved else '失败'}")

        if context.resolved and context.content:
            print(f"内容:\n{context.content[:200]}...")
        elif context.error:
            print(f"错误: {context.error}")

        print()

    # 清理
    test_file.unlink()


async def demo_agent_only():
    """演示仅提取 Agent 引用（向后兼容）"""
    print("\n=== 演示 3: 仅提取 Agent 引用 ===\n")

    parser = MentionParser()

    text = "@claude 和 @codex 协作分析 @file:~/data.csv"

    # 使用新方法
    all_mentions = parser.parse(text)
    agent_mentions = parser.extract_agent_mentions(text)

    print(f"消息: {text}\n")
    print(f"所有引用 ({len(all_mentions)}):")
    for m in all_mentions:
        print(f"  - {m.type.value}: {m.target}")

    print(f"\n仅 Agent 引用 ({len(agent_mentions)}):")
    for agent_id in agent_mentions:
        print(f"  - {agent_id}")


async def demo_complex_scenario():
    """演示复杂场景"""
    print("\n=== 演示 4: 复杂场景 ===\n")

    parser = MentionParser()

    text = """
    @coordinator 请协调以下任务:
    1. @claude 分析 @file:./report.pdf
    2. @codex 基于 @response:claude:round-3 生成代码
    3. @gemini 参考 @history:session-abc:round-10 提供建议
    4. 所有结果归档到 @task:task-789
    """

    mentions = parser.parse(text)

    print(f"复杂消息包含 {len(mentions)} 个引用:\n")

    # 按类型分组
    by_type = {}
    for mention in mentions:
        type_name = mention.type.value
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(mention.target)

    for type_name, targets in by_type.items():
        print(f"{type_name.upper()} ({len(targets)}):")
        for target in targets:
            print(f"  - {target}")
        print()


async def main():
    """运行所有演示"""
    await demo_basic_parsing()
    await demo_file_resolution()
    await demo_agent_only()
    await demo_complex_scenario()

    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
