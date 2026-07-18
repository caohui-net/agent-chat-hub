"""TUI API

提供给插件扩展TUI界面的接口
"""
from typing import Callable, Optional, Any
import structlog
from textual.screen import Screen

logger = structlog.get_logger(__name__)


class TUIAPI:
    """TUI API接口

    插件通过此API扩展TUI界面
    """

    def __init__(self, plugin_id: str, app):
        """初始化TUI API

        Args:
            plugin_id: 插件ID
            app: Textual应用实例
        """
        self.plugin_id = plugin_id
        self.app = app
        self._registered_screens: dict[str, type[Screen]] = {}
        self._registered_actions: dict[str, Callable] = {}

    def register_screen(self, name: str, screen_class: type[Screen]) -> bool:
        """注册新的TUI界面

        Args:
            name: 界面名称
            screen_class: 界面类（继承自textual.screen.Screen）

        Returns:
            bool: 是否成功注册
        """
        try:
            if name in self._registered_screens:
                logger.warning("screen_already_registered", plugin_id=self.plugin_id, name=name)
                return False

            self._registered_screens[name] = screen_class
            logger.info("screen_registered", plugin_id=self.plugin_id, name=name)
            return True

        except Exception as e:
            logger.error("register_screen_failed", plugin_id=self.plugin_id, name=name, error=str(e))
            return False

    def push_screen(self, name: str, **kwargs) -> bool:
        """打开已注册的界面

        Args:
            name: 界面名称
            **kwargs: 传递给界面构造函数的参数

        Returns:
            bool: 是否成功打开
        """
        try:
            if name not in self._registered_screens:
                logger.error("screen_not_found", plugin_id=self.plugin_id, name=name)
                return False

            screen_class = self._registered_screens[name]
            screen_instance = screen_class(**kwargs)
            self.app.push_screen(screen_instance)
            logger.info("screen_pushed", plugin_id=self.plugin_id, name=name)
            return True

        except Exception as e:
            logger.error("push_screen_failed", plugin_id=self.plugin_id, name=name, error=str(e))
            return False

    def register_action(self, action_name: str, callback: Callable,
                       binding: Optional[str] = None) -> bool:
        """注册TUI动作

        Args:
            action_name: 动作名称
            callback: 回调函数
            binding: 键盘绑定（如 "ctrl+p"）

        Returns:
            bool: 是否成功注册
        """
        try:
            if action_name in self._registered_actions:
                logger.warning("action_already_registered",
                             plugin_id=self.plugin_id, action=action_name)
                return False

            self._registered_actions[action_name] = callback

            # TODO: 实现动态添加键盘绑定
            if binding:
                logger.info("action_registered", plugin_id=self.plugin_id,
                          action=action_name, binding=binding)
            else:
                logger.info("action_registered", plugin_id=self.plugin_id, action=action_name)

            return True

        except Exception as e:
            logger.error("register_action_failed", plugin_id=self.plugin_id,
                       action=action_name, error=str(e))
            return False

    def show_notification(self, message: str, severity: str = "information",
                         timeout: int = 3) -> None:
        """显示通知消息

        Args:
            message: 通知内容
            severity: 严重级别（information/warning/error）
            timeout: 显示时长（秒）
        """
        try:
            self.app.notify(message, severity=severity, timeout=timeout)
            logger.debug("notification_shown", plugin_id=self.plugin_id, message=message)
        except Exception as e:
            logger.error("show_notification_failed", plugin_id=self.plugin_id, error=str(e))

    def update_status_bar(self, message: str) -> None:
        """更新状态栏文本

        Args:
            message: 状态栏消息
        """
        try:
            # TODO: 实现状态栏更新机制
            logger.debug("status_bar_update_requested", plugin_id=self.plugin_id, message=message)
        except Exception as e:
            logger.error("update_status_bar_failed", plugin_id=self.plugin_id, error=str(e))

    def add_menu_item(self, label: str, callback: Callable,
                     menu: str = "plugins") -> bool:
        """添加菜单项

        Args:
            label: 菜单项标签
            callback: 点击回调函数
            menu: 菜单名称（默认为plugins菜单）

        Returns:
            bool: 是否成功添加
        """
        try:
            # TODO: 实现动态菜单机制
            logger.info("menu_item_added", plugin_id=self.plugin_id,
                       label=label, menu=menu)
            return True
        except Exception as e:
            logger.error("add_menu_item_failed", plugin_id=self.plugin_id,
                       label=label, error=str(e))
            return False

    def get_registered_screens(self) -> dict[str, type[Screen]]:
        """获取插件注册的所有界面

        Returns:
            dict[str, type[Screen]]: 界面名称到类的映射
        """
        return self._registered_screens.copy()

    def get_registered_actions(self) -> dict[str, Callable]:
        """获取插件注册的所有动作

        Returns:
            dict[str, Callable]: 动作名称到回调的映射
        """
        return self._registered_actions.copy()
