"""
Agent执行器 - 负责调用模型API并获取响应（异步版本支持并发）
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING
import httpx
import structlog
import uuid
import subprocess
import json

from src.core.models import AgentConfig, ModelConfig, Message, TokenUsage, AgentMessage
from src.core.config import ConfigManager
from src.core.exceptions import UnsupportedProviderError

if TYPE_CHECKING:
    from src.agents.message_bus import MessageBus

logger = structlog.get_logger()


class AgentExecutionError(Exception):
    """Agent执行错误"""
    pass


class AgentExecutor:
    """
    Agent执行器 - 处理实际的模型API调用（异步版本）

    职责：
    - 根据agent配置调用对应的模型API
    - 处理不同provider的API差异
    - 返回标准化的响应
    - 支持并发调用多个agents
    """

    # 支持的provider列表（执行层拦截）
    SUPPORTED_PROVIDERS = ["anthropic", "openai", "gemini-cli", "gemini-http"]

    def __init__(
        self,
        config_manager: ConfigManager,
        message_bus: Optional["MessageBus"] = None
    ):
        """初始化执行器

        Args:
            config_manager: 配置管理器，用于获取模型配置和API密钥
            message_bus: 消息总线（可选），用于发布token使用事件
        """
        self.config_manager = config_manager
        self.message_bus = message_bus
        self.http_client = httpx.AsyncClient(timeout=120.0)

    async def aclose(self):
        """异步关闭HTTP客户端"""
        if hasattr(self, 'http_client'):
            await self.http_client.aclose()

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

    async def _publish_usage(self, model_id: str, token_usage: TokenUsage) -> None:
        """发布token使用事件到MessageBus

        Args:
            model_id: 模型ID
            token_usage: Token使用统计
        """
        if not self.message_bus:
            return

        # P1-001: 通过MessageBus发布usage事件
        usage_message = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type="agent_usage",
            from_agent_id="executor",
            content="Token usage event",
            metadata={
                "model_id": model_id,
                "input_tokens": token_usage.input_tokens,
                "output_tokens": token_usage.output_tokens,
                "cache_read_tokens": token_usage.cache_read_tokens,
                "cache_write_tokens": token_usage.cache_write_tokens,
                "total_tokens": token_usage.total_tokens
            }
        )
        await self.message_bus.publish(usage_message)

    async def _call_anthropic(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """调用Anthropic API（异步）

        Args:
            model_config: 模型配置
            messages: API格式的消息列表
            system_prompt: 系统提示词

        Returns:
            模型响应内容

        Raises:
            AgentExecutionError: API调用失败
        """
        # 优先使用配置文件中的api_key，否则从keyring读取
        api_key = model_config.api_key or self.config_manager.get_api_key(model_config.api_key_name)
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
            response = await self.http_client.post(
                f"{model_config.base_url}/v1/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # P1-001: 提取token使用并发布事件
            if self.message_bus and "usage" in data:
                usage_data = data["usage"]
                token_usage = TokenUsage(
                    input_tokens=usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("output_tokens", 0),
                    cache_read_tokens=usage_data.get("cache_read_input_tokens", 0),
                    cache_write_tokens=usage_data.get("cache_creation_input_tokens", 0)
                )
                await self._publish_usage(model_config.model_id, token_usage)

            return data["content"][0]["text"]

        except httpx.HTTPStatusError as e:
            logger.error("anthropic_api_error", status=e.response.status_code, body=e.response.text)
            raise AgentExecutionError(f"Anthropic API错误: {e.response.status_code}")
        except Exception as e:
            # P3-005: 保留Exception兜底 - API调用可能出现多种异常(网络、JSON解析等)
            logger.error("anthropic_call_failed", error=str(e))
            raise AgentExecutionError(f"调用Anthropic失败: {e}")

    async def _call_openai(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """调用OpenAI API（异步）

        Args:
            model_config: 模型配置
            messages: API格式的消息列表
            system_prompt: 系统提示词

        Returns:
            模型响应内容

        Raises:
            AgentExecutionError: API调用失败
        """
        # 优先使用配置文件中的api_key，否则从keyring读取
        api_key = model_config.api_key or self.config_manager.get_api_key(model_config.api_key_name)
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
            response = await self.http_client.post(
                f"{model_config.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # P1-001: 提取token使用并发布事件
            if self.message_bus and "usage" in data:
                usage_data = data["usage"]
                token_usage = TokenUsage(
                    input_tokens=usage_data.get("prompt_tokens", 0),
                    output_tokens=usage_data.get("completion_tokens", 0),
                    cache_read_tokens=0,  # OpenAI API不提供缓存信息
                    cache_write_tokens=0
                )
                await self._publish_usage(model_config.model_id, token_usage)

            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logger.error("openai_api_error", status=e.response.status_code, body=e.response.text)
            raise AgentExecutionError(f"OpenAI API错误: {e.response.status_code}")
        except Exception as e:
            # P3-005: 保留Exception兜底 - API调用可能出现多种异常(网络、JSON解析等)
            logger.error("openai_call_failed", error=str(e))
            raise AgentExecutionError(f"调用OpenAI失败: {e}")

    async def _call_gemini_cli(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """通过Gemini CLI调用模型（subprocess方式）

        Args:
            model_config: 模型配置
            messages: API格式的消息列表
            system_prompt: 系统提示词（暂不支持）

        Returns:
            模型响应内容

        Raises:
            AgentExecutionError: CLI调用失败
        """
        try:
            # 构造用户消息（只取最后一条user消息）
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            if not user_messages:
                raise AgentExecutionError("没有用户消息")

            prompt = user_messages[-1]["content"]

            # 调用gemini CLI
            result = subprocess.run(
                ["gemini", "-p", prompt, "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error("gemini_cli_error", stderr=result.stderr)
                raise AgentExecutionError(f"Gemini CLI返回错误: {result.stderr}")

            # 解析JSON输出
            output_data = json.loads(result.stdout)
            response_text = output_data.get("response", "")

            if not response_text:
                raise AgentExecutionError("Gemini CLI返回空响应")

            logger.info("gemini_cli_success", response_length=len(response_text))
            return response_text

        except subprocess.TimeoutExpired:
            logger.error("gemini_cli_timeout")
            raise AgentExecutionError("Gemini CLI调用超时")
        except json.JSONDecodeError as e:
            logger.error("gemini_cli_json_error", error=str(e))
            raise AgentExecutionError(f"解析Gemini CLI输出失败: {e}")
        except Exception as e:
            logger.error("gemini_cli_failed", error=str(e))
            raise AgentExecutionError(f"调用Gemini CLI失败: {e}")

    async def _call_gemini_http(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """通过HTTP API调用Gemini（改进版）

        Args:
            model_config: 模型配置
            messages: API格式的消息列表（完整历史）
            system_prompt: 系统提示词

        Returns:
            模型响应内容

        Raises:
            AgentExecutionError: API调用失败
        """
        try:
            # 获取API密钥
            api_key = model_config.api_key or self.config_manager.get_api_key(
                model_config.api_key_name
            )
            if not api_key:
                raise AgentExecutionError(f"API密钥未设置: {model_config.api_key_name}")

            # 转换消息格式：OpenAI格式 → Gemini格式
            contents = []
            for msg in messages:
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            # 构造请求URL
            url = f"{model_config.base_url}/v1beta/models/{model_config.model_id}:generateContent"

            # 构造请求头
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            }

            # 构造请求体
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": model_config.temperature,
                    "maxOutputTokens": model_config.max_tokens,
                }
            }

            # 添加系统指令（如果有）
            if system_prompt:
                payload["systemInstruction"] = {
                    "parts": [{"text": system_prompt}]
                }

            logger.info("gemini_http_request",
                       url=url,
                       message_count=len(messages))

            # 发送请求
            response = await self.http_client.post(
                url,
                headers=headers,
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()

            # 解析响应
            data = response.json()

            if "candidates" not in data or not data["candidates"]:
                raise AgentExecutionError("Gemini API返回空响应")

            candidate = data["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                raise AgentExecutionError("Gemini API响应格式错误")

            response_text = candidate["content"]["parts"][0]["text"]

            logger.info("gemini_http_success", response_length=len(response_text))
            return response_text

        except httpx.HTTPStatusError as e:
            logger.error("gemini_http_error",
                        status=e.response.status_code,
                        detail=e.response.text)
            raise AgentExecutionError(f"Gemini API调用失败: {e.response.status_code}")
        except Exception as e:
            logger.error("gemini_http_failed", error=str(e))
            raise AgentExecutionError(f"调用Gemini HTTP API失败: {e}")

    async def execute(
        self,
        agent_config: AgentConfig,
        messages: List[Message]
    ) -> str:
        """执行agent调用（异步）

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

        # 检查provider支持（执行层拦截）
        if model_config.provider not in self.SUPPORTED_PROVIDERS:
            raise UnsupportedProviderError(
                provider=model_config.provider,
                supported_providers=self.SUPPORTED_PROVIDERS
            )

        # 转换消息格式
        api_messages = self._build_messages(messages)

        logger.info(
            "executing_agent",
            agent_id=agent_config.agent_id,
            model=model_config.model_id,
            provider=model_config.provider,
            message_count=len(api_messages)
        )

        # 根据provider分发调用（异步）
        # provider已在上方检查，此处仅处理支持的providers
        if model_config.provider == "anthropic":
            return await self._call_anthropic(
                model_config,
                api_messages,
                agent_config.system_prompt
            )
        elif model_config.provider == "openai":
            return await self._call_openai(
                model_config,
                api_messages,
                agent_config.system_prompt
            )
        elif model_config.provider == "gemini-http":
            return await self._call_gemini_http(
                model_config,
                api_messages,
                agent_config.system_prompt
            )
        else:  # gemini-cli
            return await self._call_gemini_cli(
                model_config,
                api_messages,
                agent_config.system_prompt
            )

