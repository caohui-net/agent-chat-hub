# 使用示例和工具

本目录包含AI角色系统的使用示例和辅助工具，帮助您快速上手并验证配置。

## 📁 文件列表

| 文件 | 说明 | 用途 |
|------|------|------|
| `load_role_example.py` | 配置加载示例 | 演示如何加载角色、规则和模型配置 |
| `rule_checker.py` | 规则检查器 | 自动检查代码是否违反安全规则 |
| `validate_config.py` | 配置验证器 | 验证YAML文件格式和Schema |

---

## 🚀 快速开始

### 安装依赖

```bash
pip install pyyaml
pip install jsonschema  # 可选，用于Schema验证
```

### 运行示例

```bash
# 1. 配置加载示例
python examples/load_role_example.py

# 2. 规则检查器
python examples/rule_checker.py

# 3. 配置验证器
python examples/validate_config.py
```

---

## 📖 详细说明

### 1. load_role_example.py - 配置加载示例

**功能**:
- 加载所有角色配置
- 查看角色详情和推荐模型
- 获取角色应用的规则列表
- 对比不同角色的配置

**使用方法**:

```python
from load_role_example import AIRoleSystem

# 初始化系统
system = AIRoleSystem()

# 获取角色信息
info = system.get_role_info('reviewer')
print(f"角色: {info['name']}")
print(f"职责: {info['mission']}")

# 获取推荐模型
model_id = system.get_recommended_model('reviewer')
print(f"推荐模型: {model_id}")

# 获取应用的规则
rules = system.get_rules_for_role('reviewer')
for rule in rules:
    print(f"{rule['id']}: {rule['name']}")
```

**输出示例**:
```
📂 正在从 .collab/ai-role-system 加载配置...

  ✓ 加载了 6 个角色
  ✓ 加载了 13 条规则
  ✓ 加载了模型路由配置

✅ 配置加载完成

📋 可用角色:
  • Requirements Analyst (analyst)
    职责: 澄清需求歧义，识别边界条件，制定可验证的验收标准...
  • Software Architect (architect)
    职责: 设计模块划分、接口定义、数据流，并进行技术方案权衡...
  ...
```

---

### 2. rule_checker.py - 规则检查器

**功能**:
- 自动检查代码是否违反SEC-001到SEC-004规则
- 支持单个代码片段检查
- 支持批量文件检查

**支持的规则**:
- **SEC-001**: 所有对象访问必须验证权限
- **SEC-002**: 敏感数据不得记录到日志
- **SEC-003**: 用户输入必须验证和清理
- **SEC-004**: 密码和密钥不得硬编码

**使用方法**:

```python
from rule_checker import RuleChecker

# 初始化检查器
checker = RuleChecker()

# 检查代码片段
code = """
async function getDocument(documentId) {
    const doc = await db.query('SELECT * FROM documents WHERE id = ?', [documentId]);
    return doc;
}
"""

violations = checker.check_code(code, ['SEC-001'])
for v in violations:
    print(f"❌ {v['rule_id']}: {v['message']}")

# 检查文件
violations = checker.check_file('src/api/auth.js')
```

**检测模式**:

| 规则 | 检测模式 | 示例 |
|------|---------|------|
| SEC-001 | 查询缺少user_id/tenant_id过滤 | `SELECT * FROM documents WHERE id=?` |
| SEC-002 | 日志包含password/token | `logger.error('Login failed', {password})` |
| SEC-003 | SQL字符串拼接 | `SELECT * FROM users WHERE email='${email}'` |
| SEC-004 | 硬编码密钥 | `const apiKey = 'sk-1234567890'` |

**输出示例**:
```
【测试1】SEC-001: 权限验证检查
------------------------------------------------------------
代码:
    async function getDocument(documentId) {
        const doc = await db.query('SELECT * FROM documents WHERE id = ?', [documentId]);
        return doc;
    }

❌ SEC-001: 查询语句可能缺少权限验证（未找到user_id/tenant_id过滤）
```

---

### 3. validate_config.py - 配置验证器

**功能**:
- 验证YAML文件语法
- 验证角色配置是否符合role-schema.json
- 验证规则定义是否符合rule-schema.json
- 批量验证所有配置文件

**使用方法**:

```python
from validate_config import ConfigValidator

# 初始化验证器
validator = ConfigValidator()

# 验证单个角色配置
valid, errors = validator.validate_role_config(
    Path('roles/reviewer.yaml')
)
if not valid:
    for error in errors:
        print(f"错误: {error}")

# 验证所有角色
role_results = validator.validate_all_roles()

# 验证所有规则
rule_results = validator.validate_all_rules()
```

