# 插件API参考文档

## 概述

本文档描述了提供给插件使用的API接口。插件通过`PluginAPI`对象访问这些功能。

## PluginAPI类

插件通过构造函数接收`PluginAPI`实例：

```python
class MyPlugin(IPlugin):
    def __init__(self, plugin_api: PluginAPI):
        super().__init__(plugin_api)
        self.api = plugin_api
```

`PluginAPI`包含以下子API：
- `agent`: Agent API
- `config`: 配置API
- `message`: 消息API
- `tui`: TUI API
- `logger`: 日志API

---

## Agent API

访问和调用Agent的接口。

### 获取Agent配置

```python
agent_config = self.api.agent.get_agent_config(agent_id)
```

**参数**：
- `agent_id` (str): Agent ID

**返回**：
- `Optional[AgentConfig]`: Agent配置对象

### 列出所有Agent

```python
agents = self.api.agent.list_agents(active_only=True)
```

**参数**：
- `active_only` (bool): 是否只返回启用的Agent，默认False

**返回**：
- `List[AgentConfig]`: Agent配置列表

### 调用Agent

```python
response = await self.api.agent.call_agent(agent_id, message, context)
```

**参数**：
- `agent_id` (str): Agent ID
- `message` (str): 消息内容
- `context` (Optional[Dict]): 上下文信息

**返回**：
- `Optional[str]`: Agent的响应

### 添加Agent

```python
success = self.api.agent.add_agent(agent_config)
```

**参数**：
- `agent_config` (AgentConfig): Agent配置对象

**返回**：
- `bool`: 是否成功添加

### 更新Agent

```python
success = self.api.agent.update_agent(agent_id, {"name": "New Name"})
```

**参数**：
- `agent_id` (str): Agent ID
- `updates` (Dict): 更新字典

**返回**：
- `bool`: 是否成功更新

---

## 配置API

管理插件配置数据的接口。

### 读取配置

```python
value = self.api.config.get("section.key", default="default_value")
```

**参数**：
- `key` (str): 配置键，支持点分隔的嵌套路径
- `default` (Any): 默认值

**返回**：
- `Any`: 配置值

**示例**：
```python
# 简单键
port = self.api.config.get("port", 8080)

# 嵌套键
db_host = self.api.config.get("database.host", "localhost")
```

### 写入配置

```python
success = self.api.config.set("section.key", "value")
```

**参数**：
- `key` (str): 配置键
- `value` (Any): 配置值

**返回**：
- `bool`: 是否成功写入

### 删除配置

```python
success = self.api.config.delete("section.key")
```

**参数**：
- `key` (str): 配置键

**返回**：
- `bool`: 是否成功删除

### 获取所有配置

```python
all_config = self.api.config.get_all()
```

**返回**：
- `Dict[str, Any]`: 所有配置

### 监听配置变化

```python
def on_config_change(old_value, new_value):
    print(f"Config changed: {old_value} -> {new_value}")

self.api.config.watch("section.key", on_config_change)
```

**参数**：
- `key` (str): 配置键
- `callback` (Callable): 回调函数，接收`(old_value, new_value)`

### 取消监听

```python
self.api.config.unwatch("section.key", on_config_change)
```

---

## 消息API

订阅和发布消息的接口。

### 订阅消息

```python
def handle_message(message: AgentMessage):
    print(f"Received: {message.content}")

self.api.message.subscribe("notification", handle_message)
```

**参数**：
- `message_type` (str): 消息类型
- `callback` (Callable): 回调函数，接收`AgentMessage`

### 取消订阅

```python
self.api.message.unsubscribe("notification", handle_message)
# 或取消该类型的所有订阅
self.api.message.unsubscribe("notification")
```

### 发布消息

```python
await self.api.message.publish(
    message_type="notification",
    content="Hello from plugin!",
    to_agent_id=None,  # None表示广播
    metadata={"priority": "high"}
)
```

**参数**：
- `message_type` (str): 消息类型
- `content` (str): 消息内容
- `to_agent_id` (Optional[str]): 目标Agent ID
- `metadata` (Optional[Dict]): 消息元数据

### 发送到指定Agent

```python
await self.api.message.send_to_agent("agent_123", "Hello agent!")
```

