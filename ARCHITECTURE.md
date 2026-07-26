# Agent Chat Hub - 系统架构文档

## 1. 架构概览

Agent Chat Hub 是一个多模型AI代理协作系统，支持多个AI代理并发处理用户请求。

### 1.1 核心设计原则

- **确定性路由**：基于配置的agent选择规则，行为可预测
- **并发协作**：多个agent可以同时处理同一个用户请求
- **消息驱动**：agent间通过消息总线异步通信
- **预算控制**：限制每轮对话的资源消耗

### 1.2 技术栈

| 层次 | 技术选型 | 说明 |
|------|---------|------|
| **TUI界面** | Textual | 终端用户界面框架 |
| **输出格式** | Rich | 富文本格式化和语法高亮 |
| **编排引擎** | LangGraph | AI工作流编排 |
| **LLM集成** | LangChain | 多模型统一接口 |
| **配置存储** | JSON | models.json, agents.json |
| **会话存储** | JSON | 本地文件系统 |
| **运行时** | Python 3.14+ | 现代Python特性支持 |

---

## 2. 系统分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    TUI Layer (界面层)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  ChatScreen  │  │  ModelScreen │  │ SessionScreen│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Core Layer (核心层)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │SessionManager│  │ Coordinator  │  │ ConfigManager│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Agent Layer (代理层)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │MessageBus    │  │AgentExecutor │  │LangGraphAgent│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Plugin Layer (插件层)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  HTTP API    │  │ WebSocket API│  │Custom Plugins│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 核心组件详解

### 3.1 ResponseCoordinator (响应协调器)

**职责**：实现多agent响应的6条控制规则

**核心规则**：

1. **Qualification Rule (资格判定)**
   - 只选择 `active=True` 的agents
   - 有`@mentions` → 仅选择被@的agents
   - 无`@mentions` → 仅选择coordinator角色
   
2. **Ordering Rule (排序规则)**
   - 优先级升序排序 (priority值越小越优先)
   - 相同优先级按agent_id字典序

3. **Deduplication Rule (去重规则)**
   - 基于 `(session_id, round_num, agent_id)` 三元组去重
   - 每轮对话中每个agent最多调用一次

4. **Cancellation Rule (取消规则)**
   - 用户取消后禁止新调用
   - 标记延迟输出为已取消

5. **Budget Rule (预算规则)**
   - 最大并发agents: 3
   - 每轮最大调用次数: 3
   - 最大tokens: 12,000
   - 超时时间: 120秒

6. **Stop Rule (停止规则)**
   - 6种停止条件：用户取消、预算超限、超时、达到最大调用次数、无可用agents、轮次完成
   - 禁止agent自动续轮

**代码位置**：`src/agents/coordinator.py`

**关键方法**：
- `select_agents()` - 整合所有规则，选择要调用的agents
- `qualify_agents()` - Rule 1: 资格判定和@mention路由
- `sort_agents()` - Rule 2: 排序
- `is_duplicate_call()` - Rule 3: 去重检查
- `check_budget()` - Rule 5: 预算检查
- `should_stop()` - Rule 6: 停止条件判断

---

### 3.2 MessageBus (消息总线)

**职责**：提供agent间异步消息传递能力

**架构设计**：

