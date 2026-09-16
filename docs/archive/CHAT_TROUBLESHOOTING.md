# 🔧 Chat功能问题解决方案

## 📊 问题诊断结果

根据诊断，发现以下问题：

### ❌ 问题1: API客户端库未安装
```
✗ anthropic - 未安装
✗ google.generativeai - 未安装  
✗ openai - 未安装
```

### ❌ 问题2: API密钥未设置
```
✗ ANTHROPIC_API_KEY 未设置
✗ GOOGLE_API_KEY 未设置
✗ OPENAI_API_KEY 未设置
```

### ✅ 好消息
- ✅ 所有核心模块正常
- ✅ 新集成的5项技术全部正常
- ✅ Agent配置已存在（4个agents）
- ✅ TUI应用可以启动

---

## 🚀 解决方案

### 方案1: 安装所有API客户端（推荐）

```bash
# 安装Anthropic SDK
pip install anthropic

# 安装Google Generative AI
pip install google-generativeai

# 安装OpenAI SDK
pip install openai

# 或者一次性安装所有依赖
pip install anthropic google-generativeai openai
```

### 方案2: 只安装你需要的API客户端

如果你只想使用某个特定的AI服务：

```bash
# 只使用Claude
pip install anthropic
export ANTHROPIC_API_KEY=your_anthropic_key

# 或只使用Gemini
pip install google-generativeai
export GOOGLE_API_KEY=your_google_key

# 或只使用OpenAI
pip install openai
export OPENAI_API_KEY=your_openai_key
```

---

## 🔑 设置API密钥

### 方法1: 环境变量（临时，当前会话有效）

```bash
# Anthropic (Claude)
export ANTHROPIC_API_KEY=sk-ant-...

# Google (Gemini)
export GOOGLE_API_KEY=AIza...

# OpenAI (GPT)
export OPENAI_API_KEY=sk-proj-...
```

### 方法2: 添加到 ~/.bashrc（永久生效）

```bash
# 编辑 ~/.bashrc
nano ~/.bashrc

# 添加以下行
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-proj-...

# 保存后重新加载
source ~/.bashrc
```

### 方法3: 使用 .env 文件

```bash
# 在项目根目录创建 .env 文件
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-proj-...
EOF

# 确保 .env 在 .gitignore 中
echo ".env" >> .gitignore
```

---

## ⚡ 快速启动步骤

### 1. 安装依赖
```bash
pip install anthropic google-generativeai openai
```

### 2. 设置API密钥
```bash
# 设置至少一个API密钥（根据你的agents配置）
export ANTHROPIC_API_KEY=your_key  # 用于 Claude
export GOOGLE_API_KEY=your_key     # 用于 Gemini
export OPENAI_API_KEY=your_key     # 用于 GPT
```

### 3. 验证配置
```bash
# 运行诊断脚本
python3 diagnose_chat.py

# 应该看到 ✅ 所有检查通过
```

### 4. 测试chat功能
```bash
# 运行测试脚本
python3 test_chat_functionality.py
```

### 5. 启动TUI应用
```bash
# 启动完整的TUI界面
python3 main.py
```

---

## 🎯 当前Agent配置

你的系统已配置4个agents：

| Agent | 名称 | 角色 | 模型 | 状态 |
|-------|------|------|------|------|
| coordinator | 总管 | 团队协调者 | claude-opus-4-8 | ✓ 活跃 |
| agent_claude | Claude助手 | 主对话助手 | claude-opus-4-8 | ✓ 活跃 |
| agent_codex | Codex助手 | 代码专家 | gpt-5.6-sol | ✓ 活跃 |
| agent_gemini | Gemini助手 | 分析专家 | gemini-3.1-pro-preview | ✓ 活跃 |

**所需API密钥：**
- coordinator 和 agent_claude 需要 **ANTHROPIC_API_KEY**
- agent_codex 需要 **OPENAI_API_KEY**
- agent_gemini 需要 **GOOGLE_API_KEY**

**建议：** 至少设置 **ANTHROPIC_API_KEY**，这样coordinator和agent_claude就能工作。

---

## 💡 最小化启动方案（只使用Claude）

如果你只想快速测试，可以只安装Anthropic SDK：

```bash
# 1. 安装
pip install anthropic

# 2. 设置密钥
export ANTHROPIC_API_KEY=your_anthropic_key

# 3. 禁用其他agents（可选）
# 编辑 ~/.agent-chat-hub/agents.json
# 将 agent_codex 和 agent_gemini 的 "active" 改为 false

# 4. 启动
python3 main.py
```

这样系统只会使用coordinator和agent_claude，都是Claude模型。

---

## 🐛 如果还有问题

### 问题: 安装包后仍然提示未找到

```bash
# 检查pip安装位置
which pip3

# 确认包已安装
pip3 list | grep -E "anthropic|google-generativeai|openai"

# 如果使用虚拟环境，确保激活
source venv/bin/activate  # 如果有虚拟环境
```

### 问题: API密钥设置后仍提示未设置

```bash
# 验证环境变量
echo $ANTHROPIC_API_KEY
echo $GOOGLE_API_KEY
echo $OPENAI_API_KEY

# 确保在启动应用前设置
export ANTHROPIC_API_KEY=...
python3 main.py  # 在同一终端会话中运行
```

### 问题: TUI界面显示不正常

```bash
# 检查终端支持
echo $TERM

# 尝试不同的终端
# 推荐: gnome-terminal, konsole, iTerm2, Windows Terminal
```

---

## 📚 相关文档

- **INTEGRATION_SUMMARY.md** - 新功能集成总结
- **QUICK_START.md** - 快速开始指南
- **README.md** - 项目说明

---

## ✅ 验证清单

安装完成后，运行以下命令验证：

```bash
# ✅ 1. 检查Python包
pip3 list | grep -E "anthropic|google-generativeai|openai"

# ✅ 2. 检查环境变量
env | grep -E "ANTHROPIC_API_KEY|GOOGLE_API_KEY|OPENAI_API_KEY"

# ✅ 3. 运行诊断
python3 diagnose_chat.py

# ✅ 4. 运行测试
python3 test_chat_functionality.py

# ✅ 5. 启动应用
python3 main.py
```

---

**生成日期**: 2026-09-06  
**状态**: 问题已识别，解决方案已提供