**参数**：
- `agent_id` (str): 目标Agent ID
- `content` (str): 消息内容
- `message_type` (str): 消息类型，默认"notification"

### 广播消息

```python
await self.api.message.broadcast("Hello everyone!")
```

**参数**：
- `content` (str): 消息内容
- `message_type` (str): 消息类型，默认"broadcast"

### 处理接收的消息

```python
await self.api.message.process_messages(timeout=1.0)
```

**参数**：
- `timeout` (Optional[float]): 超时时间（秒）

---

## TUI API

扩展TUI界面的接口。

### 注册界面

```python
from textual.screen import Screen

class MyScreen(Screen):
    # ... 界面实现

success = self.api.tui.register_screen("my_screen", MyScreen)
```

**参数**：
- `name` (str): 界面名称
- `screen_class` (type[Screen]): 界面类

**返回**：
- `bool`: 是否成功注册

### 打开界面

```python
success = self.api.tui.push_screen("my_screen", param1="value1")
```

**参数**：
- `name` (str): 界面名称
- `**kwargs`: 传递给界面构造函数的参数

**返回**：
- `bool`: 是否成功打开

### 注册动作

```python
def my_action():
    print("Action executed!")

success = self.api.tui.register_action(
    "my_action",
    my_action,
    binding="ctrl+shift+m"
)
```

**参数**：
- `action_name` (str): 动作名称
- `callback` (Callable): 回调函数
- `binding` (Optional[str]): 键盘绑定

**返回**：
- `bool`: 是否成功注册

### 显示通知

```python
self.api.tui.show_notification(
    "Operation completed!",
    severity="information",  # information/warning/error
    timeout=3
)
```

**参数**：
- `message` (str): 通知内容
- `severity` (str): 严重级别
- `timeout` (int): 显示时长（秒）

### 添加菜单项

```python
def on_menu_click():
    print("Menu item clicked!")

success = self.api.tui.add_menu_item(
    "My Plugin",
    on_menu_click,
    menu="plugins"
)
```

**参数**：
- `label` (str): 菜单项标签
- `callback` (Callable): 点击回调
- `menu` (str): 菜单名称

**返回**：
- `bool`: 是否成功添加

---

## 日志API

记录插件日志的接口。

### 记录信息

```python
self.api.logger.info("Plugin initialized")
```

### 记录警告

```python
self.api.logger.warning("Configuration is missing")
```

### 记录错误

```python
self.api.logger.error("Failed to connect to service", error=str(e))
```

### 记录调试信息

```python
self.api.logger.debug("Processing message", message_id=msg.id)
```

---

## 完整示例

```python
from src.plugins.base import IPlugin
from src.plugins.models import PluginMetadata
from src.core.models import AgentMessage

class ExamplePlugin(IPlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="example_plugin",
            name="Example Plugin",
            version="1.0.0",
            description="示例插件",
            author="Your Name"
        )

    def on_load(self) -> None:
        self.api.logger.info("Plugin loaded")

    def on_enable(self) -> None:
        # 读取配置
        self.enabled_features = self.api.config.get("features", [])

        # 订阅消息
        self.api.message.subscribe("user_message", self.handle_message)

        # 注册TUI界面
        from .screen import MyScreen
        self.api.tui.register_screen("example_screen", MyScreen)

        # 显示通知
        self.api.tui.show_notification("Example Plugin enabled!")

    def on_disable(self) -> None:
        # 取消订阅
        self.api.message.unsubscribe("user_message")
        self.api.logger.info("Plugin disabled")

    def handle_message(self, message: AgentMessage) -> None:
        self.api.logger.debug("Message received", content=message.content)

        # 调用Agent
        response = await self.api.agent.call_agent(
            "claude_agent",
            message.content
        )

        # 发布响应
        await self.api.message.broadcast(f"Plugin response: {response}")
```

---

## 注意事项

1. **异步方法**：部分API方法是异步的（如`call_agent`、`publish`），需要使用`await`
2. **错误处理**：API调用可能失败，返回None或False，请检查返回值
3. **日志记录**：使用`api.logger`而不是直接`print()`
4. **配置持久化**：配置自动保存到文件，无需手动调用save
5. **消息处理**：需要定期调用`process_messages()`或在后台线程中监听
