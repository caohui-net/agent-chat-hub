# 测试用例目录

## 概述

本目录包含AI角色系统的测试用例定义。每个测试用例是一个独立的YAML文件，定义了输入、预期输出、评估标准和执行流程。

## 测试用例列表

### 需求分析师 (Analyst)

| ID | 文件 | 名称 | 优先级 | 说明 |
|----|------|------|--------|------|
| ANALYST-T001 | analyst-t001-ambiguity-identification.yaml | 需求澄清 - 模糊需求识别 | P0 | 测试识别需求歧义并提出澄清问题的能力 |
| ANALYST-T002 | （待创建） | 边界条件识别 | P0 | 测试识别边界条件和异常场景 |
| ANALYST-T003 | （待创建） | 验收标准制定 | P1 | 测试制定可验证验收标准的能力 |

### 软件架构师 (Architect)

| ID | 文件 | 名称 | 优先级 | 说明 |
|----|------|------|--------|------|
| ARCHITECT-T001 | （待创建） | 技术方案设计 - 多方案权衡 | P0 | 测试设计多个方案并进行权衡分析 |
| ARCHITECT-T002 | （待创建） | 模块划分和接口设计 | P0 | 测试模块划分和接口定义能力 |
| ARCHITECT-T003 | （待创建） | 技术风险识别 | P1 | 测试识别技术风险和缓解措施 |

### 实现工程师 (Developer)

| ID | 文件 | 名称 | 优先级 | 说明 |
|----|------|------|--------|------|
| DEVELOPER-T001 | developer-t001-user-authentication.yaml | 功能实现 - 用户认证 | P0 | 测试实现用户认证功能，包括安全规则遵守 |
| DEVELOPER-T002 | （待创建） | Bug修复 - SQL注入漏洞 | P0 | 测试修复安全漏洞的能力 |
| DEVELOPER-T003 | （待创建） | 重构 - 提取公共逻辑 | P1 | 测试代码重构能力 |

### 代码审查员 (Reviewer)

| ID | 文件 | 名称 | 优先级 | 说明 |
|----|------|------|--------|------|
| REVIEWER-T001 | （待创建） | 安全审查 - 权限验证 | P0 | 测试识别权限验证缺失 |
| REVIEWER-T002 | （待创建） | API兼容性审查 | P0 | 测试识别API破坏性变更 |
| REVIEWER-T003 | （待创建） | 代码质量审查 | P1 | 测试代码质量建议能力 |

### QA工程师 (QA)

| ID | 文件 | 名称 | 优先级 | 说明 |
|----|------|------|--------|------|
| QA-T001 | （待创建） | 测试用例设计 - 登录功能 | P0 | 测试设计完整测试用例的能力 |
| QA-T002 | （待创建） | 缺陷分析与验证 | P0 | 测试分析bug并设计验证方案 |
| QA-T003 | （待创建） | 测试覆盖率分析 | P1 | 测试识别测试缺口的能力 |

### DevOps工程师 (DevOps)

| ID | 文件 | 名称 | 优先级 | 说明 |
|----|------|------|--------|------|
| DEVOPS-T001 | （待创建） | CI/CD配置 - Node.js应用 | P0 | 测试配置CI/CD流水线 |
| DEVOPS-T002 | （待创建） | 监控告警配置 | P0 | 测试配置监控和告警 |
| DEVOPS-T003 | （待创建） | 灾难恢复方案 | P1 | 测试设计故障恢复方案 |

**总计**: 18个测试任务（已创建2个示例，待创建16个）

## 测试用例文件结构

每个测试用例YAML文件遵循以下结构：

```yaml
test_case:
  # 基本信息
  id: ROLE-T001
  name: 测试用例名称
  priority: P0|P1|P2
  role: analyst|architect|developer|reviewer|qa|devops
  category: 测试类别

  # 输入数据
  input:
    # 角色特定的输入字段
    requirement: string
    context: string
    # ...

  # 预期输出结构（JSON Schema）
  expected_output_schema:
    field1:
      type: string|array|object
      # ...

  # 标准答案（专家基线）
  expert_baseline:
    # 专家给出的理想答案
    # 用于计算评估指标

  # 评估标准
  evaluation:
    metrics:
      metric_name:
        method: 计算方法
        pass_threshold: 阈值
        # ...
    pass_conditions:
      - condition: 通过条件
        severity: blocking|warning

  # 测试执行流程
  execution:
    steps:
      - step: 1
        action: 操作说明
        command: 执行命令
      # ...
    timeout: 超时时间（秒）

  # 失败场景检测（可选）
  failure_scenarios:
    - scenario: 场景名称
      detection: 检测方法
      severity: blocking|warning
      error_message: 错误信息

  # 变体测试（可选）
  variations:
    - variation_id: ROLE-T001-V1
      name: 变体名称
      input_override: 覆盖的输入
      # ...

# 实际运行结果示例（可选，供参考）
sample_run:
  ai_output: AI实际输出
  evaluation_results: 评估结果

# 元数据
metadata:
  created: 创建日期
  version: 版本号
  estimated_duration: 预估执行时间
  model_recommendation: 推荐模型
```

