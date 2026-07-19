"""核心异常类定义"""


class UnsupportedProviderError(Exception):
    """Provider不支持错误

    当尝试执行不支持的provider时抛出。
    用于分层策略：配置可加载，但执行时拦截。
    """

    def __init__(self, provider: str, supported_providers: list):
        """初始化异常

        Args:
            provider: 不支持的provider名称
            supported_providers: 支持的provider列表
        """
        self.provider = provider
        self.supported_providers = supported_providers

        # 构建详细错误信息
        supported_list = ", ".join(supported_providers)
        message = (
            f"Provider '{provider}' 暂不支持执行。\n"
            f"当前支持的providers: {supported_list}\n"
            f"\n"
            f"迁移指引:\n"
            f"- 如需使用Anthropic模型，请设置provider='anthropic'\n"
            f"- 如需使用OpenAI兼容模型，请设置provider='openai'\n"
            f"- 历史配置（google/custom）可保留在配置文件中，但执行时需切换"
        )
        super().__init__(message)
