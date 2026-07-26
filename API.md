# Agent Chat Hub - API参考文档

## 1. API概述

Agent Chat Hub 提供多种API接口供扩展和集成：

| API类型 | 说明 | 使用场景 |
|---------|------|---------|
| **插件API** | 内部插件开发接口 | 开发自定义插件 |
| **HTTP API** | RESTful HTTP接口 | 外部系统集成 |
| **WebSocket API** | 实时双向通信 | 实时消息推送 |
| **Python API** | 核心Python模块 | 嵌入式使用 |

---

## 2. 插件API

### 2.1 插件接口

所有插件必须实现 `PluginInterface`：

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.tui.app import ChatHubApp

class PluginInterface:
    """插件接口基类"""
    
    def initialize(self, app: "ChatHubApp") -> None:
        """插件初始化
        
        Args:
            app: 应用实例，提供对系统组件的访问
        """
        raise NotImplementedError
    
    def shutdown(self) -> None:
        """插件关闭"""
        pass
```

### 2.2 MessageAPI - 消息API

订阅和发布消息。

**初始化**：

```python
from src.plugins.api.message_api import MessageAPI

message_api = MessageAPI(
    plugin_id="my-plugin",
    message_bus=app.message_bus
)
```

**方法**：

#### `subscribe(message_type: str, callback: Callable) -> None`

订阅特定类型的消息。

```python
def on_user_message(message: AgentMessage):
    print(f"收到消息: {message.content}")

message_api.subscribe("user_message", on_user_message)
```

**参数**：
- `message_type` (str): 消息类型
- `callback` (Callable): 回调函数，接收 `AgentMessage` 参数

#### `unsubscribe(message_type: str, callback: Optional[Callable] = None) -> None`

取消订阅。

```python
message_api.unsubscribe("user_message", on_user_message)
```

#### `publish(message: AgentMessage) -> None`

发布消息。

```python
from src.core.models import AgentMessage

message = AgentMessage(
    from_agent_id="my-plugin",
    to_agent_id="coordinator",
    message_type="task",
    content="执行任务"
)
message_api.publish(message)
```

### 2.3 ConfigAPI - 配置API

读取和管理系统配置。

**初始化**：

```python
from src.plugins.api.config_api import ConfigAPI

config_api = ConfigAPI(config_manager=app.config_manager)
```

**方法**：

#### `get_models() -> List[ModelConfig]`

获取所有模型配置。

```python
models = config_api.get_models()
for model in models:
    print(f"{model.model_id}: {model.display_name}")
```

**返回**：`List[ModelConfig]` - 模型配置列表

#### `get_model(model_id: str) -> Optional[ModelConfig]`

获取指定模型配置。

```python
model = config_api.get_model("gpt-4")
if model:
    print(f"Provider: {model.provider}")
```

#### `get_agents(active_only: bool = False) -> List[AgentConfig]`

获取所有Agent配置。

```python
agents = config_api.get_agents(active_only=True)
print(f"活跃Agents: {len(agents)}")
```

**参数**：
- `active_only` (bool): 是否只返回活跃的agents，默认False

#### `get_agent(agent_id: str) -> Optional[AgentConfig]`

获取指定Agent配置。

```python
agent = config_api.get_agent("coordinator")
if agent:
    print(f"Role: {agent.role}")
```

### 2.4 AgentAPI - Agent执行API

执行Agent调用。

**初始化**：

```python
from src.plugins.api.agent_api import AgentAPI

agent_api = AgentAPI(
    executor=app.executor,
    config_manager=app.config_manager
)
```

**方法**：

#### `execute_agent(agent_id: str, messages: List[Message]) -> str`

执行单个Agent。

```python
from src.core.models import Message

messages = [
    Message(role="user", content="你好")
]

response = await agent_api.execute_agent("gpt-4", messages)
print(response)
```

**参数**：
- `agent_id` (str): Agent ID
- `messages` (List[Message]): 对话历史

**返回**：`str` - Agent响应文本

#### `execute_concurrent(agent_ids: List[str], messages: List[Message]) -> Dict[str, str]`

并发执行多个Agents。

```python
agent_ids = ["gpt-4", "claude"]
responses = await agent_api.execute_concurrent(agent_ids, messages)

