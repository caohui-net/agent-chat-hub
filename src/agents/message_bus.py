"""Agent间消息总线

实现Agent之间的消息传递和事件驱动通信。
"""
import asyncio
import uuid
from typing import Any, Dict, List, Callable, Optional, Set
from collections import defaultdict

from src.core.models import AgentMessage


class MessageBus:
    """消息总线

    提供Agent间的异步消息传递能力：
    - 点对点消息（指定接收者）
    - 广播消息（所有Agent）
    - 消息订阅和路由
    - 异步消息处理
    """

    def __init__(self):
        """初始化消息总线"""
        # 消息队列：agent_id -> Queue
        self._queues: Dict[str, asyncio.Queue] = {}

        # 订阅关系：message_type -> set of agent_ids
        self._subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # 消息历史（用于调试和显示）
        self._message_history: List[AgentMessage] = []
        self._max_history = 100

        # 是否运行中
        self._running = False

    def register_agent(self, agent_id: str) -> None:
        """注册Agent到消息总线

        Args:
            agent_id: Agent唯一标识符
        """
        if agent_id not in self._queues:
            # P2-004: 设置队列容量限制防止内存问题
            self._queues[agent_id] = asyncio.Queue(maxsize=1000)

    def unregister_agent(self, agent_id: str) -> None:
        """从消息总线注销Agent

        Args:
            agent_id: Agent唯一标识符
        """
        if agent_id in self._queues:
            del self._queues[agent_id]

        # 清理订阅关系
        for message_type in list(self._subscriptions.keys()):
            self._subscriptions[message_type].discard(agent_id)

    def subscribe(self, agent_id: str, message_type: str) -> None:
        """订阅特定类型的消息

        Args:
            agent_id: Agent唯一标识符
            message_type: 消息类型
        """
        self.register_agent(agent_id)  # 确保agent已注册
        self._subscriptions[message_type].add(agent_id)

    async def publish(self, message: AgentMessage) -> None:
        """发布消息

        根据消息类型和接收者路由消息：
        - 点对点消息：发送给指定agent
        - 广播消息：发送给所有订阅了该消息类型的agent

        Args:
            message: 要发布的消息
        """
        # 记录到历史
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)

        # 确定接收者列表
        recipients: Set[str] = set()

        if message.to_agent_id:
            # 点对点消息
            recipients.add(message.to_agent_id)
        else:
            # 广播消息 - 发送给所有订阅了该类型的agent
            recipients.update(self._subscriptions.get(message.message_type, set()))

        # 发送消息到各个接收者的队列
        for agent_id in recipients:
            if agent_id in self._queues:
                await self._queues[agent_id].put(message)

    async def get_message(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """获取agent的下一条消息（阻塞直到有消息或超时）

        Args:
            agent_id: Agent唯一标识符
            timeout: 超时时间（秒），None表示永久等待

        Returns:
            AgentMessage或None（超时）
        """
        if agent_id not in self._queues:
            self.register_agent(agent_id)

        try:
            if timeout:
                return await asyncio.wait_for(self._queues[agent_id].get(), timeout=timeout)
            else:
                return await self._queues[agent_id].get()
        except asyncio.TimeoutError:
            return None

    def has_messages(self, agent_id: str) -> bool:
        """检查agent是否有待处理的消息

        Args:
            agent_id: Agent唯一标识符

        Returns:
            是否有消息
        """
        if agent_id not in self._queues:
            return False
        return not self._queues[agent_id].empty()

    def get_message_history(self, limit: int = 50) -> List[AgentMessage]:
        """获取消息历史

        Args:
            limit: 返回的最大消息数量

        Returns:
            消息历史列表
        """
        return self._message_history[-limit:]

    def clear_history(self) -> None:
        """清空消息历史"""
        self._message_history.clear()

    @staticmethod
    def create_message(
        from_agent_id: str,
        content: str,
        to_agent_id: Optional[str] = None,
        message_type: str = "notification",
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentMessage:
        """创建消息的辅助方法

        Args:
            from_agent_id: 发送方Agent ID
            content: 消息内容
            to_agent_id: 接收方Agent ID（None表示广播）
            message_type: 消息类型
            reply_to: 回复的消息ID
            metadata: 消息元数据

        Returns:
            AgentMessage对象
        """
        return AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            content=content,
            metadata=metadata or {},
            reply_to=reply_to,
        )
