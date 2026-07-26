# 配置参考手册

**版本**: 0.1.0  
**更新**: 2026-07-26

---

## 配置文件

### models.json - 模型配置

**位置**: `config/models.json`

**格式**：
```json
[
  {
    "model_id": "claude-3-sonnet",
    "provider": "anthropic",
    "display_name": "Claude 3 Sonnet",
    "base_url": "https://api.anthropic.com/v1/messages",
    "api_key_name": "anthropic_api_key"
  }
]
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model_id` | string | ✓ | 模型唯一标识符 |
| `provider` | string | ✓ | 提供商：anthropic/openai/gemini |
| `display_name` | string | ✓ | 显示名称 |
| `base_url` | string | ✓ | API端点URL |
| `api_key_name` | string | ✓ | API密钥在keyring中的名称 |

---

### agents.json - Agent配置

**位置**: `config/agents.json`

**格式**：
```json
[
  {
    "agent_id": "coordinator",
    "name": "总管",
    "role": "协调和引导对话",
    "role_type": "coordinator",
    "model_id": "claude-3-sonnet",
    "priority": 1,
    "active": true,
    "system_prompt": null,
    "extra_config": {}
  }
]
```

**字段说明**：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `agent_id` | string | ✓ | - | Agent唯一标识符 |
| `name` | string | ✓ | - | 显示名称 |
| `role` | string | ✓ | - | 角色描述 |
| `role_type` | string | ✗ | null | 角色类型（coordinator等） |
| `model_id` | string | ✓ | - | 关联的模型ID |
| `priority` | integer | ✗ | 100 | 优先级（1-1000，越小越优先） |
| `active` | boolean | ✗ | true | 是否激活 |
| `system_prompt` | string | ✗ | null | 自定义系统提示 |
| `extra_config` | object | ✗ | {} | 额外配置 |

---

## 环境变量

### LOG_LEVEL

**说明**: 日志级别

**可选值**: `DEBUG`, `INFO`, `WARNING`, `ERROR`

**默认值**: `INFO`

**示例**：
```bash
export LOG_LEVEL=DEBUG
python3 main.py
```

---

### PYTHONPATH

**说明**: Python模块搜索路径

**用途**: 未安装项目时运行脚本

**示例**：
```bash
export PYTHONPATH=.
python3 benchmarks/benchmark_phase2.py
```

---

### CONFIG_DIR

**说明**: 配置文件目录（未来支持）

**默认值**: `./config`

---

## 响应协调器配置

### BudgetLimits

**代码位置**: `src/agents/coordinator.py`

**配置示例**：
```python
from src.agents.coordinator import ResponseCoordinator, BudgetLimits

coordinator = ResponseCoordinator(
    budget_limits=BudgetLimits(
        max_agents=3,           # 最多3个并发Agent
        max_calls_per_round=5,  # 每轮最多5次调用
        max_tokens=15000,       # 最多15k tokens
        timeout_seconds=120.0   # 120秒超时
    )
)
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_agents` | int | 3 | 最大并发Agent数 |
| `max_calls_per_round` | int | 3 | 每轮最大调用次数 |
| `max_tokens` | int | 12000 | 最大token数 |
| `timeout_seconds` | float | 120.0 | 超时时间（秒） |

---

## 路由规则配置

### Coordinator路由

**规则**：
- **无@mention**：只有coordinator角色响应
- **有@mention**：只有被@的Agents响应

**配置coordinator角色**：
```json
{
  "agent_id": "coordinator",
  "role_type": "coordinator"
}
```

---

## 优先级配置建议

| Agent类型 | 推荐优先级范围 | 说明 |
|-----------|----------------|------|
| Coordinator | 1-10 | 最高优先级，引导对话 |
| 专业Agent | 50-100 | 中等优先级，专业领域 |
| 辅助Agent | 200-500 | 较低优先级，辅助功能 |

**示例**：
```json
[
  {"agent_id": "coordinator", "priority": 1},
  {"agent_id": "tech_expert", "priority": 50},
  {"agent_id": "helper", "priority": 200}
]
```

---

## API密钥管理

### Keyring配置

**查看已存储的密钥**：
```bash
keyring get agent-chat-hub anthropic_api_key
```

**设置新密钥**：
```bash
keyring set agent-chat-hub anthropic_api_key
```

**删除密钥**：
```bash
keyring del agent-chat-hub anthropic_api_key
```

---

## 会话配置

### 会话存储位置

**默认**: `config/sessions/`

**文件格式**: JSON

**命名规则**: `session_{timestamp}_{title}.json`

---

## 性能调优

### 减少并发数

```python
BudgetLimits(max_agents=2)  # 降低到2个
```

### 调整超时时间

```python
BudgetLimits(timeout_seconds=60.0)  # 缩短到60秒
```

### 优化日志

```bash
export LOG_LEVEL=WARNING  # 生产环境
```

---

## 配置最佳实践

1. **至少配置一个coordinator角色**
2. **设置合理的优先级**（避免冲突）
3. **定期备份配置文件**
4. **使用keyring管理密钥**（不要明文存储）
5. **测试配置后再部署**

---

## 相关文档

- **用户手册**: `USER_GUIDE.md`
- **部署指南**: `DEPLOYMENT.md`
- **故障排除**: `TROUBLESHOOTING.md`
- **性能分析**: `PERFORMANCE.md`
