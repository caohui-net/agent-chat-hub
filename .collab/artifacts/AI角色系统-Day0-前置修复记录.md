# AI角色系统 - Day 0 前置修复记录

**日期**: 2026-07-22  
**目的**: 修复验证报告中识别的阻塞级问题  
**状态**: 进行中

---

## 一、修复清单

### 1.1 阻塞级修复（必须完成）

- [ ] 修复fallback触发条件结构化问题
  - **文件**: 实施计划第五章
  - **问题**: 触发条件为自由文本，无法程序化判断
  - **修复**: 改为结构化条件（type/condition/logic）
  
- [ ] 添加测试任务优先级排序
  - **文件**: 实施计划第六章
  - **问题**: 未明确优先级，资源不足时无法决策
  - **修复**: 为每个测试任务添加priority字段（P0/P1/P2）

### 1.2 建议级改进（非阻塞）

- [ ] 补充configuration_management能力到模型画像
- [ ] 增加yamllint配置文件
- [ ] 创建规则引用验证脚本框架

---

## 二、修复详情

### 2.1 Fallback触发条件结构化

**原设计**（有问题）：
```yaml
fallback:
  model: claude-sonnet-5
  trigger: "cost_threshold_exceeded OR task_complexity_high"
```

**新设计**（已修复）：
```yaml
fallback:
  model: claude-sonnet-5
  triggers:
    - type: cost_threshold_exceeded
      condition:
        metric: daily_spent_ratio
        operator: ">"
        threshold: 0.8
    - type: task_complexity_high
      condition:
        metric: estimated_input_tokens
        operator: ">"
        threshold: 50000
  logic: OR  # 任一条件满足即触发
```

**修复影响范围**：
- 实施计划第五章（模型匹配配置）
- 将影响所有6个角色的路由配置
- 需要更新routing-matrix.yaml的示例格式

**验证方法**：
- YAML格式验证通过
- 可被程序解析为条件判断逻辑
- 每个trigger有明确的阈值和运算符

---

### 2.2 测试任务优先级排序

**优先级定义**：
- **P0**: 必须通过的关键测试（安全、架构）
- **P1**: 核心功能测试（开发、修复）
- **P2**: 扩展功能测试（多模态等）

**修复后的任务优先级**：

```yaml
tasks:
  - id: TASK-003
    name: "安全审查任务"
    type: security_review
    priority: P0
    priority_reason: "安全关键场景，必须验证Precision和Recall"
    
  - id: TASK-004
    name: "架构决策任务"
    type: architecture_decision
    priority: P0
    priority_reason: "架构决策影响全局，必须验证权衡分析能力"
    
  - id: TASK-001
    name: "功能开发任务"
    type: feature_development
    priority: P1
    priority_reason: "核心功能开发场景，验证端到端流程"
    
  - id: TASK-002
    name: "缺陷修复任务"
    type: bug_fix
    priority: P1
    priority_reason: "缺陷修复验证回归测试能力"
    
  - id: TASK-005
    name: "多模态UI实现"
    type: ui_implementation
    priority: P2
    priority_reason: "多模态为扩展功能，资源不足时可降级"
```

**资源分配策略**：
- 预算充足：执行所有5个任务（P0+P1+P2）
- 预算受限：执行P0+P1任务（4个）
- 预算紧张：仅执行P0任务（2个）

---

## 三、修复验证

### 3.1 阻塞级修复验证清单

- [ ] Fallback触发条件可被YAML解析器解析
- [ ] 触发条件包含明确的metric、operator、threshold
- [ ] 测试任务按优先级排序（P0 > P1 > P2）
- [ ] 每个测试任务有priority_reason字段

### 3.2 修复完成标准

**Day 0完成标志**：
1. ✅ 实施计划文档中的fallback示例已更新
2. ✅ 实施计划文档中的测试任务已添加优先级
3. ✅ 修复记录文档已创建
4. ✅ 所有修复点通过验证清单

---

## 四、后续步骤

**Day 0完成后**：
- 进入Day 1-2：基础框架搭建
- 创建目录结构（.collab/ai-role-system/）
- 编写Schema定义文件
- 设置YAML验证工具

**预计完成时间**: Day 0（当天完成）

---

**记录结束** | 状态: 进行中 | 更新时间: 2026-07-22
