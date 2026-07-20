# Export Plugin - 对话导出插件

## 功能

将Agent Chat Hub的对话历史导出为文件：
- **Markdown格式**：适合阅读和分享
- **JSON格式**：适合程序处理和备份

## 配置

```json
{
  "export_dir": "~/.agent-chat-hub/exports",
  "auto_export": false,
  "format": "markdown"
}
```

- `export_dir`: 导出文件保存目录
- `auto_export`: 是否自动导出（暂未实现）
- `format`: 默认导出格式（markdown/json）

## 使用方法

### 编程方式

```python
from plugins.export_plugin import ExportPlugin

# 初始化插件
plugin = ExportPlugin(plugin_api)

# 导出为Markdown
md_path = plugin.export_to_markdown("session_id_123")
print(f"导出至: {md_path}")

# 导出为JSON
json_path = plugin.export_to_json("session_id_123")
print(f"导出至: {json_path}")

# 自定义路径
plugin.export_to_markdown("session_id_123", "/path/to/output.md")
```

## 输出示例

### Markdown格式

```markdown
# 会话导出

**会话ID**: session_20260720_001
**导出时间**: 2026-07-20 17:25:30

---

## 👤 用户
*2026-07-20 17:20:15*

你好，请帮我分析这段代码

---

## 🤖 Claude Assistant
*2026-07-20 17:20:18*

好的，我来看看这段代码...

---
```

### JSON格式

```json
{
  "session_id": "session_20260720_001",
  "export_time": "2026-07-20T17:25:30.123456",
  "messages": [
    {
      "role": "user",
      "content": "你好，请帮我分析这段代码",
      "timestamp": "2026-07-20 17:20:15"
    },
    {
      "role": "assistant",
      "agent_name": "Claude Assistant",
      "content": "好的，我来看看这段代码...",
      "timestamp": "2026-07-20 17:20:18"
    }
  ],
  "metadata": {
    "total_messages": 2,
    "agents": ["Claude Assistant"]
  }
}
```

## 版本

- **当前版本**: 1.0.0
- **最后更新**: 2026-07-20
