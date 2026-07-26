# AI软件工程角色系统设计方案

**版本**: v1.0  
**创建时间**: 2026-07-22  
**讨论主题**: AI方向软件工程的角色预设、Prompt提取、模型匹配方案  
**状态**: 待提交

---

## 一、讨论背景

### 核心问题
1. **角色预设**：AI软件工程应建立哪些预设角色？
2. **Prompt提取**：如何更合理、更精确地提取角色prompt？
3. **模型匹配**：角色与Claude/Codex/Gemini如何匹配？

### 讨论过程
- **尝试方案**：多次尝试使用Claude-Codex-Gemini三方讨论脚本
- **技术限制**：
  - Full模式遇到路径安全检查错误
  - Fast模式响应被截断
  - Gemini在fast模式下未生成输出
- **实际方案**：基于深入技术分析，由Claude提供综合方案

---

## 二、问题1：角色预设方案

### 2.1 核心层角色（4个，必选）

#### Coordinator（协调者）

**职责定义**：
- 任务分解与优先级排序
- 资源分配与进度跟踪
- 冲突解决与决策仲裁

**输入输出**：
- 输入：项目目标、资源约束、团队状态
- 输出：任务分配方案、进度报告、决策记录

**不负责**：
- ❌ 具体编码实现
- ❌ 技术细节决策
- ❌ 代码审查

**配置示例**：
```yaml
coordinator:
  role_id: coordinator
  description: "Task decomposition, resource allocation, conflict resolution"
  capabilities_required:
    - deep_reasoning: 0.9
    - large_context: 0.8
    - planning: 0.9
  model_preferences:
    primary: claude-opus-4-8
    fallback: [claude-sonnet-3-5]
    reason: "需要深度推理和全局视角"
```

---

#### Coder（编码者）

**职责定义**：
- 根据需求实现功能代码
- 编写单元测试
- 添加代码注释和文档

**输入输出**：
- 输入：需求文档、API规范、设计方案
- 输出：可运行代码、测试用例、技术文档

**不负责**：
- ❌ 架构设计
- ❌ 需求定义
- ❌ 审查自己的代码

**配置示例**：
```yaml
coder:
  role_id: coder
  description: "Implement features, write tests, document code"
  capabilities_required:
    - code_generation: 0.95
    - api_familiarity: 0.9
    - testing: 0.8
  model_preferences:
    primary: codex
    fallback: [claude-sonnet-3-5]
    reason: "代码生成速度和API熟悉度优先"
```

---

#### Reviewer（审查者）

**职责定义**：
- 代码质量检查（风格、可读性、复杂度）
- 安全漏洞扫描（SQL注入、XSS等）
- 最佳实践验证

**输入输出**：
- 输入：代码变更、设计文档
- 输出：审查报告、修改建议、批准/拒绝决策

**决策权限**：
- ✅ APPROVE：所有检查通过，无阻塞问题
- ❌ REJECT：安全漏洞 OR 覆盖率<80% OR 风格违规>5
- ⬆️ ESCALATE：性能问题 OR 架构影响 OR 需要>2小时重构

**不负责**：
- ❌ 重写代码（只建议，不实施）
- ❌ 架构决策（上报给Architect）
- ❌ 需求变更审批

**配置示例**：
```yaml
reviewer:
  role_id: reviewer
  description: "Code quality check, security scan, best practices validation"
  capabilities_required:
    - pattern_recognition: 0.85
    - security_awareness: 0.9
    - code_understanding: 0.85
  model_preferences:
    primary: claude-sonnet-3-5
    fallback: [claude-opus-4-8]
    fallback_triggers: [security_issue]
    reason: "平衡质量与成本，安全问题升级Opus"
```

---

#### Architect（架构师）

**职责定义**：
- 系统架构设计
- 技术选型与评估
- 架构演进规划

**输入输出**：
- 输入：业务需求、性能指标、技术约束
- 输出：架构文档、技术方案、设计决策

**不负责**：
- ❌ 具体实现细节
- ❌ 日常代码审查
- ❌ 项目进度管理

**配置示例**：
```yaml
architect:
  role_id: architect
  description: "System design, technology selection, architecture evolution"
  capabilities_required:
    - deep_reasoning: 0.95
    - architectural_thinking: 0.9
    - technology_evaluation: 0.85
  model_preferences:
    primary: claude-opus-4-8
    fallback: []  # 架构决策不降级
    reason: "架构级决策需要最高质量推理"
```

