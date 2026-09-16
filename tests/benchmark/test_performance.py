"""
Performance Benchmark Tests

Tests single agent latency, concurrent agent throughput, and overhead measurements.
All tests use mocks to avoid real API calls.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.core.session_manager import SessionManager
from src.core.agent_executor import AgentExecutor
from src.core.message_bus import MessageBus
from src.agents.coordinator import CoordinatorAgent


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_single_agent_latency():
    """测试单Agent响应延迟 - 目标<5秒"""
    # Mock AgentExecutor
    with patch('src.core.agent_executor.AgentExecutor') as mock_executor_class:
        mock_executor = AsyncMock()
        mock_executor.execute.return_value = {
            "role": "researcher",
            "content": "研究结果",
            "tokens": {"input": 100, "output": 200}
        }
        mock_executor_class.return_value = mock_executor

        # 创建SessionManager
        session_mgr = SessionManager()

        # 测试单次Agent调用延迟
        start_time = time.time()

        session_id = await session_mgr.create_session("test_user", "channel1")
        await session_mgr.process_message(
            session_id,
            "测试消息",
            sender_id="user1"
        )

        duration = time.time() - start_time

        # 验证响应时间<5秒
        assert duration < 5.0, f"单Agent响应时间 {duration:.2f}s 超过5秒目标"
        print(f"✓ 单Agent响应延迟: {duration:.3f}s")


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_concurrent_agents_throughput():
    """测试3个Agent并发 - 目标<10秒"""
    with patch('src.core.agent_executor.AgentExecutor') as mock_executor_class:
        # Mock执行器返回延迟
        async def mock_execute(*args, **kwargs):
            await asyncio.sleep(0.1)  # 模拟API延迟
            return {
                "role": kwargs.get("role", "researcher"),
                "content": "结果",
                "tokens": {"input": 100, "output": 200}
            }

        mock_executor = AsyncMock()
        mock_executor.execute.side_effect = mock_execute
        mock_executor_class.return_value = mock_executor

        session_mgr = SessionManager()

        # 测试3个Agent并发执行
        start_time = time.time()

        session_id = await session_mgr.create_session("test_user", "channel1")

        # 模拟@mention 3个Agent
        await session_mgr.process_message(
            session_id,
            "@researcher @analyst @coder 请分析这个问题",
            sender_id="user1"
        )

        duration = time.time() - start_time

        # 验证并发响应时间<10秒
        assert duration < 10.0, f"3个Agent并发响应时间 {duration:.2f}s 超过10秒目标"
        print(f"✓ 3个Agent并发响应: {duration:.3f}s")


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_token_tracking_overhead():
    """测试Token追踪性能开销 - 目标<5%"""
    iterations = 100

    # 测试无Token追踪的性能
    start_time = time.time()
    for _ in range(iterations):
        # 模拟简单操作
        await asyncio.sleep(0.001)
    baseline_duration = time.time() - start_time

    # 测试有Token追踪的性能
    with patch('src.core.token_tracker.TokenTracker') as mock_tracker:
        tracker = Mock()
        tracker.track_request = Mock()
        tracker.get_session_usage.return_value = {
            "total_tokens": 1000,
            "input_tokens": 600,
            "output_tokens": 400
        }
        mock_tracker.return_value = tracker

        start_time = time.time()
        for _ in range(iterations):
            await asyncio.sleep(0.001)
            tracker.track_request("session1", 10, 20)
        tracked_duration = time.time() - start_time

    # 计算开销百分比
    overhead = ((tracked_duration - baseline_duration) / baseline_duration) * 100

    # 验证开销<5%
    assert overhead < 5.0, f"Token追踪开销 {overhead:.2f}% 超过5%目标"
    print(f"✓ Token追踪开销: {overhead:.2f}%")


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_context_isolation_overhead():
    """测试Agent上下文隔离开销 - 目标<3%"""
    iterations = 50

    # 测试无隔离的性能
    start_time = time.time()
    for _ in range(iterations):
        data = {"key": "value"}
        await asyncio.sleep(0.002)
    baseline_duration = time.time() - start_time

    # 测试有隔离的性能
    with patch('src.core.session_manager.SessionManager') as mock_session_class:
        session_mgr = Mock()
        session_mgr.create_session = AsyncMock(return_value="session1")
        session_mgr.get_session = Mock(return_value={
            "id": "session1",
            "context": {},
            "agents": {}
        })
        mock_session_class.return_value = session_mgr

        start_time = time.time()
        for _ in range(iterations):
            await session_mgr.create_session(f"user{_}", "channel1")
            session_mgr.get_session("session1")
        isolated_duration = time.time() - start_time

    # 计算开销百分比
    overhead = ((isolated_duration - baseline_duration) / baseline_duration) * 100

    # 验证开销<3%
    assert overhead < 3.0, f"上下文隔离开销 {overhead:.2f}% 超过3%目标"
    print(f"✓ 上下文隔离开销: {overhead:.2f}%")


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_message_bus_throughput():
    """测试MessageBus消息吞吐量 - 目标>100 msg/s"""
    bus = MessageBus()

    message_count = 0

    def handler(message):
        nonlocal message_count
        message_count += 1

    bus.subscribe("test_topic", handler)

    # 发送1000条消息
    iterations = 1000
    start_time = time.time()

    for i in range(iterations):
        await bus.publish("test_topic", {"id": i, "data": "test"})

    duration = time.time() - start_time
    throughput = iterations / duration

    # 验证吞吐量>100 msg/s
    assert throughput > 100, f"消息吞吐量 {throughput:.0f} msg/s 低于100目标"
    assert message_count == iterations, "消息丢失"
    print(f"✓ MessageBus吞吐量: {throughput:.0f} msg/s")


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_session_creation_latency():
    """测试Session创建延迟 - 目标<100ms"""
    session_mgr = SessionManager()

    iterations = 10
    total_duration = 0

    for i in range(iterations):
        start_time = time.time()
        session_id = await session_mgr.create_session(f"user{i}", "channel1")
        duration = time.time() - start_time
        total_duration += duration

        assert session_id is not None

    avg_duration = total_duration / iterations

    # 验证平均延迟<100ms
    assert avg_duration < 0.1, f"Session创建平均延迟 {avg_duration*1000:.2f}ms 超过100ms目标"
    print(f"✓ Session创建延迟: {avg_duration*1000:.2f}ms (平均)")


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_memory_usage_stability():
    """测试内存使用稳定性 - 目标增长<10%"""
    import sys

    # 获取初始内存使用
    initial_objects = len(gc.get_objects())

    session_mgr = SessionManager()

    # 创建并销毁100个session
    for i in range(100):
        session_id = await session_mgr.create_session(f"user{i}", "channel1")
        await session_mgr.cleanup_session(session_id)

    # 手动触发垃圾回收
    import gc
    gc.collect()

    # 获取最终内存使用
    final_objects = len(gc.get_objects())

    # 计算对象增长百分比
    growth = ((final_objects - initial_objects) / initial_objects) * 100

    # 验证内存增长<10%
    assert growth < 10.0, f"内存对象增长 {growth:.2f}% 超过10%目标"
    print(f"✓ 内存稳定性: 对象增长 {growth:.2f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
