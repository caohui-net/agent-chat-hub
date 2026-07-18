# 插件开发指南

本指南介绍如何为Agent Chat Hub开发插件。

## 快速开始

### 1. 创建插件目录

在`plugins/`目录下创建你的插件目录：

```bash
mkdir plugins/my_plugin
```

### 2. 创建插件主文件

创建`plugins/my_plugin/__init__.py`：

```python
from src.plugins.base import IPlugin
from src.plugins.models import PluginMetadata

class MyPlugin(IPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="my_plugin",
            name="My Plugin",
            version="1.0.0",
            description="插件描述",
            author="Your Name",
            dependencies=[],
            provides=[],
            hooks=[],
            config_schema={},
            default_config={}
        )

    def on_enable(self) -> None:
        self.plugin_api.logger.info("My plugin enabled!")
```

### 3. 测试插件

启动Agent Chat Hub，按`Ctrl+P`打开插件管理界面，启用你的插件。

## 插件结构

### 必需组件

1. **插件类**: 继承`IPlugin`
2. **get_metadata()**: 返回插件元数据

### 可选组件

- `on_load()`: 插件加载时调用
- `on_enable()`: 插件启用时调用
- `on_disable()`: 插件禁用时调用
- `on_unload()`: 插件卸载时调用
- `on_config_change()`: 配置更新时调用

## 插件API

插件通过`self.plugin_api`访问系统功能。

### Agent API

```python
# 列出所有Agent
agents = self.plugin_api.agent.list_agents(active_only=True)

# 调用Agent
response = await self.plugin_api.agent.call_agent("agent_id", "message")
```

### 配置API

```python
# 读取配置
value = self.plugin_api.config.get("key", default="default")

# 写入配置
self.plugin_api.config.set("key", "value")

# 监听配置变化
self.plugin_api.config.watch("key", self.on_config_update)
```

### 消息API

```python
# 订阅消息
self.plugin_api.message.subscribe("message_type", self.handle_message)

# 发布消息
await self.plugin_api.message.publish("type", "content")

# 广播消息
await self.plugin_api.message.broadcast("Hello everyone!")
```

### TUI API

```python
# 注册界面
self.plugin_api.tui.register_screen("screen_name", ScreenClass)

# 显示通知
self.plugin_api.tui.show_notification("Message", severity="information")

# 添加菜单项
self.plugin_api.tui.add_menu_item("Label", callback)
```

### 日志API

```python
self.plugin_api.logger.info("Information")
self.plugin_api.logger.warning("Warning")
self.plugin_api.logger.error("Error")
self.plugin_api.logger.debug("Debug")
```

## 配置管理

### 定义配置Schema

```python
def get_metadata(self) -> PluginMetadata:
    return PluginMetadata(
        # ...
        config_schema={
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "API密钥"
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒）",
                    "default": 30
                }
            }
        },
        default_config={
            "api_key": "",
            "timeout": 30
        }
    )
```

### 使用配置

```python
def on_enable(self) -> None:
    api_key = self.plugin_api.config.get("api_key")
    timeout = self.plugin_api.config.get("timeout", 30)
    
    if not api_key:
        self.plugin_api.logger.warning("API key not configured")
```

## 依赖管理

### 声明依赖

```python
def get_metadata(self) -> PluginMetadata:
    return PluginMetadata(
        # ...
        dependencies=["base_plugin>=1.0.0"],
        min_system_version="0.1.0"
    )
```

### 访问依赖插件

```python
# TODO: 实现插件间通信机制
```

## TUI扩展

### 注册自定义界面

```python
from textual.screen import Screen
from textual.widgets import Label, Button

class MyScreen(Screen):
    def compose(self):
        yield Label("My Custom Screen")
        yield Button("Close", id="btn_close")

    def on_button_pressed(self, event):
        if event.button.id == "btn_close":
            self.app.pop_screen()

# 在on_enable中注册
def on_enable(self) -> None:
    self.plugin_api.tui.register_screen("my_screen", MyScreen)
    
    # 添加打开界面的菜单项
    self.plugin_api.tui.add_menu_item(
        "My Plugin",
        lambda: self.plugin_api.tui.push_screen("my_screen")
    )
```

## 消息处理

### 订阅和处理消息

```python
from src.core.models import AgentMessage

def on_enable(self) -> None:
    self.plugin_api.message.subscribe("user_message", self.handle_user_message)

def handle_user_message(self, message: AgentMessage) -> None:
    self.plugin_api.logger.info("Received message", content=message.content)
    
    # 处理消息...
    
    # 发布响应
    await self.plugin_api.message.publish(
        "plugin_response",
        f"Processed: {message.content}",
        metadata={"plugin": "my_plugin"}
    )
```

## 最佳实践

### 1. 错误处理

```python
def on_enable(self) -> None:
    try:
        # 初始化逻辑
        self.init_service()
    except Exception as e:
        self.plugin_api.logger.error("Plugin initialization failed", error=str(e))
        # 通知用户
        self.plugin_api.tui.show_notification(
            f"Plugin error: {str(e)}",
            severity="error"
        )
```

### 2. 资源清理

```python
def on_disable(self) -> None:
    # 取消所有订阅
    self.plugin_api.message.unsubscribe("message_type")
    
    # 关闭连接
    if hasattr(self, 'connection'):
        self.connection.close()
    
    # 保存状态
    self.plugin_api.config.set("last_state", self.get_state())
```

### 3. 日志记录

```python
# 使用结构化日志
self.plugin_api.logger.info("action_performed", 
                           action="fetch_data",
                           status="success",
                           count=10)
```

### 4. 配置验证

```python
def on_enable(self) -> None:
    required_keys = ["api_key", "endpoint"]
    for key in required_keys:
        if not self.plugin_api.config.get(key):
            self.plugin_api.logger.error("missing_config", key=key)
            raise ValueError(f"Missing required config: {key}")
```

## 示例插件

参考`plugins/hello_plugin/`目录中的示例插件。

## 调试技巧

### 1. 使用日志

```python
self.plugin_api.logger.debug("variable_value", value=some_value)
```

### 2. 通知消息

```python
self.plugin_api.tui.show_notification(
    f"Debug: {value}",
    severity="information"
)
```

### 3. 配置检查

```python
# 打印当前配置
config = self.plugin_api.config.get_all()
self.plugin_api.logger.debug("current_config", config=config)
```

## 发布插件

（待实现：插件市场和分发机制）

## 常见问题

### Q: 插件加载失败？

A: 检查：
1. 插件目录下是否有`__init__.py`
2. 插件类是否继承了`IPlugin`
3. `get_metadata()`是否正确实现
4. 依赖是否满足

### Q: 无法访问API？

A: 确保`self.plugin_api`不为None，并且插件已启用。

### Q: 配置不持久化？

A: 配置自动保存到文件，检查`~/.agent-chat-hub/plugins/`目录权限。

## 更多资源

- [插件系统架构设计](../architecture/plugin-system-design.md)
- [插件API参考](../api/plugin-api-reference.md)
- [Hello Plugin示例](../../plugins/hello_plugin/)
