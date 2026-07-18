"""Hello Plugin - 基础插件示例

这是一个最简单的插件实现，展示插件的基本结构和生命周期
"""
from src.plugins.base import IPlugin
from src.plugins.models import PluginMetadata


class HelloPlugin(IPlugin):
    """Hello插件

    展示基础插件功能：
    - 生命周期钩子
    - 配置管理
    - 日志记录
    """

    def get_metadata(self) -> PluginMetadata:
        """返回插件元数据"""
        return PluginMetadata(
            plugin_id="hello_plugin",
            name="Hello Plugin",
            version="1.0.0",
            description="基础插件示例 - 展示插件生命周期和基本功能",
            author="Agent Chat Hub Team",
            dependencies=[],
            provides=["hello_command"],
            hooks=[],
            config_schema={
                "type": "object",
                "properties": {
                    "greeting": {
                        "type": "string",
                        "description": "问候语",
                        "default": "Hello"
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "是否启用",
                        "default": True
                    }
                }
            },
            default_config={
                "greeting": "Hello",
                "enabled": True
            }
        )

    def on_load(self) -> None:
        """插件加载时调用"""
        if self.plugin_api:
            self.plugin_api.logger.info("HelloPlugin loaded")
        print("[HelloPlugin] Plugin loaded")

    def on_enable(self) -> None:
        """插件启用时调用"""
        if self.plugin_api:
            # 读取配置
            greeting = self.plugin_api.config.get("greeting", "Hello")
            self.plugin_api.logger.info("HelloPlugin enabled", greeting=greeting)

            # 显示通知
            self.plugin_api.tui.show_notification(
                f"{greeting} from HelloPlugin!",
                severity="information",
                timeout=3
            )
        print("[HelloPlugin] Plugin enabled")

    def on_disable(self) -> None:
        """插件禁用时调用"""
        if self.plugin_api:
            self.plugin_api.logger.info("HelloPlugin disabled")
            self.plugin_api.tui.show_notification(
                "HelloPlugin disabled",
                severity="information",
                timeout=2
            )
        print("[HelloPlugin] Plugin disabled")

    def on_unload(self) -> None:
        """插件卸载时调用"""
        if self.plugin_api:
            self.plugin_api.logger.info("HelloPlugin unloaded")
        print("[HelloPlugin] Plugin unloaded")

    def on_config_change(self, new_config: dict) -> None:
        """配置更新时调用"""
        super().on_config_change(new_config)
        if self.plugin_api:
            greeting = new_config.get("greeting", "Hello")
            self.plugin_api.logger.info("HelloPlugin config changed", greeting=greeting)
        print(f"[HelloPlugin] Config changed: {new_config}")

    def say_hello(self, name: str = "World") -> str:
        """示例方法：打招呼

        Args:
            name: 名字

        Returns:
            str: 问候语
        """
        greeting = self.get_config().get("greeting", "Hello")
        message = f"{greeting}, {name}!"

        if self.plugin_api:
            self.plugin_api.logger.debug("say_hello called", name=name)

        return message