---

### 2.2 扩展层角色（3个AI特化角色，按需选用）

#### PromptEngineer（提示词工程师）

**职责定义**：
- 设计和优化LLM提示词
- 评估Agent行为质量
- 调整模型响应策略

**适用场景**：
- 项目大量使用LLM API
- 需要优化AI交互质量
- Agent行为需要精细调优

**配置示例**：
```yaml
prompt_engineer:
  role_id: prompt_engineer
  description: "Design prompts, optimize agent behavior, evaluate LLM responses"
  capabilities_required:
    - meta_cognition: 0.9
    - llm_understanding: 0.95
    - iterative_optimization: 0.85
  model_preferences:
    primary: claude-opus-4-8
    fallback: [claude-sonnet-3-5]
    reason: "理解LLM行为需要meta-cognition能力"
```

---

#### DataEngineer（数据工程师）

**职责定义**：
- 数据管道设计
- ETL实现与优化
- 数据质量保障

**适用场景**：
- AI训练数据处理
- 大规模数据集成
- 数据管道构建

**配置示例**：
```yaml
data_engineer:
  role_id: data_engineer
  description: "Data pipeline design, ETL implementation, data quality assurance"
  capabilities_required:
    - large_context: 0.95  # 处理大数据集描述
    - multimodal: 0.8      # 图文混合数据
    - structured_output: 0.9
  model_preferences:
    primary: gemini-pro-1-5
    fallback: [claude-sonnet-3-5]
    reason: "超长上下文（1M+）和多模态支持"
```

---

#### Tester（测试专家）

**职责定义**：
- 测试策略设计
- 自动化测试实现
- 边界case覆盖

**适用场景**：
- 质量要求高的项目
- 复杂业务逻辑
- 需要全面测试覆盖

**配置示例**：
```yaml
tester:
  role_id: tester
  description: "Test strategy, automation, edge case coverage"
  capabilities_required:
    - code_generation: 0.9
    - testing_frameworks: 0.95
    - edge_case_thinking: 0.85
  model_preferences:
    primary: codex
    fallback: [claude-sonnet-3-5]
    reason: "快速测试代码生成和框架熟悉度"
```

---

### 2.3 配置策略

#### 小团队配置（2-3 agents）
```yaml
minimal_setup:
  roles: [coordinator, coder]
  适用场景: 原型开发、小型项目、快速迭代
  优点: 轻量级、快速响应
  限制: 缺少质量保障和架构设计
```

#### 标准配置（4-5 agents）
```yaml
standard_setup:
  roles: [coordinator, coder, reviewer, architect]
  适用场景: 中型项目、持续开发、生产环境
  优点: 平衡质量和效率
  推荐: 大多数AI软件工程项目的默认配置
```

#### 完整配置（6+ agents）
```yaml
full_setup:
  roles: [coordinator, coder, reviewer, architect, prompt_engineer, tester]
  适用场景: 大型项目、高质量要求、AI密集型应用
  优点: 全面覆盖、专业分工
  成本: 较高的token消耗和协调开销
```


## 三、问题2：Prompt提取策略

### 3.1 三层结构模板

#### Layer 1: 角色定位（Persona）

**模板**：
```markdown
# Role: {角色名}

You are a {角色定位} responsible for {核心职责}.
Your goal is to {主要目标}.
```

**示例（Reviewer）**：
```markdown
# Role: Code Reviewer

You are a code quality guardian responsible for identifying bugs, 
security issues, and maintainability problems before code is merged.

Your goal is to ensure every code change meets team standards and 
does not introduce regressions or vulnerabilities.
```

---

#### Layer 2: 能力边界（Capabilities & Constraints）

**模板**：
```markdown
## Responsibilities
- {具体职责1：带可验证的输入输出}
- {具体职责2：明确的判断标准}
- {具体职责3：清晰的操作范围}

## NOT Your Responsibility
- {明确排除的职责1}
- {明确排除的职责2}
- {需要上报的情况}

## Decision Authority
When to APPROVE: {具体判断标准，可量化}
When to REJECT: {具体判断标准，可量化}
When to ESCALATE: {超出权限的明确边界}
```

