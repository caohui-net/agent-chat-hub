# Agent Chat Hub - 文档索引

欢迎使用 Agent Chat Hub！本文档提供了完整的文档导航和快速查找指南。

---

## 📚 文档总览

Agent Chat Hub 拥有完整的文档体系，覆盖从快速开始到生产部署的全流程。

**文档完整性**: 95%+ （生产级）  
**总文档数**: 13个  
**总文档量**: ~150KB

---

## 🚀 快速开始

**新用户推荐阅读顺序**：

1. [README.md](README.md) - 项目概述和特性介绍 (5分钟)
2. [INSTALL.md](INSTALL.md) - 安装和配置指南 (10分钟)
3. [USER_GUIDE.md](USER_GUIDE.md) - 使用手册和快捷键 (15分钟)
4. [CONFIGURATION.md](CONFIGURATION.md) - 配置参考 (10分钟)

**完成上述阅读后，你就可以开始使用 Agent Chat Hub 了！**

---

## 📖 文档分类

### 1. 用户文档

适合终端用户和系统管理员。

| 文档 | 说明 | 适合人群 | 阅读时长 |
|------|------|---------|---------|
| [README.md](README.md) | 项目概述、特性介绍、快速开始 | 所有人 | 5分钟 |
| [INSTALL.md](INSTALL.md) | 详细的安装和配置步骤 | 新用户 | 10分钟 |
| [USER_GUIDE.md](USER_GUIDE.md) | 完整的使用手册，包含操作指南、快捷键、FAQ | 日常用户 | 15分钟 |
| [CONFIGURATION.md](CONFIGURATION.md) | 配置文件格式、环境变量、优先级规则 | 高级用户 | 10分钟 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 常见问题排查、调试技巧、日志分析 | 故障排查 | 10分钟 |

**使用场景**：
- 第一次使用 → README + INSTALL
- 日常操作 → USER_GUIDE
- 遇到问题 → TROUBLESHOOTING
- 调整配置 → CONFIGURATION

---

### 2. 开发者文档

适合贡献者和插件开发者。

| 文档 | 说明 | 适合人群 | 阅读时长 |
|------|------|---------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构设计、核心组件、设计决策（ADR） | 架构师、核心开发者 | 30分钟 |
| [DEVELOPMENT.md](DEVELOPMENT.md) | 开发环境搭建、Git工作流、代码规范 | 贡献者 | 25分钟 |
| [TESTING.md](TESTING.md) | 测试策略、编写测试、覆盖率要求 | 开发者、QA | 20分钟 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献流程、PR模板、代码审查规范 | 贡献者 | 15分钟 |
| [API.md](API.md) | 完整API参考：插件API、HTTP API、Python API | 插件开发者 | 25分钟 |

**使用场景**：
- 开始贡献 → CONTRIBUTING + DEVELOPMENT
- 理解架构 → ARCHITECTURE
- 编写测试 → TESTING
- 开发插件 → API + ARCHITECTURE

---

### 3. 运维文档

适合DevOps和系统管理员。

| 文档 | 说明 | 适合人群 | 阅读时长 |
|------|------|---------|---------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署指南：标准部署、Docker部署、配置管理 | 运维人员 | 15分钟 |
| [OPERATIONS.md](OPERATIONS.md) | systemd服务、监控告警、备份恢复、安全加固 | DevOps | 20分钟 |
| [PERFORMANCE.md](PERFORMANCE.md) | 性能分析、基准测试、优化建议 | 性能工程师 | 15分钟 |

**使用场景**：
- 生产部署 → DEPLOYMENT
- 日常运维 → OPERATIONS
- 性能调优 → PERFORMANCE
- 故障排查 → TROUBLESHOOTING + OPERATIONS

---

### 4. 变更记录

| 文档 | 说明 | 更新频率 |
|------|------|---------|
| [CHANGELOG.md](CHANGELOG.md) | 版本变更历史、功能更新、Bug修复记录 | 每次发版 |
| [TEST_GUIDE.md](TEST_GUIDE.md) | 测试运行指南、测试报告 | 持续更新 |

---

## 🔍 按场景查找

### 场景1: 我是新用户，想快速上手

**推荐路径**：
1. 阅读 [README.md](README.md) 了解项目
2. 按照 [INSTALL.md](INSTALL.md) 安装系统
3. 参考 [USER_GUIDE.md](USER_GUIDE.md) 学习使用
4. 遇到问题查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**预计耗时**：30-45分钟

---

### 场景2: 我想贡献代码

**推荐路径**：
1. 阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献流程
2. 按照 [DEVELOPMENT.md](DEVELOPMENT.md) 搭建开发环境
3. 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 理解系统架构
4. 参考 [TESTING.md](TESTING.md) 编写测试
5. 提交PR前检查 [CONTRIBUTING.md](CONTRIBUTING.md) 的要求

**预计耗时**：1-2小时（首次）

---

### 场景3: 我要部署到生产环境

**推荐路径**：
1. 阅读 [DEPLOYMENT.md](DEPLOYMENT.md) 选择部署方式
2. 参考 [CONFIGURATION.md](CONFIGURATION.md) 配置系统
3. 按照 [OPERATIONS.md](OPERATIONS.md) 设置监控和备份
4. 准备 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 应对故障

