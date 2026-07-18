"""插件加载器

实现插件的动态加载、依赖解析、版本检查
"""
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
import structlog

from .base import IPlugin
from .models import PluginMetadata
from .registry import PluginRegistry

logger = structlog.get_logger(__name__)


class PluginLoader:
    """插件加载器

    负责扫描、加载、验证插件
    """

    def __init__(self, plugins_dir: Path, registry: PluginRegistry):
        """初始化加载器

        Args:
            plugins_dir: 插件目录路径
            registry: 插件注册表实例
        """
        self.plugins_dir = plugins_dir
        self.registry = registry
        self._loaded_modules: Dict[str, object] = {}

    def scan_plugins(self) -> List[str]:
        """扫描插件目录

        Returns:
            List[str]: 发现的插件目录名列表
        """
        if not self.plugins_dir.exists():
            logger.warning("plugins_dir_not_found", path=str(self.plugins_dir))
            return []

        plugin_dirs = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                plugin_dirs.append(item.name)
                logger.debug("plugin_dir_found", name=item.name)

        return plugin_dirs

    def load_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """加载单个插件

        Args:
            plugin_name: 插件目录名

        Returns:
            Optional[IPlugin]: 加载的插件实例，失败返回None
        """
        plugin_path = self.plugins_dir / plugin_name
        if not plugin_path.exists():
            logger.error("plugin_path_not_found", name=plugin_name, path=str(plugin_path))
            return None

        try:
            # 动态导入插件模块
            module_name = f"plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(
                module_name,
                plugin_path / "__init__.py"
            )
            if spec is None or spec.loader is None:
                logger.error("plugin_spec_load_failed", name=plugin_name)
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            self._loaded_modules[plugin_name] = module

            # 查找插件类（必须继承IPlugin）
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, IPlugin) and
                    attr is not IPlugin):
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.error("plugin_class_not_found", name=plugin_name)
                return None

            # 实例化插件（需要PluginAPI，暂时传None）
            plugin_instance = plugin_class(plugin_api=None)  # TODO: 传入真实的PluginAPI

            # 验证元数据
            metadata = plugin_instance.get_metadata()
            if not self._validate_metadata(metadata):
                logger.error("plugin_metadata_invalid", name=plugin_name)
                return None

            # 调用on_load生命周期
            plugin_instance.on_load()

            logger.info("plugin_loaded", plugin_id=metadata.plugin_id, name=metadata.name)
            return plugin_instance

        except Exception as e:
            logger.error("plugin_load_failed", name=plugin_name, error=str(e))
            return None

    def _validate_metadata(self, metadata: PluginMetadata) -> bool:
        """验证插件元数据

        Args:
            metadata: 插件元数据

        Returns:
            bool: 元数据是否有效
        """
        if not metadata.plugin_id:
            return False
        if not metadata.name:
            return False
        if not metadata.version:
            return False
        return True

    def check_dependencies(self, metadata: PluginMetadata) -> bool:
        """检查插件依赖是否满足

        Args:
            metadata: 插件元数据

        Returns:
            bool: 依赖是否满足
        """
        for dep in metadata.dependencies:
            # 简单实现：只检查插件是否已加载
            # TODO: 支持版本范围检查（如 "plugin>=1.0.0"）
            dep_id = dep.split(">=")[0].split(">")[0].split("=")[0].strip()
            if not self.registry.has_plugin(dep_id):
                logger.warning("plugin_dependency_missing",
                             plugin_id=metadata.plugin_id,
                             dependency=dep_id)
                return False
        return True

    def resolve_load_order(self, plugin_names: List[str]) -> List[str]:
        """解析插件加载顺序（基于依赖关系）

        Args:
            plugin_names: 插件名列表

        Returns:
            List[str]: 按依赖顺序排列的插件名列表
        """
        # 简化实现：暂不支持复杂的依赖解析
        # TODO: 实现拓扑排序
        return plugin_names

    def load_all_plugins(self) -> Dict[str, IPlugin]:
        """加载所有插件

        Returns:
            Dict[str, IPlugin]: 插件ID到实例的映射
        """
        plugin_names = self.scan_plugins()
        ordered_names = self.resolve_load_order(plugin_names)

        loaded_plugins = {}
        for name in ordered_names:
            plugin = self.load_plugin(name)
            if plugin:
                metadata = plugin.get_metadata()
                self.registry.register(plugin)
                loaded_plugins[metadata.plugin_id] = plugin

        logger.info("all_plugins_loaded", count=len(loaded_plugins))
        return loaded_plugins

    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件

        Args:
            plugin_id: 插件ID

        Returns:
            bool: 是否成功卸载
        """
        plugin = self.registry.get_plugin(plugin_id)
        if not plugin:
            return False

        try:
            # 调用on_unload生命周期
            plugin.on_unload()

            # 从注册表移除
            self.registry.unregister(plugin_id)

            logger.info("plugin_unloaded", plugin_id=plugin_id)
            return True

        except Exception as e:
            logger.error("plugin_unload_failed", plugin_id=plugin_id, error=str(e))
            return False
