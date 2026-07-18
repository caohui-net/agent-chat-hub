"""Agent API

提供给插件访问和调用Agent的接口
"""
from typing import List, Optional, Dict, Any
import structlog
from src.core.models import AgentConfig, Message
from src.core.config import ConfigManager

logger = structlog.get_logger(__name__)


class AgentAPI:
    """Agent API接口

    插件通过此API访问Agent配置和调用Agent
    """

    def __init__(self, config_manager: ConfigManager, session_manager):
        """初始化Agent API

        Args:
            config_manager: 配置管理器实例
            session_manager: 会话管理器实例
        """
        self.config_manager = config_manager
        self.session_manager = session_manager

    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """获取Agent配置

        Args:
            agent_id: Agent ID

        Returns:
            Optional[AgentConfig]: Agent配置对象，如果不存在则返回None
        """
        try:
            return self.config_manager.get_agent(agent_id)
        except Exception as e:
            logger.error("get_agent_config_failed", agent_id=agent_id, error=str(e))
            return None

    def list_agents(self, active_only: bool = False) -> List[AgentConfig]:
        """列出所有Agent

        Args:
            active_only: 是否只返回启用的Agent

        Returns:
            List[AgentConfig]: Agent配置列表
        """
        try:
            return self.config_manager.list_agents(active_only=active_only)
        except Exception as e:
            logger.error("list_agents_failed", error=str(e))
            return []

    async def call_agent(self, agent_id: str, message: str,
                        context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """调用Agent处理消息

        Args:
            agent_id: Agent ID
            message: 消息内容
            context: 上下文信息（可选）

        Returns:
            Optional[str]: Agent的响应，如果失败则返回None
        """
        try:
            # 获取Agent配置
            agent_config = self.get_agent_config(agent_id)
            if not agent_config:
                logger.error("agent_not_found", agent_id=agent_id)
                return None

            # 调用Agent执行器
            response = await self.session_manager.executor.call_agent(
                agent_config=agent_config,
                message=message,
                context=context or {}
            )

            return response

        except Exception as e:
            logger.error("call_agent_failed", agent_id=agent_id, error=str(e))
            return None

    def add_agent(self, agent_config: AgentConfig) -> bool:
        """添加新Agent配置

        Args:
            agent_config: Agent配置对象

        Returns:
            bool: 是否成功添加
        """
        try:
            self.config_manager.add_agent(agent_config)
            logger.info("agent_added_by_plugin", agent_id=agent_config.agent_id)
            return True
        except Exception as e:
            logger.error("add_agent_failed", agent_id=agent_config.agent_id, error=str(e))
            return False

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """更新Agent配置

        Args:
            agent_id: Agent ID
            updates: 更新字典

        Returns:
            bool: 是否成功更新
        """
        try:
            agent_config = self.get_agent_config(agent_id)
            if not agent_config:
                return False

            # 更新字段
            for key, value in updates.items():
                if hasattr(agent_config, key):
                    setattr(agent_config, key, value)

            self.config_manager.save_config()
            logger.info("agent_updated_by_plugin", agent_id=agent_id)
            return True

        except Exception as e:
            logger.error("update_agent_failed", agent_id=agent_id, error=str(e))
            return False

    def remove_agent(self, agent_id: str) -> bool:
        """删除Agent配置

        Args:
            agent_id: Agent ID

        Returns:
            bool: 是否成功删除
        """
        try:
            # TODO: 实现ConfigManager的remove_agent方法
            logger.warning("remove_agent_not_implemented", agent_id=agent_id)
            return False
        except Exception as e:
            logger.error("remove_agent_failed", agent_id=agent_id, error=str(e))
            return False