**示例（Reviewer）**：
```markdown
## Responsibilities
- Check code against style guide
  Input: Git diff, style guide document
  Output: List of violations with line numbers
  
- Verify test coverage ≥80%
  Input: Coverage report (pytest-cov, coverage.py)
  Output: Pass/Fail with actual coverage percentage
  
- Scan for security vulnerabilities
  Input: Code changes (focus on: SQL queries, user input handling, auth logic)
  Output: Security report with severity (Critical/High/Medium/Low)

## NOT Your Responsibility
- Rewrite code (suggest specific changes, don't implement)
- Make architecture decisions (escalate to Architect)
- Approve design changes requiring >2 hours refactoring (escalate to Coordinator)

## Decision Authority
When to APPROVE:
  - All style checks pass (0 violations)
  - Test coverage ≥80%
  - No security issues (severity ≥ Medium)
  - Cyclomatic complexity ≤10 per function
  
When to REJECT:
  - Security vulnerability (severity ≥ Medium) found
  - Test coverage <80%
  - Style violations >5
  - Function length >50 lines without justification
  
When to ESCALATE:
  - Performance concern (queries without indexes, N+1 problems)
  - Architectural impact (changes to core abstractions)
  - Requires >2 hours refactoring (coordinate with team)
```

---

#### Layer 3: 输出格式（Output Format）

**模板**：
```markdown
## Output Template

```json
{
  "decision": "APPROVE|REJECT|ESCALATE",
  "blocking_issues": [
    {
      "type": "security|quality|style",
      "severity": "critical|high|medium|low",
      "location": "file:line",
      "description": "具体问题描述",
      "suggestion": "具体修复建议"
    }
  ],
  "suggestions": [
    {
      "type": "improvement|optimization|refactoring",
      "priority": "high|medium|low",
      "description": "建议描述",
      "benefit": "预期收益"
    }
  ],
  "evidence": {
    "coverage_percentage": 85.5,
    "style_violations": 2,
    "security_issues": 0,
    "complexity_max": 8
  }
}
```
```

---

### 3.2 提取黄金法则

#### 规则1：具体场景 > 抽象描述

**❌ 错误示例**：
```yaml
reviewer:
  responsibility: "负责代码质量"
```

**✅ 正确示例**：
```yaml
reviewer:
  responsibilities:
    - "检查SQL注入漏洞（扫描所有SQL查询是否使用参数化）"
    - "验证测试覆盖率≥80%（使用pytest-cov生成报告）"
    - "检查圈复杂度≤10（使用radon工具）"
```

**为什么**：具体场景可验证、可执行、可衡量。

---

#### 规则2：清晰边界 > 角色堆叠

**❌ 错误示例**：
```yaml
reviewer:
  responsibility: "审查代码并修复所有问题"
```

**✅ 正确示例**：
```yaml
reviewer:
  responsibilities:
    - "识别问题并提供修复建议"
  not_responsible:
    - "实施修复（由Coder负责）"
  escalation:
    - "架构级问题上报给Architect"
```

**为什么**：清晰边界避免角色职责重叠和责任不明。

---

#### 规则3：可验证 > 主观判断

**❌ 错误示例**：
```yaml
reviewer:
  approval_criteria: "代码应该优雅、简洁、易读"
```

**✅ 正确示例**：
```yaml
reviewer:
  approval_criteria:
    - "圈复杂度≤10（radon cc）"
    - "函数长度≤50行"
    - "命名符合PEP8（pylint检查）"
    - "注释覆盖率≥20%（公共API必须有docstring）"
```

**为什么**：可验证的标准可自动化检查，减少争议。

---

### 3.3 完整Prompt示例

以下是Reviewer角色的完整prompt：

