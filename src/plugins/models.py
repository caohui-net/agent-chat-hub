"""插件系统数据模型

定义插件元数据、配置、状态等核心数据结构
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class PluginMetadata(BaseModel):
    """插件元数据"""
    model_config = ConfigDict(frozen=False)

    plugin_id: str = Field(..., description="插件唯一标识符")
    name: str = Field(..., description="插件名称")
    version: str = Field(..., description="插件版本（语义化版本）")
    description: str = Field(..., description="插件描述")
    author: str = Field(..., description="插件作者")

    # 依赖信息
    dependencies: List[str] = Field(default_factory=list, description="依赖的其他插件ID列表")
    min_system_version: str = Field(default="0.1.0", description="最低系统版本要求")

    # 能力声明
    provides: List[str] = Field(default_factory=list, description="提供的功能列表")
    hooks: List[str] = Field(default_factory=list, description="注册的钩子列表")

    # 配置
    config_schema: Dict[str, Any] = Field(default_factory=dict, description="配置模式（JSON Schema）")
    default_config: Dict[str, Any] = Field(default_factory=dict, description="默认配置")


class PluginConfig(BaseModel):
    """插件配置"""
    model_config = ConfigDict(frozen=False)

    plugin_id: str = Field(..., description="插件ID")
    enabled: bool = Field(default=True, description="是否启用")
    config: Dict[str, Any] = Field(default_factory=dict, description="用户配置")


class PluginState(BaseModel):
    """插件运行状态"""
    model_config = ConfigDict(frozen=False)

    plugin_id: str = Field(..., description="插件ID")
    status: str = Field(default="unloaded", description="状态: unloaded/loaded/enabled/error")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    load_time: Optional[float] = Field(default=None, description="加载时间戳")
    enable_time: Optional[float] = Field(default=None, description="启用时间戳")
