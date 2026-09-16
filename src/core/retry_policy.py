"""智能重试策略 - 支持指数退避和错误分类"""

import asyncio
from typing import Any, Callable, Optional

import structlog

logger = structlog.get_logger()


class RetryPolicy:
    """重试策略 - 支持指数退避"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        初始化重试策略

        Args:
            max_retries: 最大重试次数，默认3次
            base_delay: 基础延迟时间（秒），默认1.0秒
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        logger.info(
            "retry_policy_initialized",
            max_retries=max_retries,
            base_delay=base_delay
        )

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数，支持自动重试

        Args:
            func: 要执行的异步函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            最后一次执行的异常（如果所有重试都失败）
        """
        last_error = None

        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(
                        "retry_success",
                        func_name=func.__name__,
                        attempt=attempt,
                        total_attempts=attempt + 1
                    )
                return result

            except Exception as e:
                last_error = e

                # 最后一次尝试，不再重试
                if attempt >= self.max_retries:
                    logger.error(
                        "retry_exhausted",
                        func_name=func.__name__,
                        total_attempts=attempt + 1,
                        error=str(e)
                    )
                    raise

                # 检查是否可重试
                if not self._is_retryable(e):
                    logger.warning(
                        "retry_not_retryable",
                        func_name=func.__name__,
                        error_type=type(e).__name__,
                        error=str(e)
                    )
                    raise

                # 计算指数退避延迟
                delay = self.base_delay * (2 ** attempt)

                logger.warning(
                    "retry_attempt",
                    func_name=func.__name__,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    delay_seconds=delay,
                    error_type=type(e).__name__,
                    error=str(e)
                )

                await asyncio.sleep(delay)

        # 理论上不会到达这里，但为了类型安全
        raise last_error

    def _is_retryable(self, error: Exception) -> bool:
        """
        判断错误是否可重试

        Args:
            error: 捕获的异常

        Returns:
            True表示可重试，False表示不可重试
        """
        # 可重试的错误类型：网络超时、连接错误
        retryable_error_types = (
            asyncio.TimeoutError,
            ConnectionError,
            TimeoutError,
            ConnectionResetError,
            ConnectionRefusedError,
            ConnectionAbortedError,
        )

        # 检查错误类型
        if isinstance(error, retryable_error_types):
            return True

        # 检查API响应状态码（如果有）
        if hasattr(error, 'status_code'):
            status_code = error.status_code
            # 429 Too Many Requests, 503 Service Unavailable, 504 Gateway Timeout
            if status_code in (429, 503, 504):
                logger.debug(
                    "retryable_status_code",
                    status_code=status_code,
                    error=str(error)
                )
                return True

        # 检查Anthropic API特定错误
        error_message = str(error).lower()
        retryable_messages = [
            "timeout",
            "timed out",
            "connection reset",
            "connection refused",
            "rate limit",
            "overloaded",
            "unavailable",
            "internal server error",
        ]

        for msg in retryable_messages:
            if msg in error_message:
                logger.debug(
                    "retryable_error_message",
                    error_message=error_message,
                    matched_pattern=msg
                )
                return True

        return False


class RetryPolicyBuilder:
    """重试策略构建器 - 提供便捷的预设配置"""

    @staticmethod
    def aggressive() -> RetryPolicy:
        """激进重试策略 - 5次重试，0.5秒基础延迟"""
        return RetryPolicy(max_retries=5, base_delay=0.5)

    @staticmethod
    def standard() -> RetryPolicy:
        """标准重试策略 - 3次重试，1.0秒基础延迟"""
        return RetryPolicy(max_retries=3, base_delay=1.0)

    @staticmethod
    def conservative() -> RetryPolicy:
        """保守重试策略 - 2次重试，2.0秒基础延迟"""
        return RetryPolicy(max_retries=2, base_delay=2.0)

    @staticmethod
    def no_retry() -> RetryPolicy:
        """无重试策略 - 0次重试"""
        return RetryPolicy(max_retries=0, base_delay=0.0)
