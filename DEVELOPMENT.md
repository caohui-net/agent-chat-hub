# Agent Chat Hub - 开发指南

## 1. 快速开始

### 1.1 环境要求

| 项目 | 版本要求 | 说明 |
|------|---------|------|
| **Python** | ≥3.14 | 必需，使用现代Python特性 |
| **Git** | ≥2.0 | 版本控制 |
| **虚拟环境** | venv/virtualenv | 隔离依赖 |

### 1.2 克隆仓库

```bash
git clone https://github.com/your-org/agent-chat-hub.git
cd agent-chat-hub
```

### 1.3 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 1.4 安装依赖

```bash
# 安装核心依赖
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"
```

### 1.5 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑.env文件，添加API密钥
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

### 1.6 初始化配置

```bash
# 创建配置目录
mkdir -p ~/.agent-chat-hub/config

# 复制默认配置
cp config/models.json.example ~/.agent-chat-hub/config/models.json
cp config/agents.json.example ~/.agent-chat-hub/config/agents.json
```

### 1.7 运行应用

```bash
# 方法1: 使用入口脚本
python main.py

# 方法2: 使用模块方式
python -m src.main

# 方法3: 安装后使用命令行
agent-chat-hub
```

---

## 2. 项目结构

```
agent-chat-hub/
├── src/                      # 源代码目录
│   ├── core/                # 核心模块
│   │   ├── config.py       # 配置管理
│   │   ├── models.py       # 数据模型
│   │   └── mention_parser.py  # @mention解析
│   ├── agents/              # Agent层
│   │   ├── coordinator.py  # 响应协调器
│   │   ├── message_bus.py  # 消息总线
│   │   ├── session.py      # 会话管理
│   │   ├── executor.py     # Agent执行器
│   │   └── rule_checker.py # 规则检查器
│   ├── tui/                 # TUI界面
│   │   ├── app.py          # 主应用
│   │   ├── screens/        # 各个界面
│   │   └── components/     # UI组件
│   └── plugins/             # 插件系统
│       ├── api/            # HTTP/WebSocket API
│       └── __init__.py
├── tests/                   # 测试目录
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── conftest.py         # pytest配置
├── benchmarks/              # 性能测试
│   ├── benchmark_phase2.py
│   └── stress_test.py
├── docs/                    # 文档目录
│   ├── design/             # 设计文档
│   └── adr/                # 架构决策记录
├── config/                  # 配置模板
│   ├── models.json.example
│   └── agents.json.example
├── pyproject.toml           # 项目配置
├── README.md                # 项目说明
├── ARCHITECTURE.md          # 架构文档
├── DEVELOPMENT.md           # 开发指南（本文档）
└── CONTRIBUTING.md          # 贡献指南
```

---

## 3. 开发工作流

### 3.1 Git工作流

**主分支策略**：

- `main` - 生产就绪代码，受保护
- `develop` - 开发主分支
- `feature/*` - 功能分支
- `bugfix/*` - 修复分支
- `hotfix/*` - 紧急修复

**标准工作流程**：

```bash
# 1. 从develop创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# 2. 开发和提交
git add .
git commit -m "feat: 添加新功能描述"

# 3. 推送到远程
git push origin feature/your-feature-name

# 4. 创建Pull Request
# 在GitHub/GitLab上创建PR，从feature分支到develop

# 5. 代码审查通过后合并
# 由维护者合并到develop
```

### 3.2 提交消息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型（type）**：

- `feat` - 新功能
- `fix` - 修复bug
- `docs` - 文档更新
- `style` - 代码格式化（不影响功能）
- `refactor` - 重构（不是新功能也不是修复）
- `perf` - 性能优化
- `test` - 添加测试
- `chore` - 构建工具或辅助工具的变动

**示例**：

```bash
# 新功能
git commit -m "feat(coordinator): 添加@mention路由规则"

# 修复bug
git commit -m "fix(message_bus): 修复消息队列内存泄漏"

# 文档更新
git commit -m "docs: 更新DEVELOPMENT.md安装说明"

# 重构
git commit -m "refactor(executor): 优化并发执行逻辑"
```

