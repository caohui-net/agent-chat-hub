# Configuration Guide - 配置指南

完整的Agent Chat Hub配置说明

---

## 配置文件概览

Agent Chat Hub使用JSON配置文件，存储在用户目录：

```
~/.agent-chat-hub/
├── models.json      # 模型配置
├── agents.json      # Agent配置
└── sessions/        # 会话历史
    └── {session_id}.json
```

**安全说明**：API密钥存储在系统密钥环（不在文件中）

---

## models.json - 模型配置

### 文件结构

```json
{
  "providers": {
    "anthropic": {
      "enabled": true,
      "models": [
        {
          "id": "claude-sonnet-3-5",
          "name": "Claude Sonnet 3.5",
          "max_tokens": 8192,
          "temperature": 0.7
        },
        {
          "id": "claude-opus-3",
          "name": "Claude Opus 3",
          "max_tokens": 4096,
          "temperature": 0.7
        }
      ]
    },
    "openai": {
      "enabled": false,
      "models": [
        {
          "id": "gpt-4-turbo",
          "name": "GPT-4 Turbo",
          "max_tokens": 4096,
          "temperature": 0.7
        }
      ]
    }
  },
  "default_provider": "anthropic"
}
```

### 字段说明

#### providers

| 字段 | 类型 | 说明 |
|------|------|------|
| `enabled` | boolean | 是否启用该提供商 |
| `models` | array | 可用模型列表 |

#### models

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `id` | string | 模型ID（API调用时使用） | 必填 |
| `name` | string | 显示名称 | 必填 |
| `max_tokens` | integer | 最大输出token数 | 4096 |
| `temperature` | float | 温度参数（0.0-1.0） | 0.7 |

### 添加新模型

```bash
# 编辑配置文件
nano ~/.agent-chat-hub/models.json
```

添加新模型到对应provider：

```json
{
  "id": "claude-haiku-3",
  "name": "Claude Haiku 3",
  "max_tokens": 4096,
  "temperature": 0.5
}
```

### 切换默认提供商

```json
{
  "default_provider": "openai"  // 改为openai
}
```

---

## agents.json - Agent配置

### 文件结构

```json
{
  "agents": [
    {
      "id": "agent_researcher",
      "name": "researcher",
      "role": "research",
      "model_id": "claude-sonnet-3-5",
      "provider": "anthropic",
      "system_prompt": "You are a research assistant...",
      "temperature": 0.7,
      "max_tokens": 4096,
      "enabled": true
    },
    {
      "id": "agent_coder",
      "name": "coder",
      "role": "coding",
      "model_id": "gpt-4-turbo",
      "provider": "openai",
      "system_prompt": "You are a coding assistant...",
      "temperature": 0.3,
      "max_tokens": 8192,
      "enabled": true
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `id` | string | Agent唯一ID（系统内部使用） | ✅ |
| `name` | string | Agent名称（@mention使用） | ✅ |
| `role` | string | Agent角色类型 | ✅ |
| `model_id` | string | 使用的模型ID | ✅ |
| `provider` | string | 模型提供商（anthropic/openai） | ✅ |
| `system_prompt` | string | 系统提示词 | ✅ |
| `temperature` | float | 温度参数（0.0-1.0） | ❌ (默认0.7) |
| `max_tokens` | integer | 最大输出token数 | ❌ (默认4096) |
| `enabled` | boolean | 是否启用 | ❌ (默认true) |

### 角色类型 (role)

预定义的角色类型：

| 角色 | 说明 | 推荐模型 |
|------|------|----------|
| `research` | 研究分析 | claude-sonnet-3-5 |
| `coding` | 代码编写 | gpt-4-turbo, claude-opus-3 |
| `writing` | 文档写作 | claude-sonnet-3-5 |
| `review` | 代码审查 | claude-opus-3 |
| `translation` | 翻译 | gpt-4-turbo |
| `general` | 通用助手 | claude-sonnet-3-5 |

### 创建新Agent

#### 方法1：使用init_config.py（推荐）

```bash
python init_config.py
```

选择"创建新Agent"选项

#### 方法2：手动编辑

```bash
nano ~/.agent-chat-hub/agents.json
```

添加新Agent配置：

```json
{
  "id": "agent_translator",
  "name": "translator",
  "role": "translation",
  "model_id": "claude-sonnet-3-5",
  "provider": "anthropic",
  "system_prompt": "You are a professional translator. Translate accurately while preserving tone and context.",
  "temperature": 0.5,
  "max_tokens": 4096,
  "enabled": true
}
```

### System Prompt模板

#### Research Agent

```
You are a research assistant specializing in analyzing information and providing insights. Your strengths include:
- Breaking down complex topics
- Finding patterns and connections
- Summarizing key findings
- Citing sources when available

Always provide clear, well-structured analysis.
```

#### Coding Agent

```
You are a coding assistant expert in software development. Your capabilities include:
- Writing clean, maintainable code
- Debugging and troubleshooting
- Code reviews and optimization
- Explaining technical concepts

Follow best practices and write production-ready code.
```

#### Writing Agent

```
You are a writing assistant skilled in creating clear, engaging content. You excel at:
- Documentation and technical writing
- Content structuring
- Grammar and style refinement
- Adapting tone for different audiences