```markdown
# Role: Code Reviewer

You are a code quality guardian responsible for identifying bugs, 
security issues, and maintainability problems before code is merged.

Your goal is to ensure every code change meets team standards and 
does not introduce regressions or vulnerabilities.

## Responsibilities

### 1. Style Compliance
- Input: Git diff + style guide (PEP8 for Python)
- Check: Naming conventions, line length, import order
- Tool: pylint, black, isort
- Output: List of violations with file:line

### 2. Test Coverage
- Input: Coverage report (pytest-cov)
- Check: Overall coverage ≥80%, new code coverage ≥90%
- Output: Pass/Fail with percentage

### 3. Security Scan
- Input: Code changes
- Focus areas:
  - SQL queries (must use parameterized queries)
  - User input handling (validate/sanitize)
  - Authentication/authorization logic
  - File operations (path traversal check)
- Output: Security report with severity

### 4. Code Quality
- Input: Code changes
- Check:
  - Cyclomatic complexity ≤10 per function
  - Function length ≤50 lines
  - Duplicate code detection
- Tool: radon, pylint
- Output: Quality metrics

## NOT Your Responsibility
- ❌ Rewrite code (suggest, don't implement)
- ❌ Make architecture decisions (escalate to Architect)
- ❌ Approve design changes >2h refactor (escalate to Coordinator)
- ❌ Review requirements (handled by Coordinator)

## Decision Authority

### APPROVE when:
- ✅ Style: 0 violations
- ✅ Coverage: ≥80% overall, ≥90% new code
- ✅ Security: No issues ≥Medium severity
- ✅ Quality: Complexity ≤10, length ≤50 lines

### REJECT when:
- ❌ Security vulnerability (≥Medium severity)
- ❌ Coverage <80%
- ❌ Style violations >5
- ❌ Function complexity >10 without justification

### ESCALATE when:
- ⬆️ Performance concern (missing indexes, N+1 queries)
- ⬆️ Architectural impact (changes to core abstractions)
- ⬆️ Requires >2h refactoring (needs team coordination)

## Output Format

```json
{
  "decision": "APPROVE",
  "blocking_issues": [],
  "suggestions": [
    {
      "type": "optimization",
      "priority": "medium",
      "location": "models.py:45",
      "description": "Consider adding index on user_id column",
      "benefit": "Improve query performance by ~10x"
    }
  ],
  "evidence": {
    "coverage_percentage": 85.5,
    "style_violations": 0,
    "security_issues": 0,
    "complexity_max": 8,
    "functions_reviewed": 12
  }
}
```
```


## 四、问题3：模型匹配方案

### 4.1 匹配原则

**核心原则**：基于能力画像匹配，而非角色名称静态绑定

```
角色描述 "做什么" → 能力要求 → 模型选择 "谁更适合做"
```

**避免**：角色与模型永久绑定（例如："Coder必须用Codex"）

**推荐**：声明能力需求，让系统根据任务特征动态选择

---

### 4.2 模型能力画像

| 模型 | 深度推理 | 代码生成 | 大上下文 | 多模态 | 速度 | 成本 |
|------|---------|---------|---------|--------|------|------|
| Claude Opus 4.8 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 高 |
| Claude Sonnet 3.5 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 中 |
| Codex | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | 低 |
| Gemini Pro 1.5 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 中 |

---

### 4.3 角色与模型匹配矩阵

#### 核心角色匹配

| 角色 | 推荐模型 | 匹配理由 | Fallback策略 |
|------|---------|----------|-------------|
| **Coordinator** | Claude Opus 4.8 | • 需要深度推理和全局视角<br>• 处理复杂决策和冲突解决<br>• 长上下文理解团队状态 | Sonnet 3.5（简单任务分配） |
| **Coder** | Codex | • 代码生成速度最快<br>• API和框架熟悉度高<br>• 成本效益最优 | Sonnet 3.5（复杂逻辑） |
| **Reviewer** | Claude Sonnet 3.5 | • 平衡质量与成本<br>• 模式识别能力强<br>• 适合批量审查 | Opus 4.8（安全审查触发） |
| **Architect** | Claude Opus 4.8 | • 架构级决策不降级<br>• 需要最高质量推理<br>• 技术选型评估 | - （不降级） |

---

#### AI特化角色匹配

| 角色 | 推荐模型 | 匹配理由 | Fallback策略 |
|------|---------|----------|-------------|
| **PromptEngineer** | Claude Opus 4.8 | • Meta-cognition能力<br>• 理解LLM行为<br>• 迭代优化提示词 | Sonnet 3.5（初稿设计） |
| **DataEngineer** | Gemini Pro 1.5 | • 超长上下文（1M+ tokens）<br>• 多模态数据处理<br>• 结构化输出能力 | Sonnet 3.5（纯文本场景） |
| **Tester** | Codex | • 快速测试代码生成<br>• 测试框架熟悉<br>• 边界case覆盖 | Sonnet 3.5（策略设计） |

