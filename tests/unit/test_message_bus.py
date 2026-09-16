"""消息总线测试"""
import pytest
import asyncio
from src.agents.message_bus import MessageBus
from src.core.models import AgentMessage


@pytest.fixture
def message_bus():
    """创建消息总线实例"""
    return MessageBus()


def test_register_agent(message_bus):
    """测试注册agent"""
    message_bus.register_agent("agent_1")
    assert "agent_1" in message_bus._queues
    assert isinstance(message_bus._queues["agent_1"], asyncio.Queue)


def test_unregister_agent(message_bus):
    """测试注销agent"""
    message_bus.register_agent("agent_1")
    message_bus.subscribe("agent_1", "notification")

    message_bus.unregister_agent("agent_1")
    assert "agent_1" not in message_bus._queues
    assert "agent_1" not in message_bus._subscriptions.get("notification", set())


def test_subscribe(message_bus):
    """测试订阅消息类型"""
    message_bus.subscribe("agent_1", "query")

    assert "agent_1" in message_bus._subscriptions["query"]
    assert "agent_1" in message_bus._queues


def test_publish_point_to_point(message_bus):
    """测试点对点消息发布"""
    async def run_test():
        message_bus.register_agent("agent_1")
        message_bus.register_agent("agent_2")

        message = MessageBus.create_message(
            from_agent_id="agent_1",
            to_agent_id="agent_2",
            content="Hello agent_2!",
            message_type="notification"
        )

        await message_bus.publish(message)

        # agent_2应该收到消息
        assert message_bus.has_messages("agent_2")
        received = await message_bus.get_message("agent_2", timeout=1.0)
        assert received is not None
        assert received.content == "Hello agent_2!"
        assert received.from_agent_id == "agent_1"

        # agent_1不应该收到消息
        assert not message_bus.has_messages("agent_1")

    asyncio.run(run_test())


def test_publish_broadcast(message_bus):
    """测试广播消息"""
    async def run_test():
        message_bus.subscribe("agent_1", "broadcast")
        message_bus.subscribe("agent_2", "broadcast")
        message_bus.subscribe("agent_3", "broadcast")

        message = MessageBus.create_message(
            from_agent_id="system",
            to_agent_id=None,  # 广播
            content="System announcement",
            message_type="broadcast"
        )

        await message_bus.publish(message)

        # 所有订阅者都应该收到消息
        for agent_id in ["agent_1", "agent_2", "agent_3"]:
            assert message_bus.has_messages(agent_id)
            received = await message_bus.get_message(agent_id, timeout=1.0)
            assert received.content == "System announcement"

    asyncio.run(run_test())


def test_get_message_timeout(message_bus):
    """测试获取消息超时"""
    async def run_test():
        message_bus.register_agent("agent_1")

        # 没有消息时应该超时返回None
        received = await message_bus.get_message("agent_1", timeout=0.1)
        assert received is None

    asyncio.run(run_test())


def test_message_history(message_bus):
    """测试消息历史记录"""
    message_bus.register_agent("agent_1")
    message_bus.register_agent("agent_2")

    messages = [
        MessageBus.create_message("agent_1", "msg1", to_agent_id="agent_2"),
        MessageBus.create_message("agent_2", "msg2", to_agent_id="agent_1"),
        MessageBus.create_message("agent_1", "msg3", to_agent_id="agent_2"),
    ]

    async def publish_all():
        for msg in messages:
            await message_bus.publish(msg)

    asyncio.run(publish_all())

    history = message_bus.get_message_history()
    assert len(history) == 3
    assert history[0].content == "msg1"
    assert history[1].content == "msg2"
    assert history[2].content == "msg3"


def test_clear_history(message_bus):
    """测试清空历史"""
    message_bus.register_agent("agent_1")

    async def publish_msg():
        msg = MessageBus.create_message("agent_1", "test", to_agent_id="agent_1")
        await message_bus.publish(msg)

    asyncio.run(publish_msg())
    assert len(message_bus.get_message_history()) == 1

    message_bus.clear_history()
    assert len(message_bus.get_message_history()) == 0


def test_create_message():
    """测试创建消息辅助方法"""
    msg = MessageBus.create_message(
        from_agent_id="agent_1",
        content="test content",
        to_agent_id="agent_2",
        message_type="query",
        metadata={"key": "value"}
    )

    assert isinstance(msg, AgentMessage)
    assert msg.from_agent_id == "agent_1"
    assert msg.to_agent_id == "agent_2"
    assert msg.content == "test content"
    assert msg.message_type == "query"
    assert msg.metadata["key"] == "value"
    assert msg.message_id is not None
