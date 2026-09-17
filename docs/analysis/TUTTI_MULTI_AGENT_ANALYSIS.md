# Tutti 多 Agent 协作机制分析报告

**分析日期**: 2026-09-17  
**目标项目**: https://github.com/tutti-os/tutti  
**分析范围**: 多 agent 协调、会话管理、消息路由

---

## 1. Tutti 项目概览

### 1.1 核心定位
- **产品定位**: 首个多用户、多 agent 实时协作空间
- **核心价值**: 解决多 AI agent 之间的上下文传递和协作问题
- **技术栈**: TypeScript (前端/桌面), Go (后端 daemon), Electron (桌面应用)

### 1.2 架构特点
```
┌─────────────────────────────────────────────────┐
│          apps/desktop (Electron)                │
│  - UI/UX 交互层                                  │
│  - 实时协作界面                                  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│    packages/agent/host (Agent 生命周期核心)      │
│  - Session/Turn 生命周期管理                     │
│  - 持久化检查点 (Checkpoints)                    │
│  - Goal Control (目标控制)                       │
│  - Runtime Operation (运行时操作)                │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│      services/tuttid (Daemon 业务规则)           │
│  - Workspace 管理                                │
│  - Issue/Task 编排                               │
│  - Provider 适配 (Claude/Codex/...)             │
└──────────────────────────────────────────────────┘
```

---

## 2. 核心协作机制

### 2.1 Agent Host Boundary (最重要的设计)

**关键设计原则**: 单一职责边界
- **packages/agent/host**: 拥有 Session/Turn 生命周期的**唯一所有权**
- **services/tuttid**: 只做业务适配（HTTP/查询/编排）
- **清晰的决策规则**:
  ```
  问题: 这个变更是否定义或改变 Session/Turn/Goal 的生命周期语义？
  - 是 → 必须放在 packages/agent/host
  - 否（传输/DTO/查询/展示/产品策略）→ 适配器层
  - 不确定 → 回答"其他 Host 消费者是否也需要这个行为？"
  ```

**对本项目的启示**:
- ✅ 我们的 `ResponseCoordinator` 类似于 Agent Host，拥有协调规则的唯一所有权
- ✅ `SessionManager` 和 `AgentExecutor` 是适配器层，负责持久化和 API 调用
- ⚠️ 需要更明确的边界：哪些逻辑属于核心协调，哪些属于适配

### 2.2 Durable Checkpoints (持久化检查点)

**核心思想**: 每个关键状态变更都创建持久化检查点

```typescript
checkpoint类型:
- initial_schedule      // 初始调度
- task_settled         // 任务完成
- task_failed          // 任务失败
- task_canceled        // 任务取消
- watchdog             // 看门狗超时
- all_tasks_terminal   // 所有任务终止
- migration            // 迁移

checkpoint状态:
- pending    // 待处理
- active     // 激活中（每个执行只能有一个）
- resolved   // 已解决
- superseded // 已被取代
- canceled   // 已取消
```

**工作流**:
1. 任务完成 → 创建 checkpoint → 唤醒主 Agent
2. 主 Agent 审查结果 → 发出命令（schedule/mutate/acknowledge/complete）
3. 命令执行 → 解决当前 checkpoint → 激活下一个 pending checkpoint

**对本项目的启示**:
- ❌ 我们目前**没有**持久化检查点机制
- ✅ 可以借鉴用于多轮对话的恢复和断点续传
- ✅ 适用场景: 长时间运行的协作任务、崩溃恢复、会话迁移

### 2.3 Tutti Mode Orchestration (编排模式)

**设计要点**:
1. **Agent-Orchestrated Execution**: 主 Agent 是唯一的任务图作者
2. **显式命令驱动**: Daemon 不自动调度下一个任务，必须主 Agent 明确指示
3. **固定 5 分钟看门狗**: 防止主 Agent 无响应导致执行卡住
4. **Goal Review**: 所有任务终止后进入审查模式，必须主 Agent 明确接受才能完成