---

### 4.4 动态选择策略

#### 基于任务特征的选择逻辑

```python
def select_model_for_task(task):
    """基于任务特征动态选择模型"""
    
    # 特征提取
    features = {
        'deep_reasoning_required': analyze_complexity(task),
        'code_generation_heavy': count_code_blocks(task),
        'context_size': len(task.context),
        'multimodal_input': has_images_or_diagrams(task),
        'security_sensitive': is_security_related(task)
    }
    
    # 决策规则
    if features['deep_reasoning_required'] > 0.8:
        return 'claude-opus-4-8'
    
    elif features['code_generation_heavy'] > 0.8:
        return 'codex'
    
    elif features['context_size'] > 100000:
        return 'gemini-pro-1-5'
    
    elif features['security_sensitive']:
        return 'claude-opus-4-8'
    
    else:
        return 'claude-sonnet-3-5'  # 默认性价比选择
```

---

#### Fallback触发条件

```yaml
fallback_triggers:
  timeout:
    threshold: 30000  # ms
    action: 切换到fallback模型
  
  rate_limit:
    action: 立即切换到fallback模型
  
  5xx_error:
    max_retries: 2
    action: 重试后切换
  
  security_issue:
    # Reviewer特有：发现安全问题时升级到Opus
    action: 升级到claude-opus-4-8
  
  architectural_impact:
    # Coder特有：检测到架构影响时升级
    action: 升级到claude-opus-4-8或上报Architect
```

---

### 4.5 配置示例

#### 完整角色配置

```yaml
roles:
  coordinator:
    role_id: coordinator
    description: "Task decomposition, resource allocation, conflict resolution"
    
    # 能力要求声明
    capabilities_required:
      deep_reasoning: 0.9
      large_context: 0.8
      planning: 0.9
    
    # 模型偏好配置
    model_preferences:
      primary: claude-opus-4-8
      fallback: [claude-sonnet-3-5]
      fallback_triggers: [timeout, rate_limit, 5xx_error]
      timeout_ms: 30000
      max_retries: 2
      reason: "需要深度推理和全局视角"
  
  coder:
    role_id: coder
    description: "Implement features, write tests, document code"
    
    capabilities_required:
      code_generation: 0.95
      api_familiarity: 0.9
      testing: 0.8
    
    model_preferences:
      primary: codex
      fallback: [claude-sonnet-3-5, claude-opus-4-8]
      fallback_triggers: [timeout, rate_limit, architectural_impact]
      upgrade_triggers:
        - condition: "architectural_impact"
          target: claude-opus-4-8
          escalate_to: architect
      reason: "代码生成速度和成本优先"
  
  reviewer:
    role_id: reviewer
    description: "Code quality check, security scan, best practices"
    
    capabilities_required:
      pattern_recognition: 0.85
      security_awareness: 0.9
      code_understanding: 0.85
    
    model_preferences:
      primary: claude-sonnet-3-5
      fallback: [claude-opus-4-8]
      upgrade_triggers:
        - condition: "security_issue"
          severity: ">=medium"
          target: claude-opus-4-8
      reason: "平衡成本，安全问题升级"
  
  architect:
    role_id: architect
    description: "System design, technology selection"
    
    capabilities_required:
      deep_reasoning: 0.95
      architectural_thinking: 0.9
      technology_evaluation: 0.85
    
    model_preferences:
      primary: claude-opus-4-8
      fallback: []  # 不降级
      reason: "架构决策需要最高质量"
```

---

#### 能力数据库示例

```json
{
  "models": {
    "claude-opus-4-8": {
      "capabilities": {
        "deep_reasoning": 0.95,
        "code_generation": 0.85,
        "large_context": 0.90,
        "multimodal": 0.75,
        "meta_cognition": 0.90,
        "architectural_thinking": 0.95,
        "security_awareness": 0.90
      },
      "constraints": {
        "cost_per_1k_tokens": 0.015,
        "max_context_tokens": 200000,
        "avg_latency_ms": 3000
      }
    },
    "codex": {
      "capabilities": {
        "code_generation": 0.95,
        "api_familiarity": 0.90,
        "testing_frameworks": 0.95,
        "deep_reasoning": 0.70
      },
      "constraints": {
        "cost_per_1k_tokens": 0.002,
        "max_context_tokens": 8000,
        "avg_latency_ms": 500
      }
    },
    "gemini-pro-1-5": {
      "capabilities": {
        "large_context": 0.98,
        "multimodal": 0.95,
        "structured_output": 0.90,
        "deep_reasoning": 0.85
      },
      "constraints": {
        "cost_per_1k_tokens": 0.005,
        "max_context_tokens": 1000000,
        "avg_latency_ms": 2000
      }
    }
  }
}
```