### 3.3 分支命名规范

```bash
feature/add-agent-priority      # 功能：添加agent优先级
bugfix/fix-coordinator-crash    # 修复：修复协调器崩溃
hotfix/security-api-key         # 紧急修复：API密钥安全问题
refactor/message-bus-redesign   # 重构：消息总线重新设计
```

---

## 4. 代码规范

### 4.1 Python代码风格

项目使用以下工具保证代码质量：

| 工具 | 用途 | 配置文件 |
|------|------|---------|
| **Black** | 代码格式化 | `pyproject.toml` |
| **Ruff** | Linter（替代Flake8） | `pyproject.toml` |
| **mypy** | 类型检查（可选） | `mypy.ini` |

### 4.2 格式化代码

```bash
# 格式化所有代码
black src/ tests/

# 检查格式（CI中使用）
black --check src/ tests/

# 格式化单个文件
black src/agents/coordinator.py
```

### 4.3 Lint检查

```bash
# 运行Ruff检查
ruff check src/ tests/

# 自动修复可修复的问题
ruff check --fix src/ tests/

# 检查特定文件
ruff check src/agents/coordinator.py
```

### 4.4 代码风格指南

**命名约定**：

```python
# 模块名：小写+下划线
# 文件名：message_bus.py

# 类名：驼峰命名
class ResponseCoordinator:
    pass

# 函数名：小写+下划线
def select_agents(agents):
    pass

# 常量：全大写+下划线
MAX_AGENTS = 3

# 私有属性/方法：前缀下划线
class MessageBus:
    def __init__(self):
        self._queues = {}
    
    def _internal_method(self):
        pass
```

**类型注解**：

```python
from typing import List, Optional, Dict

def select_agents(
    agents: List[AgentConfig],
    mentions: Optional[List[str]] = None
) -> List[AgentConfig]:
    """选择要调用的agents
    
    Args:
        agents: 可用的agent配置列表
        mentions: @提及的agent_id列表
    
    Returns:
        选中的agent列表
    """
    pass
```

**文档字符串**：

使用Google风格的docstring：

```python
def process_message(self, message: str, context: Dict) -> str:
    """处理用户消息并返回响应
    
    这个方法会解析消息中的@mentions，然后根据协调器规则
    选择合适的agents进行响应。
    
    Args:
        message: 用户输入的消息文本
        context: 上下文信息，包含session_id等
    
    Returns:
        处理后的响应文本
    
    Raises:
        ValueError: 如果消息为空或格式错误
        RuntimeError: 如果没有可用的agents
    
    Examples:
        >>> process_message("@gpt4 你好", {"session_id": "123"})
        "你好！我是GPT-4..."
    """
    pass
```

### 4.5 代码复杂度控制

- 单个函数不超过50行（特殊情况除外）
- 单个文件不超过500行
- 函数圈复杂度（Cyclomatic Complexity）≤10
- 嵌套深度≤4层

**重构信号**：

```python
# ❌ 不好：嵌套过深
def process_agents(agents):
    for agent in agents:
        if agent.active:
            if agent.priority < 5:
                if agent.role_type == "coordinator":
                    # 嵌套4层
                    pass

# ✅ 好：提前返回
def process_agents(agents):
    for agent in agents:
        if not agent.active:
            continue
        if agent.priority >= 5:
            continue
        if agent.role_type != "coordinator":
            continue
        # 逻辑更清晰
        pass
```

---

## 5. 测试开发

### 5.1 测试策略

| 测试类型 | 覆盖范围 | 目标覆盖率 |
|---------|---------|-----------|
| **单元测试** | 单个函数/类 | ≥80% |
| **集成测试** | 多个组件协作 | ≥60% |
| **性能测试** | 关键路径 | 基准存在 |
| **端到端测试** | 完整流程 | 核心场景 |

### 5.2 运行测试

```bash
# 运行所有测试
pytest

# 运行单个测试文件
pytest tests/test_coordinator.py

# 运行特定测试
pytest tests/test_coordinator.py::test_select_agents

# 显示详细输出
pytest -v

# 显示print输出
pytest -s

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 并行运行测试（需要pytest-xdist）
pytest -n auto
```

