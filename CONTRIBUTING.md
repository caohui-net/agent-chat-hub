# 贡献指南

感谢你考虑为 Agent Chat Hub 项目做出贡献！本文档提供了贡献代码的指南和流程。

## 目录

1. [行为准则](#行为准则)
2. [如何贡献](#如何贡献)
3. [开发流程](#开发流程)
4. [提交规范](#提交规范)
5. [Pull Request流程](#pull-request流程)
6. [代码审查](#代码审查)
7. [问题反馈](#问题反馈)

---

## 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表现出同理心

### 不可接受的行为

以下行为被视为骚扰，不会被容忍：

- 使用性别化的语言或图像，以及不受欢迎的性关注
- 恶意评论、侮辱/贬损性评论、人身或政治攻击
- 公开或私下骚扰
- 未经明确许可，发布他人的私人信息
- 在专业环境中可能被合理认为不适当的其他行为

---

## 如何贡献

### 贡献类型

我们欢迎以下类型的贡献：

1. **Bug修复** - 修复已知问题
2. **新功能** - 添加新的功能或改进
3. **文档改进** - 改进文档、示例、教程
4. **测试** - 添加或改进测试
5. **性能优化** - 提升系统性能
6. **代码重构** - 改善代码质量

### 寻找贡献点

- 查看 [Issues](https://github.com/your-org/agent-chat-hub/issues) 标记为 `good first issue` 的问题
- 查看 [Issues](https://github.com/your-org/agent-chat-hub/issues) 标记为 `help wanted` 的问题
- 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系统设计
- 查看 [未来架构演进](ARCHITECTURE.md#11-未来架构演进) 了解计划中的功能

---

## 开发流程

### 1. Fork仓库

```bash
# 在GitHub上Fork仓库
# 然后克隆你的fork
git clone https://github.com/your-username/agent-chat-hub.git
cd agent-chat-hub
```

### 2. 设置开发环境

```bash
# 添加上游仓库
git remote add upstream https://github.com/your-org/agent-chat-hub.git

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
```

### 3. 创建分支

```bash
# 从develop分支创建功能分支
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name
```

**分支命名规范**：

- `feature/` - 新功能
- `bugfix/` - Bug修复
- `docs/` - 文档更新
- `refactor/` - 代码重构
- `test/` - 测试相关

### 4. 开发和测试

```bash
# 编写代码
# ...

# 运行测试
pytest

# 检查代码格式
black src/ tests/
ruff check src/ tests/

# 运行所有检查
make check  # 如果有Makefile
```

### 5. 提交更改

```bash
# 添加更改
git add .

# 提交（遵循提交规范）
git commit -m "feat: 添加新功能描述"

# 推送到你的fork
git push origin feature/your-feature-name
```

### 6. 创建Pull Request

1. 在GitHub上打开你的fork
2. 点击 "Compare & pull request"
3. 填写PR模板
4. 提交PR

---

## 提交规范

### Conventional Commits

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型（type）

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(coordinator): 添加优先级排序` |
| `fix` | Bug修复 | `fix(message_bus): 修复内存泄漏` |
| `docs` | 文档更新 | `docs: 更新安装指南` |
| `style` | 代码格式化 | `style: 格式化coordinator.py` |
| `refactor` | 重构 | `refactor: 简化选择逻辑` |
| `perf` | 性能优化 | `perf: 优化消息路由性能` |
| `test` | 测试 | `test: 添加coordinator单元测试` |
| `chore` | 构建工具 | `chore: 更新依赖版本` |

### 作用域（scope）

常见作用域：

- `coordinator` - 响应协调器
- `message_bus` - 消息总线
- `session` - 会话管理
- `executor` - Agent执行器
- `config` - 配置管理
- `tui` - TUI界面
- `plugins` - 插件系统

### 示例

```bash
# 新功能
git commit -m "feat(coordinator): 实现@mention路由规则

- 添加mention解析逻辑
- 更新资格判定规则
- 添加单元测试

Closes #123"

# Bug修复
git commit -m "fix(message_bus): 修复队列满时的阻塞问题

当队列达到容量上限时，publish操作会永久阻塞。
本次修复添加了超时机制。

Fixes #456"

# 文档更新
git commit -m "docs: 添加贡献指南

- 创建CONTRIBUTING.md
- 说明开发流程
- 添加提交规范"
```

---

## Pull Request流程

### PR模板

创建PR时，请填写以下信息：

```markdown
## 变更类型

- [ ] Bug修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化
- [ ] 测试

## 变更描述

<!-- 清楚地描述你做了什么改动 -->

## 相关Issue

<!-- 引用相关的Issue，例如：Closes #123 -->

## 测试

<!-- 描述你如何测试这些变更 -->

- [ ] 添加了新的测试
- [ ] 所有测试通过
- [ ] 手动测试通过

## 检查清单

- [ ] 代码遵循项目的代码风格
- [ ] 已运行 `black` 和 `ruff`
- [ ] 添加/更新了文档
- [ ] 添加/更新了测试
- [ ] 所有测试通过
- [ ] 提交消息遵循规范
```

### PR要求

**代码要求**：

- [ ] 代码通过所有测试
- [ ] 代码覆盖率不降低（当前≥80%）
- [ ] 代码通过Black和Ruff检查
- [ ] 无明显的性能退化

**文档要求**：

- [ ] 更新相关文档（如果适用）
- [ ] 添加docstring（新函数/类）
- [ ] 更新CHANGELOG.md（由维护者完成）

**测试要求**：

- [ ] 添加单元测试（新功能）
- [ ] 添加集成测试（影响多个组件）
- [ ] 测试覆盖核心逻辑

### PR大小

- 单个PR最好不超过500行代码变更
- 大型功能建议拆分为多个PR
- 每个PR应该只做一件事

### Draft PR

如果你的工作尚未完成，可以创建Draft PR：

- 用于早期反馈
- 用于讨论设计方案
- 准备好后转为正式PR

---

## 代码审查

### 审查流程

1. **自动检查**
   - CI运行所有测试
   - 代码格式检查
   - 覆盖率检查

2. **人工审查**
   - 至少1个维护者审查
   - 检查代码质量
   - 检查设计合理性

3. **反馈和修改**
   - 回复审查意见
   - 推送修改
   - 继续讨论

4. **合并**
   - 所有检查通过
   - 审查批准
   - 维护者合并

### 审查重点

**代码质量**：

- 代码清晰易懂
- 遵循项目风格
- 适当的错误处理
- 合理的性能

**设计**：

- 符合系统架构
- 接口设计合理
- 向后兼容（如果适用）

**测试**：

- 测试覆盖充分
- 测试用例有意义
- 边界情况考虑

**文档**：

- Docstring完整
- 注释清晰
- 文档更新

### 审查建议的响应

收到审查意见后：

1. **认真考虑**每个建议
2. **解释**你的设计决策（如果有异议）
3. **及时回复**和推送修改
4. **保持礼貌**和开放心态

---

## 问题反馈

### 报告Bug

使用 [Bug Report模板](https://github.com/your-org/agent-chat-hub/issues/new?template=bug_report.md)：

**必需信息**：

- **Bug描述**：清楚简洁地描述bug
- **复现步骤**：
  1. 执行步骤1
  2. 执行步骤2
  3. 观察到错误
- **期望行为**：描述你期望发生什么
- **实际行为**：描述实际发生了什么
- **环境信息**：
  - OS: [如 macOS 13.0]
  - Python版本: [如 3.14]
  - 项目版本: [如 0.1.0]
- **日志**：相关的错误日志或堆栈跟踪
- **截图**：如果适用

### 功能请求

使用 [Feature Request模板](https://github.com/your-org/agent-chat-hub/issues/new?template=feature_request.md)：

**必需信息**：

- **功能描述**：清楚地描述你想要的功能
- **使用场景**：描述这个功能的使用场景
- **替代方案**：你考虑过的其他方案
- **额外信息**：其他相关信息

### 提问

- 在 [GitHub Discussions](https://github.com/your-org/agent-chat-hub/discussions) 提问
- 搜索已有的讨论
- 提供足够的上下文

---

## 开发约定

### 代码风格

- 遵循 [PEP 8](https://pep8.org/)
- 使用 Black 格式化（line-length=100）
- 使用 Ruff 进行linting
- 使用类型注解

### 命名约定

```python
# 模块/文件：小写+下划线
message_bus.py

# 类：驼峰命名
class ResponseCoordinator:
    pass

# 函数/方法：小写+下划线
def select_agents():
    pass

# 常量：全大写+下划线
MAX_AGENTS = 3

# 私有：前缀下划线
def _internal_method():
    pass
```

### 文档字符串

使用Google风格：

```python
def function_with_docstring(param1: str, param2: int) -> bool:
    """简短描述（一行）。

    详细描述（如果需要）。可以多行。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        ValueError: 什么情况下抛出

    Examples:
        >>> function_with_docstring("test", 42)
        True
    """
    pass
```

### 测试约定

- 测试文件：`test_<module>.py`
- 测试类：`TestClassName`
- 测试函数：`test_<function>_<scenario>`
- 使用AAA模式（Arrange, Act, Assert）

---

## 发布流程

### 版本号

遵循 [Semantic Versioning](https://semver.org/)：

```
MAJOR.MINOR.PATCH

例如：0.1.0 → 0.2.0 → 1.0.0
```

### 发布检查清单

- [ ] 所有测试通过
- [ ] 更新版本号（pyproject.toml）
- [ ] 更新CHANGELOG.md
- [ ] 创建Git标签
- [ ] 发布GitHub Release
- [ ] 发布到PyPI（如果适用）

---

## 获取帮助

### 文档

- [README.md](README.md) - 项目概述
- [ARCHITECTURE.md](ARCHITECTURE.md) - 系统架构
- [DEVELOPMENT.md](DEVELOPMENT.md) - 开发指南
- [TESTING.md](TESTING.md) - 测试文档

### 联系方式

- **GitHub Issues** - Bug报告和功能请求
- **GitHub Discussions** - 提问和讨论
- **Email** - maintainer@example.com（如果有）

---

## 致谢

感谢所有贡献者！你们的贡献让这个项目变得更好。

### 贡献者列表

查看 [Contributors](https://github.com/your-org/agent-chat-hub/graphs/contributors) 页面。

---

## 许可证

通过贡献代码，你同意你的贡献将按照项目的许可证进行许可。

---

**文档版本**：v1.0  
**最后更新**：2026-07-26  
**维护者**：Agent Chat Hub Team
