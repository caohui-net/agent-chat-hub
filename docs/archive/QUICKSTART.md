# Agent Chat Hub - 快速启动指南

## 🚀 如何运行本项目

### 方式1: 快速启动（推荐）

```bash
./start.sh
```

这个脚本会自动：
- 检查虚拟环境
- 激活虚拟环境
- 启动应用

---

### 方式2: 手动启动

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 启动应用
python main.py
```

---

## 📋 首次运行 - 完整步骤

### 步骤1: 创建虚拟环境

```bash
python3 -m venv venv
```

### 步骤2: 激活虚拟环境

```bash
source venv/bin/activate
```

### 步骤3: 安装依赖

```bash
pip install -e .
```

### 步骤4: 初始化配置

```bash
python init_config.py
```

这个脚本会引导你：
- ✅ 选择模型provider（Anthropic或OpenAI）
- ✅ 输入API密钥（安全存储到系统密钥环）
- ✅ 创建第一个agent

### 步骤5: 启动应用

```bash
./start.sh
```

或

```bash
python main.py
```

---

## 🎮 使用界面

启动后你会看到Textual TUI界面：

```
┌─────────────────────────────────────────────────┐
│ Agent Chat Hub                                  │
├─────────────────────────────────────────────────┤
│ [Agent列表]  │  [聊天区域]                      │
│              │                                   │
│ • researcher │  User: 分析这段代码               │
│ • coder      │  researcher: 让我来分析...        │
│ • writer     │                                   │
│              │                                   │
├─────────────────────────────────────────────────┤
│ 输入消息: _                                      │
└─────────────────────────────────────────────────┘
```

### 快捷键

- **回车**: 发送消息
- **Ctrl+C**: 退出应用
- **Ctrl+N**: 创建新会话

### @mention功能（新增！）

现在支持智能@mention：

```bash
# 精确匹配
@researcher 分析这个函数

# 模糊匹配（新功能！）
@research 分析这个函数     # 自动匹配到researcher
@write 写文档              # 自动匹配到writer
@研究 帮我看看             # 支持中文匹配
```

---

## 🧪 测试新功能

运行集成测试验证5项新增强功能：

```bash
# 测试1: 完整集成测试
python3 test_integration.py

# 测试2: 功能验证测试
python3 test_verification.py
```

测试内容：
- ✅ Agent上下文隔离
- ✅ 实时状态追踪
- ✅ Token追踪与成本计算
- ✅ 智能重试策略
- ✅ @mention智能匹配

---

## 📁 配置文件位置

所有配置文件存储在用户目录：

```
~/.agent-chat-hub/
├── models.json      # 模型配置
├── agents.json      # Agent配置
└── sessions/        # 会话历史
```

API密钥安全存储在**系统密钥环**（不保存到文件）

---

## 🆘 常见问题

### Q1: 虚拟环境不存在

```bash
错误: 虚拟环境不存在
```

**解决**: 运行完整安装步骤（步骤1-4）

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
python init_config.py
```

### Q2: 依赖未安装

```bash
ModuleNotFoundError: No module named 'textual'
```

**解决**: 激活虚拟环境并安装依赖

```bash
source venv/bin/activate
pip install -e .
```

### Q3: API密钥未配置

```bash
错误: API密钥未配置
```

**解决**: 运行初始化配置

```bash
python init_config.py
```

### Q4: 找不到配置文件

```bash
FileNotFoundError: models.json
```

**解决**: 运行初始化配置创建配置文件

```bash
python init_config.py
```

---

## 🎯 新功能体验

### 1. 实时状态追踪

在聊天时，你现在可以看到：
- ⏳ Agent状态: PENDING → RUNNING → COMPLETED
- ⏱️ 执行时间统计
- 📊 Token使用量
- 💰 实时成本计算

### 2. 智能重试

网络错误时自动重试：
- 网络超时 → 自动重试（最多3次）
- API限流 → 自动重试（指数退避）
- 不可恢复错误 → 立即提示

### 3. Token追踪

实时显示：
```
📊 本会话Token统计:
├─ 输入: 1000 tokens
├─ 输出: 2000 tokens
├─ 总计: 3000 tokens
└─ 成本: $0.0330
```

### 4. 模糊@mention

不需要精确输入Agent名称：
```
@res     → researcher  ✅
@write   → writer      ✅
@review  → code_reviewer ✅
```

---

## 📚 更多文档

- **README.md** - 项目概述和架构
- **INTEGRATION_COMPLETE.md** - 5项新功能集成报告
- **INTEGRATION_GUIDE.md** - 技术集成指南
- **IMMEDIATE_LEARNING_APPLICATIONS.md** - 技术学习指南

---

## 🚦 项目状态

当前版本: **Phase 3 + 5项增强功能**

- ✅ Phase 1: MVP基础设施
- ✅ Phase 2: 多agent协作
- ✅ Phase 3: 插件系统
- ✅ **Phase 3.5: 5项Agent交互增强**（2026-09-05完成）

**测试状态**: 100%通过（58个测试 + 10个增强测试）

---

## 💡 快速命令参考

```bash
# 完整安装（首次）
python3 -m venv venv && source venv/bin/activate && pip install -e . && python init_config.py

# 日常启动
./start.sh

# 或手动启动
source venv/bin/activate && python main.py

# 运行测试
python3 test_integration.py

# 退出虚拟环境
deactivate
```

---

**享受使用Agent Chat Hub！** 🎉

有问题？查看 [README.md](README.md) 或 [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)
