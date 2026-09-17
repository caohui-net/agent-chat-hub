"""测试 Mention 解析器和解析器"""

import pytest
from pathlib import Path
from src.core.mention_parser import (
    MentionParser,
    MentionType,
    Mention,
    parse_mentions
)
from src.core.mention_resolver import MentionResolver, MentionContext


class TestMentionParser:
    """测试 MentionParser 类"""

    def setup_method(self):
        """每个测试前初始化"""
        self.parser = MentionParser()

    def test_parse_agent_mention(self):
        """测试解析 Agent 引用"""
        text = "请 @claude 分析这个问题"
        mentions = self.parser.parse(text)

        assert len(mentions) == 1
        assert mentions[0].type == MentionType.AGENT
        assert mentions[0].target == "claude"
        assert mentions[0].raw_text == "@claude"

    def test_parse_multiple_agent_mentions(self):
        """测试解析多个 Agent 引用"""
        text = "@claude 和 @codex 一起协作"
        mentions = self.parser.parse(text)

        assert len(mentions) == 2
        assert mentions[0].target == "claude"
        assert mentions[1].target == "codex"

    def test_parse_history_mention(self):
        """测试解析历史对话引用"""
        text = "参考 @history:session-123:round-5 的讨论"
        mentions = self.parser.parse(text)

        assert len(mentions) == 1
        assert mentions[0].type == MentionType.HISTORY
        assert mentions[0].target == "session-123"
        assert mentions[0].context == "round-5"
        assert mentions[0].raw_text == "@history:session-123:round-5"

    def test_parse_file_mention(self):
        """测试解析文件引用"""
        text = "查看 @file:~/documents/report.txt 内容"
        mentions = self.parser.parse(text)

        assert len(mentions) == 1
        assert mentions[0].type == MentionType.FILE
        assert mentions[0].target == "~/documents/report.txt"
        assert mentions[0].raw_text == "@file:~/documents/report.txt"

    def test_parse_file_mention_with_relative_path(self):
        """测试解析相对路径文件引用"""
        text = "查看 @file:./config.json 和 @file:../README.md"
        mentions = self.parser.parse(text)

        assert len(mentions) == 2
        assert mentions[0].target == "./config.json"
        assert mentions[1].target == "../README.md"

    def test_parse_task_mention(self):
        """测试解析任务引用"""
        text = "完成 @task:task-456 然后汇报"
        mentions = self.parser.parse(text)

        assert len(mentions) == 1
        assert mentions[0].type == MentionType.TASK
        assert mentions[0].target == "task-456"
        assert mentions[0].raw_text == "@task:task-456"

    def test_parse_response_mention(self):
        """测试解析响应引用"""
        text = "基于 @response:claude:round-3 继续分析"
        mentions = self.parser.parse(text)

        assert len(mentions) == 1
        assert mentions[0].type == MentionType.RESPONSE
        assert mentions[0].target == "claude"
        assert mentions[0].context == "round-3"
        assert mentions[0].raw_text == "@response:claude:round-3"

    def test_parse_mixed_mentions(self):
        """测试解析混合引用"""
        text = "@claude 查看 @file:~/doc.txt 并参考 @history:session-1:round-2"
        mentions = self.parser.parse(text)

        assert len(mentions) == 3
        assert mentions[0].type == MentionType.AGENT
        assert mentions[1].type == MentionType.FILE
        assert mentions[2].type == MentionType.HISTORY

    def test_parse_mentions_with_positions(self):
        """测试引用位置信息"""
        text = "开始 @claude 中间 @codex 结束"
        mentions = self.parser.parse(text)

        assert mentions[0].start_pos < mentions[0].end_pos
        assert mentions[1].start_pos > mentions[0].end_pos
        assert mentions[0].start_pos == text.index("@claude")
        assert mentions[1].start_pos == text.index("@codex")

    def test_parse_no_mentions(self):
        """测试无引用的文本"""
        text = "这是一段没有任何引用的文本"
        mentions = self.parser.parse(text)

        assert len(mentions) == 0

    def test_parse_agent_with_hyphen_underscore(self):
        """测试带连字符和下划线的 Agent 名称"""
        text = "@agent-name-1 和 @agent_name_2"
        mentions = self.parser.parse(text)

        assert len(mentions) == 2
        assert mentions[0].target == "agent-name-1"
        assert mentions[1].target == "agent_name_2"

    def test_deduplicate_overlapping_mentions(self):
        """测试去重重叠引用"""
        # 如果有复杂引用包含简单引用，应保留复杂的
        text = "@history:session-1:round-2"
        mentions = self.parser.parse(text)

        # 应该只匹配 HISTORY，不匹配 AGENT
        assert len(mentions) == 1
        assert mentions[0].type == MentionType.HISTORY

    def test_extract_agent_mentions(self):
        """测试仅提取 Agent 引用的快捷方法"""
        text = "@claude 查看 @file:~/doc.txt"
        agent_ids = self.parser.extract_agent_mentions(text)

        assert len(agent_ids) == 1
        assert agent_ids[0] == "claude"

    def test_backward_compatible_parse_mentions(self):
        """测试向后兼容的函数接口"""
        text = "@claude @codex"
        agent_ids = parse_mentions(text)

        assert len(agent_ids) == 2
        assert "claude" in agent_ids
        assert "codex" in agent_ids


