# 模型接入标准配置指南

**最后更新：** 2026-07-20  
**项目：** agent-chat-hub  
**状态：** 已验证可用  

---

## 概述

本文档记录了3个已成功配置的AI模型的标准接入方法，包括：
1. Claude Opus 4.8
2. GPT-5.6 Sol (Codex)
3. Gemini 3.1 Pro Preview

**所有模型均使用HTTP API调用，保持架构一致性。**

---

## 通用原则

### 配置要求

1. **API调用方式：** HTTP REST API（异步）
2. **认证方式：** API Key（支持配置文件存储）
3. **消息格式：** 完整历史传递（保持对话记忆）
4. **错误处理：** 统一的异常处理机制

### 文件结构

```
config/
├── models.json      # 模型配置
└── agents.json      # Agent配置

src/
├── core/
│   ├── models.py    # 数据模型定义
│   └── config.py    # 配置管理
└── agents/
    └── executor.py  # API调用执行器
```

---

## 模型1：Claude Opus 4.8

### 配置信息

**models.json:**
```json
{
  "claude-opus-4-8": {
    "model_id": "claude-opus-4-8",
    "provider": "anthropic",
    "display_name": "Claude Opus 4.8",
    "base_url": "https://code.newcli.com/claude/aws",
    "api_key_name": "claude_api_key",
    "api_key": "sk-ant-oat01-...",
    "max_tokens": 4096,
    "temperature": 1.0
  }
}
```

### API协议

**Endpoint:** `{base_url}/v1/messages`

**请求格式：**
```json
{
  "model": "claude-opus-4-8",
  "max_tokens": 4096,
  "temperature": 1.0,
  "messages": [
    {"role": "user", "content": "消息内容"},
    {"role": "assistant", "content": "回复内容"}
  ]
}
```

**请求头：**
```
Content-Type: application/json
x-api-key: {api_key}
anthropic-version: 2023-06-01
```

### 实现代码

**位置：** `src/agents/executor.py:_call_anthropic()`

**关键特性：**
- ✅ 支持system prompt
- ✅ 完整消息历史传递
- ✅ 异步HTTP调用（httpx）

---

## 模型2：GPT-5.6 Sol (Codex)

### 配置信息

**models.json:**
```json
{
  "gpt-5.6-sol": {
    "model_id": "gpt-5.6-sol",
    "provider": "openai",
    "display_name": "GPT-5.6 Sol (Codex)",
    "base_url": "https://code.newcli.com/codex/v1",
    "api_key_name": "codex_api_key",
    "api_key": "sk-ant-oat01-...",
    "max_tokens": 4096,
    "temperature": 1.0
  }
}
```

### API协议

**Endpoint:** `{base_url}/chat/completions`

**注意：** base_url已包含`/v1`，不要重复添加

**请求格式：**
```json
{
  "model": "gpt-5.6-sol",
  "max_tokens": 4096,
  "temperature": 1.0,
  "messages": [
    {"role": "system", "content": "系统提示"},
    {"role": "user", "content": "用户消息"},
    {"role": "assistant", "content": "助手回复"}
  ]
}
```

**请求头：**
```
Content-Type: application/json
Authorization: Bearer {api_key}
```

### 实现代码

**位置：** `src/agents/executor.py:_call_openai()`

**关键特性：**
- ✅ OpenAI兼容协议
- ✅ system prompt插入消息开头
- ✅ 完整消息历史传递

---

## 模型3：Gemini 3.1 Pro Preview

### 配置信息

**models.json:**
```json
{
  "gemini-3.1-pro-preview": {
    "model_id": "gemini-3.1-pro-preview",
    "provider": "gemini-http",
    "display_name": "Gemini 3.1 Pro Preview",
    "base_url": "https://code.newcli.com/gemini",
    "api_key_name": "gemini_api_key",
    "api_key": "sk-ant-oat01-...",
    "max_tokens": 4096,
    "temperature": 1.0
  }
}
```

### API协议

**Endpoint:** `{base_url}/v1beta/models/{model_id}:generateContent`

