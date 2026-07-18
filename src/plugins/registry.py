"""插件注册表

管理已加载插件的注册、查询、状态跟踪
"""
from typing import Dict, List, Optional
from .base import IPlugin
from .models import PluginMetadata, PluginState
import structlog

logger = structlog.get_logger(__name__)


class PluginRegistry:
    """插件注册表

    维护所有已加载插件的实例和状态信息
    """

    def __init__(self):
        """初始化注册表"""
        self._plugins: Dict[str, IPlugin] = {}  # plugin_id -> plugin instance
        self._states: Dict[str, PluginState] = {}  # plugin_id -> state
        self._metadata: Dict[str, PluginMetadata] = {}  # plugin_id -> metadata

    def register(self, plugin: IPlugin) -> None:
        """注册插件实例

        Args:
            plugin: 插件实例

        Raises:
            ValueError: 如果插件ID已存在
        """
        metadata = plugin.get_metadata()
        plugin_id = metadata.plugin_id

        if plugin_id in self._plugins:
            raise ValueError(f"Plugin {plugin_id} already registered")

        self._plugins[plugin_id] = plugin
        self._metadata[plugin_id] = metadata
        self._states[plugin_id] = PluginState(
            plugin_id=plugin_id,
            status="loaded"
        )

        logger.info("plugin_registered", plugin_id=plugin_id, name=metadata.name)

    def unregister(self, plugin_id: str) -> None:
        """注销插件

        Args:
            plugin_id: 插件ID
        """
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            del self._metadata[plugin_id]
            del self._states[plugin_id]
            logger.info("plugin_unregistered", plugin_id=plugin_id)

    def get_plugin(self, plugin_id: str) -> Optional[IPlugin]:
        """获取插件实例

        Args:
            plugin_id: 插件ID

        Returns:
            Optional[IPlugin]: 插件实例，如果不存在则返回None
        """
        return self._plugins.get(plugin_id)

    def get_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        """获取插件元数据

        Args:
            plugin_id: 插件ID

        Returns:
            Optional[PluginMetadata]: 插件元数据，如果不存在则返回None
        """
        return self._metadata.get(plugin_id)

    def get_state(self, plugin_id: str) -> Optional[PluginState]:
        """获取插件状态

        Args:
            plugin_id: 插件ID

        Returns:
            Optional[PluginState]: 插件状态，如果不存在则返回None
        """
        return self._states.get(plugin_id)

    def update_state(self, plugin_id: str, status: str,
                    error_message: Optional[str] = None) -> None:
        """更新插件状态

        Args:
            plugin_id: 插件ID
            status: 新状态
            error_message: 错误信息（可选）
        """
        if plugin_id in self._states:
            self._states[plugin_id].status = status
            if error_message:
                self._states[plugin_id].error_message = error_message
            logger.info("plugin_state_updated", plugin_id=plugin_id, status=status)

    def list_plugins(self, status_filter: Optional[str] = None) -> List[str]:
        """列出所有插件ID

        Args:
            status_filter: 状态过滤器（可选）

        Returns:
            List[str]: 插件ID列表
        """
        if status_filter:
            return [
                pid for pid, state in self._states.items()
                if state.status == status_filter
            ]
        return list(self._plugins.keys())

    def get_all_metadata(self) -> Dict[str, PluginMetadata]:
        """获取所有插件元数据

        Returns:
            Dict[str, PluginMetadata]: 插件ID到元数据的映射
        """
        return self._metadata.copy()

    def has_plugin(self, plugin_id: str) -> bool:
        """检查插件是否存在

        Args:
            plugin_id: 插件ID

        Returns:
            bool: 插件是否存在
        """
        return plugin_id in self._plugins
