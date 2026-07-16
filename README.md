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
- **Web框架**：FastAPI
- **实时通信**：SSE (Server-Sent Events) + WebSocket
- **数据验证**：Pydantic v2
- **日志**：structlog

## 快速开始

### 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖（待创建pyproject.toml后）
pip install -e .
```

### 运行

```bash
# 待实现
```

## 参考项目

本项目参考和集成了以下优秀项目（放置在`references/`目录）：

- MassGen：多Agent协调系统
- 其他相关项目...

## 开发状态

🚧 **项目初始化中** - 2026-07-16

## License

待定

## 作者

caohui