Write professionally and concisely.
```

### 禁用Agent

```json
{
  "id": "agent_old",
  "enabled": false  // 禁用但保留配置
}
```

---

## API密钥配置

### 存储位置

API密钥存储在**系统密钥环**中，不保存到文件：

- **macOS**: Keychain
- **Linux**: Secret Service API (GNOME Keyring)
- **Windows**: Windows Credential Locker

### 配置API密钥

#### 使用init_config.py（推荐）

```bash
python init_config.py
```

选择"配置API密钥"选项

#### 手动配置（Python）

```python
from src.core.config import ConfigManager

config = ConfigManager()
config.set_api_key("your-api-key-here")
```

### 验证API密钥

```python
from src.core.config import ConfigManager

config = ConfigManager()
api_key = config.get_api_key()

if api_key:
    print("✅ API密钥已配置")
else:
    print("❌ API密钥未配置")
```

### 切换API密钥

```bash
# 重新运行配置向导
python init_config.py
```

选择"更新API密钥"选项

---

## 日志配置

### 日志位置

```
~/.agent-chat-hub/logs/
├── agent-chat-hub.log        # 主日志
├── agent-chat-hub.log.1      # 轮转日志
└── agent-chat-hub.log.2
```

### 日志级别

在 `src/core/config.py` 中配置：

```python
import logging

# 开发模式：详细日志
logging.basicConfig(level=logging.DEBUG)

# 生产模式：只记录重要信息
logging.basicConfig(level=logging.INFO)

# 静默模式：只记录错误
logging.basicConfig(level=logging.ERROR)
```

### 查看日志

```bash
# 实时查看日志
tail -f ~/.agent-chat-hub/logs/agent-chat-hub.log

# 查看最近100行
tail -n 100 ~/.agent-chat-hub/logs/agent-chat-hub.log

# 搜索错误
grep "ERROR" ~/.agent-chat-hub/logs/agent-chat-hub.log
```

---

## 会话配置

### 会话历史位置

```
~/.agent-chat-hub/sessions/
└── {session_id}.json
```

### 会话文件格式

```json
{
  "session_id": "session_20260906_143022",
  "created_at": "2026-09-06T14:30:22Z",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2026-09-06T14:30:22Z"
    },
    {
      "role": "assistant",
      "agent_id": "agent_researcher",
      "content": "Hello! How can I help you?",
      "timestamp": "2026-09-06T14:30:25Z",
      "tokens": {
        "input": 10,
        "output": 15
      }
    }
  ],
  "metadata": {
    "total_tokens": 25,
    "total_cost_usd": 0.0002
  }
}
```

### 清理旧会话

```bash
# 删除30天前的会话
find ~/.agent-chat-hub/sessions/ -name "*.json" -mtime +30 -delete

# 删除所有会话（保留配置）
rm -rf ~/.agent-chat-hub/sessions/*
```

---

## 高级配置

### Token限制

在 `agents.json` 中为每个Agent设置：

```json
{
  "max_tokens": 8192,  // 单次输出最大token数
  "max_context_tokens": 100000  // 上下文最大token数（可选）
}
```

### 温度参数调优

| 温度 | 适用场景 | 示例 |
|------|----------|------|
| 0.0-0.3 | 确定性任务 | 代码生成、数据分析 |
| 0.4-0.7 | 平衡任务 | 研究、文档写作 |
| 0.8-1.0 | 创意任务 | 头脑风暴、创意写作 |

### 重试配置

在 `src/agents/executor.py` 中配置：

```python
RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 1.0,  # 秒
    "max_delay": 10.0,
    "exponential_base": 2
}
```

---

## 配置迁移

### 导出配置

```bash
# 创建备份目录
mkdir -p ~/agent-chat-hub-backup

# 导出配置
cp -r ~/.agent-chat-hub/*.json ~/agent-chat-hub-backup/
```

### 导入配置

```bash
# 从备份恢复
cp ~/agent-chat-hub-backup/*.json ~/.agent-chat-hub/
```

### 迁移到新机器

```bash
# 在旧机器上
tar -czf agent-chat-hub-config.tar.gz ~/.agent-chat-hub/

# 传输文件到新机器

# 在新机器上
tar -xzf agent-chat-hub-config.tar.gz -C ~/
```

**注意**：API密钥不会被导出，需要在新机器上重新配置

---

## 配置验证

### 检查配置文件

```bash
python -c "
from src.core.config import ConfigManager
import json

config = ConfigManager()
print('✅ 配置文件加载成功')
print(f'默认提供商: {config.default_provider}')
print(f'已配置Agent数: {len(config.agents)}')
"
```

### 测试API连接

```bash
python -c "
from src.agents.executor import AgentExecutor
from src.core.config import ConfigManager

config = ConfigManager()
executor = AgentExecutor(config)
print('✅ AgentExecutor初始化成功')
"
```

---

## 故障排除

### 配置文件损坏

```bash
# 重新生成默认配置
python init_config.py --reset
```

### API密钥丢失

```bash
# 重新配置
python init_config.py
```

选择"更新API密钥"

### Agent不可用

检查 `agents.json` 中的 `enabled` 字段：

```json
{
  "enabled": true  // 确保为true
}
```

---

## 相关文档

- [快速开始](QUICKSTART.md)
- [故障排除](TROUBLESHOOTING.md)
- [API参考](../api-reference/API.md)

---

**版本**: v1.0  
**更新日期**: 2026-09-06
