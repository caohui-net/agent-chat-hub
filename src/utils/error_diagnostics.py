"""错误诊断工具

提供统一的错误日志格式和用户友好的错误消息生成。
"""
import structlog
from typing import Optional
from src.core.errors import AgentChatHubError, ErrorCategory

logger = structlog.get_logger()


class ErrorDiagnostics:
    """错误诊断工具类

    负责：
    - 统一的错误日志格式
    - 生成用户友好的错误消息
    - 针对不同错误类型提供不同的建议
    """

    @staticmethod
    def log_error(error: AgentChatHubError, additional_context: Optional[dict] = None) -> None:
        """记录错误到日志

        Args:
            error: AgentChatHubError实例
            additional_context: 额外的上下文信息
        """
        log_context = error.to_dict()
        if additional_context:
            log_context.update(additional_context)

        logger.error(
            "agent_error_occurred",
            **log_context
        )

    @staticmethod
    def get_user_message(error: AgentChatHubError) -> str:
        """生成用户友好的错误消息

        Args:
            error: AgentChatHubError实例

        Returns:
            格式化的用户消息
        """
        # 基础消息
        base_message = str(error)

        # 根据错误类型添加建议
        if error.category == ErrorCategory.NETWORK:
            suggestion = (
                "\n💡 建议：\n"
                "- 检查网络连接\n"
                "- 确认API服务可访问\n"
                "- 如果是超时错误，系统会自动重试"
            )
        elif error.category == ErrorCategory.API_LIMIT:
            suggestion = (
                "\n💡 建议：\n"
                "- API请求已达到限流阈值\n"
                "- 系统将自动重试（带延迟）\n"
                "- 如果持续出现，请检查API配额"
            )
        elif error.category == ErrorCategory.VALIDATION:
            suggestion = (
                "\n💡 建议：\n"
                "- 检查输入数据格式\n"
                "- 确认所有必填字段已提供\n"
                "- 参考文档确认参数类型"
            )
        elif error.category == ErrorCategory.CONFIGURATION:
            suggestion = (
                "\n💡 建议：\n"
                "- 检查配置文件格式\n"
                "- 确认API密钥已正确配置\n"
                "- 验证模型ID是否存在于配置中"
            )
        elif error.category == ErrorCategory.INTERNAL:
            suggestion = (
                "\n💡 建议：\n"
                "- 这可能是代码bug，请联系开发者\n"
                "- 可以尝试重启应用\n"
                "- 查看日志获取更多信息"
            )
        elif error.category == ErrorCategory.EXTERNAL:
            suggestion = (
                "\n💡 建议：\n"
                "- 外部API服务暂时不可用\n"
                "- 系统会自动重试\n"
                "- 如果持续失败，请检查API服务状态"
            )
        else:
            suggestion = ""

        # 添加上下文信息（如果有）
        context_info = ""
        if error.context:
            context_items = []
            for key, value in error.context.items():
                context_items.append(f"  - {key}: {value}")
            if context_items:
                context_info = "\n\n🔍 错误上下文：\n" + "\n".join(context_items)

        # 组合消息
        return f"❌ {base_message}{suggestion}{context_info}"

    @staticmethod
    def format_retry_message(error: AgentChatHubError, attempt: int, max_attempts: int) -> str:
        """格式化重试消息

        Args:
            error: AgentChatHubError实例
            attempt: 当前尝试次数
            max_attempts: 最大尝试次数

        Returns:
            格式化的重试消息
        """
        if error.retryable:
            return (
                f"🔄 正在重试... (尝试 {attempt}/{max_attempts})\n"
                f"原因: {str(error)}"
            )
        else:
            return (
                f"⚠️ 错误不可重试，请修正问题后再试\n"
                f"错误: {str(error)}"
            )