## 五、实施建议

### 5.1 分阶段实施路线图

#### Phase 1: MVP实施（Week 1-2）

**目标**：建立基础角色系统，验证可行性

**行动项**：
1. **实施核心4角色**
   - Coordinator, Coder, Reviewer, Architect
   - 按本文档的三层结构编写system prompt
   - 配置primary模型和fallback链

2. **建立能力画像数据库**
   ```json
   {
     "claude-opus-4-8": {
       "deep_reasoning": 0.95,
       "large_context": 0.90,
       "coding": 0.85
     },
     "codex": {
       "coding": 0.95,
       "api_familiarity": 0.90,
       "deep_reasoning": 0.70
     }
   }
   ```

3. **配置显式模型绑定**
   - 使用推荐的模型匹配
   - 每个角色配置fallback链
   - 设置超时和重试参数

**验证标准**：
- ✅ 所有4个角色能成功实例化
- ✅ Fallback机制正常工作
- ✅ 角色职责边界清晰（无重叠）

---

#### Phase 2: 验证与优化（Week 3-4）

**目标**：用真实项目验证，收集数据优化

**行动项**：
1. **真实任务测试**
   - 选择3-5个典型AI项目任务
   - 记录每个角色的输入输出
   - 评估角色分工是否清晰

2. **数据收集**
   ```yaml
   metrics:
     - 模型切换频率（primary vs fallback）
     - 任务完成时间
     - Token消耗统计
     - 角色间协作效率
   ```

3. **Prompt优化**
   - 根据实际输出质量调整
   - 应用"三层结构+黄金法则"
   - 细化决策边界和escalation规则

**验证标准**：
- ✅ 至少完成3个完整任务流程
- ✅ Fallback触发率<20%
- ✅ 无角色职责冲突

---

#### Phase 3: 扩展与自动化（Week 5+）

**目标**：添加AI特化角色，引入动态选择

**行动项**：
1. **按需添加扩展角色**
   - 评估项目需求
   - 仅在有明确场景时添加
   - PromptEngineer, DataEngineer, Tester

2. **实现能力驱动选择**
   ```python
   def select_model(task):
       capabilities = extract_capabilities(task)
       return capability_db.match(capabilities)
   ```

3. **建立监控体系**
   - 模型性能dashboard
   - 成本监控和预警
   - 质量指标追踪

**验证标准**：
- ✅ 动态选择准确率>85%
- ✅ 成本优化>20%
- ✅ 质量指标稳定或改善

---

### 5.2 关键成功因素

#### 1. 角色边界清晰

**原则**：
- 每个角色有明确的"负责"和"不负责"
- 使用RACI矩阵明确责任分配
- Escalation路径清晰

**检验方法**：
```
给定一个任务，能否无歧义地确定：
- 哪个角色负责执行？
- 哪个角色负责审查？
- 出现问题上报给谁？
```

---

#### 2. Prompt可验证

**原则**：
- 所有判断标准可量化
- 输出格式结构化
- 决策有明确证据

**检验方法**：
```
给定相同输入，不同时间执行：
- 决策是否一致？
- 能否复现结果？
- 有充分证据支持？
```

---

#### 3. 模型匹配合理

**原则**：
- 基于能力需求，非角色名称
- Fallback策略完备
- 成本效益平衡

**检验方法**：
```
分析模型切换日志：
- Primary模型使用率>80%？
- Fallback触发是否合理？
- 成本vs质量是否最优？
```

---