**预计耗时**：2-3小时

---

### 场景4: 我要开发插件

**推荐路径**：
1. 阅读 [API.md](API.md) 了解插件API
2. 参考 [ARCHITECTURE.md](ARCHITECTURE.md) 理解插件系统
3. 查看 [DEVELOPMENT.md](DEVELOPMENT.md) 了解开发规范
4. 参考 [TESTING.md](TESTING.md) 编写测试

**预计耗时**：1-2小时

---

### 场景5: 系统出现问题

**推荐路径**：
1. 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 的常见问题
2. 检查 [CONFIGURATION.md](CONFIGURATION.md) 的配置是否正确
3. 如果是性能问题，参考 [PERFORMANCE.md](PERFORMANCE.md)
4. 如果是运维问题，查看 [OPERATIONS.md](OPERATIONS.md)

**预计耗时**：10-30分钟

---

## 📊 文档详细列表

### 核心文档

#### README.md
- **类型**: 项目概述
- **内容**: 特性介绍、快速开始、系统要求
- **关键词**: 简介、特性、快速开始
- **适合人群**: 所有人
- **必读指数**: ⭐⭐⭐⭐⭐

#### INSTALL.md
- **类型**: 安装指南
- **内容**: 详细的安装步骤、依赖配置、初始化
- **关键词**: 安装、配置、初始化
- **适合人群**: 新用户
- **必读指数**: ⭐⭐⭐⭐⭐

#### USER_GUIDE.md
- **类型**: 使用手册
- **内容**: 完整操作指南、@mention路由、快捷键、FAQ
- **关键词**: 使用、操作、快捷键
- **适合人群**: 日常用户
- **必读指数**: ⭐⭐⭐⭐

#### CONFIGURATION.md
- **类型**: 配置参考
- **内容**: models.json、agents.json格式、环境变量
- **关键词**: 配置、格式、环境变量
- **适合人群**: 高级用户
- **必读指数**: ⭐⭐⭐

#### TROUBLESHOOTING.md
- **类型**: 故障排查
- **内容**: 10个常见问题、调试技巧、日志分析
- **关键词**: 问题、调试、日志
- **适合人群**: 故障排查
- **必读指数**: ⭐⭐⭐⭐

---

### 开发者文档

#### ARCHITECTURE.md
- **类型**: 架构设计
- **大小**: 21KB / 734行
- **内容**: 
  - 系统分层架构
  - 6条响应控制规则
  - Coordinator、MessageBus、SessionManager详解
  - ADR架构决策记录
  - 数据流和控制流
- **关键词**: 架构、设计、组件、ADR
- **适合人群**: 架构师、核心开发者
- **必读指数**: ⭐⭐⭐⭐⭐（贡献者必读）

#### DEVELOPMENT.md
- **类型**: 开发指南
- **大小**: 19KB / 689行
- **内容**:
  - 开发环境搭建
  - Git工作流和分支策略
  - 代码规范（Black、Ruff）
  - 调试技巧和工具
  - 常见开发问题
- **关键词**: 开发、环境、规范、工具
- **适合人群**: 贡献者、开发者
- **必读指数**: ⭐⭐⭐⭐⭐（贡献者必读）

#### TESTING.md
- **类型**: 测试文档
- **大小**: 17KB / 642行
- **内容**:
  - 测试策略（单元/集成/性能）
  - 如何运行测试
  - 编写测试的最佳实践
  - 测试覆盖率要求（≥80%）
  - CI/CD集成
- **关键词**: 测试、覆盖率、CI
- **适合人群**: 开发者、QA
- **必读指数**: ⭐⭐⭐⭐

#### CONTRIBUTING.md
- **类型**: 贡献指南
- **大小**: 9KB / 314行
- **内容**:
  - 如何贡献（Bug修复、新功能、文档）
  - 代码审查流程
  - Issue和PR模板
  - 提交消息规范（Conventional Commits）
  - 行为准则
- **关键词**: 贡献、PR、审查、规范
- **适合人群**: 贡献者
- **必读指数**: ⭐⭐⭐⭐⭐（贡献者必读）

#### API.md
- **类型**: API参考
- **大小**: 14KB / 676行
- **内容**:
  - 插件API（MessageAPI、ConfigAPI、AgentAPI）
  - HTTP RESTful API
  - WebSocket实时通信API
  - Python嵌入式API
  - 数据模型定义
- **关键词**: API、插件、HTTP、WebSocket
- **适合人群**: 插件开发者、集成开发者
- **必读指数**: ⭐⭐⭐⭐

---

### 运维文档

#### DEPLOYMENT.md
- **类型**: 部署指南
- **大小**: 4KB / 305行
- **内容**:
  - 标准部署流程
  - Docker容器化部署
  - 配置管理
  - 备份和恢复
- **关键词**: 部署、Docker、配置
- **适合人群**: 运维人员、DevOps
- **必读指数**: ⭐⭐⭐⭐

