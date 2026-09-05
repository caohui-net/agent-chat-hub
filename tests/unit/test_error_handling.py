"""测试错误处理系统

测试错误分类、序列化和诊断功能。
"""
import pytest
from src.core.errors import (
    ErrorCategory, AgentChatHubError, NetworkError, APILimitError,
    ValidationError, ConfigurationError, InternalError, ExternalError
)
from src.utils.error_diagnostics import ErrorDiagnostics


class TestErrorCategories:
    """测试错误分类"""

    def test_network_error_is_retryable(self):
        """网络错误应该可重试"""
        error = NetworkError("Connection timeout")
        assert error.retryable is True
        assert error.category == ErrorCategory.NETWORK

    def test_api_limit_error_is_retryable(self):
        """API限流错误应该可重试"""
        error = APILimitError("Rate limit exceeded")
        assert error.retryable is True
        assert error.category == ErrorCategory.API_LIMIT

    def test_validation_error_not_retryable(self):
        """验证错误不应该重试"""
        error = ValidationError("Invalid input format")
        assert error.retryable is False
        assert error.category == ErrorCategory.VALIDATION

    def test_configuration_error_not_retryable(self):
        """配置错误不应该重试"""
        error = ConfigurationError("API key missing")
        assert error.retryable is False
        assert error.category == ErrorCategory.CONFIGURATION

    def test_internal_error_not_retryable(self):
        """内部错误不应该重试"""
        error = InternalError("Unexpected exception")
        assert error.retryable is False
        assert error.category == ErrorCategory.INTERNAL

    def test_external_error_is_retryable(self):
        """外部服务错误应该可重试"""
        error = ExternalError("Service unavailable")
        assert error.retryable is True
        assert error.category == ErrorCategory.EXTERNAL


class TestErrorSerialization:
    """测试错误序列化"""

    def test_error_to_dict_basic(self):
        """测试基础序列化"""
        error = NetworkError("Connection failed")
        result = error.to_dict()

        assert result["error_type"] == "NetworkError"
        assert result["category"] == "network"
        assert result["message"] == "Connection failed"
        assert result["retryable"] is True

    def test_error_to_dict_with_context(self):
        """测试带上下文的序列化"""
        context = {
            "agent_id": "test-agent",
            "timeout": 30.0
        }
        error = NetworkError("Timeout", context=context)
        result = error.to_dict()

        assert result["context"]["agent_id"] == "test-agent"
        assert result["context"]["timeout"] == 30.0

    def test_error_to_dict_with_original_error(self):
        """测试带原始异常的序列化"""
        original = ValueError("Invalid value")
        error = ValidationError("Validation failed", original_error=original)
        result = error.to_dict()

        assert "Invalid value" in result["original_error"]

    def test_all_error_types_serializable(self):
        """确保所有错误类型都可序列化"""
        errors = [
            NetworkError("Network error"),
            APILimitError("Rate limit"),
            ValidationError("Validation error"),
            ConfigurationError("Config error"),
            InternalError("Internal error"),
            ExternalError("External error")
        ]

        for error in errors:
            result = error.to_dict()
            assert "error_type" in result
            assert "category" in result
            assert "message" in result
            assert "retryable" in result


class TestErrorDiagnostics:
    """测试错误诊断"""

    def test_get_user_message_network_error(self):
        """测试网络错误的用户消息"""
        error = NetworkError("Connection timeout")
        message = ErrorDiagnostics.get_user_message(error)

        assert "Connection timeout" in message
        assert "检查网络连接" in message
        assert "自动重试" in message

    def test_get_user_message_api_limit_error(self):
        """测试API限流错误的用户消息"""
        error = APILimitError("Rate limit exceeded")
        message = ErrorDiagnostics.get_user_message(error)

        assert "Rate limit exceeded" in message
        assert "限流阈值" in message
        assert "自动重试" in message

    def test_get_user_message_validation_error(self):
        """测试验证错误的用户消息"""
        error = ValidationError("Invalid input")
        message = ErrorDiagnostics.get_user_message(error)

        assert "Invalid input" in message
        assert "输入数据格式" in message

    def test_get_user_message_configuration_error(self):
        """测试配置错误的用户消息"""
        error = ConfigurationError("API key missing")
        message = ErrorDiagnostics.get_user_message(error)

        assert "API key missing" in message
        assert "配置文件" in message
        assert "API密钥" in message

    def test_get_user_message_internal_error(self):
        """测试内部错误的用户消息"""
        error = InternalError("Unexpected bug")
        message = ErrorDiagnostics.get_user_message(error)

        assert "Unexpected bug" in message
        assert "代码bug" in message

    def test_get_user_message_external_error(self):
        """测试外部服务错误的用户消息"""
        error = ExternalError("Service unavailable")
        message = ErrorDiagnostics.get_user_message(error)

        assert "Service unavailable" in message
        assert "外部API服务" in message

    def test_get_user_message_with_context(self):
        """测试带上下文的用户消息"""
        context = {
            "agent_id": "test-agent",
            "model": "claude-3-opus"
        }
        error = NetworkError("Timeout", context=context)
        message = ErrorDiagnostics.get_user_message(error)

        assert "test-agent" in message
        assert "claude-3-opus" in message

    def test_format_retry_message_retryable(self):
        """测试可重试错误的重试消息"""
        error = NetworkError("Timeout")
        message = ErrorDiagnostics.format_retry_message(error, attempt=2, max_attempts=3)

        assert "正在重试" in message
        assert "2/3" in message
        assert "Timeout" in message

    def test_format_retry_message_not_retryable(self):
        """测试不可重试错误的重试消息"""
        error = ConfigurationError("API key missing")
        message = ErrorDiagnostics.format_retry_message(error, attempt=1, max_attempts=3)

        assert "不可重试" in message
        assert "API key missing" in message


class TestErrorContext:
    """测试错误上下文"""

    def test_context_preserved(self):
        """确保上下文信息被保留"""
        context = {
            "agent_id": "coordinator",
            "model": "gpt-4",
            "timeout": 120.0,
            "retry_count": 2
        }
        error = NetworkError("Connection failed", context=context)

        assert error.context["agent_id"] == "coordinator"
        assert error.context["model"] == "gpt-4"
        assert error.context["timeout"] == 120.0
        assert error.context["retry_count"] == 2

    def test_empty_context(self):
        """测试空上下文"""
        error = NetworkError("Error without context")
        assert error.context == {}

    def test_context_in_serialization(self):
        """确保上下文在序列化中被包含"""
        context = {"key": "value"}
        error = NetworkError("Error", context=context)
        result = error.to_dict()

        assert result["context"]["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
