# Agent Chat Hub

多模型Agent聊天系统 - 个人用户与不同AI模型建立的Agent进行沟通和交互。

## 项目概述

本项目旨在构建一个统一的平台，允许用户与多个AI模型（Claude、Codex、Gemini等）建立的Agent进行实时对话和协作。

## 核心特性

- 🤖 **多模型支持**：集成Claude、Codex、Gemini等多个AI模型
- 💬 **实时聊天**：支持流式响应和实时交互
- 🔄 **Agent协作**：多个Agent可以协同工作
- 🛡️ **消息验证**：自动处理和修复Agent输出格式问题
- 📊 **会话管理**：完整的会话生命周期管理

## 项目结构

```
agent-chat-hub/
├── docs/          # 文档
├── src/           # 源代码
│   ├── core/     # 核心功能（MessageValidator, SessionManager等）
│   ├── agents/   # Agent实现
│   └── ui/       # 用户界面
├── references/    # 参考项目集合
├── config/        # 配置文件
├── tests/         # 测试
└── README.md
```

## 技术栈

- **语言**：Python 3.14+
- **UI框架**：Textual (TUI终端界面) - 基于ADR-0001决策
- **数据验证**：Pydantic v2
- **日志**：structlog
- **API密钥管理**：keyring (系统密钥环)
- **HTTP客户端**：httpx

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 初始化配置

首次使用需要配置模型和agent：

```bash
python init_config.py
```

脚本会引导你：
- 选择模型provider（Anthropic或OpenAI）
- 输入API密钥（安全存储到系统密钥环）
- 创建第一个agent

### 3. 启动应用

```bash
python main.py
```

### 4. 使用界面

- 在底部输入框输入消息，按回车发送
- `Ctrl+C`: 退出应用
- `Ctrl+N`: 创建新会话

## 配置文件

- 配置目录: `~/.agent-chat-hub/`
- 模型配置: `~/.agent-chat-hub/models.json`
- Agent配置: `~/.agent-chat-hub/agents.json`
- 会话历史: `~/.agent-chat-hub/sessions/`
- API密钥: 系统密钥环（不保存到文件）

## 参考项目

本项目参考和集成了以下优秀项目（放置在`references/`目录）：

- MassGen：多Agent协调系统
- 其他相关项目...

## 开发状态

### Phase 1 - MVP基础设施 ✅ (2026-07-17)

- [x] **ADR-0001**: TUI替代React架构决策
- [x] **数据模型**: ModelConfig, AgentConfig, Message, SessionConfig
- [x] **配置管理**: 模型/agent配置，API密钥安全存储（keyring）
- [x] **响应协调器**: 6条响应控制规则 + 18个单元测试全部通过
- [x] **Agent执行器**: Anthropic/OpenAI API调用支持
- [x] **会话管理器**: 对话历史管理，会话持久化
- [x] **TUI界面**: 基于Textual的终端界面
- [x] **单agent对话PoC**: 完整的对话流程验证

**响应协调规则（6条 - 基于ADR-0001）：**
1. Qualification: 确定性路由，基于配置
2. Ordering: 优先级升序 + agent_id字典序
3. Deduplication: (session, round, agent)三元组去重
4. Cancellation: 取消后禁止新调用
5. Budget: MVP限额（3 agents, 3 calls, 12k tokens, 120s）
6. Stop: 6种停止条件，禁止agent自动续轮

**MVP预算限制：**
- 最大并发agents: 3
- 每轮最大调用次数: 3
- 最大token数: 12,000
- 超时时间: 120秒

### Phase 2 - 多agent协作 ✅ (2026-07-20)

- [x] **Agent执行器异步化**: 支持并发API调用
- [x] **高级TUI组件**: Agent面板、状态栏、快捷键系统
- [x] **Agent间消息传递**: MessageBus消息总线实现
- [x] **配置管理界面**: 查看和添加模型配置
- [x] **集成测试**: 13个Phase 2集成测试，100%通过率
- [x] **性能基准测试**: 并发性能基准测试脚本

**Phase 2.1强化（2026-07-20）：**
- 新增7个并发响应测试（预算限制、去重、取消、排序）
- 修复ResponseCoordinator排序一致性问题
- 全部13个Phase 2集成测试达到100%通过率

### Phase 3 - 插件系统 ✅ (2026-07-18)

- [x] **插件系统架构**: Ruflo风格插件设计
- [x] **插件加载机制**: 插件注册表和加载器
- [x] **插件API**: Agent/Config/Message/TUI API
- [x] **示例插件**: Hello插件实现
- [x] **插件管理界面**: TUI插件管理界面

## 测试

运行测试：

```bash
pytest tests/ -v
```

当前测试覆盖：
- **单元测试**: 45个测试，100%通过 ✅
  - 响应协调器: 18个测试
  - MessageBus: 9个测试
  - 其他核心模块: 18个测试
- **集成测试**: 13个Phase 2集成测试，100%通过 ✅
- **总计**: 58个测试，100%通过率

## 架构文档

- **ADR-0001**: [采用TUI替代React Web界面](docs/adr/0001-采用TUI替代React-Web界面.md)
- **实施计划**: [Agent Chat Hub MVP实施计划](.omc/plans/Agent-Chat-Hub-MVP-实施计划.md)
- **HTTP/WebSocket消费者清单**: [消费者清单](docs/architecture/HTTP-WebSocket-消费者清单.md)

## License

待定

## 作者

caohui