for agent_id, response in responses.items():
    print(f"{agent_id}: {response}")
```

**返回**：`Dict[str, str]` - Agent ID到响应的映射

---

## 3. HTTP API

### 3.1 基础信息

**Base URL**: `http://localhost:8000`

**认证**：暂不需要（本地部署）

**Content-Type**: `application/json`

### 3.2 健康检查

#### `GET /health`

检查服务健康状态。

**请求**：

```bash
curl http://localhost:8000/health
```

**响应**：

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 3600,
  "active_sessions": 5
}
```

### 3.3 会话管理

#### `POST /sessions`

创建新会话。

**请求**：

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "新对话"}'
```

**请求体**：

```json
{
  "title": "新对话"
}
```

**响应**：

```json
{
  "session_id": "session_1721998800000",
  "title": "新对话",
  "created_at": 1721998800.0
}
```

#### `GET /sessions`

获取所有会话列表。

**请求**：

```bash
curl http://localhost:8000/sessions
```

**响应**：

```json
{
  "sessions": [
    {
      "session_id": "session_1721998800000",
      "title": "新对话",
      "created_at": 1721998800.0,
      "message_count": 10
    }
  ]
}
```

#### `GET /sessions/{session_id}`

获取指定会话详情。

**请求**：

```bash
curl http://localhost:8000/sessions/session_1721998800000
```

**响应**：

```json
{
  "session_id": "session_1721998800000",
  "title": "新对话",
  "created_at": 1721998800.0,
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "timestamp": 1721998801.0
    },
    {
      "role": "assistant",
      "content": "你好！",
      "agent_id": "coordinator",
      "timestamp": 1721998802.0
    }
  ]
}
```

#### `DELETE /sessions/{session_id}`

删除会话。

**请求**：

```bash
curl -X DELETE http://localhost:8000/sessions/session_1721998800000
```

**响应**：

```json
{
  "success": true,
  "message": "会话已删除"
}
```

### 3.4 消息发送

#### `POST /sessions/{session_id}/messages`

向会话发送消息。

**请求**：

```bash
curl -X POST http://localhost:8000/sessions/session_123/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "@gpt4 介绍一下Python",
    "stream": false
  }'
```

**请求体**：

```json
{
  "content": "消息内容",
  "stream": false
}
```

**参数**：
- `content` (string): 消息内容，支持@mention
- `stream` (boolean): 是否流式返回，默认false

**响应**（非流式）：

```json
{
  "responses": [
    {
      "agent_id": "gpt4",
      "content": "Python是一门高级编程语言...",
      "timestamp": 1721998803.0,
      "tokens_used": 150
    }
  ]
}
```

**响应**（流式）：

```
data: {"agent_id": "gpt4", "delta": "Python"}
data: {"agent_id": "gpt4", "delta": "是"}
data: {"agent_id": "gpt4", "delta": "一门"}
...
data: {"agent_id": "gpt4", "done": true, "tokens_used": 150}
```

### 3.5 配置管理

#### `GET /config/models`

获取模型配置列表。

**请求**：

```bash
curl http://localhost:8000/config/models
```

**响应**：

```json
{
  "models": [
    {
      "model_id": "gpt-4",
      "provider": "openai",
      "display_name": "GPT-4",
      "base_url": "https://api.openai.com/v1"
    }
  ]
}
```

#### `GET /config/agents`

获取Agent配置列表。

**请求**：

```bash
curl http://localhost:8000/config/agents
```

**响应**：

```json
{
  "agents": [
    {
      "agent_id": "coordinator",
      "name": "总管",
      "role": "协调多个agents的响应",
      "role_type": "coordinator",
      "model_id": "gpt-4",
      "priority": 1,
      "active": true
    }
  ]
}
```

### 3.6 错误响应

所有API错误返回统一格式：

