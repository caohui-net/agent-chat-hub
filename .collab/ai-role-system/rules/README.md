# 原子规则库

## 概述

本目录包含可执行、可验证的工程规则，用于指导AI角色的决策和行为。每条规则遵循统一的结构，可独立验证，支持自动化检查。

## 规则文件

| 文件 | 规则数量 | 适用范围 | 说明 |
|------|---------|---------|------|
| `api-compatibility.yaml` | 3 | API设计 | 接口兼容性规则，防止破坏性变更 |
| `database-safety.yaml` | 3 | 数据库 | 数据库变更安全规则，支持零停机部署 |
| `security-checklist.yaml` | 4 | 安全 | 安全检查清单，覆盖权限、日志、输入验证、密钥管理 |
| `test-requirements.yaml` | 3 | 测试 | 测试要求规则，确保关键路径覆盖和测试独立性 |

**总计**: 13条规则

## 规则结构

每条规则遵循 `schemas/rule-schema.json` 定义的结构：

```yaml
- id: CATEGORY-NNN          # 唯一标识符（如 API-001）
  name: 规则名称             # 简短描述
  scope: 适用范围            # api/database/security/testing等
  condition: 触发条件        # 何时应用此规则
  requirement: 具体要求      # 必须满足的条件
  severity: blocking|warning|info  # 严重程度
  verification: 验证方法     # 如何检查是否遵守
  source: 参考文档           # 规则来源或详细说明
  owner: 责任角色            # 执行者（developer/architect等）
  reviewer: 审查角色         # 审查者（reviewer/qa等）
  examples:
    pass:                    # 正确示例
      - case: 场景描述
        code: |
          代码示例
    fail:                    # 错误示例
      - case: 场景描述
        code: |
          代码示例
  tags:                      # 分类标签
    - tag1
    - tag2
```

## 严重程度定义

- **blocking**: 阻塞性问题，必须修复才能继续（如安全漏洞、API破坏性变更）
- **warning**: 警告性问题，强烈建议修复（如性能问题、可维护性问题）
- **info**: 信息性提示，可选优化（如代码风格建议）

## 使用方式

### 1. 角色集成

规则在角色配置中通过 `constraints.rules` 引用：

```yaml
# roles/reviewer.yaml
constraints:
  rules:
    - id: SEC-001
      severity_override: blocking
    - id: API-001
      severity_override: blocking
```

### 2. 编程式加载

```python
import yaml
from pathlib import Path

# 加载所有规则
rules_dir = Path('.collab/ai-role-system/rules')
all_rules = []
for rule_file in rules_dir.glob('*.yaml'):
    with open(rule_file) as f:
        rules = yaml.safe_load(f)
        all_rules.extend(rules)

# 按严重程度筛选
blocking_rules = [r for r in all_rules if r['severity'] == 'blocking']

# 按标签筛选
security_rules = [r for r in all_rules if 'security' in r['tags']]
```

### 3. 自动化验证

```python
def check_rule(rule, code_change):
    """检查代码变更是否符合规则"""
    if rule['id'] == 'API-001':
        # 检查是否删除响应字段
        deleted_fields = extract_deleted_fields(code_change)
        if deleted_fields:
            return {
                'passed': False,
                'rule_id': 'API-001',
                'severity': 'blocking',
                'message': f'不得删除响应字段: {deleted_fields}'
            }
    # ... 其他规则检查逻辑
    return {'passed': True}
```

## 规则分类索引

### API兼容性 (api-compatibility.yaml)
- **API-001**: 不得删除或重命名已有响应字段 (blocking)
- **API-002**: 新增响应字段必须有合理默认值 (blocking)
- **API-003**: HTTP状态码不得随意更改 (warning)

### 数据库安全 (database-safety.yaml)
- **DB-001**: Migration必须支持滚动发布 (blocking)
- **DB-002**: 不在单次事务中重写大表 (blocking)
- **DB-003**: 添加索引前评估锁影响 (warning)

### 安全检查 (security-checklist.yaml)
- **SEC-001**: 所有对象访问必须验证权限 (blocking)
- **SEC-002**: 敏感数据不得记录到日志 (blocking)
- **SEC-003**: 用户输入必须验证和清理 (blocking)
- **SEC-004**: 密码和密钥不得硬编码 (blocking)

### 测试要求 (test-requirements.yaml)
- **TEST-001**: 关键路径必须有自动化测试 (blocking)
- **TEST-002**: 边界条件和异常必须有负向测试 (blocking)
- **TEST-003**: 测试必须独立且可重复执行 (blocking)

## 扩展规则库

### 添加新规则

1. 选择合适的规则文件（或创建新文件）
2. 按照规则结构添加新条目
3. 确保ID遵循命名规范（`CATEGORY-NNN`）
4. 提供至少1个pass示例和1个fail示例
5. 运行schema验证：
   ```bash
   python scripts/validate-rules.py
   ```

### 创建新规则类别

1. 创建新的YAML文件（如 `performance-optimization.yaml`）
2. 定义类别前缀（如 `PERF-`）
3. 更新本README的分类索引
4. 在相关角色配置中引用新规则

## 规则设计原则

1. **可执行**: 规则必须可通过代码或工具验证
2. **明确**: 条件和要求必须清晰无歧义
3. **有例可循**: 必须提供正确和错误示例
4. **可追溯**: 必须说明规则来源和验证方法
5. **适度严格**: blocking级别仅用于真正的阻塞性问题

## 维护指南

- **定期审查**: 每季度审查规则有效性
- **版本控制**: 规则变更需要说明理由
- **反馈循环**: 收集执行反馈优化规则定义
- **文档同步**: 更新规则后同步更新本README

## 参考文档

- 规则Schema定义: `../schemas/rule-schema.json`
- 实施指南: `../IMPLEMENTATION-GUIDE.md`
- 角色配置示例: `../roles/*.yaml`
