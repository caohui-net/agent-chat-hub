"""配置API

提供给插件读写配置的接口
"""
from typing import Any, Optional, Dict, Callable
import structlog
from pathlib import Path
import json

logger = structlog.get_logger(__name__)


class ConfigAPI:
    """配置API接口

    插件通过此API管理自己的配置数据
    """

    def __init__(self, plugin_id: str, config_dir: Path):
        """初始化配置API

        Args:
            plugin_id: 插件ID
            config_dir: 插件配置目录
        """
        self.plugin_id = plugin_id
        self.config_dir = config_dir
        self.plugin_config_file = config_dir / f"{plugin_id}.json"
        self._config_cache: Dict[str, Any] = {}
        self._watchers: Dict[str, list[Callable]] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载插件配置"""
        if self.plugin_config_file.exists():
            try:
                with open(self.plugin_config_file, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
            except Exception as e:
                logger.error("load_config_failed", plugin_id=self.plugin_id, error=str(e))
                self._config_cache = {}
        else:
            self._config_cache = {}

    def _save_config(self) -> bool:
        """保存插件配置"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.plugin_config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_cache, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error("save_config_failed", plugin_id=self.plugin_id, error=str(e))
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """读取配置值

        Args:
            key: 配置键（支持点分隔的嵌套路径，如 "section.subsection.key"）
            default: 默认值

        Returns:
            Any: 配置值，如果不存在则返回默认值
        """
        keys = key.split('.')
        value = self._config_cache

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> bool:
        """写入配置值

        Args:
            key: 配置键（支持点分隔的嵌套路径）
            value: 配置值

        Returns:
            bool: 是否成功写入
        """
        keys = key.split('.')
        config = self._config_cache

        # 导航到目标位置，创建中间字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        old_value = config.get(keys[-1])
        config[keys[-1]] = value

        # 保存配置
        if self._save_config():
            # 触发监听器
            if key in self._watchers:
                for callback in self._watchers[key]:
                    try:
                        callback(old_value, value)
                    except Exception as e:
                        logger.error("config_watcher_failed", key=key, error=str(e))
            return True
        return False

    def delete(self, key: str) -> bool:
        """删除配置值

        Args:
            key: 配置键

        Returns:
            bool: 是否成功删除
        """
        keys = key.split('.')
        config = self._config_cache

        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                return False
            config = config[k]

        # 删除值
        if keys[-1] in config:
            del config[keys[-1]]
            return self._save_config()

        return False

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        return self._config_cache.copy()

    def watch(self, key: str, callback: Callable[[Any, Any], None]) -> None:
        """监听配置变化

        Args:
            key: 配置键
            callback: 回调函数，接收 (old_value, new_value) 参数
        """
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)
        logger.debug("config_watcher_added", plugin_id=self.plugin_id, key=key)

    def unwatch(self, key: str, callback: Callable[[Any, Any], None]) -> None:
        """取消监听配置变化

        Args:
            key: 配置键
            callback: 回调函数
        """
        if key in self._watchers and callback in self._watchers[key]:
            self._watchers[key].remove(callback)
            logger.debug("config_watcher_removed", plugin_id=self.plugin_id, key=key)
