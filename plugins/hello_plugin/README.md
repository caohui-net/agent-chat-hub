# Hello Plugin

基础插件示例 - 展示插件的基本结构和生命周期

## 功能

- 展示插件生命周期钩子（load/enable/disable/unload）
- 展示配置管理（读取、更新、监听）
- 展示日志记录
- 展示TUI通知

## 安装

插件已经包含在Agent Chat Hub的`plugins/`目录中，无需额外安装。

## 配置

插件配置保存在 `~/.agent-chat-hub/plugins/hello_plugin.json`

```json
{
  "greeting": "Hello",
  "enabled": true
}
```

### 配置项

- `greeting` (string): 问候语，默认为"Hello"
- `enabled` (boolean): 是否启用，默认为true

## 使用

### 启用插件

1. 打开Agent Chat Hub
2. 按 `Ctrl+P` 打开插件管理界面
3. 找到 "Hello Plugin"
4. 点击 "启用"

启用后会显示通知消息。

### 配置插件

在插件管理界面中：
1. 选择 "Hello Plugin"
2. 点击 "配置"
3. 修改配置项
4. 保存

### 代码示例

```python
# 获取插件实例
hello_plugin = plugin_registry.get_plugin("hello_plugin")

# 调用插件方法
message = hello_plugin.say_hello("Alice")
print(message)  # 输出: Hello, Alice!

# 更新配置
hello_plugin.plugin_api.config.set("greeting", "Hi")

# 再次调用
message = hello_plugin.say_hello("Bob")
print(message)  # 输出: Hi, Bob!
```

## 开发参考

此插件是最简单的实现示例，适合作为开发新插件的起点。

### 关键要点

1. **继承IPlugin**: 所有插件必须继承`IPlugin`基类
2. **实现get_metadata()**: 返回插件元数据
3. **生命周期钩子**: 可选实现`on_load`、`on_enable`、`on_disable`、`on_unload`
4. **配置管理**: 通过`self.plugin_api.config`访问配置
5. **日志记录**: 通过`self.plugin_api.logger`记录日志

### 文件结构

```
plugins/hello_plugin/
├── __init__.py    # 插件主文件
└── README.md      # 本文档
```

## 许可证

MIT License
