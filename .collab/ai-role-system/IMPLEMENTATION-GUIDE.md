# AI角色系统实施指南

**版本**: v1.0  
**目标用户**: 系统集成者、AI工程师  
**更新时间**: 2026-07-23

---

## 一、系统架构

### 1.1 核心设计理念

**角色定义与模型解耦**：角色描述"要完成什么、遵循什么标准、交付什么"；模型适配描述"由哪个模型、使用哪些工具、以什么参数执行"。

### 1.2 三层架构

```
┌─────────────────────────────────────┐
│  应用层：任务编排和结果汇总          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  角色层：核心角色定义（6个角色）     │
│  - mission/scope/workflow           │
│  - 与模型无关的纯角色契约            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  适配器层：模型特定配置              │
│  - Claude/Codex/Gemini适配器        │
│  - tools/capabilities/policies       │
└─────────────────────────────────────┘
```

---

## 二、快速集成

### 2.1 加载角色配置

```python
import yaml
from pathlib import Path

def load_role(role_id: str):
    """加载角色配置"""
    role_path = Path(f"roles/{role_id}.yaml")
    with open(role_path) as f:
        return yaml.safe_load(f)

# 示例：加载代码审查员
reviewer = load_role("reviewer")
print(reviewer['role']['mission'])
```

### 2.2 选择模型适配器

```python
def get_model_adapter(role_id: str, model_family: str):
    """获取角色的模型适配器"""
    routing = yaml.safe_load(open("model-config/routing-matrix.yaml"))
    role_config = routing['routing_matrix'][role_id]
    
    # 获取primary或fallback模型
    model = role_config['primary']['model']
    adapter_path = f"prompts/adapters/{model_family}-adapter.yaml"
    
    return yaml.safe_load(open(adapter_path))
```

### 2.3 应用原子规则

```python
def load_rules_for_scope(scope: str):
    """加载指定范围的规则"""
    rules_files = Path("rules").glob("*.yaml")
    applicable_rules = []
    
    for file in rules_files:
        rules = yaml.safe_load(open(file))
        for rule in rules:
            if rule['scope'] == scope or rule['scope'] == 'all':
                applicable_rules.append(rule)
    
    return applicable_rules
```

---


## 三、角色使用指南

### 3.1 代码审查员（Reviewer）

**典型使用场景**：
- PR代码审查
- 安全漏洞扫描
- 架构合规检查

**输入准备**：
```python
review_inputs = {
    "task_description": "审查用户登录功能的实现",
    "acceptance_criteria": ["密码加密", "SQL注入防护", "会话管理"],
    "git_diff": diff_content,
    "repository_rules": load_rules_for_scope("backend")
}
```

**输出解析**：
```python
review_result = execute_role("reviewer", review_inputs)
# 期望输出格式：
# {
#   "decision": "APPROVE" | "REJECT" | "NEEDS_CHANGES",
#   "blocking_issues": [...],
#   "suggestions": [...],
#   "evidence": {...}
# }
```

---

### 3.2 实现工程师（Developer）

**典型使用场景**：
- 功能开发
- Bug修复
- 代码重构

**推荐模型**：gpt-5.3-codex（编程专用）

**关键约束**：
- 只修改必要文件
- 修改后运行测试
- 不跳过失败的测试

---

### 3.3 架构师（Architect）

**典型使用场景**：
- 技术方案选型
- 模块划分设计
- ADR（架构决策记录）编写

**推荐模型**：claude-opus-4-8（深度推理）

**输出包含**：
- 至少2个备选方案
- 权衡分析（pros/cons）
- 明确推荐和理由

---

## 四、模型路由策略

### 4.1 动态路由决策

```python
def select_model(role_id: str, task_context: dict):
    """动态选择模型"""
    routing = load_routing_matrix()
    role_routing = routing[role_id]
    
    # 检查fallback触发条件
    for trigger in role_routing['fallback']['triggers']:
        if evaluate_trigger(trigger, task_context):
            return role_routing['fallback']['model']
    
    # 使用primary模型
    return role_routing['primary']['model']

def evaluate_trigger(trigger: dict, context: dict):
    """评估触发条件"""
    metric_value = context.get(trigger['condition']['metric'])
    threshold = trigger['condition']['threshold']
    operator = trigger['condition']['operator']
    
    if operator == ">":
        return metric_value > threshold
    elif operator == "<":
        return metric_value < threshold
    # ... 其他运算符
```

### 4.2 成本控制

```python
class CostController:
    def __init__(self, daily_budget: float):
        self.daily_budget = daily_budget
        self.daily_spent = 0.0
    
    def check_budget(self, estimated_cost: float) -> bool:
        """检查是否在预算内"""
        return (self.daily_spent + estimated_cost) <= self.daily_budget
    
    def should_fallback(self) -> bool:
        """是否应该切换到更便宜的模型"""
        return self.daily_spent > (self.daily_budget * 0.8)
```

---

