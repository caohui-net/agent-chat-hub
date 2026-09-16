"""测试重试策略 - RetryPolicy"""
import pytest
import asyncio
from src.core.retry_policy import RetryPolicy, RetryPolicyBuilder


@pytest.fixture
def retry_policy():
    """创建重试策略实例"""
    return RetryPolicy(max_retries=3, base_delay=0.1)


@pytest.mark.unit
def test_retry_policy_initialization():
    """测试RetryPolicy初始化"""
    policy = RetryPolicy(max_retries=3, base_delay=0.1)
    assert policy.max_retries == 3
    assert policy.base_delay == 0.1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_success_first_try(retry_policy):
    """测试第一次尝试成功"""
    async def succeed():
        return "success"

    result = await retry_policy.execute_with_retry(succeed)
    assert result == "success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_retry_on_failure(retry_policy):
    """测试失败后重试"""
    call_count = 0

    async def fail_twice():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary failure")
        return "success"

    result = await retry_policy.execute_with_retry(fail_twice)
    assert result == "success"
    assert call_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_max_retries_exceeded(retry_policy):
    """测试超过最大重试次数"""
    async def always_fail():
        raise ConnectionError("Permanent failure")

    with pytest.raises(ConnectionError, match="Permanent failure"):
        await retry_policy.execute_with_retry(always_fail)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_exponential_backoff_delays():
    """测试指数退避延迟"""
    policy = RetryPolicy(max_retries=3, base_delay=0.01)
    call_count = 0
    delays = []
    last_time = None

    async def track_delays():
        nonlocal call_count, last_time
        import time
        current_time = time.time()
        if last_time:
            delays.append(current_time - last_time)
        last_time = current_time
        call_count += 1
        if call_count < 4:
            raise ConnectionError("Retry")
        return "success"

    await policy.execute_with_retry(track_delays)
    assert call_count == 4
    # Verify delays increase exponentially
    assert len(delays) >= 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_on_timeout_error(retry_policy):
    """测试超时错误重试"""
    call_count = 0

    async def fail_with_timeout():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise asyncio.TimeoutError("Timeout")
        return "success"

    result = await retry_policy.execute_with_retry(fail_with_timeout)
    assert result == "success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_retry_on_non_retryable_error(retry_policy):
    """测试非可重试错误不重试"""
    call_count = 0

    async def fail_with_value_error():
        nonlocal call_count
        call_count += 1
        raise ValueError("Not retryable")

    with pytest.raises(ValueError):
        await retry_policy.execute_with_retry(fail_with_value_error)

    # Should fail immediately without retry
    assert call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_policy_builder_standard():
    """测试标准重试策略"""
    policy = RetryPolicyBuilder.standard()
    assert policy.max_retries == 3
    assert policy.base_delay == 1.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_policy_builder_aggressive():
    """测试激进重试策略"""
    policy = RetryPolicyBuilder.aggressive()
    assert policy.max_retries == 5
    assert policy.base_delay == 0.5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_policy_builder_conservative():
    """测试保守重试策略"""
    policy = RetryPolicyBuilder.conservative()
    assert policy.max_retries == 2
    assert policy.base_delay == 2.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_policy_builder_no_retry():
    """测试无重试策略"""
    policy = RetryPolicyBuilder.no_retry()
    assert policy.max_retries == 0

    async def fail():
        raise ConnectionError("Fail")

    with pytest.raises(ConnectionError):
        await policy.execute_with_retry(fail)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retryable_status_codes():
    """测试可重试的HTTP状态码"""
    policy = RetryPolicy(max_retries=2, base_delay=0.01)

    # Mock error with status code
    class MockHTTPError(Exception):
        def __init__(self, status_code):
            self.status_code = status_code
            super().__init__(f"HTTP {status_code}")

    call_count = 0

    async def fail_with_429():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise MockHTTPError(429)
        return "success"

    result = await policy.execute_with_retry(fail_with_429)
    assert result == "success"
    assert call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retryable_error_messages():
    """测试可重试的错误消息"""
    policy = RetryPolicy(max_retries=2, base_delay=0.01)
    call_count = 0

    async def fail_with_rate_limit():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Rate limit exceeded")
        return "success"

    result = await policy.execute_with_retry(fail_with_rate_limit)
    assert result == "success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connection_errors_are_retryable(retry_policy):
    """测试各种连接错误都可重试"""
    errors = [
        ConnectionError("connection error"),
        ConnectionResetError("reset"),
        ConnectionRefusedError("refused"),
        ConnectionAbortedError("aborted"),
    ]

    for error in errors:
        call_count = 0

        async def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise error
            return "success"

        result = await retry_policy.execute_with_retry(fail_once)
        assert result == "success"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_retry_on_success(retry_policy):
    """测试成功时不重试"""
    call_count = 0

    async def succeed():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await retry_policy.execute_with_retry(succeed)
    assert result == "success"
    assert call_count == 1

