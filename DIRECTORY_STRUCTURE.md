# 项目目录结构说明

## 📂 目录层次

```
/home/caohui/orca/workspaces/agent-chat-hub/    (工作空间目录)
└── agent-chat-hub/                              (项目根目录 ← 这里!)
    ├── src/                   # 源代码
    │   ├── agents/           # Agent系统
    │   ├── core/             # 核心功能
    │   └── tui/              # TUI界面
    ├── docs/                  # 文档
    ├── tests/                 # 测试
    ├── config/                # 配置
    ├── venv/                  # 虚拟环境
    ├── main.py                # 入口文件
    ├── start.sh               # 启动脚本
    ├── README.md              # 主文档
    └── ...
```

---

## 🎯 重要说明

### 当前所在位置
```bash
pwd
# 输出: /home/caohui/orca/workspaces/agent-chat-hub/agent-chat-hub
```

这就是**项目根目录**，所有命令都应该在这里执行。

---

## 🚀 启动应用

### 如果你在工作空间目录
```bash
cd /home/caohui/orca/workspaces/agent-chat-hub
cd agent-chat-hub    # 进入项目根目录
./start.sh
```

### 如果你已经在项目根目录
```bash
pwd  # 确认位置
# 应该输出: /home/caohui/orca/workspaces/agent-chat-hub/agent-chat-hub

./start.sh  # 直接启动
```

---

## 📝 常用命令

所有命令都假设你在**项目根目录**执行：

```bash
# 启动应用
./start.sh

# 运行测试
pytest tests/

# 查看Git状态
git status

# 推送代码
git push

# 激活虚拟环境
source venv/bin/activate
```

---

## ⚠️ 常见错误

### 错误1: 找不到start.sh
```bash
$ ./start.sh
-bash: ./start.sh: 没有那个文件或目录
```

**原因**: 不在项目根目录  
**解决**: 
```bash
cd /home/caohui/orca/workspaces/agent-chat-hub/agent-chat-hub
./start.sh
```

### 错误2: 找不到venv目录
```bash
$ source venv/bin/activate
-bash: venv/bin/activate: 没有那个文件或目录
```

**原因**: 不在项目根目录  
**解决**: 
```bash
cd /home/caohui/orca/workspaces/agent-chat-hub/agent-chat-hub
source venv/bin/activate
```

---

## 💡 快速导航

### 保存为别名
在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
alias agent-hub="cd /home/caohui/orca/workspaces/agent-chat-hub/agent-chat-hub"
```

然后：
```bash
source ~/.bashrc  # 或 source ~/.zshrc
agent-hub         # 快速进入项目目录
./start.sh        # 启动应用
```

---

## 📌 总结

- **工作空间**: `/home/caohui/orca/workspaces/agent-chat-hub/`
- **项目根目录**: `/home/caohui/orca/workspaces/agent-chat-hub/agent-chat-hub/` ⭐
- **启动命令**: `./start.sh`（在项目根目录执行）

**记住**: 所有文档中的命令都假设在**项目根目录**执行！
