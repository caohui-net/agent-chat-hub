"""配置管理模块 - 处理模型和Agent配置，提供API密钥安全存储"""

import json
from pathlib import Path
from typing import Optional, Dict, List
import keyring
from .models import ModelConfig, AgentConfig


class ConfigManager:
    """配置管理器

    负责：
    1. API密钥的安全存储（使用系统keyring）
    2. 模型配置和Agent配置的管理
    3. 配置文件的加载和保存
    """

    # Keyring service名称
    KEYRING_SERVICE = "agent-chat-hub"

    def __init__(self, config_dir: Optional[Path] = None):
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为~/.agent-chat-hub
        """
        if config_dir is None:
            config_dir = Path.home() / ".agent-chat-hub"

        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.models_file = self.config_dir / "models.json"
        self.agents_file = self.config_dir / "agents.json"

        # 内存中的配置
        self.models: Dict[str, ModelConfig] = {}
        self.agents: Dict[str, AgentConfig] = {}

    # ========== API密钥管理（存储层：keyring）==========

    def set_api_key(self, key_name: str, api_key: str) -> None:
        """安全存储API密钥到系统keyring

        Args:
            key_name: 密钥名称（如 'anthropic_api_key'）
            api_key: API密钥值

        注意：密钥存储在操作系统密钥环中，不会写入配置文件或日志。
        """
        keyring.set_password(self.KEYRING_SERVICE, key_name, api_key)

    def get_api_key(self, key_name: str) -> Optional[str]:
        """从系统keyring获取API密钥

        Args:
            key_name: 密钥名称

        Returns:
            API密钥值，若不存在则返回None

        注意：此方法返回实际密钥值，仅用于API调用，不应用于显示。
        """
        return keyring.get_password(self.KEYRING_SERVICE, key_name)

    def delete_api_key(self, key_name: str) -> None:
        """从系统keyring删除API密钥

        Args:
            key_name: 密钥名称
        """
        try:
            keyring.delete_password(self.KEYRING_SERVICE, key_name)
        except keyring.errors.PasswordDeleteError:
            pass  # 密钥不存在，忽略

    def mask_api_key(self, key_name: str) -> str:
        """返回API密钥的固定长度遮罩（显示层）

        Args:
            key_name: 密钥名称

        Returns:
            固定长度遮罩字符串（8个星号），若密钥不存在则返回"未设置"

        注意：遮罩长度固定，不泄露密钥长度、前缀或后缀。
        """
        api_key = self.get_api_key(key_name)
        if api_key is None:
            return "未设置"
        return "********"  # 固定8个星号，符合ADR-0001要求

    # ========== 模型配置管理 ==========

    def add_model(self, model: ModelConfig) -> None:
        """添加或更新模型配置

        Args:
            model: 模型配置对象
        """
        self.models[model.model_id] = model

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """获取模型配置

        Args:
            model_id: 模型ID

        Returns:
            模型配置对象，若不存在则返回None
        """
        return self.models.get(model_id)

    def delete_model(self, model_id: str) -> bool:
        """删除模型配置

        Args:
            model_id: 模型ID

        Returns:
            是否成功删除
        """
        if model_id in self.models:
            del self.models[model_id]
            return True
        return False

    def list_models(self) -> List[ModelConfig]:
        """列出所有模型配置

        Returns:
            模型配置列表
        """
        return list(self.models.values())

    # ========== Agent配置管理 ==========

    def add_agent(self, agent: AgentConfig) -> None:
        """添加或更新Agent配置

        Args:
            agent: Agent配置对象
        """
        self.agents[agent.agent_id] = agent

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """获取Agent配置

        Args:
            agent_id: Agent ID

        Returns:
            Agent配置对象，若不存在则返回None
        """
        return self.agents.get(agent_id)

    def delete_agent(self, agent_id: str) -> bool:
        """删除Agent配置

        Args:
            agent_id: Agent ID

        Returns:
            是否成功删除
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False

    def list_agents(self, active_only: bool = False) -> List[AgentConfig]:
        """列出所有Agent配置

        Args:
            active_only: 是否只返回激活的Agent

        Returns:
            Agent配置列表
        """
        agents = list(self.agents.values())
        if active_only:
            agents = [a for a in agents if a.active]
        return agents

    # ========== 配置文件加载和保存 ==========

    def load_configs(self) -> None:
        """从文件加载模型和Agent配置"""
        # 加载模型配置
        if self.models_file.exists():
            try:
                with open(self.models_file, "r", encoding="utf-8") as f:
                    models_data = json.load(f)
                    self.models = {
                        model_id: ModelConfig(**data)
                        for model_id, data in models_data.items()
                    }
            except (json.JSONDecodeError, ValueError) as e:
                print(f"警告: 模型配置文件加载失败: {e}")
                self.models = {}

        # 加载Agent配置
        if self.agents_file.exists():
            try:
                with open(self.agents_file, "r", encoding="utf-8") as f:
                    agents_data = json.load(f)
                    self.agents = {
                        agent_id: AgentConfig(**data)
                        for agent_id, data in agents_data.items()
                    }
            except (json.JSONDecodeError, ValueError) as e:
                print(f"警告: Agent配置文件加载失败: {e}")
                self.agents = {}

    def save_configs(self) -> None:
        """保存模型和Agent配置到文件

        注意：API密钥不会保存到文件，只保存配置中的api_key_name字段。
        """
        # 保存模型配置
        models_data = {
            model_id: model.model_dump()
            for model_id, model in self.models.items()
        }
        with open(self.models_file, "w", encoding="utf-8") as f:
            json.dump(models_data, f, indent=2, ensure_ascii=False)

        # 保存Agent配置
        agents_data = {
            agent_id: agent.model_dump()
            for agent_id, agent in self.agents.items()
        }
        with open(self.agents_file, "w", encoding="utf-8") as f:
            json.dump(agents_data, f, indent=2, ensure_ascii=False)