### 5.3 编写单元测试

**测试文件命名**：`test_<module>.py`

**测试函数命名**：`test_<function>_<scenario>`

**示例**：

```python
# tests/unit/test_coordinator.py
import pytest
from src.agents.coordinator import ResponseCoordinator
from src.core.models import AgentConfig

class TestResponseCoordinator:
    """ResponseCoordinator单元测试"""
    
    def test_sort_agents_by_priority(self):
        """测试按优先级排序agents"""
        # Arrange
        coordinator = ResponseCoordinator()
        agents = [
            AgentConfig(agent_id="a", priority=3, active=True),
            AgentConfig(agent_id="b", priority=1, active=True),
            AgentConfig(agent_id="c", priority=2, active=True),
        ]
        
        # Act
        sorted_agents = coordinator.sort_agents(agents)
        
        # Assert
        assert sorted_agents[0].agent_id == "b"  # priority=1
        assert sorted_agents[1].agent_id == "c"  # priority=2
        assert sorted_agents[2].agent_id == "a"  # priority=3
    
    def test_qualify_agents_with_mentions(self):
        """测试@mention路由规则"""
        # Arrange
        coordinator = ResponseCoordinator()
        agents = [
            AgentConfig(agent_id="coordinator", role_type="coordinator", active=True),
            AgentConfig(agent_id="gpt4", role_type="specialist", active=True),
        ]
        mentions = ["gpt4"]
        
        # Act
        qualified = coordinator.qualify_agents(agents, mentions=mentions)
        
        # Assert
        assert len(qualified) == 1
        assert qualified[0].agent_id == "gpt4"
```

### 5.4 编写集成测试

```python
# tests/integration/test_session_flow.py
import pytest
from src.agents.session import SessionManager
from src.core.config import ConfigManager

@pytest.mark.asyncio
async def test_full_user_message_flow():
    """测试完整的用户消息处理流程"""
    # Arrange
    config_manager = ConfigManager()
    session_manager = SessionManager(config_manager)
    session = session_manager.create_session("测试会话")
    
    # Act
    session_manager.add_message("user", "@gpt4 你好")
    responses = await session_manager.process_user_message()
    
    # Assert
    assert len(responses) > 0
    assert responses[0].agent_id == "gpt4"
```

### 5.5 Mock和Fixture

```python
# tests/conftest.py
import pytest
from src.core.config import ConfigManager

@pytest.fixture
def mock_config_manager():
    """提供模拟的ConfigManager"""
    config = ConfigManager()
    # 加载测试配置
    return config

@pytest.fixture
def sample_agents():
    """提供测试用的agent配置"""
    return [
        AgentConfig(agent_id="coordinator", role_type="coordinator", active=True),
        AgentConfig(agent_id="gpt4", role_type="specialist", active=True),
    ]

# 使用fixture
def test_something(mock_config_manager, sample_agents):
    # 测试代码
    pass
```

---

## 6. 调试技巧

### 6.1 日志系统

项目使用 `structlog` 进行结构化日志：

```python
import structlog

logger = structlog.get_logger()

# 记录信息日志
logger.info("session_created", session_id="123", title="新对话")

# 记录警告
logger.warning("budget_exceeded", total_calls=5, max_calls=3)

# 记录错误（带异常）
try:
    do_something()
except Exception as e:
    logger.error("operation_failed", exc_info=e)
```

**日志级别配置**：

```bash
# 环境变量控制日志级别
export LOG_LEVEL=DEBUG  # DEBUG/INFO/WARNING/ERROR

# 运行应用
python main.py
```

### 6.2 调试工具

**IPython调试器**：

```python
# 在代码中插入断点
import ipdb; ipdb.set_trace()

# 或使用内置pdb
import pdb; pdb.set_trace()
```

**常用调试命令**：

```
n - 下一行
s - 进入函数
c - 继续执行
p variable - 打印变量
l - 显示当前位置代码
h - 帮助
q - 退出
```

