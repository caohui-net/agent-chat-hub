"""插件系统基类和接口

定义插件的基类、生命周期钩子、事件系统
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from .models import PluginMetadata


class IPlugin(ABC):
    """插件接口（抽象基类）

    所有插件必须继承此类并实现必要的方法
    """

    def __init__(self, plugin_api: 'PluginAPI'):
        """初始化插件

        Args:
            plugin_api: 插件API实例，提供系统功能访问
        """
        self.plugin_api = plugin_api
        self._metadata: Optional[PluginMetadata] = None
        self._config: Dict[str, Any] = {}

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """返回插件元数据

        Returns:
            PluginMetadata: 插件元数据对象
        """
        pass

    def on_load(self) -> None:
        """插件加载时的回调

        在插件被加载到内存后调用，用于初始化资源
        """
        pass

    def on_enable(self) -> None:
        """插件启用时的回调

        在插件被启用后调用，用于注册钩子、启动服务等
        """
        pass

    def on_disable(self) -> None:
        """插件禁用时的回调

        在插件被禁用前调用，用于清理资源、取消注册等
        """
        pass

    def on_unload(self) -> None:
        """插件卸载时的回调

        在插件从内存中卸载前调用，用于释放所有资源
        """
        pass

    def on_config_change(self, new_config: Dict[str, Any]) -> None:
        """配置更新时的回调

        Args:
            new_config: 新的配置字典
        """
        self._config = new_config

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置

        Returns:
            Dict[str, Any]: 当前配置字典
        """
        return self._config


class PluginHook:
    """插件钩子

    用于在特定事件发生时调用插件的回调函数
    """

    def __init__(self, name: str):
        """初始化钩子

        Args:
            name: 钩子名称
        """
        self.name = name
        self._callbacks: List[tuple] = []  # (priority, plugin_id, callback)

    def register(self, plugin_id: str, callback, priority: int = 50) -> None:
        """注册回调函数

        Args:
            plugin_id: 插件ID
            callback: 回调函数
            priority: 优先级（0-100，数字越小优先级越高）
        """
        self._callbacks.append((priority, plugin_id, callback))
        self._callbacks.sort(key=lambda x: x[0])  # 按优先级排序

    def unregister(self, plugin_id: str) -> None:
        """取消注册插件的所有回调

        Args:
            plugin_id: 插件ID
        """
        self._callbacks = [cb for cb in self._callbacks if cb[1] != plugin_id]

    def execute(self, *args, **kwargs) -> List[Any]:
        """执行所有注册的回调

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[Any]: 所有回调的返回值列表
        """
        results = []
        for priority, plugin_id, callback in self._callbacks:
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                # TODO: 记录错误日志
                print(f"Hook {self.name} execution error in {plugin_id}: {e}")
        return results


class PluginEvent:
    """插件事件

    用于插件间的事件通信
    """

    def __init__(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """初始化事件

        Args:
            event_type: 事件类型
            data: 事件数据
        """
        self.event_type = event_type
        self.data = data or {}
        self.cancelled = False

    def cancel(self) -> None:
        """取消事件"""
        self.cancelled = True
