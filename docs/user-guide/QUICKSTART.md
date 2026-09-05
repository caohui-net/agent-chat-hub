# Agent Chat Hub - 快速开始指南

**5分钟快速上手** - 从零开始运行Agent Chat Hub

---

## 前置要求

- Python 3.10+
- API密钥（Anthropic Claude 或 OpenAI）
- 终端/命令行工具

---

## 第1步：克隆项目

```bash
git clone https://github.com/yourusername/agent-chat-hub.git
cd agent-chat-hub
```

---

## 第2步：创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

✅ **验证**: 终端提示符应显示 `(venv)`

---

## 第3步：安装依赖

```bash
pip install -e .
```

✅ **验证**: 运行 `pip list | grep textual` 应看到 textual 包

---

## 第4步：配置API密钥

运行交互式配置向导：

```bash
python init_config.py
```

向导会引导你：
1. 选择模型提供商（Anthropic/OpenAI）
2. 输入API密钥（安全存储到系统密钥环）
3. 创建第一个Agent

**示例输出**：
```
🤖 欢迎使用 Agent Chat Hub 配置向导

1. 选择模型提供商
   [1] Anthropic Claude
   [2] OpenAI GPT
   选择 (1/2): 1

2. 输入Anthropic API密钥
   API密钥: sk-ant-***************

✅ API密钥已安全存储到系统密钥环

3. 创建Agent
   Agent名称: researcher
   模型: claude-sonnet-3-5
   ✅ Agent创建成功
```

✅ **验证**: 配置文件应存在于 `~/.agent-chat-hub/`

---

## 第5步：启动应用

```bash
./start.sh
```

或手动启动：

```bash
python main.py
```

✅ **验证**: 应看到Textual TUI界面

---

## 界面概览

启动成功后，你会看到：

```
┌─────────────────────────────────────────────────┐
│ Agent Chat Hub                    v1.0          │
├──────────────┬──────────────────────────────────┤
│ Agent列表    │ 聊天区域                         │
│              │                                  │
│ ● researcher │ User: 你好                       │
│ ○ coder      │ researcher: 你好！我可以帮你...  │
│ ○ writer     │                                  │
│              │                                  │
├──────────────┴──────────────────────────────────┤
│ 输入消息: _                                      │
└─────────────────────────────────────────────────┘
```

**状态指示器**：
- `●` 绿色 = 在线/就绪
- `○` 灰色 = 离线/空闲

---

## 基本使用

### 1. 发送消息

在底部输入框输入消息，按 **Enter** 发送。

```
输入消息: 分析这段Python代码
```

### 2. 选择Agent

点击左侧Agent列表中的Agent名称，或使用 `@mention`：

```
输入消息: @researcher 分析这段代码
```

### 3. 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Enter` | 发送消息 |
| `Ctrl+C` | 退出应用 |
| `Ctrl+N` | 创建新会话 |
| `Tab` | 切换焦点 |

---

## 高级功能

### @mention 智能匹配

支持模糊匹配，无需输入完整Agent名称：

```bash
@res     → researcher   ✅
@write   → writer       ✅
@研究    → researcher   ✅ (支持中文)
```

**工作原理**：
1. 精确匹配（researcher）
2. 前缀匹配（res*）
3. 包含匹配（*search*）
4. 模糊匹配（不区分大小写）

### 实时状态追踪

界面会显示Agent的实时状态：

```
⏳ researcher: 思考中... (2.1s)
📊 Token: 450 | 💰 成本: $0.0036
```

**状态类型**：
- `IDLE` - 空闲
- `PENDING` - 等待中
- `RUNNING` - 执行中
- `COMPLETED` - 已完成
- `ERROR` - 错误

### Token追踪

查看本会话的Token使用情况：

```
📊 本会话统计
├─ 输入: 1,000 tokens
├─ 输出: 2,000 tokens
├─ 总计: 3,000 tokens
└─ 成本: $0.0330
```

### 自动重试

网络错误时自动重试（最多3次）：
- 超时错误 → 重试 (1s, 2s, 4s)
- API限流 → 重试 (指数退避)
- 致命错误 → 立即提示

---

## 配置文件位置

所有配置文件存储在用户目录：

```
~/.agent-chat-hub/
├── models.json      # 模型配置
├── agents.json      # Agent配置
└── sessions/        # 会话历史
```

**注意**：API密钥存储在系统密钥环（不在文件中）

---

## 常见问题

### Q1: 虚拟环境不存在

**错误**：
```
错误: 虚拟环境不存在
```

**解决**：
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

### Q2: 依赖未安装

**错误**：
```
ModuleNotFoundError: No module named 'textual'
```

**解决**：
```bash
source venv/bin/activate
pip install -e .
```

---

### Q3: API密钥未配置

**错误**：
```
错误: API密钥未配置
```

**解决**：
```bash
python init_config.py
```

按向导提示输入API密钥

---

### Q4: 找不到配置文件

**错误**：
```
FileNotFoundError: models.json
```

**解决**：
```bash
python init_config.py
```

创建默认配置文件

---

### Q5: Agent无响应

**检查清单**：
1. API密钥是否有效
2. 网络连接是否正常
3. 模型ID是否正确
4. 查看错误日志：`~/.agent-chat-hub/logs/`

**调试命令**：
```bash
# 查看日志
tail -f ~/.agent-chat-hub/logs/agent-chat-hub.log

# 测试API连接
python -c "from src.core.config import ConfigManager; cm = ConfigManager(); print(cm.get_api_key())"
```

---

## 下一步

恭喜！你已经成功运行Agent Chat Hub。接下来可以：

1. **创建自定义Agent** - 阅读 [tutorials/FIRST_AGENT.md](../tutorials/FIRST_AGENT.md)
2. **配置多模型** - 阅读 [CONFIGURATION.md](CONFIGURATION.md)
3. **了解架构** - 阅读 [../architecture/](../architecture/)

---

## 快速命令参考

```bash
# 完整安装（首次）
python3 -m venv venv && \
source venv/bin/activate && \
pip install -e . && \
python init_config.py

# 日常启动
./start.sh

# 手动启动
source venv/bin/activate && python main.py

# 退出虚拟环境
deactivate
```

---

## 获取帮助

- **文档首页**: [README.md](../../README.md)
- **故障排除**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **配置指南**: [CONFIGURATION.md](CONFIGURATION.md)
- **API参考**: [../api-reference/API.md](../api-reference/API.md)

---

**版本**: v1.0  
**更新日期**: 2026-09-06
