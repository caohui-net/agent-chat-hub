# Agent Chat Hub

多模型Agent聊天系统 - 支持Claude、OpenAI、Gemini等多个AI模型的统一对话平台

---

## 🎯 项目概述

Agent Chat Hub是一个强大的多模型AI Agent管理平台，允许用户与多个AI模型建立的Agent进行实时对话和协作。

### 核心特性

- 🤖 **多模型支持** - 集成Anthropic Claude、OpenAI GPT、Google Gemini
- 💬 **实时对话** - Textual TUI界面，支持流式响应
- 🔄 **Agent协作** - @mention机制，支持多Agent并发协作
- 📊 **状态追踪** - 实时显示Agent状态、Token使用和成本
- 🛡️ **智能重试** - 自动处理网络错误和API限流
- 🔒 **安全存储** - API密钥安全存储在系统密钥环
- 📁 **文件上传** - 完整文件浏览器，支持文件预览和管理

---

## 🚀 5分钟快速开始

### 前置要求

- Python 3.10+
- API密钥（Anthropic Claude 或 OpenAI）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/agent-chat-hub.git
cd agent-chat-hub

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -e .

# 4. 配置API密钥
python init_config.py

# 5. 启动应用
./start.sh
```

**详细指南**: [docs/user-guide/QUICKSTART.md](docs/user-guide/QUICKSTART.md)

---

## 📖 文档

### 用户指南

- [快速开始](docs/user-guide/QUICKSTART.md) - 5分钟上手指南
- [配置指南](docs/user-guide/CONFIGURATION.md) - 完整配置说明
- [故障排除](docs/user-guide/TROUBLESHOOTING.md) - 常见问题解决
- [文件上传功能](QUICK_START.md) - 文件浏览器使用指南 🆕

### 开发文档

- [API参考](docs/api-reference/API.md) - 完整API文档
- [架构设计](docs/architecture/) - 系统架构和设计文档
- [教程](docs/tutorials/FIRST_AGENT.md) - 创建你的第一个Agent

### 功能文档

- [文件上传完整说明](FILE_UPLOAD_COMPLETE.md) - 文件浏览器详细功能 🆕
- [UI改进说明](UI_IMPROVEMENTS.md) - 最新UI改进 🆕
- [测试清单](TESTING_CHECKLIST.md) - 功能测试指南 🆕

### ADR文档

- [ADR-0001](docs/adr/0001-采用TUI替代React-Web界面.md) - 采用TUI替代React Web界面

---

## 💻 项目结构

```
agent-chat-hub/
├── docs/                       # 📚 文档
│   ├── user-guide/            # 用户指南
│   ├── api-reference/         # API文档
│   ├── architecture/          # 架构文档
│   ├── tutorials/             # 教程
│   └── adr/                   # 架构决策记录
├── src/                        # 💻 源代码
│   ├── core/                  # 核心功能
│   │   ├── config.py         # 配置管理
│   │   ├── models.py         # 数据模型
│   │   ├── agent_status.py   # 状态管理
│   │   ├── token_tracker.py  # Token追踪
│   │   └── retry_policy.py   # 重试策略
│   ├── agents/                # Agent系统
│   │   ├── executor.py       # Agent执行器
│   │   ├── session.py        # 会话管理
│   │   ├── coordinator.py    # 响应协调
│   │   └── message_bus.py    # 消息总线
│   └── tui/                   # TUI界面
│       ├── app.py            # 主应用
│       └── agent_status_panel.py  # 状态面板
├── tests/                      # 🧪 测试
├── config/                     # ⚙️ 配置文件
├── main.py                     # 🎯 入口文件
└── README.md                   # 📄 本文档
```

---

## 🎮 使用示例

### 基本对话

```
User: @researcher 分析这段Python代码
researcher: 让我来分析这段代码的结构和功能...
```

### @mention智能匹配

支持模糊匹配，无需输入完整Agent名称：

```
@res      → researcher  ✅
@write    → writer      ✅
@研究     → researcher  ✅
```

### 多Agent协作

```
User: @researcher @coder 帮我优化这个算法
researcher: 从算法角度分析...
coder: 这里是优化后的代码...
```

### 实时状态显示

```
📊 Agent执行状态
⚙️  researcher: running (1.2s...)
✅ coder: completed (0.8s) | 450 tokens

