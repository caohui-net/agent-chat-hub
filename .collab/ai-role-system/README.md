# AI软件工程角色系统

**版本**: v1.0.0 (Phase 1 MVP)  
**状态**: ✅ Phase 1 已完成  
**创建时间**: 2026-07-23  
**完成时间**: 2026-07-23

---

## 概述

这是一个基于角色的AI软件工程协作系统，实现了**角色定义与模型解耦**的设计理念。通过标准化的角色配置、原子规则库和动态模型路由，支持多AI模型协同完成软件工程任务。

### 核心特性

- **6个核心角色**：需求分析师、软件架构师、实现工程师、代码审查员、QA工程师、DevOps工程师
- **角色-模型分离**：角色定义与模型实现完全解耦，支持灵活切换
- **13条原子规则**：可执行、可验证的工程规则（API兼容性、数据库安全、安全检查、测试要求）
- **动态模型路由**：基于任务复杂度、成本预算和能力匹配的智能模型选择
- **完整测试框架**：18个测试任务、36个评估指标，覆盖所有角色
- **4个AI模型支持**：Claude Opus 4.8、Claude Sonnet 5、GPT-5.3-Codex、Gemini 3.1 Pro

### 设计原则

1. **角色职责单一**：每个角色专注特定领域，避免职责重叠
2. **输出契约标准化**：所有角色输出JSON格式，支持自动化验证
3. **规则可执行**：每条规则有明确的验证方法和示例
4. **成本可控**：模型路由考虑成本因素，支持预算控制
5. **质量可量化**：所有角色有明确的质量指标和阈值

---

## 快速开始

### 1. 目录结构

```
.collab/ai-role-system/
├── README.md                      # 本文件
├── IMPLEMENTATION-GUIDE.md        # 集成使用指南
│
├── roles/                         # 角色配置（6个）
│   ├── analyst.yaml              # 需求分析师
│   ├── architect.yaml            # 软件架构师
│   ├── developer.yaml            # 实现工程师
│   ├── reviewer.yaml             # 代码审查员
│   ├── qa.yaml                   # QA工程师
│   └── devops.yaml               # DevOps工程师
│
├── prompts/                      # Prompt模板系统
│   ├── core-template.yaml        # 核心模板（Mustache）
│   ├── adapters/                 # 模型适配器
│   │   ├── claude-adapter.yaml
│   │   ├── codex-adapter.yaml
│   │   └── gemini-adapter.yaml
│   └── examples/                 # 完整示例
│       ├── reviewer-full-prompt.md
│       └── developer-full-prompt.md
│
├── rules/                        # 原子规则库（13条）
│   ├── README.md
│   ├── api-compatibility.yaml    # API兼容性（3条）
│   ├── database-safety.yaml      # 数据库安全（3条）
│   ├── security-checklist.yaml   # 安全检查（4条）
│   └── test-requirements.yaml    # 测试要求（3条）
│
├── model-config/                 # 模型匹配配置
│   ├── routing-matrix.yaml       # 路由矩阵（角色→模型映射）
│   ├── capability-profiles.yaml  # 能力配置（4个模型）
│   └── cost-thresholds.yaml      # 成本控制配置
│
├── test-suite/                   # 测试框架
│   ├── task-definitions.yaml     # 测试任务定义（18个）
│   ├── evaluation-metrics.yaml   # 评估指标（36个）
│   └── test-cases/               # 测试用例
│       ├── README.md
│       ├── analyst-t001-ambiguity-identification.yaml
│       └── developer-t001-user-authentication.yaml
│
└── schemas/                      # JSON Schema定义
    ├── role-schema.json          # 角色配置schema
    ├── rule-schema.json          # 规则定义schema
    └── output-contract-schema.json
```

### 2. 使用角色配置

```python
import yaml
from pathlib import Path

# 加载角色配置
role_path = Path('.collab/ai-role-system/roles/reviewer.yaml')
with open(role_path) as f:
    reviewer_config = yaml.safe_load(f)

# 获取角色信息
print(f"角色: {reviewer_config['role']['name']}")
print(f"职责: {reviewer_config['role']['mission']}")

# 获取输出契约
output_contract = reviewer_config['output_contract']
print(f"输出格式: {output_contract['format']}")
```

### 3. 应用原子规则

```python
# 加载规则库
rules_dir = Path('.collab/ai-role-system/rules')
security_rules = yaml.safe_load(open(rules_dir / 'security-checklist.yaml'))

# 检查代码是否符合规则
for rule in security_rules:
    if rule['id'] == 'SEC-001':
        print(f"规则: {rule['name']}")
        print(f"要求: {rule['requirement']}")
        print(f"验证: {rule['verification']}")
```

### 4. 模型路由

