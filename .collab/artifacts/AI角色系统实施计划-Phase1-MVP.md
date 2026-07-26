# AI软件工程角色系统实施计划 - Phase 1 MVP

**版本**: v1.0  
**创建时间**: 2026-07-22  
**计划范围**: Phase 1 MVP（Week 1-2）  
**基于文档**: 
- AI软件工程角色系统设计方案-v1.0.md
- AI软件工程角色系统设计方案-v1.0-附录A-2026模型数据.md
- Codex技术反馈（讨论artifact）

---

## 一、Phase 1 MVP 目标

### 1.1 核心目标

**交付物**：
1. 6个核心角色的完整配置（需求分析师、架构师、实现工程师、审查员、测试工程师、DevOps）
2. 标准化Prompt结构模板（核心角色层 + 模型适配器层）
3. 原子规则库基础框架（至少10条示例规则）
4. 模型匹配配置（基于2026年7月数据）
5. 质量验证测试集（至少5个典型任务）
6. 实施文档和使用指南

### 1.2 成功标准

- [ ] 每个角色有明确的mission、scope、inputs、workflow、output_contract
- [ ] 每个角色有Claude/Codex/Gemini三个模型适配器
- [ ] 原子规则包含：id、condition、requirement、severity、verification、source
- [ ] 模型匹配配置包含：primary、fallback、capability_score、cost_threshold
- [ ] 测试集覆盖：功能开发、缺陷修复、安全审查、架构决策、多模态UI
- [ ] 所有配置文件通过YAML/JSON schema验证

### 1.3 不包含范围（Phase 2）

- 扩展角色（安全审查员、数据库工程师等）
- 动态模型路由算法实现
- 成本监控和优化系统
- 持续评测框架
- 生产环境集成

---

## 二、文件结构设计

```
.collab/ai-role-system/
├── README.md                          # 系统概述和快速开始
├── IMPLEMENTATION-GUIDE.md            # 实施指南
├── roles/                             # 角色配置目录
│   ├── analyst.yaml                   # 需求分析师
│   ├── architect.yaml                 # 架构师
│   ├── developer.yaml                 # 实现工程师
│   ├── reviewer.yaml                  # 代码审查员
│   ├── qa.yaml                        # 测试工程师
│   └── devops.yaml                    # 交付工程师
├── prompts/                           # Prompt模板目录
│   ├── core-template.yaml             # 核心角色层模板
│   ├── adapters/                      # 模型适配器
│   │   ├── claude-adapter.yaml
│   │   ├── codex-adapter.yaml
│   │   └── gemini-adapter.yaml
│   └── examples/                      # 完整示例
│       ├── reviewer-full-prompt.md
│       └── developer-full-prompt.md
├── rules/                             # 原子规则库
│   ├── api-compatibility.yaml         # API兼容性规则
│   ├── database-safety.yaml           # 数据库安全规则
│   ├── security-checklist.yaml        # 安全检查清单
│   ├── test-requirements.yaml         # 测试要求规则
│   └── README.md                      # 规则库使用说明
├── model-config/                      # 模型匹配配置
│   ├── routing-matrix.yaml            # 路由矩阵
│   ├── capability-profiles.yaml       # 能力画像
│   └── cost-thresholds.yaml           # 成本阈值
├── tests/                             # 测试集
│   ├── task-suite.yaml                # 任务集定义
│   ├── evaluation-metrics.yaml        # 评测指标
│   └── test-cases/                    # 测试用例
│       ├── feature-development.md
│       ├── bug-fix.md
│       ├── security-review.md
│       ├── architecture-decision.md
│       └── ui-implementation.md
└── schemas/                           # Schema定义
    ├── role-schema.json
    ├── rule-schema.json
    └── output-contract-schema.json
```

---

## 三、角色配置模板规范

### 3.1 核心角色层结构

每个角色配置文件（`roles/*.yaml`）包含以下标准字段：

```yaml
role:
  id: string                           # 角色唯一标识
  name: string                         # 角色名称
  version: string                      # 版本号
  mission: string                      # 核心使命（一句话）
  
scope:
  included: [string]                   # 职责范围（做什么）
  excluded: [string]                   # 明确边界（不做什么）
  
inputs:
  required: [string]                   # 必需输入
  optional: [string]                   # 可选输入
  
workflow:
  - step: string                       # 工作步骤描述
    verification: string               # 验证方法（可选）
    
output_contract:
  format: string                       # json | markdown | yaml
  schema: object                       # 输出结构定义
  
constraints:
  - string                             # 约束条件列表
  
completion_criteria:
  - string                             # 完成标准列表
  
quality_gates:
  - gate: string                       # 质量门
    threshold: string                  # 阈值
```

