# 插件系统架构设计

## 概述

Agent Chat Hub采用Ruflo风格的插件系统，支持动态加载和扩展功能。

## 核心组件

### 1. 插件基类（IPlugin）

所有插件必须继承`IPlugin`抽象基类：

```python
class IPlugin(ABC):
    def get_metadata(self) -> PluginMetadata  # 必须实现
    def on_load(self) -> None                  # 可选实现
    def on_enable(self) -> None                # 可选实现
    def on_disable(self) -> None               # 可选实现
    def on_unload(self) -> None                # 可选实现
    def on_config_change(self, config) -> None # 可选实现
```

### 2. 插件生命周期

```
[未加载] --load--> [已加载] --enable--> [已启用]
   ↑                  ↓                      ↓
   └----unload----←---┘←--------disable-----┘
```

生命周期回调：
- `on_load()`: 插件加载时调用，初始化资源
- `on_enable()`: 插件启用时调用，注册钩子和功能
- `on_disable()`: 插件禁用时调用，清理和取消注册
- `on_unload()`: 插件卸载时调用，释放所有资源

### 3. 钩子系统（Hooks）

钩子允许插件在特定事件发生时执行代码：

**系统预定义钩子**：
- `before_agent_call`: Agent调用前
- `after_agent_call`: Agent调用后
- `before_message_send`: 消息发送前
- `after_message_receive`: 消息接收后
- `on_session_create`: 会话创建时
- `on_session_close`: 会话关闭时

**钩子注册**：
```python
def on_enable(self):
    self.plugin_api.register_hook('before_agent_call', self.my_callback, priority=10)
```

### 4. 事件系统（Events）

事件用于插件间的松耦合通信：

**事件发布**：
```python
event = PluginEvent('my_custom_event', {'data': 'value'})
self.plugin_api.emit_event(event)
```

**事件订阅**：
```python
def on_enable(self):
    self.plugin_api.subscribe_event('my_custom_event', self.handle_event)
```

### 5. 扩展点（Extension Points）

扩展点允许插件注册新功能：

- `agent_providers`: 注册新的Agent提供商
- `tui_screens`: 注册新的TUI界面
- `commands`: 注册新的命令
- `formatters`: 注册消息格式化器

## 插件元数据

每个插件通过`PluginMetadata`声明自身信息：

```python
PluginMetadata(
    plugin_id="my_plugin",
    name="My Plugin",
    version="1.0.0",
    description="插件描述",
    author="作者名",
    dependencies=["other_plugin"],  # 依赖的插件
    min_system_version="0.1.0",     # 最低系统版本
    provides=["feature1", "feature2"],  # 提供的功能
    hooks=["before_agent_call"],    # 注册的钩子
    config_schema={...},            # 配置JSON Schema
    default_config={...}            # 默认配置
)
```

## 插件API

插件通过`PluginAPI`访问系统功能：

### Agent API
- `get_agent_config(agent_id)`: 获取Agent配置
- `call_agent(agent_id, message)`: 调用Agent
- `list_agents()`: 列出所有Agent

### TUI API
- `register_screen(name, screen_class)`: 注册新界面
- `add_menu_item(label, callback)`: 添加菜单项
- `show_notification(message)`: 显示通知

### 配置API
- `get_config(key)`: 读取配置
- `set_config(key, value)`: 写入配置
- `watch_config(key, callback)`: 监听配置变化

### 消息API
- `subscribe_message(message_type, callback)`: 订阅消息
- `publish_message(message)`: 发布消息

### 存储API
- `get(key)`: 读取数据
- `set(key, value)`: 写入数据
- `delete(key)`: 删除数据

### 日志API
- `log_info(message)`: 记录信息
- `log_warning(message)`: 记录警告
- `log_error(message)`: 记录错误

## 插件目录结构

```
plugins/
├── my_plugin/
│   ├── __init__.py          # 插件入口
│   ├── plugin.py            # 插件实现
│   ├── config.json          # 默认配置
│   └── README.md            # 插件文档
```

## 插件加载流程

1. **扫描**: PluginLoader扫描`plugins/`目录
2. **加载**: 动态导入插件模块
3. **验证**: 检查插件元数据和依赖
4. **注册**: 将插件添加到PluginRegistry
5. **初始化**: 调用`on_load()`
6. **启用**: 调用`on_enable()`（如果配置为启用）

## 依赖管理

插件可以声明对其他插件的依赖：

```python
dependencies=["base_plugin", "utils_plugin>=1.2.0"]
```

加载器会：
1. 解析依赖关系
2. 按拓扑顺序加载插件
3. 检查版本兼容性
4. 如果依赖缺失，拒绝加载

## 版本控制

使用语义化版本（SemVer）：
- `1.0.0`: 主版本.次版本.修订版本
- `>=1.0.0`: 最低版本要求
- `^1.0.0`: 兼容性版本范围

## 安全考虑

1. **命名空间隔离**: 插件在独立命名空间中运行
2. **权限控制**: 插件需要声明使用的API权限
3. **资源限制**: 限制插件的CPU和内存使用
4. **沙箱环境**: 考虑使用沙箱隔离插件代码（未来）

## 示例插件

参见`plugins/`目录下的示例插件：
- `hello_plugin`: 基础插件示例
- `weather_plugin`: Agent增强示例
- `theme_plugin`: TUI扩展示例