```python
# 加载路由配置
routing = yaml.safe_load(open('.collab/ai-role-system/model-config/routing-matrix.yaml'))

# 获取角色推荐模型
analyst_routing = routing['routing_matrix']['analyst']
print(f"主模型: {analyst_routing['primary']['model']}")
print(f"原因: {analyst_routing['primary']['reason']}")

# 检查降级触发条件
for fallback in analyst_routing['fallback']:
    print(f"降级到: {fallback['model']}")
    print(f"触发条件: {fallback['triggers']}")
```

---

## 角色详细说明

### 需求分析师 (Requirements Analyst)

**文件**: `roles/analyst.yaml`

**核心职责**:
- 澄清模糊需求，识别歧义
- 制定可验证的验收标准
- 识别边界条件和异常场景

**输出格式**:
```json
{
  "clarified_requirements": [...],
  "acceptance_criteria": [...],
  "boundary_conditions": [...],
  "open_questions": [...]
}
```

**推荐模型**: Claude Sonnet 5 (长上下文理解能力强)

**质量指标**:
- 歧义覆盖率 >90%
- 验收标准可测试性 100%

---

### 软件架构师 (Software Architect)

**文件**: `roles/architect.yaml`

**核心职责**:
- 设计模块划分和接口定义
- 提供至少2个技术方案并权衡
- 识别技术风险和缓解措施

**输出格式**:
```json
{
  "recommended_solution": {...},
  "alternative_solutions": [...],
  "tradeoff_analysis": {...},
  "technical_risks": [...]
}
```

**推荐模型**: Claude Opus 4.8 (推理深度最高)

**质量指标**:
- 至少2个可行方案
- 权衡深度 >85%
- 技术可行性 >90%

---

### 实现工程师 (Implementation Engineer)

**文件**: `roles/developer.yaml`

**核心职责**:
- 按验收标准完成代码实现
- 遵守安全和测试规则
- 最小必要修改原则

**输出格式**:
```json
{
  "changed_files": [...],
  "implementation_summary": "...",
  "verification_results": {...},
  "acceptance_status": {...}
}
```

**推荐模型**: GPT-5.3-Codex (代码生成能力最强，成本最低)

**质量指标**:
- 测试通过率 100%
- 代码覆盖率 >80%
- 安全规则遵守度 100%

---

### 代码审查员 (Code Reviewer)

**文件**: `roles/reviewer.yaml`

**核心职责**:
- 识别正确性、安全性、兼容性问题
- 提供改进建议
- 决策：APPROVE / REJECT / REQUEST_CHANGES

**输出格式**:
```json
{
  "decision": "APPROVE|REJECT|REQUEST_CHANGES",
  "blocking_issues": [...],
  "suggestions": [...],
  "test_gaps": [...],
  "evidence": [...]
}
```

**推荐模型**: Claude Sonnet 5 (平衡推理和成本)

**质量指标**:
- 精确率 >80%
- 召回率 >85%
- 误报率 <10%

---

### QA工程师 (QA Engineer)

**文件**: `roles/qa.yaml`

**核心职责**:
- 设计测试方案和用例
- 覆盖边界和异常路径
- 验证功能正确性

**输出格式**:
```json
{
  "test_plan": {...},
  "test_cases": [...],
  "test_results": {...},
  "defects": [...],
  "coverage_report": {...}
}
```

**推荐模型**: GPT-5.3-Codex (测试生成能力强)

**质量指标**:
- 场景覆盖率 >90%
- 边界用例覆盖率 >85%

---

### DevOps工程师 (DevOps Engineer)

**文件**: `roles/devops.yaml`

**核心职责**:
- 管理CI/CD流水线
- 配置监控和告警
- 制定发布和回滚方案

**输出格式**:
```json
{
  "pipeline_config": {...},
  "deployment_plan": {...},
  "environment_config": {...},
  "monitoring_setup": {...},
  "rollback_plan": {...}
}
```

**推荐模型**: GPT-5.3-Codex (脚本生成能力强)

**质量指标**:
- 流水线完整性 >90%
- 关键指标覆盖率 100%

---

## 原子规则库

**总计**: 13条规则，分4个类别

### API兼容性规则 (api-compatibility.yaml)

- **API-001** (blocking): 不得删除或重命名已有响应字段
- **API-002** (blocking): 新增响应字段必须有合理默认值
- **API-003** (warning): HTTP状态码不得随意更改

### 数据库安全规则 (database-safety.yaml)

- **DB-001** (blocking): Migration必须支持滚动发布
- **DB-002** (blocking): 不在单次事务中重写大表
- **DB-003** (warning): 添加索引前评估锁影响

### 安全检查规则 (security-checklist.yaml)

- **SEC-001** (blocking): 所有对象访问必须验证权限
- **SEC-002** (blocking): 敏感数据不得记录到日志
- **SEC-003** (blocking): 用户输入必须验证和清理
- **SEC-004** (blocking): 密码和密钥不得硬编码

### 测试要求规则 (test-requirements.yaml)