### 3.2 模型适配器层结构

每个模型适配器（`prompts/adapters/*.yaml`）包含：

```yaml
adapter:
  model_family: string                 # claude | codex | gemini
  version: string                      # 适配器版本
  
capabilities:
  repository_access: boolean           # 仓库读写能力
  shell_execution: boolean             # Shell执行能力
  multimodal: boolean                  # 多模态输入
  long_context: boolean                # 长上下文支持
  
tools:
  - tool_name: string                  # 工具名称
    required: boolean                  # 是否必需
    permission: string                 # read | write | execute
    
execution_policy:
  - policy: string                     # 执行策略描述
    enforcement: string                # strict | advisory
    
output_format:
  preference: string                   # 输出格式偏好
  examples: [string]                   # 示例列表
```

---


## 四、原子规则库设计

### 4.1 规则标准格式

每条原子规则（`rules/*.yaml`）包含：

```yaml
- id: string                           # 规则唯一标识（如 API-001）
  name: string                         # 规则名称
  scope: string                        # 适用范围（backend | frontend | database）
  condition: string                    # 触发条件
  requirement: string                  # 具体要求（可执行、可验证）
  severity: string                     # blocking | warning | info
  verification: string                 # 验证方法（测试/检查/工具）
  source: string                       # 规则来源文档
  owner: string                        # 执行负责人（角色）
  reviewer: string                     # 复核负责人（角色）
  examples:
    pass: string                       # 正确示例
    fail: string                       # 错误示例
```

### 4.2 Phase 1 必需规则集

**API兼容性规则**（`rules/api-compatibility.yaml`）：
- API-001: 不删除/重命名已有响应字段
- API-002: 新增字段必须有默认值
- API-003: HTTP状态码不得随意更改

**数据库安全规则**（`rules/database-safety.yaml`）：
- DB-001: Migration必须支持滚动发布
- DB-002: 不在单次事务中重写大表
- DB-003: 添加索引前评估锁影响

**安全检查清单**（`rules/security-checklist.yaml`）：
- SEC-001: 所有对象访问验证权限
- SEC-002: 敏感数据不记录到日志
- SEC-003: 用户输入必须验证

**测试要求规则**（`rules/test-requirements.yaml`）：
- TEST-001: 缺陷修复必须有回归测试
- TEST-002: 新功能必须覆盖正常和异常路径
- TEST-003: 并发逻辑必须有竞态测试

### 4.3 规则冲突处理优先级

```yaml
priority_order:
  1: system_security_constraints       # 系统安全约束
  2: legal_compliance                  # 法律和合规
  3: organization_rules                # 组织规则
  4: repository_rules                  # 仓库规则
  5: task_requirements                 # 当前任务要求
  6: role_defaults                     # 角色默认偏好
  7: model_inference                   # 模型自行判断
```

---


## 五、模型匹配配置

### 5.1 路由矩阵（`model-config/routing-matrix.yaml`）

```yaml
routing_matrix:
  analyst:
    primary:
      model: claude-opus-4-8
      reason: "深度推理能力+需求澄清"
    fallback:
      model: claude-sonnet-5
      trigger: "cost_threshold_exceeded"
    capability_requirements:
      long_context: true
      reasoning_depth: high
      
  architect:
    primary:
      model: claude-opus-4-8
      reason: "架构决策不降级"
    fallback: null
    capability_requirements:
      reasoning_depth: high
      architecture_knowledge: required
      
  developer:
    primary:
      model: gpt-5.3-codex
      reason: "编程专用+性价比($1.75/$14)"
    fallback:
      model: claude-sonnet-5
      trigger: "codex_unavailable OR task_complexity_high"
    capability_requirements:
      repository_access: required
      code_generation: high
      
  reviewer:
    primary:
      model: claude-sonnet-5
      reason: "质量优先+平衡成本($3/$15)"
    fallback:
      model: claude-opus-4-8
      trigger: "security_critical OR architecture_review"
    capability_requirements:
      code_understanding: high
      security_awareness: high
      
  qa:
    primary:
      model: gpt-5.3-codex
      reason: "快速测试生成+执行能力"
    fallback:
      model: claude-sonnet-5
      trigger: "complex_test_design"
    capability_requirements:
      test_generation: high
      repository_access: required
      
  devops:
    primary:
      model: gpt-5.3-codex
      reason: "工程脚本熟悉+工具执行"
    fallback:
      model: claude-sonnet-5
      trigger: "infrastructure_design"
    capability_requirements:
      shell_execution: required
      configuration_management: high
```