### 6.3 TUI调试

```bash
# 使用textual的开发控制台
textual console -x SYSTEM -x EVENT -x DEBUG -x INFO

# 在另一个终端运行应用
python main.py

# 或直接使用textual run
textual run --dev src.tui.app:ChatHubApp
```

### 6.4 性能分析

```bash
# 使用cProfile分析性能
python -m cProfile -o profile.stats main.py

# 分析结果
python -m pstats profile.stats
>>> sort cumulative
>>> stats 20

# 或使用line_profiler（逐行分析）
pip install line_profiler
kernprof -l -v script.py
```

---

## 7. 开发最佳实践

### 7.1 编码原则

1. **KISS (Keep It Simple, Stupid)**
   - 优先选择简单的解决方案
   - 避免过度设计

2. **DRY (Don't Repeat Yourself)**
   - 提取公共逻辑到函数/类
   - 避免复制粘贴代码

3. **SOLID原则**
   - 单一职责原则（SRP）
   - 开闭原则（OCP）
   - 里氏替换原则（LSP）
   - 接口隔离原则（ISP）
   - 依赖倒置原则（DIP）

### 7.2 错误处理

```python
# ✅ 好：明确的异常类型
def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("config_not_found", path=path)
        raise ConfigError(f"配置文件不存在: {path}")
    except json.JSONDecodeError as e:
        logger.error("invalid_json", path=path, error=str(e))
        raise ConfigError(f"配置文件格式错误: {e}")

# ❌ 不好：捕获所有异常
def load_config(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}  # 吞掉异常，隐藏问题
```

### 7.3 配置管理

```python
# 使用Pydantic进行配置验证
from pydantic import BaseModel, Field

class BudgetLimits(BaseModel):
    max_agents: int = Field(default=3, ge=1, le=10)
    max_calls_per_round: int = Field(default=3, ge=1, le=20)
    max_tokens: int = Field(default=12000, ge=1000)
    timeout_seconds: float = Field(default=120.0, ge=10.0)

# 加载配置时自动验证
config = BudgetLimits(**config_dict)
```

### 7.4 异步编程

```python
# ✅ 好：使用asyncio.gather并发执行
async def execute_agents(agents):
    tasks = [execute_agent(agent) for agent in agents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# ✅ 好：使用asyncio.wait_for设置超时
async def execute_with_timeout(agent):
    try:
        return await asyncio.wait_for(agent.execute(), timeout=30.0)
    except asyncio.TimeoutError:
        logger.warning("agent_timeout", agent_id=agent.id)
        return None

# ❌ 不好：在异步函数中使用time.sleep
async def bad_async():
    time.sleep(1)  # 阻塞整个事件循环！
    
# ✅ 好：使用asyncio.sleep
async def good_async():
    await asyncio.sleep(1)  # 释放事件循环
```

---

## 8. 常见开发问题

### 8.1 依赖问题

**问题**：`ModuleNotFoundError: No module named 'textual'`

**解决**：
```bash
# 确认虚拟环境已激活
source .venv/bin/activate

# 重新安装依赖
pip install -e ".[dev]"
```

### 8.2 测试失败

**问题**：测试运行时找不到模块

**解决**：
```bash
# 确保项目根目录在PYTHONPATH中
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 或者安装为可编辑模式
pip install -e .
```

### 8.3 TUI显示问题

**问题**：TUI界面显示异常

**解决**：
```bash
# 检查终端支持
echo $TERM  # 应该是 xterm-256color 或类似

# 如果不支持，设置环境变量
export TERM=xterm-256color

# 或使用textual的诊断工具
textual diagnose
```

### 8.4 性能问题

**问题**：应用响应缓慢

**调试步骤**：
1. 使用cProfile分析瓶颈
2. 检查是否有同步阻塞操作
3. 查看日志中的性能指标
4. 运行性能基准测试对比

### 8.5 配置问题

**问题**：API密钥未生效

**检查清单**：
```bash
# 1. 检查环境变量
env | grep API_KEY

# 2. 检查.env文件
cat .env

# 3. 检查配置文件
cat ~/.agent-chat-hub/config/models.json

# 4. 验证keyring存储
python -c "import keyring; print(keyring.get_password('agent-chat-hub', 'OPENAI_API_KEY'))"
```

---

## 9. 开发工具推荐

### 9.1 IDE/编辑器

| 工具 | 优势 | 配置 |
|------|------|------|
| **VS Code** | 轻量、插件丰富 | 安装Python扩展 |
| **PyCharm** | 强大的Python IDE | 自动识别项目结构 |
| **Vim/Neovim** | 高效、可定制 | 配置LSP和插件 |

**VS Code推荐插件**：
- Python (Microsoft)
- Pylance (类型检查)
- Black Formatter
- Ruff
- Git Graph

### 9.2 命令行工具

```bash
# 安装常用工具
pip install ipython ipdb rich

# IPython - 增强的Python shell
ipython

# Rich - 终端美化（已集成在项目中）
python -m rich.markdown README.md
```

### 9.3 开发环境配置

**VS Code设置（.vscode/settings.json）**：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.rulers": [100],
  "[python]": {
    "editor.tabSize": 4
  }
}
```

---

## 10. 发布流程

### 10.1 版本号规范

遵循 [Semantic Versioning 2.0.0](https://semver.org/)：

```
MAJOR.MINOR.PATCH

