"""Mention 解析器

解析消息中的各种引用类型（@agent、@history、@file、@task、@response）
"""

import re
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MentionType(Enum):
    """引用类型枚举"""
    AGENT = "agent"  # @agent_name
    HISTORY = "history"  # @history:session-123:round-5
    FILE = "file"  # @file:~/doc.txt
    TASK = "task"  # @task:task-456
    RESPONSE = "response"  # @response:agent-claude:round-3


class Mention(BaseModel):
    """引用数据模型

    表示消息中的单个引用。
    """
    type: MentionType = Field(..., description="引用类型")
    target: str = Field(..., description="引用目标（agent_id/session_id/file_path/task_id等）")
    context: Optional[str] = Field(default=None, description="额外上下文信息（如 round_num）")
    raw_text: str = Field(..., description="原始引用文本")
    start_pos: int = Field(..., description="在消息中的起始位置")
    end_pos: int = Field(..., description="在消息中的结束位置")


class MentionParser:
    """Mention 解析器

    解析消息中的所有引用，支持:
    - @agent_name - Agent 引用
    - @history:session-123:round-5 - 历史对话引用
    - @file:~/doc.txt - 文件引用
    - @task:task-456 - 任务引用
    - @response:agent-claude:round-3 - 特定响应引用
    """

    # 正则表达式模式
    # Agent: @word_chars (字母、数字、下划线、连字符)
    AGENT_PATTERN = r'@([a-zA-Z0-9_-]+)(?=\s|$|[^\w:-])'

    # History: @history:session-id:round-num
    HISTORY_PATTERN = r'@history:([a-zA-Z0-9_-]+):round-(\d+)'

    # File: @file:path (支持 ~/ ./ ../ / 开头的路径)
    FILE_PATTERN = r'@file:((?:~|\.\.?)?/[^\s]+)'

    # Task: @task:task-id
    TASK_PATTERN = r'@task:([a-zA-Z0-9_-]+)'

    # Response: @response:agent-id:round-num
    RESPONSE_PATTERN = r'@response:([a-zA-Z0-9_-]+):round-(\d+)'

    def __init__(self):
        """初始化解析器"""
        # 编译正则表达式以提高性能
        self.patterns = {
            MentionType.HISTORY: re.compile(self.HISTORY_PATTERN),
            MentionType.FILE: re.compile(self.FILE_PATTERN),
            MentionType.TASK: re.compile(self.TASK_PATTERN),
            MentionType.RESPONSE: re.compile(self.RESPONSE_PATTERN),
            MentionType.AGENT: re.compile(self.AGENT_PATTERN),  # 最后匹配，避免误判
        }

    def parse(self, text: str) -> List[Mention]:
        """解析消息中的所有引用

        Args:
            text: 消息文本

        Returns:
            解析出的引用列表，按出现顺序排序
        """
        mentions: List[Mention] = []

        # 按优先级顺序匹配（先匹配复杂格式，避免被简单格式误判）
        for mention_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                mention = self._create_mention(mention_type, match)
                if mention:
                    mentions.append(mention)

        # 去重并按位置排序
        mentions = self._deduplicate_mentions(mentions)
        mentions.sort(key=lambda m: m.start_pos)

        return mentions

    def _create_mention(self, mention_type: MentionType, match: re.Match) -> Optional[Mention]:
        """根据匹配结果创建 Mention 对象

        Args:
            mention_type: 引用类型
            match: 正则匹配对象

        Returns:
            Mention 对象或 None
        """
        try:
            if mention_type == MentionType.AGENT:
                return Mention(
                    type=MentionType.AGENT,
                    target=match.group(1),
                    raw_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end()
                )

            elif mention_type == MentionType.HISTORY:
                return Mention(
                    type=MentionType.HISTORY,
                    target=match.group(1),  # session_id
                    context=f"round-{match.group(2)}",  # round_num
                    raw_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end()
                )

            elif mention_type == MentionType.FILE:
                return Mention(
                    type=MentionType.FILE,
                    target=match.group(1),  # file_path
                    raw_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end()
                )

            elif mention_type == MentionType.TASK:
                return Mention(
                    type=MentionType.TASK,
                    target=match.group(1),  # task_id
                    raw_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end()
                )

            elif mention_type == MentionType.RESPONSE:
                return Mention(
                    type=MentionType.RESPONSE,
                    target=match.group(1),  # agent_id
                    context=f"round-{match.group(2)}",  # round_num
                    raw_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end()
                )

        except (IndexError, ValueError):
            # 匹配失败，返回 None
            return None

        return None

    def _deduplicate_mentions(self, mentions: List[Mention]) -> List[Mention]:
        """去重重叠的引用（保留更具体的引用）

        例如: "@claude" 可能同时匹配 AGENT 和其他模式的一部分，
        需要保留更具体的匹配。

        Args:
            mentions: 原始引用列表

        Returns:
            去重后的引用列表
        """
        if not mentions:
            return mentions

        # 按位置排序
        mentions.sort(key=lambda m: (m.start_pos, -len(m.raw_text)))

        result = []
        last_end = -1

        for mention in mentions:
            # 如果当前引用与上一个不重叠，则保留
            if mention.start_pos >= last_end:
                result.append(mention)
                last_end = mention.end_pos

        return result

    def extract_agent_mentions(self, text: str) -> List[str]:
        """仅提取 Agent 引用的快捷方法（向后兼容）

        Args:
            text: 消息文本

        Returns:
            Agent ID 列表
        """
        mentions = self.parse(text)
        return [m.target for m in mentions if m.type == MentionType.AGENT]


# 向后兼容的函数接口
def parse_mentions(content: str) -> List[str]:
    """
    从消息内容中提取@mentions（向后兼容接口）

    支持格式：
    - @agent_id

    Args:
        content: 消息内容

    Returns:
        被提及的agent_id列表（去重）
    """
    parser = MentionParser()
    return parser.extract_agent_mentions(content)