💰 本会话统计
├─ 输入: 1,000 tokens
├─ 输出: 2,000 tokens
├─ 总计: 3,000 tokens
└─ 成本: $0.0330
```

---

## 🔧 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| **语言** | Python | 3.10+ |
| **UI框架** | Textual | 最新 |
| **数据验证** | Pydantic | v2 |
| **HTTP客户端** | httpx | 最新 |
| **日志** | structlog | 最新 |
| **密钥管理** | keyring | 最新 |
| **异步** | asyncio | 标准库 |

---

## 🎯 开发路线图

### ✅ Phase 1 - MVP基础设施 (已完成)

- 核心数据模型（ModelConfig, AgentConfig, Message, SessionConfig）
- 配置管理（模型/Agent配置，API密钥安全存储）
- 响应协调器（6条响应控制规则）
- Agent执行器（Anthropic/OpenAI API支持）
- 会话管理器（对话历史管理）
- TUI界面（基于Textual）
- 单Agent对话PoC

### ✅ Phase 2 - 多Agent协作 (已完成)

- Agent执行器异步化（并发API调用）
- 高级TUI组件（Agent面板、状态栏）
- Agent间消息传递（MessageBus）
- 配置管理界面
- 集成测试（13个测试，100%通过）
- 性能基准测试

### ✅ Phase 3 - 插件系统 (已完成)

- 插件系统架构（Ruflo风格设计）
- 插件加载机制
- 插件API（Agent/Config/Message/TUI）
- 示例插件实现
- 插件管理界面

### ✅ Phase 3.5 - 增强功能 (2026-09-05完成)

- ✅ Agent上下文隔离 - 每个Agent独立上下文
- ✅ 实时状态追踪 - IDLE/PENDING/RUNNING/COMPLETED/ERROR
- ✅ Token追踪与成本计算 - 实时显示Token使用和成本
- ✅ 智能重试策略 - 自动处理网络错误（指数退避）
- ✅ @mention智能匹配 - 支持模糊匹配（部分匹配、不区分大小写）

### 🔄 Phase 4 - 未来规划

- [ ] Agent工具调用（函数调用）
- [ ] 流式响应显示
- [ ] 会话搜索和导出
- [ ] Agent模板市场
- [ ] Web界面（可选）

---

## 🧪 测试

### 运行测试

```bash
# 所有测试
pytest tests/ -v

# 单元测试
pytest tests/test_coordinator.py -v

# 集成测试
python test_integration.py

# 功能验证
python test_verification.py
```

### 测试覆盖率

- **单元测试**: 45个测试，100%通过 ✅
  - 响应协调器: 18个测试
  - MessageBus: 9个测试
  - 其他核心模块: 18个测试
- **增强功能测试**: 10个测试，100%通过 ✅
  - 上下文隔离: 2个测试
  - 状态追踪: 2个测试
  - Token追踪: 2个测试
  - 重试策略: 2个测试
  - @mention匹配: 2个测试
- **集成测试**: 13个Phase 2测试，100%通过 ✅
- **总计**: 68个测试，100%通过率 ✅

---

## 📊 性能指标

### 响应协调规则（6条）

1. **Qualification** - 确定性路由，基于配置
2. **Ordering** - 优先级升序 + agent_id字典序
3. **Deduplication** - (session, round, agent)三元组去重
4. **Cancellation** - 取消后禁止新调用
5. **Budget** - MVP限额（3 agents, 3 calls, 12k tokens, 120s）
6. **Stop** - 6种停止条件，禁止agent自动续轮

### MVP预算限制

| 限制项 | 值 |
|--------|-----|
| 最大并发Agents | 3 |
| 每轮最大调用次数 | 3 |
| 最大Token数 | 12,000 |
| 超时时间 | 120秒 |

### 重试策略

- **最大重试次数**: 3次
- **基础延迟**: 1秒
- **指数退避**: 2倍（1s → 2s → 4s）
- **可重试错误**: 超时、连接错误、限流（429）、服务不可用（503/504）

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

### 贡献流程

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 开发指南

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 代码格式化
black src/ tests/

# 类型检查
mypy src/
```

---

## 📝 变更日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本变更历史

---

## 📄 许可证

待定

---

## 👥 作者

**caohui** - 项目创建者和维护者

---

## 🙏 致谢

本项目参考和借鉴了以下优秀项目：

- [MassGen](references/massgen/) - 多Agent协调系统
- [Textual](https://github.com/Textualize/textual) - TUI框架
- 其他相关项目...

---

## 📮 联系方式

- **Issues**: [GitHub Issues](https://github.com/yourusername/agent-chat-hub/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/agent-chat-hub/discussions)

---

## 🔗 相关链接

- [项目主页](https://github.com/yourusername/agent-chat-hub)
- [文档站点](https://yourusername.github.io/agent-chat-hub)
- [发布页面](https://github.com/yourusername/agent-chat-hub/releases)

---

**快速链接**: [快速开始](docs/user-guide/QUICKSTART.md) | [配置指南](docs/user-guide/CONFIGURATION.md) | [API文档](docs/api-reference/API.md) | [教程](docs/tutorials/FIRST_AGENT.md)

---

**版本**: v1.0  
**更新日期**: 2026-09-06  
**状态**: 生产就绪 ✅
