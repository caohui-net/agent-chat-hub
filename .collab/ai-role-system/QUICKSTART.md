# 快速开始指南

**版本**: v1.0.0  
**适用对象**: 开发者、集成工程师  
**预计时间**: 15分钟

---

## 前置要求

- Python 3.8+
- YAML处理库 (`pip install pyyaml`)
- 访问AI模型API (Claude/OpenAI/Gemini)

---

## 5分钟快速体验

### 步骤1: 加载角色配置

```python
import yaml
from pathlib import Path

# 加载代码审查员角色
role_file = Path('.collab/ai-role-system/roles/reviewer.yaml')
with open(role_file) as f:
    reviewer = yaml.safe_load(f)

print(f"角色: {reviewer['role']['name']}")
print(f"职责: {reviewer['role']['mission']}")
```

**预期输出**:
```
角色: Code Reviewer
职责: 识别代码变更中的正确性、安全性、兼容性和可维护性问题
```

---

### 步骤2: 查看输出契约

```python
# 获取输出格式
output_contract = reviewer['output_contract']
print(f"格式: {output_contract['format']}")
print(f"字段: {list(output_contract['schema']['properties'].keys())}")
```

**预期输出**:
```
格式: json
字段: ['decision', 'blocking_issues', 'suggestions', 'test_gaps', 'evidence']
```

---

### 步骤3: 应用安全规则

```python
# 加载安全检查规则
rules_file = Path('.collab/ai-role-system/rules/security-checklist.yaml')
with open(rules_file) as f:
    security_rules = yaml.safe_load(f)

# 显示第一条规则
rule = security_rules[0]
print(f"规则ID: {rule['id']}")
print(f"名称: {rule['name']}")
print(f"严重程度: {rule['severity']}")
```

**预期输出**:
```
规则ID: SEC-001
名称: 所有对象访问必须验证权限
严重程度: blocking
```

---

### 步骤4: 选择模型

```python
# 加载模型路由配置
routing_file = Path('.collab/ai-role-system/model-config/routing-matrix.yaml')
with open(routing_file) as f:
    routing = yaml.safe_load(f)

# 获取reviewer的推荐模型
reviewer_routing = routing['routing_matrix']['reviewer']
primary_model = reviewer_routing['primary']
print(f"推荐模型: {primary_model['model']}")
print(f"原因: {primary_model['reason']}")
print(f"成本级别: {primary_model['cost']}")
```

**预期输出**:
```
推荐模型: claude-sonnet-5
原因: 平衡推理能力和成本，适合标准代码审查
成本级别: medium
```

---

## 完整集成示例

### 场景: 代码审查流程

```python
import yaml
import json
from pathlib import Path

class AIRoleSystem:
    def __init__(self, base_path='.collab/ai-role-system'):
        self.base_path = Path(base_path)
        self.roles = {}
        self.rules = {}
        self.routing = None
        self._load_config()
    
    def _load_config(self):
        """加载所有配置"""
        # 加载角色
        for role_file in (self.base_path / 'roles').glob('*.yaml'):
            with open(role_file) as f:
                config = yaml.safe_load(f)
                role_id = role_file.stem
                self.roles[role_id] = config
        
        # 加载规则
        for rule_file in (self.base_path / 'rules').glob('*.yaml'):
            if rule_file.name == 'README.md':
                continue
            with open(rule_file) as f:
                rules = yaml.safe_load(f)
                for rule in rules:
                    self.rules[rule['id']] = rule
        
        # 加载路由
        with open(self.base_path / 'model-config/routing-matrix.yaml') as f:
            self.routing = yaml.safe_load(f)
    
    def get_role(self, role_id):
        """获取角色配置"""
        return self.roles.get(role_id)
    
    def get_model_for_role(self, role_id):
        """获取角色推荐模型"""
        routing = self.routing['routing_matrix'].get(role_id)
        if routing:
            return routing['primary']['model']
        return None
    
    def get_rules_for_role(self, role_id):
        """获取角色应用的规则"""
        role = self.get_role(role_id)
        if not role or 'constraints' not in role:
            return []
        
        rule_ids = [r['id'] for r in role['constraints'].get('rules', [])]
        return [self.rules[rid] for rid in rule_ids if rid in self.rules]
    
    def build_prompt(self, role_id, user_input):
        """构建完整prompt"""
        role = self.get_role(role_id)
        rules = self.get_rules_for_role(role_id)
        
        # 简化的prompt构建
        prompt = f"""# 角色: {role['role']['name']}

## 职责
{role['role']['mission']}

## 输入
{json.dumps(user_input, indent=2, ensure_ascii=False)}

## 应用规则
"""
        for rule in rules:
            prompt += f"\n### {rule['id']}: {rule['name']}\n"
            prompt += f"- 要求: {rule['requirement']}\n"
            prompt += f"- 严重程度: {rule['severity']}\n"
        
        prompt += f"\n## 输出格式\n{role['output_contract']['format']}\n"
        prompt += f"\n请严格按照以上要求完成任务。\n"
        
        return prompt

# 使用示例
system = AIRoleSystem()

# 场景: 代码审查
code_change = {
    "file": "src/api/user.js",
    "diff": """
- const user = db.query(`SELECT * FROM users WHERE id=${userId}`);
+ const user = db.query('SELECT * FROM users WHERE id=?', [userId]);
"""
}

# 构建审查prompt
prompt = system.build_prompt('reviewer', code_change)
print("=== 生成的Prompt ===")
print(prompt[:500] + "...\n")

# 获取推荐模型
model = system.get_model_for_role('reviewer')
print(f"推荐使用模型: {model}")

# 获取应用的规则
rules = system.get_rules_for_role('reviewer')
print(f"应用规则数量: {len(rules)}")
for rule in rules[:3]:
    print(f"  - {rule['id']}: {rule['name']}")
```

