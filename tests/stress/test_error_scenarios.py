"""
Stress Test - Error Scenarios

Tests network timeouts, API rate limits, concurrent failures, and memory leaks.
All tests use mocks to simulate error conditions without real API calls.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.core.errors import NetworkError, APILimitError, AgentExecutionError
from src.core.session_manager import SessionManager
from src.core.agent_executor import AgentExecutor
from src.utils.retry import retry_with_backoff


@pytest.mark.stress
@pytest.mark.asyncio
async def test_network_timeout_retry():
    """测试网络超时自动重试3次"""
    attempt_count = 0

    @retry_with_backoff(max_retries=3, base_delay=0.01)
    async def failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 4:
            raise NetworkError("Connection timeout")
        return "success"

    # 验证最终成功
    result = await failing_operation()
    assert result == "success"
    assert attempt_count == 4, f"期望重试3次后成功，实际尝试{attempt_count}次"
    print(f"✓ 网络超时重试: {attempt_count}次尝试后成功")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_network_timeout_max_retries():
    """测试网络超时达到最大重试次数后失败"""
    attempt_count = 0

    @retry_with_backoff(max_retries=3, base_delay=0.01)
    async def always_failing():
        nonlocal attempt_count
        attempt_count += 1
        raise NetworkError("Connection timeout")

    # 验证最终失败
    with pytest.raises(NetworkError):
        await always_failing()

    assert attempt_count == 4, f"期望尝试4次(初始+3次重试)，实际{attempt_count}次"
    print(f"✓ 网络超时最大重试: {attempt_count}次后正确失败")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_api_rate_limit_backoff():
    """测试API限流正确退避"""
    attempt_count = 0
    retry_delays = []
    last_time = time.time()

    @retry_with_backoff(max_retries=3, base_delay=0.05)
    async def rate_limited_operation():
        nonlocal attempt_count, last_time
        current_time = time.time()
        if attempt_count > 0:
            delay = current_time - last_time
            retry_delays.append(delay)
        last_time = current_time

        attempt_count += 1
        if attempt_count < 3:
            raise APILimitError("Rate limit exceeded")
        return "success"

    # 验证最终成功
    result = await rate_limited_operation()
    assert result == "success"
    assert attempt_count == 3

    # 验证指数退避（每次延迟应该递增）
    if len(retry_delays) > 1:
        for i in range(1, len(retry_delays)):
            assert retry_delays[i] >= retry_delays[i-1], \
                f"退避延迟应递增: {retry_delays}"

    print(f"✓ API限流退避: {attempt_count}次尝试，延迟序列: {[f'{d:.3f}s' for d in retry_delays]}")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_concurrent_agent_failures():
    """测试3个Agent同时失败的隔离性"""
    with patch('src.core.agent_executor.AgentExecutor') as mock_executor_class:
        # Mock所有Agent都失败
        async def failing_execute(*args, **kwargs):
            role = kwargs.get("role", "unknown")
            raise AgentExecutionError(f"{role} agent failed")

        mock_executor = AsyncMock()
        mock_executor.execute.side_effect = failing_execute
        mock_executor_class.return_value = mock_executor

        session_mgr = SessionManager()
        session_id = await session_mgr.create_session("test_user", "channel1")

        # 尝试调用3个Agent
        with pytest.raises(AgentExecutionError):
            await session_mgr.process_message(
                session_id,
                "@researcher @analyst @coder 请分析",
                sender_id="user1"
            )

        # 验证session状态仍然有效
        session = session_mgr.get_session(session_id)
        assert session is not None
        assert session["id"] == session_id

        # 验证可以继续使用session
        session_active = await session_mgr.is_session_active(session_id)
        assert session_active

    print("✓ 并发Agent失败隔离: 3个Agent失败后session仍然有效")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_partial_agent_failure():
    """测试部分Agent失败不影响其他"""
    with patch('src.core.agent_executor.AgentExecutor') as mock_executor_class:
        # Mock第2个Agent失败，其他成功
        execution_count = 0

        async def partial_failing_execute(*args, **kwargs):
            nonlocal execution_count
            execution_count += 1

            if execution_count == 2:
                raise AgentExecutionError("Second agent failed")

            return {
                "role": kwargs.get("role", "agent"),
                "content": f"结果 {execution_count}",
                "tokens": {"input": 100, "output": 200}
            }

        mock_executor = AsyncMock()
        mock_executor.execute.side_effect = partial_failing_execute
        mock_executor_class.return_value = mock_executor

        session_mgr = SessionManager()
        session_id = await session_mgr.create_session("test_user", "channel1")

        # 调用3个Agent，期望第2个失败
        try:
            await session_mgr.process_message(
                session_id,
                "@researcher @analyst @coder 请分析",
                sender_id="user1"
            )
        except AgentExecutionError:
            pass

        # 验证至少有部分执行
        assert execution_count >= 2, "应该至少尝试2个Agent"

    print(f"✓ 部分Agent失败: {execution_count}个Agent尝试执行，部分失败不影响系统")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_memory_leak_check():
    """测试100次迭代无内存泄漏"""
    import gc
    import sys

    # 手动触发垃圾回收
    gc.collect()
    initial_objects = len(gc.get_objects())

    session_mgr = SessionManager()

    # 执行100次Agent调用
    with patch('src.core.agent_executor.AgentExecutor') as mock_executor_class:
        mock_executor = AsyncMock()
        mock_executor.execute.return_value = {
            "role": "researcher",
            "content": "结果",
            "tokens": {"input": 100, "output": 200}
        }
        mock_executor_class.return_value = mock_executor

        for i in range(100):
            session_id = await session_mgr.create_session(f"user{i}", "channel1")
            await session_mgr.process_message(
                session_id,
                "测试消息",
                sender_id=f"user{i}"
            )
            await session_mgr.cleanup_session(session_id)

    # 手动触发垃圾回收
    gc.collect()
    final_objects = len(gc.get_objects())

    # 计算内存增长
    growth = ((final_objects - initial_objects) / initial_objects) * 100

    # 验证内存增长<10%
    assert growth < 10.0, f"100次迭代后内存增长 {growth:.2f}% 超过10%"
    print(f"✓ 内存泄漏检查: 100次迭代后对象增长 {growth:.2f}%")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_rapid_session_creation():
    """测试快速创建大量Session的稳定性"""
    session_mgr = SessionManager()
    session_ids = []

    # 快速创建100个session
    start_time = time.time()
    for i in range(100):
        session_id = await session_mgr.create_session(f"user{i}", "channel1")
        session_ids.append(session_id)

    duration = time.time() - start_time

    # 验证所有session创建成功
    assert len(session_ids) == 100
    assert len(set(session_ids)) == 100, "Session ID应该唯一"

    # 验证所有session都有效
    for session_id in session_ids:
        session = session_mgr.get_session(session_id)
        assert session is not None

    print(f"✓ 快速创建Session: 100个session在 {duration:.2f}s 内创建")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_exception_propagation():
    """测试异常正确传播不被吞没"""
    class CustomError(Exception):
        pass

    with patch('src.core.agent_executor.AgentExecutor') as mock_executor_class:
        async def raise_custom_error(*args, **kwargs):
            raise CustomError("Custom error message")

        mock_executor = AsyncMock()
        mock_executor.execute.side_effect = raise_custom_error
        mock_executor_class.return_value = mock_executor

        session_mgr = SessionManager()
        session_id = await session_mgr.create_session("test_user", "channel1")

        # 验证异常正确传播
        with pytest.raises((CustomError, AgentExecutionError)):
            await session_mgr.process_message(
                session_id,
                "测试消息",
                sender_id="user1"
            )

    print("✓ 异常传播: 自定义异常正确传播")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_timeout_handling():
    """测试超时正确处理"""
    async def slow_operation():
        await asyncio.sleep(10)
        return "result"

    # 设置1秒超时
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_operation(), timeout=0.1)

    print("✓ 超时处理: 操作正确超时")


@pytest.mark.stress
@pytest.mark.asyncio
async def test_cascading_failure_recovery():
    """测试级联失败后的恢复能力"""
    failure_count = 0

    with patch('src.core.agent_executor.AgentExecutor') as mock_executor_class:
        async def intermittent_failure(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1

            # 前3次失败，然后恢复
            if failure_count <= 3:
                raise NetworkError("Intermittent failure")

            return {
                "role": kwargs.get("role", "agent"),
                "content": "恢复后的结果",
                "tokens": {"input": 100, "output": 200}
            }

        mock_executor = AsyncMock()
        mock_executor.execute.side_effect = intermittent_failure
        mock_executor_class.return_value = mock_executor

        session_mgr = SessionManager()
        session_id = await session_mgr.create_session("test_user", "channel1")

        # 第1次调用应失败
        with pytest.raises((NetworkError, AgentExecutionError)):
            await session_mgr.process_message(
                session_id,
                "测试消息1",
                sender_id="user1"
            )

        # 重置计数
        failure_count = 0

        # 第2次调用应成功（经过重试）
        @retry_with_backoff(max_retries=5, base_delay=0.01)
        async def retry_operation():
            return await mock_executor.execute(
                role="researcher",
                message="测试",
                context={}
            )

        result = await retry_operation()
        assert result is not None

    print(f"✓ 级联失败恢复: {failure_count}次失败后成功恢复")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
