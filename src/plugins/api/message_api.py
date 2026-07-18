"""消息API

提供给插件订阅和发布消息的接口
"""
from typing import Callable, Optional, Any
import structlog
from src.core.models import AgentMessage
from src.agents.message_bus import MessageBus

logger = structlog.get_logger(__name__)


class MessageAPI:
    """消息API接口

    插件通过此API订阅和发布消息
    """

    def __init__(self, plugin_id: str, message_bus: MessageBus):
        """初始化消息API

        Args:
            plugin_id: 插件ID
            message_bus: 消息总线实例
        """
        self.plugin_id = plugin_id
        self.message_bus = message_bus
        self._subscriptions: dict[str, list[Callable]] = {}

        # 注册插件到消息总线
        self.message_bus.register_agent(f"plugin:{plugin_id}")

    def subscribe(self, message_type: str, callback: Callable[[AgentMessage], None]) -> None:
        """订阅消息类型

        Args:
            message_type: 消息类型
            callback: 回调函数，接收AgentMessage参数
        """
        if message_type not in self._subscriptions:
            self._subscriptions[message_type] = []
            # 订阅消息总线
            self.message_bus.subscribe(f"plugin:{self.plugin_id}", message_type)

        self._subscriptions[message_type].append(callback)
        logger.info("message_subscribed", plugin_id=self.plugin_id, message_type=message_type)

    def unsubscribe(self, message_type: str, callback: Optional[Callable] = None) -> None:
        """取消订阅消息类型

        Args:
            message_type: 消息类型
            callback: 回调函数，如果为None则取消该类型的所有订阅
        """
        if message_type not in self._subscriptions:
            return

        if callback:
            if callback in self._subscriptions[message_type]:
                self._subscriptions[message_type].remove(callback)
        else:
            self._subscriptions[message_type] = []

        logger.info("message_unsubscribed", plugin_id=self.plugin_id, message_type=message_type)

    async def publish(self, message_type: str, content: str,
                     to_agent_id: Optional[str] = None,
                     metadata: Optional[dict[str, Any]] = None) -> None:
        """发布消息

        Args:
            message_type: 消息类型
            content: 消息内容
            to_agent_id: 目标Agent ID（None表示广播）
            metadata: 消息元数据
        """
        message = MessageBus.create_message(
            from_agent_id=f"plugin:{self.plugin_id}",
            content=content,
            to_agent_id=to_agent_id,
            message_type=message_type,
            metadata=metadata or {}
        )

        await self.message_bus.publish(message)
        logger.info("message_published", plugin_id=self.plugin_id,
                   message_type=message_type, to_agent=to_agent_id or "broadcast")

    async def send_to_agent(self, agent_id: str, content: str,
                           message_type: str = "notification") -> None:
        """发送消息到指定Agent

        Args:
            agent_id: 目标Agent ID
            content: 消息内容
            message_type: 消息类型
        """
        await self.publish(message_type, content, to_agent_id=agent_id)

    async def broadcast(self, content: str, message_type: str = "broadcast") -> None:
        """广播消息到所有订阅者

        Args:
            content: 消息内容
            message_type: 消息类型
        """
        await self.publish(message_type, content, to_agent_id=None)

    async def process_messages(self, timeout: Optional[float] = None) -> None:
        """处理接收到的消息

        Args:
            timeout: 超时时间（秒），None表示立即返回
        """
        message = await self.message_bus.get_message(f"plugin:{self.plugin_id}", timeout=timeout)
        if message:
            # 调用订阅的回调函数
            if message.message_type in self._subscriptions:
                for callback in self._subscriptions[message.message_type]:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error("message_callback_failed",
                                   plugin_id=self.plugin_id,
                                   message_type=message.message_type,
                                   error=str(e))