**验证项**:
- ✅ YAML语法正确性
- ✅ 必需字段完整性
- ✅ 字段类型正确性
- ✅ 规则ID格式（CATEGORY-NNN）
- ✅ Severity枚举值有效性
- ✅ JSON Schema验证（需要jsonschema库）

**输出示例**:
```
角色配置验证结果
============================================================
✅ analyst.yaml
✅ architect.yaml
✅ developer.yaml
✅ devops.yaml
✅ qa.yaml
✅ reviewer.yaml
------------------------------------------------------------
总计: 6/6 个文件通过验证

规则文件验证结果
============================================================
✅ api-compatibility.yaml
✅ database-safety.yaml
✅ security-checklist.yaml
✅ test-requirements.yaml
------------------------------------------------------------
总计: 4/4 个文件通过验证

============================================================
✅ 所有配置文件验证通过
============================================================
```

---

## 🔧 集成到项目

### 在Python项目中使用

```python
# 1. 复制examples目录到你的项目
cp -r .collab/ai-role-system/examples ./my_project/

# 2. 在代码中导入
from examples.load_role_example import AIRoleSystem

system = AIRoleSystem(base_path='.collab/ai-role-system')
```

### 在CI/CD中使用

```yaml
# .github/workflows/validate.yml
name: Validate AI Role Configs

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      
      - name: Install dependencies
        run: |
          pip install pyyaml jsonschema
      
      - name: Validate configs
        run: |
          python .collab/ai-role-system/examples/validate_config.py
```

---

## 💡 使用技巧

### 1. 自定义规则检查

扩展`rule_checker.py`添加自定义规则：

```python
class RuleChecker:
    def _check_custom_001(self, code: str, rule: Dict) -> str:
        """自定义规则检查"""
        if 'TODO' in code:
            return "代码包含TODO注释，需要清理"
        return None
```

### 2. 生成配置报告

```python
system = AIRoleSystem()

# 生成角色报告
for role_id in system.list_roles():
    info = system.get_role_info(role_id)
    model = system.get_recommended_model(role_id)
    rules = system.get_rules_for_role(role_id)
    
    print(f"## {info['name']}")
    print(f"- 推荐模型: {model}")
    print(f"- 应用规则: {len(rules)}条")
```

### 3. 批量检查项目代码

```python
from pathlib import Path
checker = RuleChecker()

# 检查所有JavaScript文件
for js_file in Path('src').rglob('*.js'):
    violations = checker.check_file(str(js_file))
    if violations:
        print(f"\n{js_file}:")
        for v in violations:
            print(f"  {v['rule_id']}: {v['message']}")
```

---

## 📋 依赖说明

### 必需依赖

```
pyyaml>=6.0      # YAML文件解析
```

### 可选依赖

```
jsonschema>=4.0  # JSON Schema验证（强烈推荐）
```

安装命令：

```bash
# 最小安装
pip install pyyaml

# 完整安装（推荐）
pip install pyyaml jsonschema
```

---

## 🐛 故障排查

### 问题1: 找不到配置文件

**错误**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'roles/analyst.yaml'
```

**解决方法**:
```python
# 显式指定base_path
system = AIRoleSystem(base_path='/path/to/.collab/ai-role-system')
```

---

### 问题2: jsonschema未安装

**警告**:
```
⚠️  警告: jsonschema库未安装，将跳过Schema验证
```

**解决方法**:
```bash
pip install jsonschema
```

---

### 问题3: YAML编码错误

**错误**:
```
UnicodeDecodeError: 'utf-8' codec can't decode...
```

**解决方法**:
确保所有YAML文件使用UTF-8编码保存。

---

## 📚 相关文档

- [主README](../README.md) - 系统概述
- [快速开始指南](../QUICKSTART.md) - 15分钟上手
- [实施指南](../IMPLEMENTATION-GUIDE.md) - 详细集成说明
- [规则库说明](../rules/README.md) - 13条原子规则详解

---

## 🤝 贡献

欢迎提交更多使用示例和工具脚本！

**建议的扩展**:
- 更多规则检查器（API-001, DB-001等）
- 交互式CLI工具
- 配置文件生成器
- 测试用例生成器

---

**版本**: v1.0.0  
**最后更新**: 2026-07-23
