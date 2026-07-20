"""核心数据模型 - 使用Pydantic进行数据验证"""

import time
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from dataclasses import dataclass


def _current_timestamp() -> float:
    """获取当前Unix时间戳（秒）

    P3-001: 提取时间戳生成为独立函数，提升代码清晰度和可测试性

    Returns:
        当前Unix时间戳
    """
    return time.time()


@dataclass
class TokenUsage:
    """Token使用统计（统一接口）

    用于跨provider的token使用追踪，支持缓存token统计。
    """
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """总token数（不包括缓存读取，只计算实际消耗）"""
        return self.input_tokens + self.output_tokens


class ModelConfig(BaseModel):
    """模型配置

    定义单个AI模型的配置信息，包括API端点、认证信息和参数。
    """

    model_config = ConfigDict(frozen=False)

    # 基本信息
    model_id: str = Field(..., description="模型唯一标识符，如 'claude-opus-4'")
    provider: str = Field(..., description="模型提供商，如 'anthropic', 'openai'")
    display_name: str = Field(..., description="模型显示名称")

    # API配置
    base_url: str = Field(..., description="API基础URL")
    api_key_name: str = Field(..., description="API密钥在keyring中的名称")
    api_key: Optional[str] = Field(default=None, description="API密钥（可选，直接存储）")

    # 模型参数
    max_tokens: int = Field(default=4096, ge=1, le=200000, description="最大生成token数")
    temperature: float = Field(default=1.0, ge=0.0, le=2.0, description="温度参数")

    # 可选参数
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="额外的模型参数")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """验证base_url格式"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url必须以http://或https://开头")
        return v.rstrip("/")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """验证provider值"""
        allowed = ["anthropic", "openai", "google", "custom", "gemini-cli"]
        if v not in allowed:
            raise ValueError(f"provider必须是以下之一: {allowed}")
        return v


class AgentConfig(BaseModel):
    """Agent配置

    定义单个Agent的配置信息，包括关联的模型、角色和优先级。
    """

    model_config = ConfigDict(frozen=False)

    # 基本信息
    agent_id: str = Field(..., description="Agent唯一标识符")
    name: str = Field(..., description="Agent显示名称")
    role: str = Field(..., description="Agent角色描述，如 '技术助手', '代码审查'")

    # 模型关联
    model_id: str = Field(..., description="关联的模型ID，对应ModelConfig.model_id")

    # 行为配置
    priority: int = Field(default=100, ge=0, le=1000, description="优先级，用于排序（升序）")
    active: bool = Field(default=True, description="是否激活")

    # 可选配置
    system_prompt: Optional[str] = Field(default=None, description="自定义系统提示")
    extra_config: Dict[str, Any] = Field(default_factory=dict, description="额外配置")

    @field_validator("agent_id", "name")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """验证非空字符串"""
        if not v or not v.strip():
            raise ValueError("字段不能为空")
        return v.strip()


class Message(BaseModel):
    """聊天消息

    表示用户或Agent的单条消息。
    """

    model_config = ConfigDict(frozen=False)

    # 消息内容
    role: str = Field(..., description="消息角色: 'user', 'assistant', 'system'")
    content: str = Field(..., description="消息内容")

    # 元数据
    agent_id: Optional[str] = Field(default=None, description="发送此消息的Agent ID（若为Agent消息）")
    timestamp: float = Field(default_factory=_current_timestamp, description="消息时间戳")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """验证角色值"""
        allowed = ["user", "assistant", "system"]
        if v not in allowed:
            raise ValueError(f"role必须是以下之一: {allowed}")
        return v


class SessionConfig(BaseModel):
    """会话配置

    定义单个会话的配置和状态。
    """

    model_config = ConfigDict(frozen=False)

    # 会话信息
    session_id: str = Field(..., description="会话唯一标识符")
    title: str = Field(default="新对话", description="会话标题")

    # 激活的Agents
    active_agent_ids: list[str] = Field(default_factory=list, description="当前激活的Agent ID列表")

    # 会话历史
    messages: list[Message] = Field(default_factory=list, description="消息历史")

    # 元数据
    created_at: float = Field(default_factory=_current_timestamp, description="创建时间戳")
    updated_at: float = Field(default_factory=_current_timestamp, description="更新时间戳")


class AgentMessage(BaseModel):
    """Agent间消息

    用于Agent之间的通信。
    """

    model_config = ConfigDict(frozen=False)

    # 消息标识
    message_id: str = Field(..., description="消息唯一标识符")
    message_type: str = Field(..., description="消息类型: 'query', 'response', 'notification', 'broadcast'")

    # 路由信息
    from_agent_id: str = Field(..., description="发送方Agent ID")
    to_agent_id: Optional[str] = Field(default=None, description="接收方Agent ID，None表示广播")

    # 消息内容
    content: str = Field(..., description="消息内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="消息元数据")

    # 时间戳
    timestamp: float = Field(default_factory=_current_timestamp, description="消息时间戳")

    # 关联信息（用于响应消息）
    reply_to: Optional[str] = Field(default=None, description="回复的消息ID")