### 5.2 能力画像（`model-config/capability-profiles.yaml`）

```yaml
models:
  claude-opus-4-8:
    capabilities:
      reasoning_depth: 9.5
      code_understanding: 8.8
      architecture_design: 9.2
      long_context: 9.0
      security_awareness: 8.5
    benchmarks:
      swe_bench_verified: 88.6
    pricing:
      input: 5.00
      output: 25.00
      
  claude-sonnet-5:
    capabilities:
      reasoning_depth: 8.5
      code_understanding: 9.0
      architecture_design: 8.5
      long_context: 8.8
      security_awareness: 8.2
    benchmarks:
      swe_bench_verified: 85.2
    pricing:
      input: 3.00
      output: 15.00
      
  gpt-5.3-codex:
    capabilities:
      reasoning_depth: 7.8
      code_understanding: 9.2
      code_generation: 9.5
      repository_access: 9.8
      test_generation: 9.0
    benchmarks:
      swe_bench_verified: 82.1
    pricing:
      input: 1.75
      output: 14.00
      
  gemini-3.1-pro:
    capabilities:
      reasoning_depth: 8.2
      code_understanding: 8.5
      multimodal: 9.5
      long_context: 9.2
    benchmarks:
      swe_bench_verified: 80.6
    pricing:
      input: 2.50
      output: 12.50
```

### 5.3 成本阈值配置（`model-config/cost-thresholds.yaml`）

```yaml
cost_control:
  daily_budget: 100.00              # USD per day
  per_task_max: 5.00                # USD per task
  fallback_triggers:
    - condition: "daily_spent > daily_budget * 0.8"
      action: "switch_to_cheaper_model"
    - condition: "task_cost > per_task_max"
      action: "require_human_approval"
      
model_cost_tiers:
  tier_1_premium:
    models: [claude-opus-4-8]
    use_cases: ["architecture_decision", "security_critical"]
    
  tier_2_standard:
    models: [claude-sonnet-5, gemini-3.1-pro]
    use_cases: ["code_review", "feature_development"]
    
  tier_3_efficient:
    models: [gpt-5.3-codex, gemini-3.5-flash]
    use_cases: ["test_generation", "bug_fix", "documentation"]
```

---


## 六、测试验证框架

### 6.1 测试任务集定义（`tests/task-suite.yaml`）

```yaml
test_suite:
  version: "1.0"
  purpose: "Phase 1 MVP validation"
  total_tasks: 5
  
tasks:
  - id: TASK-001
    name: "功能开发任务"
    type: feature_development
    description: "实现用户登录功能（email+password）"
    inputs:
      - 需求描述文档
      - 现有代码库
      - API设计规范
    expected_roles: [analyst, architect, developer, qa, reviewer]
    success_criteria:
      - 代码实现正确且可运行
      - 测试覆盖率 >80%
      - 通过代码审查
      - 符合API兼容性规则
      
  - id: TASK-002
    name: "缺陷修复任务"
    type: bug_fix
    description: "修复并发场景下的数据竞态问题"
    inputs:
      - Bug报告
      - 复现步骤
      - 相关代码
    expected_roles: [developer, qa, reviewer]
    success_criteria:
      - 添加回归测试（TEST-001规则）
      - 修复不引入新问题
      - 测试在修复前失败、修复后通过
      
  - id: TASK-003
    name: "安全审查任务"
    type: security_review
    description: "审查支付接口的权限验证逻辑"
    inputs:
      - 代码变更diff
      - 安全规范文档
    expected_roles: [reviewer]
    success_criteria:
      - 发现所有已知漏洞（Recall >85%）
      - 报告问题准确性（Precision >80%）
      - 包含可执行修复建议
      
  - id: TASK-004
    name: "架构决策任务"
    type: architecture_decision
    description: "选择缓存方案（Redis vs Memcached）"
    inputs:
      - 业务需求
      - 性能要求
      - 技术限制
    expected_roles: [architect, analyst]
    success_criteria:
      - 列出至少2个方案
      - 包含权衡分析
      - 给出明确建议和理由
      - 输出ADR文档
      
  - id: TASK-005
    name: "多模态UI实现"
    type: ui_implementation
    description: "根据设计稿实现响应式表单"
    inputs:
      - UI设计稿截图
      - 组件库规范
    expected_roles: [developer, qa]
    success_criteria:
      - 组件与设计稿一致
      - 通过浏览器测试
      - 响应式布局正确
```

