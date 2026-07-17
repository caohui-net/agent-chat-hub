"""
Agent执行器 - 负责调用模型API并获取响应
"""
from typing import List, Optional, Dict, Any
import httpx
import structlog

from src.core.models import AgentConfig, ModelConfig, Message
from src.core.config import ConfigManager

logger = structlog.get_logger()


class AgentExecutionError(Exception):
    """Agent执行错误"""
    pass


class AgentExecutor:
    """
    Agent执行器 - 处理实际的模型API调用

    职责：
    - 根据agent配置调用对应的模型API
    - 处理不同provider的API差异
    - 返回标准化的响应
    """

    def __init__(self, config_manager: ConfigManager):
        """初始化执行器

        Args:
            config_manager: 配置管理器，用于获取模型配置和API密钥
        """
        self.config_manager = config_manager
        self.http_client = httpx.Client(timeout=120.0)

    def __del__(self):
        """清理HTTP客户端"""
        if hasattr(self, 'http_client'):
            self.http_client.close()

    def _build_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """将Message对象转换为API消息格式

        Args:
            messages: Message对象列表

        Returns:
            API格式的消息列表
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role in ("user", "assistant")  # 过滤system消息
        ]

    def _call_anthropic(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """调用Anthropic API

        Args:
            model_config: 模型配置
            messages: API格式的消息列表
            system_prompt: 系统提示词

        Returns:
            模型响应内容

        Raises:
            AgentExecutionError: API调用失败
        """
        api_key = self.config_manager.get_api_key(model_config.api_key_name)
        if not api_key:
            raise AgentExecutionError(f"API密钥未设置: {model_config.api_key_name}")

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": model_config.model_id,
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature,
            "messages": messages,
        }

        if system_prompt:
            payload["system"] = system_prompt

        # 合并额外参数
        payload.update(model_config.extra_params)

        try:
            response = self.http_client.post(
                f"{model_config.base_url}/v1/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

        except httpx.HTTPStatusError as e:
            logger.error("anthropic_api_error", status=e.response.status_code, body=e.response.text)
            raise AgentExecutionError(f"Anthropic API错误: {e.response.status_code}")
        except Exception as e:
            logger.error("anthropic_call_failed", error=str(e))
            raise AgentExecutionError(f"调用Anthropic失败: {e}")

    def _call_openai(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """调用OpenAI API

        Args:
            model_config: 模型配置
            messages: API格式的消息列表
            system_prompt: 系统提示词

        Returns:
            模型响应内容

        Raises:
            AgentExecutionError: API调用失败
        """
        api_key = self.config_manager.get_api_key(model_config.api_key_name)
        if not api_key:
            raise AgentExecutionError(f"API密钥未设置: {model_config.api_key_name}")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # 如果有system prompt，插入到messages开头
        api_messages = messages.copy()
        if system_prompt:
            api_messages.insert(0, {"role": "system", "content": system_prompt})

        payload = {
            "model": model_config.model_id,
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature,
            "messages": api_messages,
        }

        # 合并额外参数
        payload.update(model_config.extra_params)

        try:
            response = self.http_client.post(
                f"{model_config.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logger.error("openai_api_error", status=e.response.status_code, body=e.response.text)
            raise AgentExecutionError(f"OpenAI API错误: {e.response.status_code}")
        except Exception as e:
            logger.error("openai_call_failed", error=str(e))
            raise AgentExecutionError(f"调用OpenAI失败: {e}")

    def execute(
        self,
        agent_config: AgentConfig,
        messages: List[Message]
    ) -> str:
        """执行agent调用

        Args:
            agent_config: Agent配置
            messages: 对话历史消息

        Returns:
            Agent响应内容

        Raises:
            AgentExecutionError: 执行失败
        """
        # 获取模型配置
        model_config = self.config_manager.get_model(agent_config.model_id)
        if not model_config:
            raise AgentExecutionError(f"模型配置不存在: {agent_config.model_id}")

        # 转换消息格式
        api_messages = self._build_messages(messages)

        logger.info(
            "executing_agent",
            agent_id=agent_config.agent_id,
            model=model_config.model_id,
            provider=model_config.provider,
            message_count=len(api_messages)
        )

        # 根据provider分发调用
        if model_config.provider == "anthropic":
            return self._call_anthropic(
                model_config,
                api_messages,
                agent_config.system_prompt
            )
        elif model_config.provider == "openai":
            return self._call_openai(
                model_config,
                api_messages,
                agent_config.system_prompt
            )
        else:
            raise AgentExecutionError(f"不支持的provider: {model_config.provider}")