#### OPERATIONS.md
- **类型**: 运维指南
- **大小**: 12KB / 428行
- **内容**:
  - systemd服务配置
  - 日志管理和轮转
  - 监控和告警
  - 性能调优
  - 安全加固
- **关键词**: 运维、监控、安全、性能
- **适合人群**: DevOps、系统管理员
- **必读指数**: ⭐⭐⭐⭐

#### PERFORMANCE.md
- **类型**: 性能分析
- **大小**: 7KB / ~250行
- **内容**:
  - 性能基准测试结果
  - 压力测试方案
  - 性能优化建议
  - 瓶颈分析
- **关键词**: 性能、基准、优化
- **适合人群**: 性能工程师
- **必读指数**: ⭐⭐⭐

---

### 其他文档

#### CHANGELOG.md
- **类型**: 变更日志
- **内容**: 版本历史、功能更新、Bug修复
- **更新频率**: 每次发版
- **必读指数**: ⭐⭐⭐

#### TEST_GUIDE.md
- **类型**: 测试指南
- **内容**: 测试运行方法、测试报告
- **更新频率**: 持续更新
- **必读指数**: ⭐⭐⭐

---

## 🎯 按关键词查找

### 安装和配置
- [INSTALL.md](INSTALL.md) - 安装步骤
- [CONFIGURATION.md](CONFIGURATION.md) - 配置格式
- [DEPLOYMENT.md](DEPLOYMENT.md) - 生产部署

### 使用和操作
- [USER_GUIDE.md](USER_GUIDE.md) - 使用手册
- [README.md](README.md) - 快速开始
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 问题排查

### 开发和贡献
- [ARCHITECTURE.md](ARCHITECTURE.md) - 系统架构
- [DEVELOPMENT.md](DEVELOPMENT.md) - 开发指南
- [TESTING.md](TESTING.md) - 测试文档
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献流程
- [API.md](API.md) - API参考

### 运维和监控
- [OPERATIONS.md](OPERATIONS.md) - 运维指南
- [DEPLOYMENT.md](DEPLOYMENT.md) - 部署方案
- [PERFORMANCE.md](PERFORMANCE.md) - 性能分析

### 故障排查
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 常见问题
- [OPERATIONS.md](OPERATIONS.md) - 日志分析
- [PERFORMANCE.md](PERFORMANCE.md) - 性能问题

---

## 📝 文档维护

### 文档更新频率

| 文档类型 | 更新频率 | 维护者 |
|---------|---------|--------|
| 用户文档 | 按需更新 | 核心团队 |
| 开发者文档 | 版本发布时 | 核心团队 |
| 运维文档 | 按需更新 | DevOps团队 |
| CHANGELOG | 每次发版 | 发版负责人 |
| API文档 | API变更时 | API负责人 |

### 文档反馈

如果你发现文档中的问题或有改进建议：

1. **报告问题**: 在 [GitHub Issues](https://github.com/your-org/agent-chat-hub/issues) 创建Issue，标记为 `documentation`
2. **提出改进**: 创建Pull Request直接修改文档
3. **提问讨论**: 在 [GitHub Discussions](https://github.com/your-org/agent-chat-hub/discussions) 提问

---

## 🔗 外部资源

### 官方链接
- **GitHub仓库**: https://github.com/your-org/agent-chat-hub
- **在线文档**: https://docs.agent-chat-hub.io (如果有)
- **问题追踪**: https://github.com/your-org/agent-chat-hub/issues

### 相关技术文档
- [Textual文档](https://textual.textualize.io/) - TUI框架
- [LangChain文档](https://python.langchain.com/) - LLM集成
- [LangGraph文档](https://langchain-ai.github.io/langgraph/) - 工作流编排

---

## 📊 文档统计

**总览**：

| 类型 | 数量 | 总大小 | 总行数 |
|------|------|--------|--------|
| 用户文档 | 5个 | ~30KB | ~1200行 |
| 开发者文档 | 5个 | ~90KB | ~3500行 |
| 运维文档 | 3个 | ~25KB | ~1000行 |
| **总计** | **13个** | **~150KB** | **~5700行** |

**完成度**: 95%+（生产级）

---

## 🚀 下一步

根据你的角色，选择合适的起点：

**👤 普通用户**  
→ [README.md](README.md) → [INSTALL.md](INSTALL.md) → [USER_GUIDE.md](USER_GUIDE.md)

**💻 开发者**  
→ [CONTRIBUTING.md](CONTRIBUTING.md) → [DEVELOPMENT.md](DEVELOPMENT.md) → [ARCHITECTURE.md](ARCHITECTURE.md)

**🔧 运维人员**  
→ [DEPLOYMENT.md](DEPLOYMENT.md) → [OPERATIONS.md](OPERATIONS.md) → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**🔌 插件开发者**  
→ [API.md](API.md) → [ARCHITECTURE.md](ARCHITECTURE.md) → [DEVELOPMENT.md](DEVELOPMENT.md)

---

**文档版本**: v1.0  
**最后更新**: 2026-07-26  
**维护者**: Agent Chat Hub Team

---

**有疑问？** 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 或在 [GitHub Discussions](https://github.com/your-org/agent-chat-hub/discussions) 提问。
