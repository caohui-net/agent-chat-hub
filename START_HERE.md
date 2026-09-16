# 🚀 从这里开始！

## 第一步：确认你的位置

```bash
pwd
```

**应该显示**: `/home/caohui/orca/workspaces/agent-chat-hub/agent-chat-hub`

如果不是，执行：
```bash
cd /home/caohui/orca/workspaces/agent-chat-hub/agent-chat-hub
```

---

## 第二步：启动应用

```bash
./start.sh
```

就这么简单！

---

## 🎮 快速上手

启动后，你会看到3个区域：

```
┌─────────────┬────────────────────┬─────────────┐
│  Agent面板  │    聊天对话区      │  文件面板   │
│  (左侧)     │    (中间)          │  (右侧)     │
└─────────────┴────────────────────┴─────────────┘
```

### 上传文件
1. 点击右侧 **📤 浏览上传** 按钮
2. 像文件管理器一样浏览选择文件
3. 双击或按 `Enter` 选择文件

### 查看文件
1. 在右侧文件列表选择文件（↑/↓键）
2. 点击 **📝 查看内容**
3. 聊天区显示文件内容

### 返回聊天
- 点击 **↩️ 返回聊天** 按钮
- 或按 `Ctrl+B` 快捷键

---

## ⌨️ 快捷键

| 按键 | 功能 |
|------|------|
| `Ctrl+C` | 退出应用 |
| `Ctrl+N` | 新会话 |
| `Ctrl+B` | 返回聊天（文件预览后）|
| `Esc` | 取消（文件浏览器中）|
| `Enter` | 选择文件/进入目录 |
| `Backspace` | 返回上一级目录 |

---

## 📚 更多文档

- **QUICK_START.md** - 详细快速指南
- **DIRECTORY_STRUCTURE.md** - 目录结构说明
- **FINAL_REPORT.md** - 完整功能报告
- **README.md** - 项目主文档

---

## ❓ 遇到问题？

### 找不到 start.sh？
确认你在项目根目录：
```bash
ls start.sh
# 应该显示: start.sh
```

### 应用无法启动？
检查虚拟环境：
```bash
ls venv/
# 应该看到虚拟环境目录
```

如果没有，创建虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## 🎉 开始使用吧！

```bash
./start.sh
```

就是这么简单！享受新的文件浏览器功能吧！