**命令系统**:
```bash
# 调度任务（精确控制哪些任务运行）
tutti plan issue schedule --issue-id --task-ids-json

# 修改任务图（添加/更新/重做/取代任务）
tutti plan issue mutate --issue-id --operations-json

# 确认检查点（无需新任务，仅审查结果）
tutti plan issue acknowledge --issue-id

# 完成目标（必须在 Goal Review 检查点）
tutti plan issue complete --issue-id --decision goal_satisfied
```

**对本项目的启示**:
- ⚠️ 我们的协调是**自动的**（6条规则自动决定谁响应）
- ✅ 可以借鉴**显式命令**机制：用户或 coordinator 明确指定下一个 agent
- ✅ **看门狗机制**可以防止 agent 无响应卡住整个系统

### 2.4 Big @ (跨 Agent 引用机制)

**核心能力**:
- 在 Codex 中 @ Claude Code 的历史对话、文件、任务
- 在 Agent A 中 @ Agent B 去执行某项工作
- 跨用户的 agent 引用（VM 版本）

**技术实现**（推测）:
```typescript
// @ 引用的对象类型
@history:conversation-id   // 历史对话
@file:file-path            // 文件
@task:task-id              // 任务
@agent:agent-name          // 其他 agent
@app:app-name              // 应用调用
```

**对本项目的启示**:
- ✅ 我们已经实现了 **@mention 协作机制**（coordinator 可 @worker）
- ✅ 可以扩展支持更多引用类型（@history、@file、@task）
- ✅ 增强上下文传递能力

### 2.5 Provider-Neutral Design (提供商中立设计)

**关键原则**:
- **Agent Host 不依赖任何特定提供商**（Claude/OpenAI/Codex）
- **Provider 适配器**负责翻译 Host 命令到具体 API
- **Turn Identity**: 跨进程屏障，确保提供商 Turn ID 持久化后才能暴露输出

**架构**:
```
Host (provider-neutral)
  ↓
Adapter (Anthropic/OpenAI/...)
  ↓
Provider API
```

**对本项目的启示**:
- ✅ 我们已经是 **provider-neutral** 设计（`AgentExecutor` 支持多提供商）
- ✅ `ModelConfig` 和 `AgentConfig` 分离了逻辑和提供商细节
- ✅ 继续保持这个设计，未来扩展新模型会更容易

---

## 3. 关键技术对比

| 特性 | Tutti | Agent Chat Hub | 差异分析 |
|------|-------|----------------|----------|
| **架构模式** | 分层清晰：Host → Adapter → Provider | 三层架构：Core → Agent → UI | ✅ 相似度高 |
| **协调方式** | 显式命令驱动 + 检查点 | 6条规则自动协调 | ⚠️ Tutti 更可控，我们更自动 |
| **持久化** | Durable Checkpoints (每个状态变更) | LangGraph Checkpoint (会话级别) | ⚠️ Tutti 粒度更细 |
| **恢复机制** | 启动时恢复所有未完成检查点 | LangGraph 自动恢复会话 | ✅ 都支持恢复 |
| **看门狗** | 固定 5 分钟超时 | 120 秒超时（MVP 限制） | ✅ 类似，Tutti 更长 |
| **@mention** | Big @ 支持多种引用类型 | @agent 触发协作 | ⚠️ Tutti 功能更丰富 |
| **提供商支持** | 多提供商（Claude/Codex/DeepSeek/...） | 多提供商（Anthropic/OpenAI） | ✅ 都是 provider-neutral |
| **实时协作** | 多用户实时共享工作空间 | 单用户多 agent | ❌ Tutti 支持多用户 |
| **Goal Control** | 独立的 Goal 生命周期（无 Turn） | 无独立 Goal 概念 | ⚠️ Tutti 有专门的目标系统 |

---

## 4. 可借鉴的技术点

### 4.1 高优先级（建议实现）