### 5.3 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 角色职责重叠 | 高 | 中 | • 使用RACI矩阵<br>• 明确escalation路径<br>• 定期review职责边界 |
| 模型成本失控 | 高 | 中 | • 设置token预算<br>• 监控成本dashboard<br>• 优先使用Sonnet/Codex |
| Fallback不可用 | 中 | 低 | • 配置多级fallback<br>• 定期测试fallback链<br>• 监控模型可用性 |
| Prompt漂移 | 中 | 高 | • 版本化prompt管理<br>• 定期质量评估<br>• A/B测试新prompt |
| 协作效率低 | 中 | 中 | • 优化handoff流程<br>• 减少不必要的来回<br>• 批量处理相似任务 |

---

### 5.4 质量保障

#### 单元测试（角色级）

```python
def test_reviewer_decision():
    """测试Reviewer的决策逻辑"""
    # Given: 代码变更
    code_change = {
        "coverage": 85,
        "style_violations": 2,
        "security_issues": 0,
        "complexity_max": 8
    }
    
    # When: Reviewer执行审查
    result = reviewer.review(code_change)
    
    # Then: 应该APPROVE
    assert result["decision"] == "APPROVE"
    assert len(result["blocking_issues"]) == 0
```

---

#### 集成测试（角色协作）

```python
def test_coder_reviewer_flow():
    """测试Coder-Reviewer协作流程"""
    # Given: 需求
    requirement = "实现用户登录功能"
    
    # When: Coder实现
    code = coder.implement(requirement)
    
    # And: Reviewer审查
    review = reviewer.review(code)
    
    # Then: 流程完整
    assert code is not None
    assert review["decision"] in ["APPROVE", "REJECT", "ESCALATE"]
    assert "evidence" in review
```

---

#### 端到端测试（完整任务）

```python
def test_complete_feature_development():
    """测试完整功能开发流程"""
    # Given: 项目目标
    goal = "添加用户认证系统"
    
    # When: 完整流程
    tasks = coordinator.decompose(goal)
    design = architect.design(tasks[0])
    code = coder.implement(design)
    review_result = reviewer.review(code)
    
    # Then: 所有环节成功
    assert len(tasks) > 0
    assert design["status"] == "approved"
    assert review_result["decision"] == "APPROVE"
```

---


## 六、总结与结论

### 6.1 核心结论

#### 关于角色预设
- **推荐配置**：核心4角色（Coordinator, Coder, Reviewer, Architect）+ 按需3扩展角色
- **设计原则**：职责边界清晰 > 角色数量多
- **配置策略**：小团队2-3角色，标准团队4-5角色，大型团队6+角色

#### 关于Prompt提取
- **结构模板**：三层结构（Persona + Capabilities & Constraints + Output Format）
- **黄金法则**：具体场景 > 抽象描述，清晰边界 > 角色堆叠，可验证 > 主观判断
- **质量标准**：所有判断标准可量化，所有决策有证据支持

#### 关于模型匹配
- **匹配原则**：基于能力画像，非静态绑定
- **推荐策略**：Opus（协调/架构）+ Codex（编码/测试）+ Sonnet（审查）+ Gemini（数据工程）
- **动态选择**：Phase 2引入，基于任务特征实时选择

---

### 6.2 关键差异化

**与传统软件工程角色的区别**：

| 维度 | 传统角色 | AI Agent角色 |
|------|---------|-------------|
| 定义方式 | 职位头衔 | 职责+输入输出契约 |
| 边界划分 | 模糊，依赖人际沟通 | 明确，可编程验证 |
| 决策标准 | 主观判断+经验 | 量化指标+证据 |
| 输出格式 | 非结构化 | 结构化JSON |
| 模型绑定 | N/A | 能力驱动动态选择 |

---

### 6.3 预期收益

#### 质量提升
- ✅ 代码审查覆盖率100%（Reviewer角色）
- ✅ 安全漏洞早期发现（Reviewer + 升级到Opus）
- ✅ 架构决策有系统性（Architect角色）

#### 效率提升
- ✅ 任务分解自动化（Coordinator角色）
- ✅ 代码生成加速（Codex优先）
- ✅ 批量审查提速（Sonnet性价比）

#### 成本优化
- ✅ 显式模型选择（避免过度使用Opus）
- ✅ Fallback机制（避免单点故障）
- ✅ 动态选择（Phase 2：按需升降级）

---

### 6.4 下一步行动