## 创建新测试用例

### 步骤1: 选择模板

根据角色选择合适的现有测试用例作为模板：
- Analyst → `analyst-t001-ambiguity-identification.yaml`
- Developer → `developer-t001-user-authentication.yaml`
- 其他角色 → 参考上述两个示例

### 步骤2: 定义输入

根据角色的输入契约（`roles/*.yaml`中的`inputs`字段）定义测试输入：

```yaml
input:
  # 从角色配置复制输入字段
  requirement: "具体的测试需求"
  context: "测试上下文"
  # ...
```

### 步骤3: 定义专家基线

提供专家答案作为评估基准：

```yaml
expert_baseline:
  # 理想答案
  # 用于计算召回率、覆盖率等指标
```

### 步骤4: 选择评估指标

从`../evaluation-metrics.yaml`中选择适用的指标：

```yaml
evaluation:
  metrics:
    metric_name:  # 从evaluation-metrics.yaml复制
      method: ...
      pass_threshold: ...
```

### 步骤5: 定义通过条件

明确什么情况下测试通过：

```yaml
pass_conditions:
  - condition: "metric_name >= threshold"
    severity: blocking
  - condition: "必须满足的条件"
    severity: blocking
```

### 步骤6: 验证测试用例

运行验证脚本检查格式：

```bash
python scripts/validate-test-cases.py test-cases/your-test.yaml
```

## 执行测试用例

### 方式1: 单个测试用例

```bash
python scripts/run-test.py test-cases/analyst-t001-ambiguity-identification.yaml
```

### 方式2: 按角色执行

```bash
python scripts/run-test.py --role analyst
```

### 方式3: 按优先级执行

```bash
python scripts/run-test.py --priority P0
```

### 方式4: 执行全部

```bash
python scripts/run-test.py --all
```

## 测试报告

测试执行后会生成报告：

- **格式**: Markdown + JSON
- **位置**: `test-results/`
- **内容**:
  - 每个测试用例的通过/失败状态
  - 评估指标得分
  - 失败原因和详细日志
  - 综合统计

示例报告结构：

```
test-results/
├── 2026-07-23-14-30-00/
│   ├── summary.md          # 综合报告
│   ├── summary.json        # JSON格式结果
│   ├── analyst/
│   │   ├── t001-result.yaml
│   │   └── t001-log.txt
│   ├── developer/
│   │   └── t001-result.yaml
│   └── ...
```

## 持续集成

测试用例可集成到CI/CD流水线：

```yaml
# .github/workflows/test-ai-roles.yml
name: AI Role System Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run P0 tests
        run: python scripts/run-test.py --priority P0
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test-results/
```

## 测试数据管理

### 输入数据

- 真实场景优先（从实际项目收集）
- 覆盖典型和边界情况
- 避免敏感信息

### 专家基线

- 由领域专家提供
- 定期审查和更新
- 版本控制

### 评估标准

- 基于业务目标设定阈值
- 参考行业标准
- 根据实际表现调整

## 测试维护

### 定期审查

- **频率**: 每月
- **内容**: 测试用例有效性、阈值合理性
- **责任人**: QA团队 + 角色专家

### 更新触发

- 角色配置变更
- 原子规则更新
- 模型能力变化
- 新需求场景

### 版本管理

- 每个测试用例有version字段
- 重大变更需要说明理由
- 保留历史版本用于回归测试

## 故障排查

### 测试失败

1. 检查AI输出是否符合schema
2. 对比专家基线，分析差异
3. 检查评估指标计算逻辑
4. 审查通过条件是否过严

### 指标异常

1. 验证专家基线质量
2. 检查指标计算公式
3. 对比历史数据识别趋势
4. 考虑模型能力变化

### 执行超时

1. 检查timeout设置
2. 优化输入规模
3. 考虑使用更快的模型
4. 分解为多个子任务

## 扩展测试用例

### 添加变体

为现有测试用例添加变体场景：

```yaml
variations:
  - variation_id: ANALYST-T001-V3
    name: 新的变体场景
    input_override:
      requirement: "不同的需求"
    expected_differences:
      - "预期的不同点"
```

### 创建新类别

定义新的测试类别：

1. 在`test-suite/task-definitions.yaml`中添加新任务定义
2. 创建对应的测试用例文件
3. 定义专门的评估指标（如需要）
4. 更新本README

## 参考文档

- 测试任务定义: `../task-definitions.yaml`
- 评估指标配置: `../evaluation-metrics.yaml`
- 角色配置: `../../roles/*.yaml`
- 原子规则: `../../rules/*.yaml`
- 实施指南: `../../IMPLEMENTATION-GUIDE.md`

## 元数据

- **版本**: 1.0.0
- **创建日期**: 2026-07-23
- **维护团队**: AI角色系统开发组
- **最后更新**: 2026-07-23