```
┌─────────────────────────────────────────────────┐
│              MessageBus                          │
│  ┌───────────────────────────────────────────┐  │
│  │     _queues: Dict[str, asyncio.Queue]    │  │
│  │     agent_id → Queue                      │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  _subscriptions: Dict[str, Set[str]]     │  │
│  │  message_type → agent_ids                │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  _message_history: List[AgentMessage]    │  │
│  │  (最多100条)                               │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**核心功能**：

1. **Agent注册**
   ```python
   register_agent(agent_id: str) -> None
   ```
   - 为agent创建独立的消息队列
   - 队列容量限制：1000条（防止内存溢出）

2. **消息发布**
   ```python
   publish(message: AgentMessage) -> None
   ```
   - 点对点消息：`message.to_agent_id` 指定接收者
   - 广播消息：发送给所有订阅该类型的agents

3. **消息订阅**
   ```python
   subscribe(agent_id: str, message_type: str) -> None
   ```
   - 订阅特定类型的消息
   - 支持多个agent订阅同一类型

4. **消息获取**
   ```python
   get_message(agent_id: str, timeout: float) -> Optional[AgentMessage]
   ```
   - 异步阻塞直到有消息或超时
   - 支持超时控制

**代码位置**：`src/agents/message_bus.py`

---

### 3.3 SessionManager (会话管理器)

**职责**：管理对话历史和会话状态

**核心功能**：

1. **会话生命周期管理**
   - 创建会话：生成唯一session_id
   - 加载会话：从本地文件恢复
   - 持久化：保存会话状态到JSON文件

2. **消息管理**
   - 添加用户/助手/系统消息
   - 维护完整对话历史
   - 支持@mention解析

3. **Agent协调**
   - 集成ResponseCoordinator进行agent选择
   - 通过AgentExecutor并发调用agents
   - 管理MessageBus注册

**工作流程**：

```
用户输入
   ↓
parse_mentions() → 提取@mentions
   ↓
coordinator.start_round() → 开始新轮次
   ↓
coordinator.select_agents() → 选择要调用的agents
   ↓
executor.execute_concurrent() → 并发执行agents
   ↓
收集结果 → 添加到对话历史
   ↓
持久化会话状态
```

**代码位置**：`src/agents/session.py`

---

### 3.4 AgentExecutor (代理执行器)

**职责**：执行agent调用和结果收集

**核心能力**：

1. **并发执行**
   ```python
   execute_concurrent(agents: List[AgentConfig], messages: List[Message])
   ```
   - 使用 `asyncio.gather()` 并发调用多个agents
   - 超时控制：每个agent 30秒超时
   - 错误隔离：单个agent失败不影响其他agents

2. **LangGraph集成**
   - 通过LangGraphAgent调用LLM
   - 支持流式输出
   - 自动token计数

3. **结果聚合**
   - 收集所有agent的响应
   - 统计执行时间和token使用
   - 错误处理和日志记录

**代码位置**：`src/agents/executor.py`

---

### 3.5 ConfigManager (配置管理器)

**职责**：加载和管理系统配置

**配置文件**：

1. **models.json** - 模型配置
   ```json
   {
     "model_id": "gpt-4",
     "provider": "openai",
     "display_name": "GPT-4",
     "base_url": "https://api.openai.com/v1",
     "api_key_name": "OPENAI_API_KEY"
   }
   ```

2. **agents.json** - Agent配置
   ```json
   {
     "agent_id": "coordinator",
     "name": "总管",
     "role": "协调各个agent的响应",
     "role_type": "coordinator",
     "model_id": "gpt-4",
     "priority": 1,
     "active": true
   }
   ```

**代码位置**：`src/core/config.py`

---

## 4. 数据流和控制流

### 4.1 用户消息处理流程

```
┌─────────────────────────────────────────────────────┐
│ 1. 用户在TUI输入消息                                  │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. parse_mentions() 解析@mentions                    │
│    例：@gpt4 @claude → mentions=["gpt4", "claude"]  │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. SessionManager.add_message(role="user", ...)     │
│    添加用户消息到对话历史                              │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 4. coordinator.start_round(session_id, round_num)   │
│    初始化新轮次状态                                    │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 5. coordinator.select_agents(agents, mentions)      │
│    - Rule 1: 资格判定（@mention过滤）                 │
│    - Rule 2: 排序（priority + agent_id）             │
│    - Rule 3: 去重过滤                                 │
│    - Rule 5: 预算检查                                 │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 6. executor.execute_concurrent(selected_agents)     │
│    并发调用所有选中的agents                            │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 7. 收集结果并显示在TUI                                 │
│    SessionManager.add_message(role="assistant", ...)│
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 8. 持久化会话状态到 ~/.agent-chat-hub/sessions/      │
└─────────────────────────────────────────────────────┘
```

### 4.2 @Mention路由机制

**规则**：

- **无@mentions**：仅coordinator角色响应
  ```
  用户：你好
  → 仅 coordinator agent 响应
  ```

- **有@mentions**：仅被@的agents响应
  ```
  用户：@gpt4 @claude 请比较两个方案
  → gpt4 和 claude agents 响应
  → coordinator 不响应
  ```

- **部分匹配**：支持简写
  ```
  用户：@gpt 总结一下
  → 匹配所有包含"gpt"的agent（不区分大小写）
  ```

**实现位置**：
- 解析：`src/core/mention_parser.py::parse_mentions()`
- 路由：`src/agents/coordinator.py::qualify_agents()`

---

## 5. 插件系统架构

### 5.1 插件接口

所有插件必须实现 `PluginInterface`：

```python
class PluginInterface:
    def initialize(self, app: "AgentChatHub") -> None
    def shutdown(self) -> None
