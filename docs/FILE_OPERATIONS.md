# 文件操作功能使用指南

## 功能概述

Agent Chat Hub的TUI界面提供完整的文件管理功能，支持文件上传、下载、删除和列表查看。

## 架构设计

### 混合存储架构

```
~/.agent-chat-hub/files/
├── workspace/          # 全局共享区
│   └── (共享文件)
└── sessions/           # 会话隔离区
    ├── session_1/
    ├── session_2/
    └── ...
```

**特点：**
- **会话隔离**：默认文件存储在当前会话目录，生命周期与会话一致
- **全局共享**：workspace目录用于跨会话共享的工具文件和模板
- **安全性**：自动路径清理，防止路径穿越攻击

## 使用方法

### 1. 文件列表

**位置**：TUI右侧文件面板

**显示信息**：
- 🌐 全局文件（workspace）
- 📁 会话文件（session）
- 文件名、大小、类型

**操作**：
- 使用方向键选择文件
- 文件列表自动刷新

### 2. 上传文件

**触发**：点击 `📤 上传文件` 按钮

**流程**：
1. 弹出路径输入对话框
2. 输入文件绝对路径
3. 按Enter确认或取消
4. 文件复制到会话目录
5. 列表自动刷新

**示例**：
```
输入：/home/user/document.pdf
结果：document.pdf 上传到 ~/.agent-chat-hub/files/sessions/{session_id}/
```

### 3. 下载文件

**触发**：选中文件 → 点击 `📥 下载选中` 按钮

**流程**：
1. 在文件列表中选择目标文件
2. 点击下载按钮
3. 弹出保存路径对话框（默认：~/Downloads/文件名）
4. 修改路径或直接确认
5. 文件复制到指定位置

**默认路径**：`~/Downloads/` + 原文件名

### 4. 删除文件

**触发**：选中文件 → 点击 `🗑️ 删除选中` 按钮

**流程**：
1. 在文件列表中选择目标文件
2. 点击删除按钮
3. 弹出确认对话框（显示文件信息）
4. 确认后永久删除
5. 列表自动刷新

**警告**：删除操作不可恢复！

## 技术特性

### 异步I/O

所有文件操作使用Textual Worker异步执行，确保：
- ✅ UI不阻塞
- ✅ 支持大文件操作
- ✅ 后台执行，实时反馈

### 错误处理

完善的错误提示：
- 文件不存在
- 权限不足
- 路径无效
- 操作失败

### 安全机制

- **路径清理**：自动移除`../`和特殊字符
- **同名冲突**：自动重命名（file_1.txt, file_2.txt）
- **权限检查**：验证文件访问权限
- **类型检查**：确保操作对象是文件而非目录

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| 方向键 | 在文件列表中移动 |
| Tab | 切换面板焦点 |
| Enter | 执行按钮操作 |
| Esc | 取消对话框 |

## 存储管理API

### FileStorageManager

```python
from src.core.file_storage import FileStorageManager
from pathlib import Path

# 初始化
manager = FileStorageManager(
    base_dir=Path.home() / ".agent-chat-hub" / "files",
    session_id="your_session_id"
)

# 上传文件
metadata = manager.upload_file(
    src=Path("/path/to/file.txt"),
    scope="session"  # 或 "workspace"
)

# 列出文件
files = manager.list_files(scope="session")

# 下载文件
success = manager.download_file(
    file_id="abc123",
    dest=Path("/path/to/save.txt")
)

# 删除文件
success = manager.delete_file(file_id="abc123")
```

## 常见问题

**Q: 文件上传后在哪里？**
A: 默认存储在 `~/.agent-chat-hub/files/sessions/{session_id}/`

**Q: 如何共享文件给其他会话？**
A: 当前版本使用session隔离，跨会话共享需要手动复制到workspace目录

**Q: 支持哪些文件类型？**
A: 支持所有文件类型，无大小限制（受磁盘空间约束）

**Q: 删除会话时文件会被删除吗？**
A: 是的，会话目录下的文件会随会话删除

**Q: 如何备份重要文件？**
A: 使用下载功能将文件保存到系统其他位置

## 未来改进

- [ ] 拖拽上传支持
- [ ] 文件预览功能
- [ ] 批量操作（多选）
- [ ] 文件搜索和过滤
- [ ] 压缩/解压缩
- [ ] 文件分享链接

---

**版本**：v1.0 (MVP)  
**更新日期**：2026-07-26  
**讨论记录**：`.collab/discussions/agent-chat-hub项目TUI文件操作功能实现方案*`