**预期输出**:
```
=== 生成的Prompt ===
# 角色: Code Reviewer

## 职责
识别代码变更中的正确性、安全性、兼容性和可维护性问题

## 输入
{
  "file": "src/api/user.js",
  "diff": "\n- const user = db.query(`SELECT * FROM users WHERE id=${userId}`);\n+ const user = db.query('SELECT * FROM users WHERE id=?', [userId]);\n"
}

## 应用规则
...

推荐使用模型: claude-sonnet-5
应用规则数量: 6
  - API-001: 不得删除或重命名已有响应字段
  - SEC-001: 所有对象访问必须验证权限
  - SEC-003: 用户输入必须验证和清理
```

---

## 使用场景

### 场景1: 需求澄清

```python
system = AIRoleSystem()

# 用户提出模糊需求
user_requirement = {
    "requirement": "系统需要更快",
    "context": "订单处理系统，当前5秒"
}

# 使用需求分析师
prompt = system.build_prompt('analyst', user_requirement)
model = system.get_model_for_role('analyst')

# 调用AI模型 (伪代码)
# response = call_ai_model(model, prompt)
# clarified = json.loads(response)

print(f"使用 {model} 进行需求分析")
```

---

### 场景2: 架构设计

```python
# 架构决策场景
design_request = {
    "problem": "需要支持10万在线用户的实时消息推送",
    "constraints": {
        "budget": "medium",
        "team_skill": ["Node.js", "Python"],
        "timeline": "2个月"
    }
}

prompt = system.build_prompt('architect', design_request)
model = system.get_model_for_role('architect')

print(f"使用 {model} 进行架构设计")
# 预期: claude-opus-4.8 (最高推理深度)
```

---

### 场景3: 代码实现

```python
# 功能实现场景
dev_task = {
    "requirements": [
        "用户可以通过邮箱和密码注册",
        "密码必须加密存储",
        "登录成功返回JWT token"
    ],
    "tech_stack": {
        "language": "Node.js",
        "framework": "Express",
        "libraries": ["bcrypt", "jsonwebtoken"]
    }
}

prompt = system.build_prompt('developer', dev_task)
model = system.get_model_for_role('developer')

print(f"使用 {model} 进行代码实现")
# 预期: gpt-5.3-codex (代码生成能力最强，成本最低)
```

---

## 测试验证

### 运行测试任务

```python
# 加载测试定义
test_file = Path('.collab/ai-role-system/test-suite/task-definitions.yaml')
with open(test_file) as f:
    test_suite = yaml.safe_load(f)

# 获取analyst的P0测试任务
analyst_tasks = test_suite['test_tasks']['analyst_tasks']
p0_tasks = [t for t in analyst_tasks if t['priority'] == 'P0']

print(f"Analyst P0测试任务数量: {len(p0_tasks)}")
for task in p0_tasks:
    print(f"  - {task['id']}: {task['name']}")
```

---

## 常见问题

### Q1: 如何切换模型？

**A**: 修改`model-config/routing-matrix.yaml`中的primary模型：

```yaml
reviewer:
  primary:
    model: claude-opus-4.8  # 从sonnet切换到opus
    reason: 需要更高推理深度
```

---

### Q2: 如何添加自定义规则？

**A**: 在`rules/`目录创建新YAML文件：

```yaml
- id: CUSTOM-001
  name: 自定义规则名称
  scope: 适用范围
  condition: 触发条件
  requirement: 具体要求
  severity: blocking
  verification: 验证方法
  examples:
    pass: [...]
    fail: [...]
```

---

### Q3: 如何处理成本控制？

**A**: 配置`model-config/cost-thresholds.yaml`：

```yaml
daily_budget:
  default_limit: 50.00  # 降低每日预算
  warning_threshold: 0.6  # 60%时警告
```

---

### Q4: 输出格式不符合预期怎么办？

**A**: 检查输出是否符合schema：

```python
import jsonschema

# 加载schema
role = system.get_role('reviewer')
schema = role['output_contract']['schema']

# 验证输出
output = {"decision": "APPROVE", ...}
try:
    jsonschema.validate(output, schema)
    print("输出格式正确")
except jsonschema.ValidationError as e:
    print(f"格式错误: {e.message}")
```

---

## 下一步

1. **深入学习**: 阅读 [IMPLEMENTATION-GUIDE.md](IMPLEMENTATION-GUIDE.md)
2. **查看示例**: 浏览 `prompts/examples/` 目录
3. **运行测试**: 执行测试框架验证集成
4. **定制配置**: 根据项目需求调整角色和规则

---

## 获取帮助

- **文档**: [README.md](README.md)
- **规则库**: [rules/README.md](rules/README.md)
- **测试用例**: [test-suite/test-cases/README.md](test-suite/test-cases/README.md)
- **问题反馈**: 提交到项目Issue跟踪

---

**版本**: v1.0.0  
**最后更新**: 2026-07-23
