# Agent Chat Hub - 安装指南

本文档提供详细的安装和配置说明。

## 系统要求

### 必需条件

- **操作系统**: Linux, macOS, 或 Windows (WSL)
- **Python**: 3.14 或更高版本
- **pip**: 最新版本（通常随Python安装）
- **网络**: 需要访问API服务（Anthropic, OpenAI等）

### 可选组件

- **git**: 用于从源码安装
- **virtualenv**: 推荐使用虚拟环境隔离依赖

### 硬件要求

- **内存**: 最低 512MB，推荐 1GB+
- **存储**: 约 100MB（含依赖）
- **CPU**: 任意现代处理器

---

## 安装方法

### 方法1: 从源码安装（推荐开发者）

**1. 克隆仓库**

```bash
git clone https://github.com/caohui-net/agent-chat-hub.git
cd agent-chat-hub
```

**2. 创建虚拟环境（推荐）**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows
```

**3. 安装依赖**

```bash
pip install -e .
```

`-e` 参数表示以"可编辑模式"安装，修改代码后无需重新安装。

**4. 验证安装**

```bash
agent-chat-hub --version  # 应显示版本号
```

### 方法2: 从发布包安装（未来支持）

```bash
pip install agent-chat-hub
```

*注意: 当前项目尚未发布到PyPI，请使用方法1。*

---

## 初始化配置

首次使用需要配置模型和Agent。

### 1. 运行配置向导

```bash
python init_config.py
```

或者，如果已安装CLI命令：

```bash
agent-chat-hub --init
```

### 2. 配置步骤

配置向导会引导你完成以下步骤：

**步骤1: 选择模型提供商**

```
请选择模型provider:
1. Anthropic (Claude)
2. OpenAI (GPT-4)
请输入选项 (1 或 2):
```

**步骤2: 输入API密钥**

```
请输入API密钥:
```

- API密钥会安全存储到系统密钥环（keyring）
- 不会保存到配置文件或日志中
- 支持Linux (Secret Service)、macOS (Keychain)、Windows (Credential Locker)

**步骤3: 配置模型参数**

```
请输入base URL [可选，留空使用默认]:
请输入最大token数 [默认: 4096]:
```

**步骤4: 创建第一个Agent**

```
请输入agent名称:
请输入agent描述 [可选]:
请输入系统提示词 [可选]:
```

### 3. 验证配置

配置完成后，会在以下位置创建文件：

- `~/.agent-chat-hub/models.json` - 模型配置
- `~/.agent-chat-hub/agents.json` - Agent配置
- 系统密钥环 - API密钥

检查配置文件：

```bash
cat ~/.agent-chat-hub/models.json
cat ~/.agent-chat-hub/agents.json
```

---

## 启动应用

### 基本启动

```bash
agent-chat-hub
```

或者：

```bash
python main.py
```

### 启动选项（未来支持）

```bash
agent-chat-hub --config /path/to/config  # 指定配置目录
agent-chat-hub --debug                   # 启用调试模式
agent-chat-hub --log-level INFO          # 设置日志级别
```

---

## 使用界面

### TUI界面操作

启动后进入基于Textual的终端用户界面（TUI）：

**主要快捷键:**

- **输入消息**: 在底部输入框输入，按 `Enter` 发送
- **退出应用**: `Ctrl+C` 或 `Ctrl+Q`
- **新建会话**: `Ctrl+N`
- **切换Agent**: `Ctrl+A`（未来支持）
- **查看配置**: `Ctrl+,`（未来支持）

**界面布局:**

```
┌─────────────────────────────────────┐
│  Agent Chat Hub - 会话列表          │
├─────────────────────────────────────┤
│                                     │
│  [Agent1] 你好！                    │
│  [User] 请帮我分析这段代码          │
│  [Agent1] 好的，我来看看...         │
│                                     │
├─────────────────────────────────────┤
│ 输入消息: _                         │
└─────────────────────────────────────┘
```

---

## 配置文件详解

### 目录结构

```
~/.agent-chat-hub/
├── models.json      # 模型配置
├── agents.json      # Agent配置
├── sessions/        # 会话历史
│   ├── session-1.json
│   └── session-2.json
└── logs/            # 日志文件
    └── app.log