```json
{
  "error": "错误类型",
  "message": "错误详细说明",
  "code": 400
}
```

**常见错误码**：

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

---

## 4. WebSocket API

### 4.1 连接

**端点**: `ws://localhost:8001/ws`

**连接示例**：

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onopen = () => {
    console.log('已连接');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

ws.onerror = (error) => {
    console.error('错误:', error);
};

ws.onclose = () => {
    console.log('连接已关闭');
};
```

### 4.2 消息格式

**客户端发送**：

```json
{
  "type": "message",
  "session_id": "session_123",
  "content": "@gpt4 你好"
}
```

**服务端响应**：

```json
{
  "type": "response",
  "agent_id": "gpt4",
  "content": "你好！",
  "timestamp": 1721998804.0
}
```

**事件通知**：

```json
{
  "type": "event",
  "event_name": "agent_started",
  "data": {
    "agent_id": "gpt4",
    "session_id": "session_123"
  }
}
```

### 4.3 消息类型

| 类型 | 说明 | 方向 |
|------|------|------|
| `message` | 用户消息 | 客户端→服务端 |
| `response` | Agent响应 | 服务端→客户端 |
| `event` | 系统事件 | 服务端→客户端 |
| `error` | 错误消息 | 服务端→客户端 |
| `ping` | 心跳检测 | 双向 |

---

## 5. Python API

### 5.1 核心模块

直接使用Python模块进行嵌入式集成。

#### 创建会话管理器

```python
from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager

# 初始化组件
config_manager = ConfigManager()
coordinator = ResponseCoordinator()
executor = AgentExecutor(config_manager)

# 创建会话管理器
session_manager = SessionManager(
    config_manager=config_manager,
    coordinator=coordinator,
    executor=executor
)
```

#### 创建会话

```python
session = session_manager.create_session("测试会话")
print(f"会话ID: {session.session_id}")
```

#### 发送消息

```python
# 添加用户消息
session_manager.add_message("user", "@gpt4 你好")

# 处理消息并获取响应
responses = await session_manager.process_user_message()

for response in responses:
    print(f"{response.agent_id}: {response.content}")
```

### 5.2 使用Coordinator

```python
from src.agents.coordinator import ResponseCoordinator, BudgetLimits
from src.core.models import AgentConfig

# 创建协调器
budget = BudgetLimits(
    max_agents=5,
    max_calls_per_round=10,
    max_tokens=20000
)
coordinator = ResponseCoordinator(budget)

# 开始新轮次
coordinator.start_round("session_123", round_num=1)

# 选择agents
agents = config_manager.list_agents(active_only=True)
mentions = ["gpt4", "claude"]
selected, stop_reason = coordinator.select_agents(agents, mentions=mentions)

print(f"选中的agents: {[a.agent_id for a in selected]}")

# 记录调用
for agent in selected:
    coordinator.record_call(agent.agent_id, tokens_used=100)

# 检查预算
budget_reason = coordinator.check_budget()
if budget_reason:
    print(f"预算超限: {budget_reason}")
```

### 5.3 使用MessageBus

```python
from src.agents.message_bus import MessageBus
from src.core.models import AgentMessage

# 创建消息总线
message_bus = MessageBus()

# 注册agents
message_bus.register_agent("agent_a")
message_bus.register_agent("agent_b")

# 订阅消息
message_bus.subscribe("agent_a", "task")
message_bus.subscribe("agent_b", "task")

# 发布消息
message = AgentMessage(
    from_agent_id="system",
    to_agent_id="agent_a",
    message_type="task",
    content="执行任务"
)
await message_bus.publish(message)

# 获取消息
received = await message_bus.get_message("agent_a", timeout=5.0)
if received:
    print(f"收到消息: {received.content}")
```

---

## 6. 数据模型

### 6.1 核心模型

#### Message

对话消息。

```python
@dataclass
class Message:
    role: str                    # "user" | "assistant" | "system"
    content: str                 # 消息内容
    timestamp: float             # 时间戳
    agent_id: Optional[str]      # Agent ID（assistant消息）
    metadata: Dict[str, Any]     # 元数据
```

#### AgentMessage

Agent间消息。

```python
@dataclass
class AgentMessage:
    from_agent_id: str           # 发送者ID
    to_agent_id: Optional[str]   # 接收者ID（None=广播）
    message_type: str            # 消息类型
    content: Any                 # 消息内容
    timestamp: float             # 时间戳
    metadata: Dict[str, Any]     # 元数据
```

#### AgentConfig

Agent配置。

```python
@dataclass
class AgentConfig:
    agent_id: str                # Agent唯一ID
    name: str                    # 显示名称
    role: str                    # 角色描述
    role_type: str               # 角色类型（coordinator/specialist）
    model_id: str                # 使用的模型ID
    priority: int                # 优先级（数值越小越优先）
    active: bool                 # 是否激活
    system_prompt: Optional[str] # 系统提示词
```

#### ModelConfig

模型配置。

```python
@dataclass
class ModelConfig:
    model_id: str                # 模型唯一ID
    provider: str                # 提供商（openai/anthropic）
    display_name: str            # 显示名称
    base_url: str                # API基础URL
    api_key_name: str            # API密钥环境变量名
```

#### SessionConfig

会话配置。

```python
@dataclass
class SessionConfig:
    session_id: str              # 会话唯一ID
    title: str                   # 会话标题
    created_at: float            # 创建时间
    updated_at: float            # 更新时间
    messages: List[Message]      # 消息列表
```

---

## 7. 插件开发示例

### 7.1 简单插件

```python
# plugins/hello_plugin.py
from src.plugins.base import PluginInterface
from src.core.models import AgentMessage

class HelloPlugin(PluginInterface):
    """示例插件：监听用户消息并响应"""
    
    def initialize(self, app):
        self.app = app
        self.message_api = app.get_message_api("hello-plugin")
        
        # 订阅用户消息
        self.message_api.subscribe("user_message", self.on_user_message)
        
        print("HelloPlugin initialized")
    
    def on_user_message(self, message: AgentMessage):
        """处理用户消息"""
        if "hello" in message.content.lower():
            # 发布响应
            response = AgentMessage(
                from_agent_id="hello-plugin",
                to_agent_id=None,
                message_type="plugin_response",
                content="Hello from plugin!"
            )
            self.message_api.publish(response)
    
    def shutdown(self):
        print("HelloPlugin shutdown")
```

### 7.2 HTTP插件

```python
# plugins/http_plugin.py
from fastapi import FastAPI
from src.plugins.base import PluginInterface
import uvicorn
import threading

class HTTPPlugin(PluginInterface):
    """HTTP API插件"""
    
    def initialize(self, app):
        self.app = app
        self.fastapi_app = FastAPI()
        
        # 定义路由
        @self.fastapi_app.get("/status")
        def get_status():
            return {
                "status": "running",
                "sessions": len(app.session_manager.sessions)
            }
        
        # 启动服务器
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()
    
    def _run_server(self):
        uvicorn.run(self.fastapi_app, host="0.0.0.0", port=8000)
    
    def shutdown(self):
        # 关闭服务器
        pass
```

---

## 8. API认证（未来支持）

### 8.1 API Key认证

```bash
curl http://localhost:8000/sessions \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 8.2 JWT认证

```bash
curl http://localhost:8000/sessions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 9. API速率限制

**当前版本**：无速率限制（本地部署）

**未来支持**：
- 每IP限制：100请求/分钟
- 每用户限制：1000请求/小时

---

## 10. API版本控制

**当前版本**: v1

**版本策略**：
- URL前缀：`/api/v1/...`
- 向后兼容：保留旧版本至少6个月

---

## 11. 参考资源

- [ARCHITECTURE.md](ARCHITECTURE.md) - 系统架构
- [DEVELOPMENT.md](DEVELOPMENT.md) - 开发指南
- [插件开发示例](src/plugins/examples/) - 示例代码

---

**文档版本**：v1.0  
**最后更新**：2026-07-26  
**维护者**：Agent Chat Hub Team