例如：0.1.0 → 0.2.0 → 1.0.0
```

- **MAJOR**: 不兼容的API变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的bug修复

### 10.2 发版检查清单

```bash
# 1. 确保所有测试通过
pytest

# 2. 更新CHANGELOG.md
# 记录本次发版的变更

# 3. 更新版本号
# 编辑 pyproject.toml 中的 version 字段

# 4. 提交版本变更
git add pyproject.toml CHANGELOG.md
git commit -m "chore: 发布版本 v0.2.0"

# 5. 打标签
git tag -a v0.2.0 -m "Release v0.2.0"

# 6. 推送到远程
git push origin develop
git push origin v0.2.0

# 7. 创建GitHub Release
# 在GitHub上创建Release，附带CHANGELOG
```

### 10.3 构建和发布

```bash
# 构建分发包
python -m build

# 检查分发包
twine check dist/*

# 上传到PyPI（需要先注册账号）
twine upload dist/*
```

---

## 11. 参考资源

### 11.1 项目文档

- [README.md](README.md) - 项目概述
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计
- [INSTALL.md](INSTALL.md) - 安装指南
- [CONFIGURATION.md](CONFIGURATION.md) - 配置参考
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 故障排除
- [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南

### 11.2 外部资源

**Python**：
- [Python官方文档](https://docs.python.org/3/)
- [Real Python教程](https://realpython.com/)

**Textual (TUI)**：
- [Textual文档](https://textual.textualize.io/)
- [Textual示例](https://github.com/Textualize/textual/tree/main/examples)

**LangChain/LangGraph**：
- [LangChain文档](https://python.langchain.com/)
- [LangGraph文档](https://langchain-ai.github.io/langgraph/)

**测试**：
- [Pytest文档](https://docs.pytest.org/)
- [Python测试最佳实践](https://testdriven.io/blog/testing-best-practices/)

### 11.3 社区

- GitHub Issues: 报告bug和功能请求
- GitHub Discussions: 技术讨论和问答
- Discord/Slack: 实时交流（如果有的话）

---

## 12. 常见问题 (FAQ)

**Q: 如何添加新的Agent？**

A: 编辑 `~/.agent-chat-hub/config/agents.json`，添加新的agent配置，然后重启应用。

**Q: 如何切换使用的LLM模型？**

A: 在agents配置中修改 `model_id` 字段，指向models.json中定义的模型。

**Q: 如何贡献代码？**

A: 请参考 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献流程。

**Q: 遇到问题如何寻求帮助？**

A: 
1. 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. 搜索GitHub Issues
3. 在GitHub Discussions提问
4. 提交新的Issue

---

**文档版本**：v1.0  
**最后更新**：2026-07-26  
**维护者**：Agent Chat Hub Team