class TestMentionResolver:
    """测试 MentionResolver 类"""

    def setup_method(self):
        """每个测试前初始化"""
        self.resolver = MentionResolver()

    @pytest.mark.asyncio
    async def test_resolve_agent_without_config(self):
        """测试无 ConfigManager 时解析 Agent"""
        mention = Mention(
            type=MentionType.AGENT,
            target="claude",
            raw_text="@claude",
            start_pos=0,
            end_pos=7
        )

        context = await self.resolver.resolve(mention)

        assert not context.resolved
        assert "ConfigManager 未提供" in context.error

    @pytest.mark.asyncio
    async def test_resolve_history_without_session(self):
        """测试无 SessionManager 时解析历史"""
        mention = Mention(
            type=MentionType.HISTORY,
            target="session-123",
            context="round-5",
            raw_text="@history:session-123:round-5",
            start_pos=0,
            end_pos=29
        )

        context = await self.resolver.resolve(mention)

        assert not context.resolved
        assert "SessionManager 未提供" in context.error

    @pytest.mark.asyncio
    async def test_resolve_file_not_found(self):
        """测试解析不存在的文件"""
        mention = Mention(
            type=MentionType.FILE,
            target="/nonexistent/file.txt",
            raw_text="@file:/nonexistent/file.txt",
            start_pos=0,
            end_pos=28
        )

        context = await self.resolver.resolve(mention)

        assert not context.resolved
        assert "文件不存在" in context.error

    @pytest.mark.asyncio
    async def test_resolve_file_exists(self, tmp_path):
        """测试解析存在的文件"""
        # 创建临时测试文件
        test_file = tmp_path / "test.txt"
        test_content = "这是测试内容"
        test_file.write_text(test_content, encoding='utf-8')

        mention = Mention(
            type=MentionType.FILE,
            target=str(test_file),
            raw_text=f"@file:{test_file}",
            start_pos=0,
            end_pos=20
        )

        context = await self.resolver.resolve(mention)

        assert context.resolved
        assert test_content in context.content
        assert context.metadata["file_path"] == str(test_file)
        assert context.metadata["readable"] is True

    @pytest.mark.asyncio
    async def test_resolve_file_too_large(self, tmp_path):
        """测试解析过大的文件"""
        # 创建超过 100KB 的文件
        test_file = tmp_path / "large.txt"
        large_content = "x" * (101 * 1024)  # 101KB
        test_file.write_text(large_content, encoding='utf-8')

        mention = Mention(
            type=MentionType.FILE,
            target=str(test_file),
            raw_text=f"@file:{test_file}",
            start_pos=0,
            end_pos=20
        )

        context = await self.resolver.resolve(mention)

        assert context.resolved
        assert "文件过大" in context.content
        assert context.metadata["readable"] is False

    @pytest.mark.asyncio
    async def test_resolve_task_placeholder(self):
        """测试解析任务（占位符实现）"""
        mention = Mention(
            type=MentionType.TASK,
            target="task-456",
            raw_text="@task:task-456",
            start_pos=0,
            end_pos=14
        )

        context = await self.resolver.resolve(mention)

        assert context.resolved
        assert "task-456" in context.content
        assert context.metadata.get("placeholder") is True

    @pytest.mark.asyncio
    async def test_resolve_response_without_session(self):
        """测试无 SessionManager 时解析响应"""
        mention = Mention(
            type=MentionType.RESPONSE,
            target="claude",
            context="round-3",
            raw_text="@response:claude:round-3",
            start_pos=0,
            end_pos=24
        )

        context = await self.resolver.resolve(mention)

        assert not context.resolved
        assert "SessionManager 未提供" in context.error

    @pytest.mark.asyncio
    async def test_resolve_all(self, tmp_path):
        """测试批量解析"""
        # 创建测试文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("测试", encoding='utf-8')

        mentions = [
            Mention(
                type=MentionType.AGENT,
                target="claude",
                raw_text="@claude",
                start_pos=0,
                end_pos=7
            ),
            Mention(
                type=MentionType.FILE,
                target=str(test_file),
                raw_text=f"@file:{test_file}",
                start_pos=10,
                end_pos=30
            ),
        ]

        contexts = await self.resolver.resolve_all(mentions)

        assert len(contexts) == 2
        assert contexts[0].mention.type == MentionType.AGENT
        assert contexts[1].mention.type == MentionType.FILE
        assert contexts[1].resolved  # 文件应该成功解析


class TestMentionIntegration:
    """集成测试：Parser + Resolver"""

    @pytest.mark.asyncio
    async def test_parse_and_resolve_workflow(self, tmp_path):
        """测试完整的解析和解析工作流"""
        # 准备测试数据
        test_file = tmp_path / "data.txt"
        test_file.write_text("重要数据", encoding='utf-8')

        # 解析消息
        text = f"@claude 分析 @file:{test_file} 的内容"
        parser = MentionParser()
        mentions = parser.parse(text)

        # 解析引用
        resolver = MentionResolver()
        contexts = await resolver.resolve_all(mentions)

        # 验证结果
        assert len(contexts) == 2
        assert contexts[0].mention.type == MentionType.AGENT
        assert contexts[1].mention.type == MentionType.FILE
        assert contexts[1].resolved
        assert "重要数据" in contexts[1].content