- **TEST-001** (blocking): 关键路径必须有自动化测试
- **TEST-002** (blocking): 边界条件和异常必须有负向测试
- **TEST-003** (blocking): 测试必须独立且可重复执行

**详细文档**: [rules/README.md](rules/README.md)

---

## 模型支持

### 支持的模型

| 模型 | 定价 (输入/输出) | 推理深度 | 代码能力 | 推荐角色 |
|------|-----------------|---------|---------|---------|
| Claude Opus 4.8 | $5/$25 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Architect, Reviewer (关键任务) |
| Claude Sonnet 5 | $3/$15 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Analyst, Reviewer (标准任务) |
| GPT-5.3-Codex | $1.75/$14 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Developer, QA, DevOps |
| Gemini 3.1 Pro | $2.5/$12.5 | ⭐⭐⭐ | ⭐⭐⭐ | Developer (UI任务) |

### 模型路由策略

- **Primary模型**: 根据角色和任务类型选择最佳模型
- **Fallback触发**: 基于成本、复杂度、风险等结构化条件
- **成本控制**: 每日预算、调用限制、降级策略

**详细配置**: [model-config/](model-config/)

---

## 测试框架

### 测试任务覆盖

| 角色 | P0任务 | P1任务 | 总计 |
|------|--------|--------|------|
| Analyst | 2 | 1 | 3 |
| Architect | 2 | 1 | 3 |
| Developer | 2 | 1 | 3 |
| Reviewer | 2 | 1 | 3 |
| QA | 2 | 1 | 3 |
| DevOps | 2 | 1 | 3 |
| **总计** | **12** | **6** | **18** |

### 评估指标体系

- **36个量化指标**：覆盖准确性、质量、效率等维度
- **阈值定义**：每个指标有明确的最低要求和推荐值
- **综合评分**：角色级别和系统级别的综合质量得分

**详细文档**: [test-suite/](test-suite/)

---

## 文档索引

### 核心文档

- [实施指南](IMPLEMENTATION-GUIDE.md) - 集成使用详细说明
- [实施计划](../artifacts/AI角色系统实施计划-Phase1-MVP.md) - Phase 1完整计划
- [验证报告](../artifacts/AI角色系统实施计划-验证报告.md) - 计划可靠性验证
- [前置修复记录](../artifacts/AI角色系统-Day0-前置修复记录.md) - Day 0阻塞问题修复

### 分类文档

- **角色配置**: [roles/](roles/) - 6个角色的完整YAML配置
- **Prompt系统**: [prompts/](prompts/) - 模板和适配器
- **规则库**: [rules/README.md](rules/README.md) - 13条原子规则详解
- **模型配置**: [model-config/](model-config/) - 路由、能力、成本配置
- **测试框架**: [test-suite/test-cases/README.md](test-suite/test-cases/README.md) - 测试用例说明

---

## Phase 1 交付清单

### ✅ 已完成

**Day 0: 前置修复**
- ✅ 结构化fallback trigger格式
- ✅ 测试任务优先级定义

**Day 2-3: 角色配置**
- ✅ 6个角色YAML配置文件
- ✅ 统一的输出契约
- ✅ 完整的约束和完成标准

**Day 4-5: Prompt模板**
- ✅ 核心Mustache模板
- ✅ 3个模型适配器（Claude, Codex, Gemini）
- ✅ 2个完整示例

**Day 6-7: Schema定义**
- ✅ role-schema.json
- ✅ rule-schema.json
- ✅ output-contract-schema.json

**Day 8-9: 原子规则库**
- ✅ 4个规则文件（13条规则）
- ✅ 每条规则有pass/fail示例
- ✅ rules/README.md

**Day 10-11: 模型配置**
- ✅ routing-matrix.yaml（路由矩阵）
- ✅ capability-profiles.yaml（能力配置）
- ✅ cost-thresholds.yaml（成本控制）

**Day 12-13: 测试框架**
- ✅ task-definitions.yaml（18个任务）
- ✅ evaluation-metrics.yaml（36个指标）
- ✅ 2个测试用例示例
- ✅ test-cases/README.md

**Day 14-15: 集成验证**
- ✅ 文档更新和完善
- ✅ Phase 1交付清单

### 📊 统计数据

- **角色数量**: 6
- **规则数量**: 13
- **模型支持**: 4
- **测试任务**: 18
- **评估指标**: 36
- **文档文件**: 25+
- **总代码行数**: ~5000+ (YAML/Markdown)

---

## 下一步计划

### Phase 2: 生产化（预计2周）

- 实现Python集成库
- 开发CLI工具
- 添加日志和监控
- 补全测试用例实现

### Phase 3: 扩展（预计2周）

- 添加更多角色（前端、数据工程等）
- 扩展规则库（50+规则）
- 支持更多模型
- 多语言Prompt支持

---

## 维护

**责任团队**: AI角色系统开发组  
**更新频率**: 按需更新  
**版本策略**: 语义化版本（SemVer）

---

## 许可

内部使用 | © 2026