**请求格式：**
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "用户消息"}]
    },
    {
      "role": "model",
      "parts": [{"text": "模型回复"}]
    }
  ],
  "generationConfig": {
    "temperature": 1.0,
    "maxOutputTokens": 4096
  },
  "systemInstruction": {
    "parts": [{"text": "系统指令"}]
  }
}
```

**请求头：**
```
Content-Type: application/json
x-goog-api-key: {api_key}
```

**消息格式转换：**
- `user` → `user`
- `assistant` → `model`

### 实现代码

**位置：** `src/agents/executor.py:_call_gemini_http()`

**关键特性：**
- ✅ 完整消息历史传递
- ✅ Gemini原生格式支持
- ✅ systemInstruction支持

**⚠️ 重要：不要使用CLI方式**
- ❌ 不要用`subprocess.run(["gemini", ...])`
- ✅ 必须用HTTP API确保对话记忆

---

## Agent配置

**agents.json:**
```json
{
  "agent_claude": {
    "agent_id": "agent_claude",
    "name": "Claude助手",
    "role": "主对话助手",
    "model_id": "claude-opus-4-8",
    "priority": 100,
    "active": true,
    "system_prompt": "你是Claude，一个有帮助、诚实、无害的AI助手。"
  },
  "agent_codex": {
    "agent_id": "agent_codex",
    "name": "Codex助手",
    "role": "代码专家",
    "model_id": "gpt-5.6-sol",
    "priority": 150,
    "active": true,
    "system_prompt": "你是Codex，专注于代码编写和技术问题解答的AI助手。"
  },
  "agent_gemini": {
    "agent_id": "agent_gemini",
    "name": "Gemini助手",
    "role": "分析专家",
    "model_id": "gemini-3.1-pro-preview",
    "priority": 200,
    "active": true,
    "system_prompt": "你是Gemini，擅长数据分析和推理的AI助手。"
  }
}
```

---

## 使用示例

### Python代码调用

```python
from src.core.config import ConfigManager
from src.agents.executor import AgentExecutor
from src.core.models import Message

# 初始化
config_manager = ConfigManager(config_dir="config")
config_manager.load_configs()
executor = AgentExecutor(config_manager)

# 获取Agent配置
agent_config = config_manager.get_agent("agent_claude")

# 构造消息
messages = [
    Message(role="user", content="你好"),
    Message(role="assistant", content="你好！有什么可以帮助你的？"),
    Message(role="user", content="请介绍你自己")
]

# 执行调用（异步）
import asyncio
response = asyncio.run(executor.execute(agent_config, messages))
print(response)
```

---

## 测试验证

### 基本响应测试

```python
async def test_basic_response():
    """测试基本响应"""
    messages = [Message(role="user", content="你好")]
    response = await executor.execute(agent_config, messages)
    assert response and len(response) > 0
```

### 多轮对话测试（必须）

```python
async def test_multiturn_dialogue():
    """测试多轮对话记忆"""
    messages = [
        Message(role="user", content="我的名字叫小明"),
        Message(role="assistant", content="你好，小明！"),
        Message(role="user", content="我叫什么名字？")
    ]
    response = await executor.execute(agent_config, messages)
    assert "小明" in response
```

---

## 常见问题

### Q1: 如何添加新模型？

1. 在`models.json`添加配置
2. 在`models.py`添加provider验证（如需要）
3. 在`executor.py`实现调用方法
4. 更新`SUPPORTED_PROVIDERS`列表
5. 在`execute()`方法添加路由逻辑
6. **必须测试多轮对话**

### Q2: API Key存储在哪里？

两种方式（优先级）：
1. `models.json`中的`api_key`字段（直接存储）
2. 系统keyring（`api_key_name`指定）

代码会优先使用配置文件中的api_key。

### Q3: 如何保证对话记忆？

**关键：传递完整消息历史**

```python
# ✅ 正确：完整历史
messages = [msg1, msg2, msg3, ...]
response = await executor.execute(agent_config, messages)

# ❌ 错误：只传最后一条
last_message = messages[-1]
response = await executor.execute(agent_config, [last_message])
```

### Q4: 为什么不用CLI？

CLI方式（如`gemini` CLI）的问题：
- ❌ 每次调用独立subprocess，无法保持会话
- ❌ 需要手动管理session state
- ❌ 架构不一致，增加维护成本

HTTP API方式的优势：
- ✅ 完整消息历史传递
- ✅ 架构一致
- ✅ 易于测试和调试

---

## 架构设计原则

### 1. 一致性优先

所有模型使用相同的调用方式（HTTP API），除非有明确的技术障碍。

### 2. 消息历史完整性

所有实现必须支持完整消息历史传递，确保对话记忆功能。

### 3. 异步优先

使用`async/await`模式，支持多Agent并发调用。

### 4. 配置驱动

模型配置和Agent配置分离，便于管理和扩展。

---

## 验证清单

新模型接入前必须完成：

- [ ] HTTP API可行性验证（curl测试）
- [ ] 配置文件添加（models.json + agents.json）
- [ ] 实现调用方法（executor.py）
- [ ] provider验证更新（models.py）
- [ ] 路由逻辑更新（executor.py:execute()）
- [ ] 基本响应测试
- [ ] **多轮对话测试**（必须）
- [ ] 错误处理测试
- [ ] 文档更新

---

## 参考资料

- **实现代码：** `src/agents/executor.py`
- **配置文件：** `config/models.json`, `config/agents.json`
- **数据模型：** `src/core/models.py`
- **测试脚本：** `test_gemini_http.py`

---

**版本：** v1.0  
**验证日期：** 2026-07-20  
**所有模型测试通过率：** 100%