```

### 5.2 内置插件

| 插件 | 功能 | 端口 |
|------|------|------|
| **HTTP API** | REST API接口 | 8000 |
| **WebSocket API** | 实时双向通信 | 8001 |

### 5.3 插件加载流程

```
1. 扫描 src/plugins/ 目录
   ↓
2. 动态导入插件模块
   ↓
3. 调用 plugin.initialize(app)
   ↓
4. 注册插件到app.plugins列表
   ↓
5. 启动插件服务（如HTTP服务器）
```

**代码位置**：`src/plugins/`

---

## 6. TUI架构设计

### 6.1 Screen结构

```
App (ChatHubApp)
 ├─ ChatScreen (默认界面)
 │   ├─ MessageList (消息列表)
 │   ├─ InputArea (输入框)
 │   └─ StatusBar (状态栏)
 ├─ ModelScreen (模型管理)
 │   ├─ ModelList
 │   └─ ModelEditor
 ├─ SessionScreen (会话历史)
 │   └─ SessionList
 └─ AgentScreen (Agent管理)
     ├─ AgentList
     └─ AgentEditor
```

### 6.2 快捷键系统

| 快捷键 | 功能 | 作用域 |
|--------|------|--------|
| `Ctrl+N` | 新建会话 | 全局 |
| `Ctrl+S` | 会话列表 | 全局 |
| `Ctrl+M` | 模型管理 | 全局 |
| `Ctrl+A` | Agent管理 | 全局 |
| `Ctrl+C` | 复制消息 | ChatScreen |
| `Ctrl+Q` | 退出 | 全局 |
| `Esc` | 返回/取消 | 全局 |

**代码位置**：`src/tui/`

---

## 7. 性能优化

### 7.1 并发策略

1. **Agent并发调用**
   - 使用 `asyncio.gather()` 同时调用多个agents
   - 每个agent独立超时控制（30秒）
   - 失败隔离：单agent失败不影响其他

2. **消息队列容量限制**
   - 每个agent队列最多1000条消息
   - 防止内存无限增长

3. **会话历史限制**
   - MessageBus历史最多100条
   - 定期清理旧消息

### 7.2 性能基准

根据 `benchmarks/benchmark_phase2.py` 测试结果：

| 指标 | 性能 | 目标 |
|------|------|------|
| 会话创建 | 0.07ms/次 | <10ms |
| 吞吐量 | 14,439次/秒 | >100次/秒 |
| MessageBus延迟 | <1ms | <5ms |

**结论**：当前性能远超目标，无需进一步优化。

---

## 8. 安全考虑

### 8.1 API密钥管理

- 通过环境变量传递：`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- 配置文件中不存储明文密钥
- 使用 `api_key_name` 字段引用环境变量

### 8.2 输入验证

- @mention解析限制：最多10个mentions
- 消息长度限制：最大10MB
- 配置文件JSON schema验证

### 8.3 资源限制