#### A. 显式命令系统
**现状**: ResponseCoordinator 自动决定谁响应  
**改进**: 增加显式模式，用户/coordinator 可明确指定下一步

```python
# 新增命令类型
class CoordinationCommand:
    SCHEDULE = "schedule"      # 调度特定 agents
    DELEGATE = "delegate"      # 委托给特定 agent
    ACKNOWLEDGE = "acknowledge" # 确认结果，无新任务
    COMPLETE = "complete"      # 完成协作

# 使用示例
@dataclass
class ExplicitCoordinationRequest:
    command: CoordinationCommand
    agent_ids: List[str]  # 明确指定哪些 agents
    context: Dict[str, Any]
```

**实现难度**: 中等  
**预期收益**: 更可控的协作流程，用户可以精确干预

---

#### B. 细粒度检查点机制
**现状**: LangGraph 会话级别检查点  
**改进**: Agent 响应级别的检查点

```python
@dataclass
class ResponseCheckpoint:
    checkpoint_id: str
    session_id: str
    round_num: int
    agent_id: str
    checkpoint_type: CheckpointType  # AGENT_START, AGENT_COMPLETE, ERROR, TIMEOUT
    state: CheckpointState           # PENDING, ACTIVE, RESOLVED, FAILED
    timestamp: datetime
    response_data: Optional[str]
    error: Optional[str]

class CheckpointManager:
    def create_checkpoint(self, type: CheckpointType) -> ResponseCheckpoint:
        """创建检查点"""
        
    def resolve_checkpoint(self, checkpoint_id: str) -> None:
        """解决检查点（任务完成）"""
        
    def recover_from_checkpoint(self, checkpoint_id: str) -> None:
        """从检查点恢复"""
```

**实现难度**: 中等  
**预期收益**: 
- ✅ 更精确的崩溃恢复
- ✅ 更好的调试能力（每个 agent 响应都有快照）
- ✅ 支持"回滚到某个 agent 响应前"的功能

---

#### C. 增强的 @mention 机制
**现状**: @agent_name 触发协作  
**改进**: 支持多种引用类型

```python
# 扩展引用类型
@history:session-123:round-5    # 引用历史对话
@file:~/doc.txt                 # 引用文件
@response:agent-claude:round-3  # 引用特定 agent 的历史响应
@agent:codex "implement this"   # 明确委托任务

# 解析器
class MentionParser:
    def parse(self, text: str) -> List[Mention]:
        """解析所有 @ 引用"""
        
    def resolve(self, mention: Mention) -> MentionContext:
        """解析引用为具体上下文"""
```

**实现难度**: 中等  
**预期收益**: 
- ✅ 更强大的上下文传递
- ✅ Agent 间协作更自然
- ✅ 支持引用历史对话避免重复解释

---

### 4.2 中优先级（可选实现）

#### D. Goal Control System
**新增**: 独立的目标管理系统（类似 Tutti 的 Goal Control）

```python
@dataclass
class Goal:
    goal_id: str
    session_id: str
    description: str
    status: GoalStatus  # ACTIVE, PAUSED, COMPLETED, FAILED
    subtasks: List[str]  # task IDs
    assigned_agents: List[str]
    
class GoalController:
    def create_goal(self, description: str) -> Goal:
        """创建目标（不开启 Turn）"""
        
    def pause_goal(self, goal_id: str) -> None:
        """暂停目标执行"""
        
    def resume_goal(self, goal_id: str) -> None:
        """恢复目标执行"""
```

**实现难度**: 高  
**预期收益**: 
- ✅ 支持长期运行的复杂任务
- ✅ 用户可暂停/恢复整个目标
- ✅ 更清晰的任务层次结构

---

#### E. 5 分钟看门狗 + 自动恢复提示
**现状**: 120 秒超时后停止  
**改进**: 超时后自动提示用户是否继续