```

### models.json 格式

```json
{
  "models": [
    {
      "model_id": "claude-3-opus",
      "provider": "anthropic",
      "api_base": "https://api.anthropic.com",
      "max_tokens": 4096
    }
  ]
}
```

### agents.json 格式

```json
{
  "agents": [
    {
      "agent_id": "assistant",
      "name": "AI助手",
      "model_id": "claude-3-opus",
      "system_prompt": "你是一个有帮助的AI助手。",
      "priority": 1,
      "enabled": true
    }
  ]
}
```

---

## 常见问题排查

### 问题1: 安装失败

**症状**: `pip install -e .` 报错

**可能原因**:
1. Python版本过低（<3.14）
2. pip版本过旧
3. 网络问题

**解决方案**:

```bash
# 检查Python版本
python3 --version  # 应 >= 3.14

# 升级pip
pip install --upgrade pip

# 使用国内镜像（如有网络问题）
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2: 命令找不到

**症状**: `agent-chat-hub: command not found`

**解决方案**:

```bash
# 检查是否在虚拟环境中
which python3

# 重新激活虚拟环境
source venv/bin/activate

# 或使用完整路径
python main.py
```

### 问题3: API密钥错误

**症状**: 启动后提示"API key not found"或"Invalid API key"

**解决方案**:

```bash
# 重新运行配置向导
python init_config.py

# 手动检查密钥环
python -c "import keyring; print(keyring.get_password('agent-chat-hub', 'anthropic'))"
```

### 问题4: 依赖冲突

**症状**: 安装时提示版本冲突

**解决方案**:

```bash
# 使用新的虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 问题5: TUI界面显示异常

**症状**: 界面显示乱码或布局错误

**可能原因**:
1. 终端不支持ANSI颜色
2. 终端窗口太小

**解决方案**:

```bash
# 检查终端类型
echo $TERM  # 应为 xterm-256color 或类似

# 设置终端颜色支持
export TERM=xterm-256color

# 调整窗口大小（最低 80x24）
```

---

## 更新升级

### 从源码更新

```bash
cd agent-chat-hub
git pull origin main
pip install -e . --upgrade
```

### 检查版本

```bash
agent-chat-hub --version
```

---

## 卸载

### 1. 卸载软件包

```bash
pip uninstall agent-chat-hub
```

### 2. 删除配置文件（可选）

```bash
rm -rf ~/.agent-chat-hub
```

### 3. 清除密钥环中的密钥（可选）

```bash
python -c "import keyring; keyring.delete_password('agent-chat-hub', 'anthropic')"
python -c "import keyring; keyring.delete_password('agent-chat-hub', 'openai')"
```

### 4. 删除虚拟环境（如使用）

```bash
rm -rf venv
```

---

## 开发安装

如果你想参与开发，需要额外安装开发依赖：

```bash
pip install -e ".[dev]"
```

这会安装：
- pytest (测试框架)
- pytest-asyncio (异步测试)
- pytest-cov (测试覆盖率)
- black (代码格式化)
- ruff (代码检查)

运行测试：

```bash
pytest tests/ -v
```

代码格式化：

```bash
black src/ tests/
ruff check src/ tests/
```

---

## 获取帮助

如遇到问题，可以：

1. 查看 [README.md](README.md) 了解项目概况
2. 查看 [docs/](docs/) 目录中的文档
3. 提交 Issue: https://github.com/caohui-net/agent-chat-hub/issues
4. 联系作者: caohui

---

**安装指南版本**: 1.0  
**最后更新**: 2026-07-20