### 6.2 评测指标定义（`tests/evaluation-metrics.yaml`）

```yaml
metrics:
  correctness:
    description: "最终实现是否正确"
    measurement: "人工验证 OR 自动化测试通过率"
    target: 100%
    weight: 0.30
    
  test_pass_rate:
    description: "测试通过率"
    measurement: "通过测试数 / 总测试数"
    target: ">90%"
    weight: 0.15
    
  regression_rate:
    description: "是否引入回归"
    measurement: "新引入缺陷数 / 代码变更行数"
    target: "<5%"
    weight: 0.15
    
  review_precision:
    description: "代码审查准确性"
    measurement: "真问题数 / 报告问题总数"
    target: ">80%"
    weight: 0.10
    
  review_recall:
    description: "代码审查覆盖率"
    measurement: "发现的已知问题数 / 预埋问题总数"
    target: ">85%"
    weight: 0.10
    
  patch_minimality:
    description: "修改最小化"
    measurement: "必要修改行数 / 总修改行数"
    target: ">90%"
    weight: 0.05
    
  instruction_compliance:
    description: "遵守规则约束"
    measurement: "违反规则数 / 总规则数"
    target: ">95%"
    weight: 0.10
    
  cost_efficiency:
    description: "成本效率"
    measurement: "任务成本 / 预算"
    target: "<1.0"
    weight: 0.05
```

### 6.3 验证流程

```yaml
validation_workflow:
  step1_unit_test:
    description: "单元测试：单个角色配置验证"
    checks:
      - YAML格式正确性
      - Schema验证通过
      - 必需字段完整
      - 引用规则存在
      
  step2_integration_test:
    description: "集成测试：角色协作流程验证"
    checks:
      - 角色依赖关系正确
      - 工作流步骤完整
      - 输出契约匹配
      - 规则冲突处理正确
      
  step3_end_to_end_test:
    description: "端到端测试：完整任务执行"
    checks:
      - 5个测试任务执行
      - 评测指标达标
      - 成本在预算内
      - 无阻塞问题
      
  step4_regression_test:
    description: "回归测试：修改后重新验证"
    checks:
      - 原有通过测试仍通过
      - 新测试覆盖新功能
      - 性能无明显下降
```

---


## 七、具体实施步骤

### 7.1 Day 1-2: 基础框架搭建

**任务清单**：
```yaml
- [ ] 创建目录结构（.collab/ai-role-system/）
- [ ] 编写README.md和IMPLEMENTATION-GUIDE.md
- [ ] 创建Schema定义文件（role-schema.json等）
- [ ] 设置YAML验证工具配置
```

**交付物**：
- 完整目录结构
- 文档框架
- Schema验证脚本

---

### 7.2 Day 3-5: 角色配置创建

**任务清单**：
```yaml
- [ ] 创建6个核心角色配置文件（roles/*.yaml）
  - [ ] analyst.yaml
  - [ ] architect.yaml  
  - [ ] developer.yaml
  - [ ] reviewer.yaml
  - [ ] qa.yaml
  - [ ] devops.yaml
- [ ] 每个角色配置通过schema验证
- [ ] 编写角色使用示例
```

**质量检查**：
- 每个角色包含完整的mission/scope/inputs/workflow/output_contract
- constraints和completion_criteria明确可验证
- 引用的规则ID存在于规则库中

---

### 7.3 Day 6-7: Prompt模板和适配器

**任务清单**：
```yaml
- [ ] 创建核心Prompt模板（prompts/core-template.yaml）
- [ ] 创建3个模型适配器
  - [ ] claude-adapter.yaml
  - [ ] codex-adapter.yaml
  - [ ] gemini-adapter.yaml
- [ ] 生成2个完整Prompt示例
  - [ ] reviewer-full-prompt.md
  - [ ] developer-full-prompt.md
```

