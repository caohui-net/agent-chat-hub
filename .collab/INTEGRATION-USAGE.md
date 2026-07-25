# AI角色系统集成使用指南

**版本**: v1.0  
**日期**: 2026-07-25  
**状态**: 集成框架已完成

---

## 概述

本指南说明如何在agent-chat-hub中使用AI角色系统创建和管理Agent。

## 快速开始

### 1. 创建基于角色的Agent

```python
from src.core.models import AgentConfig
from src.core.role_integration import load_role_config

# 创建基于标准角色的Agent
developer_config = load_role_config('developer')

agent = AgentConfig(
    agent_id="dev-001",
    name="Python开发工程师",
    role="实现工程师",
    role_type="developer",  # 指定角色类型
    role_config=developer_config,  # 加载的角色配置
    model_id="claude-opus-4.8",
    priority=100
)
```

### 2. 可用的标准角色

- `analyst` - 需求分析师
- `architect` - 软件架构师
- `developer` - 实现工程师
- `reviewer` - 代码审查员
- `qa` - QA工程师
- `devops` - DevOps工程师

### 3. 使用规则检查

```python
from src.agents.rule_checker import RuleChecker

checker = RuleChecker()

# 检查agent选择是否违反规则
violations = checker.check_agent_selection(
    session_id="session-123",
    selected_agents=["dev-001", "reviewer-001"],
    context={"operation": "code_review"}
)

if violations:
    print(f"规则违规: {violations}")
```

## 集成组件

### 已完成
- ✅ AgentConfig扩展（支持role_type和role_config）
- ✅ role_integration.py（角色配置加载）
- ✅ rule_checker.py（规则检查封装）

### 待实施
- ⏳ ResponseCoordinator集成（在select_agents中使用RuleChecker）
- ⏳ Executor集成（智能模型路由）

## 后续步骤

1. 修改ResponseCoordinator使用RuleChecker
2. 修改Executor使用ModelRouter
3. 创建集成测试
4. 更新配置管理

---

**参考文档**:
- `.collab/INTEGRATION-PLAN.md` - 详细集成方案
- `.collab/ai-role-system/USAGE-GUIDE.md` - 角色系统使用指南