- 预算规则（Budget Rule）防止资源耗尽
- 队列容量限制防止内存溢出
- 超时机制防止长时间阻塞

---

## 9. 扩展性设计

### 9.1 新增Agent

1. 在 `agents.json` 添加配置
2. 设置 `role_type`, `priority`, `model_id`
3. 重启应用即可生效

### 9.2 新增模型

1. 在 `models.json` 添加配置
2. 设置环境变量（API密钥）
3. 在agents配置中引用 `model_id`

### 9.3 开发插件

1. 在 `src/plugins/` 创建插件目录
2. 实现 `PluginInterface`
3. 自动加载和初始化

---

## 10. 架构决策记录 (ADR)

### ADR-0001: 响应协调器6条规则

**背景**：多agent并发响应需要明确的控制规则

**决策**：实现6条规则（Qualification, Ordering, Deduplication, Cancellation, Budget, Stop）

**理由**：
- 确定性路由，行为可预测
- 防止重复调用和资源浪费
- 用户可控（@mention机制）

**影响**：所有agent调用必须通过ResponseCoordinator

---

### ADR-0002: MessageBus异步设计

**背景**：Agent间需要解耦通信

**决策**：使用asyncio.Queue实现异步消息总线

**理由**：
- 解耦：agents无需直接调用彼此
- 异步：不阻塞主流程
- 可扩展：支持订阅/发布模式

**影响**：所有agent通信通过MessageBus

---

### ADR-0003: JSON配置存储

**背景**：需要持久化配置和会话

**决策**：使用JSON文件存储

**理由**：
- 简单：无需数据库依赖
- 可读：人类可编辑
- 轻量：适合桌面应用

**影响**：大规模部署需迁移到数据库

---

## 11. 未来架构演进

### 11.1 短期优化（1-3个月）

- [ ] 实现agent间协作工作流（通过MessageBus）
- [ ] 添加更多内置插件（文件管理、代码执行）
- [ ] 增强TUI交互体验（流式输出、实时状态）

### 11.2 中期演进（3-6个月）

- [ ] 支持分布式部署（多机协作）
- [ ] 添加Web界面（React前端）
- [ ] 实现agent权限管理系统
- [ ] 集成向量数据库（RAG能力）

### 11.3 长期愿景（6-12个月）

- [ ] Agent自主学习和优化
- [ ] 多租户SaaS部署
- [ ] 企业级安全审计
- [ ] AI工作流市场（插件生态）

---

## 附录

### A. 关键文件索引

| 文件 | 说明 |
|------|------|
| `src/agents/coordinator.py` | 响应协调器（6条规则） |
| `src/agents/message_bus.py` | 消息总线 |
| `src/agents/session.py` | 会话管理器 |
| `src/agents/executor.py` | Agent执行器 |
| `src/core/config.py` | 配置管理器 |
| `src/core/mention_parser.py` | @mention解析 |
| `src/tui/` | TUI界面实现 |
| `src/plugins/` | 插件系统 |
| `benchmarks/` | 性能基准测试 |

### B. 外部依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| `textual` | >=0.40.0 | TUI框架 |
| `rich` | >=13.0.0 | 富文本格式化 |
| `langchain` | >=0.1.0 | LLM集成 |
| `langgraph` | >=0.1.0 | 工作流编排 |
| `structlog` | >=23.0.0 | 结构化日志 |
| `pydantic` | >=2.0.0 | 数据验证 |

### C. 术语表

- **Agent**: AI代理，封装了特定LLM模型和角色定义
- **Coordinator**: 总管角色，负责协调多个agents的响应
- **Round**: 轮次，一次完整的用户请求和所有agent响应的周期
- **MessageBus**: 消息总线，agent间异步通信的基础设施
- **Session**: 会话，一系列相关的对话消息和状态
- **@Mention**: 用户通过@符号指定要调用的agents

---

**文档版本**：v1.0  
**最后更新**：2026-07-26  
**维护者**：Agent Chat Hub Team
