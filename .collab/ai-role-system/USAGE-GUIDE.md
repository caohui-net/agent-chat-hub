# AI角色系统 - 使用指南

## 📖 概述

AI角色系统是一个生产就绪的角色-模型解耦框架，支持6个核心角色、13条原子规则、4个AI模型的智能协同。

**版本**: v2.0.0  
**状态**: ✅ 生产就绪

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pyyaml jsonschema
```

### 2. 设置项目路径

```python
import sys
from pathlib import Path

# 设置AI角色系统路径
project_root = Path('.collab/ai-role-system')
sys.path.insert(0, str(project_root))
```

### 3. 导入核心组件

```python
from core.role_loader import RoleLoader
from core.rule_engine import RuleEngine
from core.model_router import ModelRouter, TaskComplexity
```

---

## 📚 核心功能

### 功能1：角色加载

**加载单个角色**
```python
loader = RoleLoader()
developer = loader.load_role('developer')

print(developer['role']['name'])      # Implementation Engineer
print(developer['role']['mission'])   # 职责说明
print(developer['output_contract'])   # 输出契约
```

**加载所有角色**
```python
all_roles = loader.load_all_roles()
# 返回: {'analyst': {...}, 'architect': {...}, 'developer': {...}, ...}

for role_id, config in all_roles.items():
    print(f"{role_id}: {config['role']['name']}")
```

**获取角色信息**
```python
info = loader.get_role_info('reviewer')
# 返回: {'id': 'reviewer', 'name': 'Code Reviewer', ...}
```

---

### 功能2：规则引擎

**加载所有规则**
```python
engine = RuleEngine()
rules = engine.load_rules()
print(f"总规则数: {len(rules)}")  # 13
```

**按作用域过滤**
```python
# 只加载后端相关规则
backend_rules = engine.load_rules(scope='backend')

# 只加载前端相关规则
frontend_rules = engine.load_rules(scope='frontend')
```

**按严重级别过滤**
```python
# 获取所有blocking级别规则
blocking_rules = engine.get_rules_by_severity('blocking')
print(f"Blocking规则数: {len(blocking_rules)}")  # 11
```

**获取规则统计**
```python
summary = engine.get_rules_summary()
# 返回: {'total': 13, 'blocking': 11, 'warning': 2, 'info': 0}
```

**检查规则违规**
```python
violations = engine.check_blocking_rules(
    scope='backend',
    context={'operation': 'database_migration'}
)

for violation in violations:
    print(f"🚫 {violation.rule_name}: {violation.message}")
```

---

### 功能3：智能模型路由

**基础路由**
```python
router = ModelRouter()

decision = router.route(
    task_type='code_review',
    complexity=TaskComplexity.SIMPLE
)

print(f"模型: {decision.selected_model}")
print(f"成本: ${decision.estimated_cost:.4f}")
print(f"原因: {decision.reason}")
```

**带约束的路由**
```python
# 限制上下文大小
decision = router.route(
    task_type='implementation',
    complexity=TaskComplexity.MEDIUM,
    context_size=50000  # 50K tokens
)

# 限制成本预算
decision = router.route(
    task_type='architecture',
    complexity=TaskComplexity.COMPLEX,
    cost_budget=0.05  # $0.05
)
```

**获取模型信息**
```python
model_info = router.get_model_info('claude-opus-4.8')
print(f"厂商: {model_info.vendor}")
print(f"层级: {model_info.tier}")
print(f"上下文窗口: {model_info.context_window}")
```

**列出所有模型**
```python
models = router.list_models()
# 返回: ['claude-opus-4.8', 'claude-sonnet-5', 'gpt-5.3-codex', 'gemini-3.1-pro']
```

---

## 🎯 实际使用场景

### 场景1：代码审查工作流

```python
from core.role_loader import RoleLoader
from core.rule_engine import RuleEngine
from core.model_router import ModelRouter, TaskComplexity

# 1. 加载审查员角色
loader = RoleLoader()
reviewer = loader.load_role('reviewer')

