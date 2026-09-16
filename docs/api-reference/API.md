# API Reference - API参考文档

Agent Chat Hub核心API文档

---

## 目录

- [AgentExecutor](#agentexecutor) - Agent执行器
- [SessionManager](#sessionmanager) - 会话管理器
- [ResponseCoordinator](#responsecoordinator) - 响应协调器
- [ConfigManager](#configmanager) - 配置管理器
- [ContextManager](#contextmanager) - 上下文管理器
- [AgentStatusManager](#agentstatusmanager) - 状态管理器
- [TokenTracker](#tokentracker) - Token追踪器

---

## AgentExecutor

Agent执行器 - 负责调用模型API并获取响应

### 类定义

```python
from src.agents.executor import AgentExecutor
from src.core.config import ConfigManager

executor = AgentExecutor(
    config_manager: ConfigManager,
    message_bus: Optional[MessageBus] = None
)
```

### 参数

| 参数 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `config_manager` | `ConfigManager` | 配置管理器 | ✅ |
| `message_bus` | `MessageBus` | 消息总线（用于发布token事件） | ❌ |

### 方法

#### execute_agent

异步执行单个Agent并获取响应

```python
async def execute_agent(
    agent: AgentConfig,
    messages: List[Message],
    session_id: str
) -> AgentMessage
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent` | `AgentConfig` | Agent配置对象 |
| `messages` | `List[Message]` | 消息历史 |
| `session_id` | `str` | 会话ID |

**返回**：

- `AgentMessage`: Agent响应消息对象

**异常**：

- `AgentExecutionError`: Agent执行失败
- `UnsupportedProviderError`: 不支持的模型提供商

**示例**：

```python
from src.core.models import Message, AgentConfig

# 准备消息
messages = [
    Message(role="user", content="Hello")
]

# 获取Agent配置
agent = config_manager.get_agent("agent_researcher")

# 执行Agent
response = await executor.execute_agent(
    agent=agent,
    messages=messages,
    session_id="session_123"
)

print(f"响应: {response.content}")
print(f"Token: {response.token_usage.total_tokens}")
```

#### execute_agents_parallel

并发执行多个Agent

```python
async def execute_agents_parallel(
    agents: List[AgentConfig],
    messages: List[Message],
    session_id: str
) -> List[AgentMessage]
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agents` | `List[AgentConfig]` | Agent配置列表 |
| `messages` | `List[Message]` | 消息历史 |
| `session_id` | `str` | 会话ID |

**返回**：

- `List[AgentMessage]`: Agent响应列表

**示例**：

```python
# 并发执行3个Agent
agents = [
    config_manager.get_agent("agent_researcher"),
    config_manager.get_agent("agent_coder"),
    config_manager.get_agent("agent_writer")
]

responses = await executor.execute_agents_parallel(
    agents=agents,
    messages=messages,
    session_id="session_123"
)

for response in responses:
    print(f"{response.agent_id}: {response.content}")
```

#### aclose

异步关闭HTTP客户端（清理资源）

```python
async def aclose()
```

**示例**：

```python
# 使用完毕后关闭
await executor.aclose()
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `retry_policy` | `RetryPolicy` | 重试策略配置 |
| `token_tracker` | `TokenTracker` | Token追踪器 |
| `SUPPORTED_PROVIDERS` | `List[str]` | 支持的模型提供商列表 |

---

## SessionManager

会话管理器 - 管理对话历史和会话状态

### 类定义

```python
from src.agents.session import SessionManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor

session_manager = SessionManager(
    config_manager: ConfigManager,
    coordinator: ResponseCoordinator,
    executor: AgentExecutor,
    session_dir: Optional[Path] = None,
    status_callback: Optional[callable] = None
)
```

### 参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `config_manager` | `ConfigManager` | 配置管理器 | - |
| `coordinator` | `ResponseCoordinator` | 响应协调器 | - |
| `executor` | `AgentExecutor` | Agent执行器 | - |
| `session_dir` | `Path` | 会话存储目录 | `~/.agent-chat-hub/sessions` |
| `status_callback` | `callable` | 状态变化回调函数 | `None` |

### 方法

#### create_session

创建新会话

```python
def create_session(title: str = "新对话") -> SessionConfig
```

**参数**：

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `title` | `str` | 会话标题 | `"新对话"` |

**返回**：

- `SessionConfig`: 新创建的会话配置

**示例**：

```python
session = session_manager.create_session("项目讨论")
print(f"会话ID: {session.session_id}")
```

#### process_user_input

处理用户输入并获取Agent响应

```python
async def process_user_input(
    user_input: str,
    mentioned_agents: Optional[List[str]] = None
) -> List[AgentMessage]
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_input` | `str` | 用户输入文本 |
| `mentioned_agents` | `List[str]` | 明确指定的Agent ID列表（可选） |

**返回**：

- `List[AgentMessage]`: Agent响应列表

**示例**：

```python
# 方法1: 自动解析@mention
responses = await session_manager.process_user_input(
    "@researcher 分析这段代码"
)

# 方法2: 明确指定Agent
responses = await session_manager.process_user_input(
    "分析这段代码",
    mentioned_agents=["agent_researcher"]
)

for response in responses:
    print(f"{response.agent_id}: {response.content}")
```

#### save_session

保存会话到磁盘

```python
def save_session()
```

**示例**：

```python
session_manager.save_session()
```

#### load_session

从磁盘加载会话

```python
def load_session(session_id: str) -> SessionConfig
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `session_id` | `str` | 会话ID |

**返回**：

- `SessionConfig`: 会话配置对象

**异常**：

- `FileNotFoundError`: 会话文件不存在

**示例**：

```python
session = session_manager.load_session("session_20260906_143022")
print(f"加载会话: {session.title}")
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `current_session` | `SessionConfig` | 当前会话配置 |
| `context_manager` | `ContextManager` | Agent上下文管理器 |
| `status_manager` | `AgentStatusManager` | Agent状态管理器 |
| `token_tracker` | `TokenTracker` | Token追踪器 |
| `message_bus` | `MessageBus` | Agent间消息总线 |

---

## ResponseCoordinator

响应协调器 - 决定哪些Agent应该响应

### 类定义

```python
from src.agents.coordinator import ResponseCoordinator

coordinator = ResponseCoordinator()
```

### 方法

#### determine_responding_agents

确定应该响应的Agent列表

```python
def determine_responding_agents(
    message: str,
    available_agents: List[AgentConfig],
    mentioned_agents: Optional[List[str]] = None
) -> List[AgentConfig]
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `message` | `str` | 用户消息 |
| `available_agents` | `List[AgentConfig]` | 可用Agent列表 |
| `mentioned_agents` | `List[str]` | 被@mention的Agent ID列表 |

**返回**：

- `List[AgentConfig]`: 应该响应的Agent列表

**示例**：

```python
message = "@researcher 分析这段代码"
available_agents = config_manager.list_agents(active_only=True)
mentioned_agents = ["agent_researcher"]

responding_agents = coordinator.determine_responding_agents(
    message=message,
    available_agents=available_agents,
    mentioned_agents=mentioned_agents
)

print(f"响应Agent数: {len(responding_agents)}")
```

---

## ConfigManager

配置管理器 - 管理模型和Agent配置

### 类定义

```python
from src.core.config import ConfigManager

config_manager = ConfigManager(
    config_dir: Optional[Path] = None
)
```

### 参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `config_dir` | `Path` | 配置目录 | `~/.agent-chat-hub` |

### 方法

#### get_api_key

获取API密钥（从系统密钥环）

```python
def get_api_key(provider: str = "anthropic") -> Optional[str]
```

**参数**：

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `provider` | `str` | 提供商名称 | `"anthropic"` |

**返回**：

- `str`: API密钥，如果未配置则返回`None`

**示例**：

```python
api_key = config_manager.get_api_key("anthropic")
if api_key:
    print("✅ API密钥已配置")
```

#### set_api_key

设置API密钥（保存到系统密钥环）

```python
def set_api_key(api_key: str, provider: str = "anthropic")
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `api_key` | `str` | API密钥 |
| `provider` | `str` | 提供商名称 |

**示例**：

```python
config_manager.set_api_key(
    "sk-ant-api03-...",
    provider="anthropic"
)
```

#### get_agent

获取单个Agent配置

```python
def get_agent(agent_id: str) -> Optional[AgentConfig]
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent_id` | `str` | Agent ID |

**返回**：

- `AgentConfig`: Agent配置对象，如果不存在则返回`None`

**示例**：

```python
agent = config_manager.get_agent("agent_researcher")
if agent:
    print(f"模型: {agent.model_id}")
```

#### list_agents

列出所有Agent

```python
def list_agents(active_only: bool = False) -> List[AgentConfig]
```

**参数**：

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `active_only` | `bool` | 只返回已启用的Agent | `False` |

**返回**：

- `List[AgentConfig]`: Agent配置列表

**示例**：

```python
# 获取所有Agent
all_agents = config_manager.list_agents()

# 只获取已启用的Agent
active_agents = config_manager.list_agents(active_only=True)

for agent in active_agents:
    print(f"{agent.name}: {agent.role}")
```

---

## ContextManager

Agent上下文管理器 - 管理每个Agent的独立上下文

### 类定义

```python
from src.core.agent_context import ContextManager

context_manager = ContextManager()
```

### 方法

#### get_agent_context

获取Agent的上下文

```python
def get_agent_context(agent_id: str) -> AgentContext
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent_id` | `str` | Agent ID |

**返回**：

- `AgentContext`: Agent上下文对象

**示例**：

```python
context = context_manager.get_agent_context("agent_researcher")

# 访问Agent的私有消息
for msg in context.session_messages:
    print(f"{msg.role}: {msg.content}")

# 访问Agent的状态
print(f"状态: {context.state}")
```

#### add_message_to_context

添加消息到Agent上下文

```python
def add_message_to_context(
    agent_id: str,
    message: Message
)
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent_id` | `str` | Agent ID |
| `message` | `Message` | 消息对象 |

**示例**：

```python
from src.core.models import Message

message = Message(role="user", content="Hello")
context_manager.add_message_to_context("agent_researcher", message)
```

---

## AgentStatusManager

Agent状态管理器 - 追踪Agent执行状态

### 类定义

```python
from src.core.agent_status import AgentStatusManager

status_manager = AgentStatusManager()
```

### 方法

#### update_status

更新Agent状态

```python
def update_status(
    agent_id: str,
    status: AgentStatus,
    error: Optional[str] = None
)
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent_id` | `str` | Agent ID |
| `status` | `AgentStatus` | 状态枚举值 |
| `error` | `str` | 错误消息（可选） |

**状态枚举**：

```python
class AgentStatus(Enum):
    IDLE = "idle"           # 空闲
    PENDING = "pending"     # 等待中
    RUNNING = "running"     # 执行中
    COMPLETED = "completed" # 已完成
    ERROR = "error"         # 错误
```

**示例**：

```python
from src.core.agent_status import AgentStatus

# 开始执行
status_manager.update_status("agent_researcher", AgentStatus.RUNNING)

# 执行完成
status_manager.update_status("agent_researcher", AgentStatus.COMPLETED)

# 执行失败
status_manager.update_status(
    "agent_researcher",
    AgentStatus.ERROR,
    error="API超时"
)
```

#### get_status

获取Agent状态

```python
def get_status(agent_id: str) -> AgentState
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent_id` | `str` | Agent ID |

**返回**：

- `AgentState`: Agent状态对象

**AgentState属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `status` | `AgentStatus` | 当前状态 |
| `start_time` | `float` | 开始时间（时间戳） |
| `elapsed_seconds` | `float` | 已耗时（秒） |
| `total_tokens` | `int` | 累计token数 |
| `error` | `str` | 错误消息 |

**示例**：

```python
state = status_manager.get_status("agent_researcher")

print(f"状态: {state.status.value}")
print(f"耗时: {state.elapsed_seconds:.1f}s")
print(f"Token: {state.total_tokens}")

if state.error:
    print(f"错误: {state.error}")
```

#### get_all_statuses

获取所有Agent状态

```python
def get_all_statuses() -> Dict[str, AgentState]
```

**返回**：

- `Dict[str, AgentState]`: Agent ID到状态的映射

**示例**：

```python
all_statuses = status_manager.get_all_statuses()

for agent_id, state in all_statuses.items():
    print(f"{agent_id}: {state.status.value} ({state.elapsed_seconds:.1f}s)")
```

---

## TokenTracker

Token追踪器 - 追踪token使用和成本

### 类定义

```python
from src.core.token_tracker import TokenTracker

token_tracker = TokenTracker()
```

### 方法

#### record_usage

记录token使用

```python
def record_usage(
    agent_id: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float
)
```

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `agent_id` | `str` | Agent ID |
| `input_tokens` | `int` | 输入token数 |
| `output_tokens` | `int` | 输出token数 |
| `cost_usd` | `float` | 成本（美元） |

**示例**：

```python
token_tracker.record_usage(
    agent_id="agent_researcher",
    input_tokens=100,
    output_tokens=200,
    cost_usd=0.0030
)
```

#### get_session_stats

获取会话统计

```python
def get_session_stats() -> Dict[str, Any]
```

**返回**：

```python
{
    "total_input_tokens": 1000,
    "total_output_tokens": 2000,
    "total_tokens": 3000,
    "total_cost_usd": 0.0330,
    "by_agent": {
        "agent_researcher": {
            "input": 500,
            "output": 1000,
            "total": 1500,
            "cost": 0.0165
        },
        "agent_coder": {
            "input": 500,
            "output": 1000,
            "total": 1500,
            "cost": 0.0165
        }
    }
}
```

**示例**：

```python
stats = token_tracker.get_session_stats()

print(f"总输入: {stats['total_input_tokens']:,} tokens")
print(f"总输出: {stats['total_output_tokens']:,} tokens")
print(f"总成本: ${stats['total_cost_usd']:.4f}")

for agent_id, agent_stats in stats['by_agent'].items():
    print(f"{agent_id}: {agent_stats['total']} tokens (${agent_stats['cost']:.4f})")
```

#### reset_session

重置会话统计

```python
def reset_session()
```

**示例**：

```python
# 创建新会话时重置
token_tracker.reset_session()
```

---

## 数据模型

### Message

消息对象

```python
from src.core.models import Message

message = Message(
    role: str,              # "user" | "assistant" | "system"
    content: str,           # 消息内容
    agent_id: Optional[str] = None,  # Agent ID（assistant消息）
    timestamp: Optional[float] = None  # 时间戳
)
```

### AgentConfig

Agent配置对象

```python
from src.core.models import AgentConfig

agent = AgentConfig(
    agent_id: str,          # Agent唯一ID
    name: str,              # Agent名称
    role: str,              # 角色类型
    model_id: str,          # 模型ID
    provider: str,          # 提供商（anthropic/openai）
    system_prompt: str,     # 系统提示词
    temperature: float = 0.7,     # 温度参数
    max_tokens: int = 4096,       # 最大token数
    enabled: bool = True          # 是否启用
)
```

### AgentMessage

Agent响应消息

```python
from src.core.models import AgentMessage

response = AgentMessage(
    agent_id: str,          # Agent ID
    content: str,           # 响应内容
    role: str = "assistant",  # 角色
    token_usage: Optional[TokenUsage] = None,  # Token使用
    timestamp: Optional[float] = None  # 时间戳
)
```

### TokenUsage

Token使用统计

```python
from src.core.models import TokenUsage

usage = TokenUsage(
    input_tokens: int,      # 输入token数
    output_tokens: int,     # 输出token数
    total_tokens: int       # 总token数
)
```

---

## 完整示例

### 示例1: 基本使用

```python
import asyncio
from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager

async def main():
    # 初始化组件
    config_manager = ConfigManager()
    coordinator = ResponseCoordinator()
    executor = AgentExecutor(config_manager)
    session_manager = SessionManager(config_manager, coordinator, executor)
    
    # 创建会话
    session = session_manager.create_session("测试会话")
    
    # 处理用户输入
    responses = await session_manager.process_user_input("@researcher 你好")
    
    # 输出响应
    for response in responses:
        print(f"{response.agent_id}: {response.content}")
    
    # 保存会话
    session_manager.save_session()
    
    # 清理资源
    await executor.aclose()

asyncio.run(main())
```

### 示例2: Token统计

```python
# 获取会话统计
stats = session_manager.token_tracker.get_session_stats()

print(f"📊 Token统计")
print(f"输入: {stats['total_input_tokens']:,} tokens")
print(f"输出: {stats['total_output_tokens']:,} tokens")
print(f"总计: {stats['total_tokens']:,} tokens")
print(f"成本: ${stats['total_cost_usd']:.4f}")

# 按Agent查看
for agent_id, agent_stats in stats['by_agent'].items():
    print(f"  {agent_id}: {agent_stats['total']} tokens")
```

### 示例3: 状态监控

```python
# 获取所有Agent状态
statuses = session_manager.status_manager.get_all_statuses()

for agent_id, state in statuses.items():
    status_icon = {
        "idle": "⚪",
        "pending": "⏳",
        "running": "⚙️",
        "completed": "✅",
        "error": "❌"
    }[state.status.value]
    
    print(f"{status_icon} {agent_id}: {state.status.value}")
    print(f"   耗时: {state.elapsed_seconds:.1f}s")
    print(f"   Token: {state.total_tokens}")
    
    if state.error:
        print(f"   错误: {state.error}")
```

---

## 相关文档

- [快速开始](../user-guide/QUICKSTART.md)
- [配置指南](../user-guide/CONFIGURATION.md)
- [故障排除](../user-guide/TROUBLESHOOTING.md)
- [教程](../tutorials/FIRST_AGENT.md)

---

**版本**: v1.0  
**更新日期**: 2026-09-06
