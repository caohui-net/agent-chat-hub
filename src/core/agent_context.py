"""Agent Context Management - 为每个Agent提供独立的上下文和状态隔离"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import structlog

from ..core.models import Message

logger = structlog.get_logger()


@dataclass
class AgentContext:
    """Agent独立上下文 - 隔离状态"""

    agent_id: str
    session_messages: List[Message] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def add_message(self, message: Message) -> None:
        """添加消息到Agent的私有会话"""
        self.session_messages.append(message)
        self.last_active = time.time()
        logger.debug(
            "agent_context_message_added",
            agent_id=self.agent_id,
            message_role=message.role,
            message_length=len(message.content)
        )

    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """获取最近的N条消息"""
        return self.session_messages[-limit:]

    def set_state(self, key: str, value: Any) -> None:
        """设置Agent私有状态"""
        self.state[key] = value
        self.last_active = time.time()

    def get_state(self, key: str, default: Any = None) -> Any:
        """获取Agent私有状态"""
        return self.state.get(key, default)

    def clear_messages(self) -> None:
        """清空消息历史"""
        self.session_messages.clear()
        logger.info("agent_context_cleared", agent_id=self.agent_id)


class ContextManager:
    """管理所有Agent的上下文"""

    def __init__(self):
        self.contexts: Dict[str, AgentContext] = {}
        logger.info("context_manager_initialized")

    def get_agent_context(self, agent_id: str) -> AgentContext:
        """获取Agent的独立上下文，不存在则创建"""
        if agent_id not in self.contexts:
            self.contexts[agent_id] = AgentContext(agent_id=agent_id)
            logger.info("agent_context_created", agent_id=agent_id)
        return self.contexts[agent_id]

    def has_context(self, agent_id: str) -> bool:
        """检查Agent是否已有上下文"""
        return agent_id in self.contexts

    def get_all_contexts(self) -> Dict[str, AgentContext]:
        """获取所有Agent上下文"""
        return dict(self.contexts)

    def remove_context(self, agent_id: str) -> bool:
        """移除Agent的上下文"""
        if agent_id in self.contexts:
            del self.contexts[agent_id]
            logger.info("agent_context_removed", agent_id=agent_id)
            return True
        return False

    def get_shared_context(self, filter_roles: Optional[List[str]] = None) -> List[Message]:
        """
        获取共享的全局消息（用于Agent对话）

        Args:
            filter_roles: 可选的角色过滤列表，例如 ["user", "coordinator"]

        Returns:
            过滤后的消息列表
        """
        # 从所有Agent上下文中收集消息
        all_messages = []
        for context in self.contexts.values():
            all_messages.extend(context.session_messages)

        # 按时间戳排序（假设Message有timestamp）
        # 如果没有timestamp，保持原有顺序
        all_messages.sort(key=lambda m: getattr(m, 'timestamp', 0))

        # 应用角色过滤
        if filter_roles:
            all_messages = [m for m in all_messages if m.role in filter_roles]

        return all_messages

    def get_active_agents(self, inactive_threshold_seconds: float = 300) -> List[str]:
        """
        获取活跃的Agent列表

        Args:
            inactive_threshold_seconds: 不活跃阈值（秒），默认5分钟

        Returns:
            活跃的agent_id列表
        """
        current_time = time.time()
        active_agents = []

        for agent_id, context in self.contexts.items():
            if current_time - context.last_active < inactive_threshold_seconds:
                active_agents.append(agent_id)

        return active_agents

    def cleanup_inactive_contexts(self, inactive_threshold_seconds: float = 3600) -> int:
        """
        清理不活跃的上下文

        Args:
            inactive_threshold_seconds: 不活跃阈值（秒），默认1小时

        Returns:
            清理的上下文数量
        """
        current_time = time.time()
        to_remove = []

        for agent_id, context in self.contexts.items():
            if current_time - context.last_active > inactive_threshold_seconds:
                to_remove.append(agent_id)

        for agent_id in to_remove:
            self.remove_context(agent_id)

        if to_remove:
            logger.info(
                "inactive_contexts_cleaned",
                removed_count=len(to_remove),
                removed_agents=to_remove
            )

        return len(to_remove)