# 2. 获取相关规则
engine = RuleEngine()
code_rules = engine.load_rules(scope='backend')

# 3. 选择合适模型
router = ModelRouter()
decision = router.route(
    task_type='code_review',
    complexity=TaskComplexity.MEDIUM,
    context_size=30000
)

print(f"使用 {decision.selected_model} 进行代码审查")
print(f"需要检查 {len(code_rules)} 条规则")
```

### 场景2：多角色协同

```python
# 需求分析 → 架构设计 → 实现 → 审查 → 测试 → 部署
workflow = ['analyst', 'architect', 'developer', 'reviewer', 'qa', 'devops']

loader = RoleLoader()
router = ModelRouter()

for role_id in workflow:
    role = loader.load_role(role_id)
    
    # 根据角色确定任务复杂度
    complexity = TaskComplexity.COMPLEX if role_id == 'architect' else TaskComplexity.MEDIUM
    
    decision = router.route(
        task_type=role['role']['focus_area'],
        complexity=complexity
    )
    
    print(f"{role['role']['name']}: {decision.selected_model}")
```

### 场景3：成本优化

```python
router = ModelRouter()

# 批量任务，控制总成本
tasks = [
    ('code_review', TaskComplexity.SIMPLE),
    ('implementation', TaskComplexity.MEDIUM),
    ('testing', TaskComplexity.SIMPLE),
]

total_cost = 0
for task_type, complexity in tasks:
    decision = router.route(task_type, complexity, cost_budget=0.02)
    total_cost += decision.estimated_cost
    print(f"{task_type}: {decision.selected_model} (${decision.estimated_cost:.4f})")

print(f"\n总成本: ${total_cost:.4f}")
```

---

## 🧪 运行测试

### 运行单元测试

```bash
# 测试角色加载器
python3 tests/test_role_loader.py

# 测试规则引擎
python3 tests/test_rule_engine.py

# 测试模型路由器
python3 tests/test_model_router.py
```

### 运行端到端测试

```bash
# 执行完整测试套件（18个任务）
python3 integration/run_full_test.py

# 查看测试报告
ls -lh reports/test_reports/
ls -lh reports/evaluation_reports/
```

---

## 📂 项目结构

```
.collab/ai-role-system/
├── core/                    # 核心组件
│   ├── role_loader.py      # 角色加载器
│   ├── rule_engine.py      # 规则引擎
│   └── model_router.py     # 模型路由器
│
├── integration/             # 集成层
│   ├── test_runner.py      # 测试执行器
│   ├── evaluator.py        # 评估器
│   └── run_full_test.py    # 端到端测试
│
├── tests/                   # 单元测试
│   ├── test_role_loader.py
│   ├── test_rule_engine.py
│   └── test_model_router.py
│
├── roles/                   # 6个角色配置
├── rules/                   # 13条原子规则
├── model-config/            # 模型配置
├── test-suite/              # 测试框架
└── examples/                # 使用示例
```

---

## 📖 进阶文档

- **完整文档**: [README.md](README.md)
- **实施指南**: [IMPLEMENTATION-GUIDE.md](IMPLEMENTATION-GUIDE.md)
- **验证报告**: [PHASE2-VERIFICATION-REPORT.md](PHASE2-VERIFICATION-REPORT.md)
- **完成报告**: [PROJECT-COMPLETION-REPORT.md](PROJECT-COMPLETION-REPORT.md)

---

## ❓ 常见问题

**Q: 如何添加新角色？**
A: 在`roles/`目录下创建新的YAML配置文件，遵循`role-schema.json`

**Q: 如何添加新规则？**
A: 在`rules/`目录下对应文件添加规则，遵循`rule-schema.json`

**Q: 如何添加新模型？**
A: 在`model-config/capability-profiles.yaml`添加模型配置

**Q: 成本预估准确吗？**
A: 基于官方定价计算，实际成本可能因API版本和优惠而有差异

---

**版本**: v2.0.0  
**更新日期**: 2026-07-25  
**许可**: 项目内部使用