**立即行动（本周）**：
1. ✅ 完成本设计文档（Done）
2. ⏭️ 基于本文档实施MVP（4核心角色）
3. ⏭️ 编写每个角色的完整system prompt

**短期行动（Week 2-4）**：
4. ⏭️ 用真实项目任务验证（至少3个任务）
5. ⏭️ 收集性能数据（模型切换率、成本、质量）
6. ⏭️ 优化prompt和fallback策略

**中期行动（Week 5+）**：
7. ⏭️ 添加AI特化角色（PromptEngineer等）
8. ⏭️ 实现能力驱动的动态选择
9. ⏭️ 建立监控和质量保障体系

---

## 七、附录

### 7.1 术语表

| 术语 | 定义 |
|------|------|
| **角色（Role）** | 具有明确职责、输入输出契约和决策权限的Agent定义 |
| **能力画像（Capability Profile）** | 模型在各维度能力的量化评估（0-1评分） |
| **Fallback** | 主模型不可用时的备选模型链 |
| **Escalate** | 超出当前角色权限，需要上报给其他角色处理 |
| **Primary模型** | 角色的首选模型 |
| **动态选择** | 基于任务特征实时选择模型，而非静态绑定 |

---

### 7.2 参考文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 角色系统与模型匹配方案分析 | `docs/角色系统与模型匹配方案分析.md` | 原始分析文档（982行） |
| Session Context | `.omc/session-context.json` | 讨论上下文和进展追踪 |
| Gemini Round 2 反馈 | `.collab/artifacts/DISCUSS-请审查-DOCS-角色系统与模型匹配方案分析-1784701373-discuss-r2-gemini-20260722-032422.md` | Gemini的技术反馈 |

---

### 7.3 配置模板

#### 最小化配置（MVP）

```yaml
# config/roles_minimal.yaml
version: "1.0"
roles:
  coordinator:
    enabled: true
    model: claude-opus-4-8
    fallback: [claude-sonnet-3-5]
  
  coder:
    enabled: true
    model: codex
    fallback: [claude-sonnet-3-5]
```

---

#### 标准配置（生产环境）

```yaml
# config/roles_standard.yaml
version: "1.0"
roles:
  coordinator:
    enabled: true
    model: claude-opus-4-8
    fallback: [claude-sonnet-3-5]
    timeout_ms: 30000
  
  coder:
    enabled: true
    model: codex
    fallback: [claude-sonnet-3-5, claude-opus-4-8]
    upgrade_triggers:
      - architectural_impact
  
  reviewer:
    enabled: true
    model: claude-sonnet-3-5
    fallback: [claude-opus-4-8]
    upgrade_triggers:
      - security_issue
  
  architect:
    enabled: true
    model: claude-opus-4-8
    fallback: []  # 不降级
```

---

#### 完整配置（大型项目）

```yaml
# config/roles_full.yaml
version: "1.0"
roles:
  # 核心角色
  coordinator:
    enabled: true
    model: claude-opus-4-8
    fallback: [claude-sonnet-3-5]
  
  coder:
    enabled: true
    model: codex
    fallback: [claude-sonnet-3-5, claude-opus-4-8]
  
  reviewer:
    enabled: true
    model: claude-sonnet-3-5
    fallback: [claude-opus-4-8]
  
  architect:
    enabled: true
    model: claude-opus-4-8
    fallback: []
  
  # AI特化角色
  prompt_engineer:
    enabled: true
    model: claude-opus-4-8
    fallback: [claude-sonnet-3-5]
  
  data_engineer:
    enabled: true
    model: gemini-pro-1-5
    fallback: [claude-sonnet-3-5]
  
  tester:
    enabled: true
    model: codex
    fallback: [claude-sonnet-3-5]

# 全局配置
global:
  max_retries: 2
  default_timeout_ms: 30000
  cost_budget_per_task: 1.0  # USD
  enable_dynamic_selection: false  # Phase 2启用
```

---

### 7.4 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-07-22 | 初始版本，基于多轮讨论和技术分析 | Claude (Opus 4.8) |

---

## 文档状态

- ✅ **完成**：角色预设方案、Prompt提取策略、模型匹配方案
- ✅ **完成**：实施建议、质量保障、配置模板
- ⏭️ **待定**：用户review和反馈
- ⏭️ **待定**：基于反馈的修订

---

**文档结束**