**质量检查**：
- 核心层和适配器层清晰分离
- 每个适配器明确capabilities和tools
- execution_policy具体可执行

---

### 7.4 Day 8-9: 原子规则库

**任务清单**：
```yaml
- [ ] 创建4个规则文件（rules/*.yaml）
  - [ ] api-compatibility.yaml（至少3条规则）
  - [ ] database-safety.yaml（至少3条规则）
  - [ ] security-checklist.yaml（至少4条规则）
  - [ ] test-requirements.yaml（至少3条规则）
- [ ] 每条规则包含正确/错误示例
- [ ] 编写规则库README.md
```

**质量检查**：
- 每条规则有明确的verification方法
- severity分级合理（blocking vs warning）
- source追溯到具体文档

---

### 7.5 Day 10-11: 模型匹配配置

**任务清单**：
```yaml
- [ ] 创建routing-matrix.yaml（6个角色的路由配置）
- [ ] 创建capability-profiles.yaml（4个模型的能力画像）
- [ ] 创建cost-thresholds.yaml（成本控制策略）
- [ ] 验证配置的一致性和完整性
```

**质量检查**：
- 每个角色有primary和fallback模型
- 能力画像基于2026年7月实际数据
- 成本阈值符合预算约束

---

### 7.6 Day 12-13: 测试框架

**任务清单**：
```yaml
- [ ] 创建task-suite.yaml（5个测试任务）
- [ ] 创建evaluation-metrics.yaml（8个评测指标）
- [ ] 编写5个测试用例详细说明
  - [ ] feature-development.md
  - [ ] bug-fix.md
  - [ ] security-review.md
  - [ ] architecture-decision.md
  - [ ] ui-implementation.md
- [ ] 创建验证脚本
```

**质量检查**：
- 测试任务覆盖典型场景
- 评测指标可量化
- 成功标准明确

---

### 7.7 Day 14: 集成验证

**任务清单**：
```yaml
- [ ] 运行schema验证（所有YAML文件）
- [ ] 执行单元测试（单个角色配置）
- [ ] 执行集成测试（角色协作流程）
- [ ] 修复发现的问题
- [ ] 更新文档
```

**验收标准**：
- 所有配置文件通过schema验证
- 至少执行1个端到端测试任务
- 文档完整且无明显错误

---

## 八、风险和应对

### 8.1 已识别风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| Schema定义不完善 | 中 | 中 | 迭代改进，保留扩展字段 |
| 规则冲突处理复杂 | 高 | 低 | 使用明确优先级，记录决策 |
| 模型能力变化 | 中 | 中 | 定期更新capability_profiles |
| 测试覆盖不足 | 高 | 中 | 优先覆盖高风险场景 |
| 成本超预算 | 中 | 低 | 实施成本监控和告警 |

### 8.2 依赖和前置条件

**必需**：
- 2026年7月模型数据文档可访问
- YAML解析和验证工具可用
- 至少一个AI模型API可调用（用于测试）

**推荐**：
- 真实代码仓库用于测试
- 人工评审团队（验证评测指标）
- 成本跟踪工具

---

## 九、成功度量

### 9.1 Phase 1完成标志

- [ ] 6个角色配置文件创建并通过验证
- [ ] 至少10条原子规则定义完整
- [ ] 模型匹配配置覆盖所有角色
- [ ] 5个测试任务定义完成
- [ ] 至少1个端到端测试执行成功
- [ ] 所有文档完整且可读

### 9.2 质量指标目标

```yaml
target_metrics:
  schema_validation_pass_rate: 100%
  documentation_completeness: 100%
  test_task_success_rate: ">80%"
  average_precision: ">75%"
  average_recall: ">75%"
  cost_per_test_task: "<$2"
```

---

## 十、后续Phase 2-3预览

**Phase 2（Week 3-4）**：
- 真实任务测试和数据收集
- 评测指标优化
- Prompt和fallback策略调整

**Phase 3（Week 5+）**：
- 扩展角色添加
- 动态路由算法实现
- 成本优化和监控系统

---

**计划结束** | 版本: v1.0 | 更新时间: 2026-07-22
