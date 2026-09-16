"""统一错误分类体系

定义了系统中所有错误类型的层级结构，支持错误分类、重试判断和上下文记录。
"""
from enum import Enum
from typing import Dict, Any, Optional


class ErrorCategory(Enum):
    """错误分类枚举"""
    NETWORK = "network"              # 网络错误（超时、连接失败）
    API_LIMIT = "api_limit"          # API限流错误（429, quota exceeded）
    VALIDATION = "validation"         # 数据验证错误（输入格式错误）
    CONFIGURATION = "configuration"   # 配置错误（缺少API密钥、模型不存在）
    INTERNAL = "internal"            # 内部错误（代码bug、未预期异常）
    EXTERNAL = "external"            # 外部服务错误（API返回5xx）


class AgentChatHubError(Exception):
    """基础错误类

    所有系统错误的基类，提供统一的错误分类和上下文记录。

    Attributes:
        category: 错误分类
        retryable: 是否可重试
        context: 错误上下文（agent_id, timeout等）
        original_error: 原始异常（如果是包装其他异常）
    """

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        retryable: bool = False,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """初始化错误

        Args:
            message: 错误消息
            category: 错误分类
            retryable: 是否可重试
            context: 错误上下文字典
            original_error: 原始异常
        """
        super().__init__(message)
        self.category = category
        self.retryable = retryable
        self.context = context or {}
        self.original_error = original_error

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（用于日志）

        Returns:
            包含错误信息的字典
        """
        return {
            "error_type": self.__class__.__name__,
            "category": self.category.value,
            "message": str(self),
            "retryable": self.retryable,
            "context": self.context,
            "original_error": str(self.original_error) if self.original_error else None
        }


class NetworkError(AgentChatHubError):
    """网络错误

    网络超时、连接失败、DNS解析失败等。
    默认可重试。
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            retryable=True,
            context=context,
            original_error=original_error
        )


class APILimitError(AgentChatHubError):
    """API限流错误

    包括429错误、quota超限等。
    默认可重试（但需要更长的重试间隔）。
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.API_LIMIT,
            retryable=True,
            context=context,
            original_error=original_error
        )


class ValidationError(AgentChatHubError):
    """数据验证错误

    输入格式错误、字段缺失、类型不匹配等。
    不可重试（需要修正输入）。
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            retryable=False,
            context=context,
            original_error=original_error
        )


class ConfigurationError(AgentChatHubError):
    """配置错误

    缺少API密钥、模型不存在、配置文件格式错误等。
    不可重试（需要修正配置）。
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            retryable=False,
            context=context,
            original_error=original_error
        )


class InternalError(AgentChatHubError):
    """内部错误

    代码bug、未预期异常、逻辑错误等。
    不可重试（需要修复代码）。
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.INTERNAL,
            retryable=False,
            context=context,
            original_error=original_error
        )


class ExternalError(AgentChatHubError):
    """外部服务错误

    外部API返回5xx、服务不可用等。
    默认可重试。
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL,
            retryable=True,
            context=context,
            original_error=original_error
        )
