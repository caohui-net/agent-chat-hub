"""Mention 解析器

将 Mention 引用解析为具体的上下文内容
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field

from src.core.mention_parser import Mention, MentionType


class MentionContext(BaseModel):
    """解析后的引用上下文

    包含引用的具体内容和元数据
    """
    mention: Mention = Field(..., description="原始引用对象")
    resolved: bool = Field(default=False, description="是否成功解析")
    content: Optional[str] = Field(default=None, description="解析后的内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    error: Optional[str] = Field(default=None, description="解析失败时的错误信息")


class MentionResolver:
    """Mention 解析器

    将各种引用类型解析为具体内容:
    - AGENT: 解析为 agent 配置信息
    - HISTORY: 解析为历史对话内容
    - FILE: 解析为文件内容
    - TASK: 解析为任务详情
    - RESPONSE: 解析为特定 agent 的响应内容
    """

    def __init__(self, session_manager=None, config_manager=None):
        """初始化解析器

        Args:
            session_manager: 会话管理器（用于解析历史对话）
            config_manager: 配置管理器（用于解析 agent 配置）
        """
        self.session_manager = session_manager
        self.config_manager = config_manager

    async def resolve(self, mention: Mention) -> MentionContext:
        """解析单个引用

        Args:
            mention: 要解析的引用

        Returns:
            解析后的上下文
        """
        if mention.type == MentionType.AGENT:
            return await self._resolve_agent(mention)
        elif mention.type == MentionType.HISTORY:
            return await self._resolve_history(mention)
        elif mention.type == MentionType.FILE:
            return await self._resolve_file(mention)
        elif mention.type == MentionType.TASK:
            return await self._resolve_task(mention)
        elif mention.type == MentionType.RESPONSE:
            return await self._resolve_response(mention)
        else:
            return MentionContext(
                mention=mention,
                resolved=False,
                error=f"未知的引用类型: {mention.type}"
            )

    async def resolve_all(self, mentions: List[Mention]) -> List[MentionContext]:
        """批量解析引用

        Args:
            mentions: 引用列表

        Returns:
            解析后的上下文列表
        """
        contexts = []
        for mention in mentions:
            context = await self.resolve(mention)
            contexts.append(context)
        return contexts

    async def _resolve_agent(self, mention: Mention) -> MentionContext:
        """解析 Agent 引用

        Args:
            mention: Agent 引用

        Returns:
            解析后的上下文
        """
        if not self.config_manager:
            return MentionContext(
                mention=mention,
                resolved=False,
                error="ConfigManager 未提供"
            )

        try:
            # 获取 agent 配置
            agent_config = self.config_manager.get_agent(mention.target)
            if not agent_config:
                return MentionContext(
                    mention=mention,
                    resolved=False,
                    error=f"Agent '{mention.target}' 不存在"
                )

            # 构建上下文内容
            content = f"Agent: {agent_config.name} ({agent_config.agent_id})\n"
            content += f"Role: {agent_config.role}\n"
            if agent_config.system_prompt:
                content += f"System Prompt: {agent_config.system_prompt[:100]}...\n"

            return MentionContext(
                mention=mention,
                resolved=True,
                content=content,
                metadata={
                    "agent_id": agent_config.agent_id,
                    "name": agent_config.name,
                    "role": agent_config.role,
                    "priority": agent_config.priority
                }
            )

        except Exception as e:
            return MentionContext(
                mention=mention,
                resolved=False,
                error=f"解析 Agent 失败: {str(e)}"
            )

    async def _resolve_history(self, mention: Mention) -> MentionContext:
        """解析历史对话引用

        Args:
            mention: 历史对话引用 (@history:session-123:round-5)

        Returns:
            解析后的上下文
        """
        if not self.session_manager:
            return MentionContext(
                mention=mention,
                resolved=False,
                error="SessionManager 未提供"
            )

        try:
            session_id = mention.target
            round_num = None
            if mention.context and mention.context.startswith("round-"):
                round_num = int(mention.context.split("-")[1])

            # TODO: 实现从 SessionManager 获取历史对话
            # 当前返回占位符
            content = f"[历史对话引用: session={session_id}, round={round_num}]"

            return MentionContext(
                mention=mention,
                resolved=True,
                content=content,
                metadata={
                    "session_id": session_id,
                    "round_num": round_num
                }
            )

        except Exception as e:
            return MentionContext(
                mention=mention,
                resolved=False,
                error=f"解析历史对话失败: {str(e)}"
            )

    async def _resolve_file(self, mention: Mention) -> MentionContext:
        """解析文件引用

        Args:
            mention: 文件引用 (@file:~/doc.txt)

        Returns:
            解析后的上下文
        """
        try:
            file_path = Path(mention.target).expanduser()

            if not file_path.exists():
                return MentionContext(
                    mention=mention,
                    resolved=False,
                    error=f"文件不存在: {file_path}"
                )

            if not file_path.is_file():
                return MentionContext(
                    mention=mention,
                    resolved=False,
                    error=f"路径不是文件: {file_path}"
                )

            # 读取文件内容（限制大小）
            max_size = 100 * 1024  # 100KB
            file_size = file_path.stat().st_size

            if file_size > max_size:
                content = f"[文件过大: {file_path}, 大小: {file_size} bytes]"
                content += f"\n建议使用文件工具处理大文件"
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                content = f"[文件内容: {file_path}]\n"
                content += f"{'=' * 60}\n"
                content += file_content
                content += f"\n{'=' * 60}"

            return MentionContext(
                mention=mention,
                resolved=True,
                content=content,
                metadata={
                    "file_path": str(file_path),
                    "file_size": file_size,
                    "readable": file_size <= max_size
                }
            )

        except Exception as e:
            return MentionContext(
                mention=mention,
                resolved=False,
                error=f"解析文件失败: {str(e)}"
            )

    async def _resolve_task(self, mention: Mention) -> MentionContext:
        """解析任务引用

        Args:
            mention: 任务引用 (@task:task-456)

        Returns:
            解析后的上下文
        """
        # TODO: 实现任务系统集成
        # 当前返回占位符
        task_id = mention.target
        content = f"[任务引用: {task_id}]"
        content += f"\n任务系统尚未实现"

        return MentionContext(
            mention=mention,
            resolved=True,
            content=content,
            metadata={
                "task_id": task_id,
                "placeholder": True
            }
        )

    async def _resolve_response(self, mention: Mention) -> MentionContext:
        """解析响应引用

        Args:
            mention: 响应引用 (@response:agent-claude:round-3)

        Returns:
            解析后的上下文
        """
        if not self.session_manager:
            return MentionContext(
                mention=mention,
                resolved=False,
                error="SessionManager 未提供"
            )

        try:
            agent_id = mention.target
            round_num = None
            if mention.context and mention.context.startswith("round-"):
                round_num = int(mention.context.split("-")[1])

            # TODO: 实现从 SessionManager 获取特定响应
            # 当前返回占位符
            content = f"[响应引用: agent={agent_id}, round={round_num}]"

            return MentionContext(
                mention=mention,
                resolved=True,
                content=content,
                metadata={
                    "agent_id": agent_id,
                    "round_num": round_num
                }
            )

        except Exception as e:
            return MentionContext(
                mention=mention,
                resolved=False,
                error=f"解析响应失败: {str(e)}"
            )