```python
class WatchdogManager:
    WATCHDOG_TIMEOUT = 300  # 5 分钟
    
    def on_timeout(self, session_id: str, agent_id: str):
        """超时处理"""
        # 1. 保存检查点
        checkpoint = self.checkpoint_manager.create_checkpoint(
            type=CheckpointType.TIMEOUT
        )
        
        # 2. 提示用户
        self.ui.prompt_user(
            f"Agent {agent_id} 已超时 5 分钟，是否继续等待？",
            options=["继续等待", "取消任务", "重试"]
        )
```

**实现难度**: 低  
**预期收益**: 
- ✅ 更长的超时时间适合复杂任务
- ✅ 用户有机会干预而不是直接失败

---

### 4.3 低优先级（暂不建议）

#### F. 多用户实时协作
**原因**: 本项目目前定位是单用户多 agent，多用户协作复杂度极高

#### G. Runtime Operation 系统
**原因**: Tutti 的 Runtime Operation 是为了管理多个 provider 的复杂运行时状态，我们目前的场景不需要这么复杂

---

## 5. 实施建议

### 5.1 Phase 1: 增强协调能力（2-3 周）
- ✅ 实现显式命令系统（A）
- ✅ 增强 @mention 支持多种引用类型（C）
- ✅ 延长看门狗超时到 5 分钟（E）

### 5.2 Phase 2: 持久化改进（3-4 周）
- ✅ 实现细粒度检查点机制（B）
- ✅ 增加崩溃恢复测试
- ✅ 支持"回滚到某个响应"功能

### 5.3 Phase 3: 目标管理（可选，4-5 周）
- ✅ 实现 Goal Control System（D）
- ✅ 支持长期任务管理
- ✅ 增加任务暂停/恢复功能

---

## 6. 风险评估

### 6.1 架构复杂度
- **风险**: Tutti 是企业级产品，架构极其复杂（monorepo、多语言、分布式）
- **应对**: 只借鉴核心思想，不照搬整体架构

### 6.2 过度工程
- **风险**: 引入 Tutti 的全部机制会导致过度设计
- **应对**: 优先实现高优先级特性（A、C、E），验证效果后再考虑其他

### 6.3 兼容性
- **风险**: 新机制可能与现有 ResponseCoordinator 6 条规则冲突
- **应对**: 
  - 保留现有自动模式作为默认
  - 显式命令作为可选增强
  - 通过配置开关切换模式

---

## 7. 总结

### 7.1 Tutti 的核心优势
1. **清晰的边界设计**: Agent Host Boundary 确保职责单一
2. **持久化检查点**: 每个状态变更都可恢复，极高的可靠性
3. **显式命令驱动**: 用户/主 Agent 完全控制协作流程
4. **Provider-Neutral**: 支持任意 AI 提供商，扩展性强

### 7.2 对本项目的最大价值
1. **细粒度检查点**（B）- 提升可靠性和可调试性
2. **显式命令系统**（A）- 增加用户控制能力
3. **增强 @mention**（C）- 改善 agent 间上下文传递

### 7.3 不适合借鉴的部分
1. **多用户协作** - 超出当前项目范围
2. **复杂的 Runtime Operation** - 当前场景不需要
3. **完整的 monorepo 架构** - 我们是单体 Python 应用

---

## 8. 行动计划

### 立即行动（本周）
1. ✅ 设计显式命令系统的 API
2. ✅ 实现 `@history` 和 `@file` 引用类型
3. ✅ 延长看门狗超时到 5 分钟

### 短期计划（1 个月内）
1. ✅ 实现细粒度检查点机制
2. ✅ 增加崩溃恢复测试用例
3. ✅ 完善显式命令系统

### 长期规划（3 个月内）
1. ✅ 评估 Goal Control 的必要性
2. ✅ 考虑支持多用户场景（如果有需求）
3. ✅ 持续优化协调算法

---

**分析完成日期**: 2026-09-17  
**下一步**: 与团队讨论优先级，确定 Phase 1 实施计划
