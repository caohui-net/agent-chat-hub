# AI角色系统集成方案

**日期**: 2026-07-25  
**状态**: 执行中  
**目标**: 将AI角色系统深度集成到agent-chat-hub

---

## 集成目标

### 核心目标
1. AgentConfig支持角色系统（6个标准角色可用）
2. 规则引擎集成到ResponseCoordinator
3. 模型路由集成到Executor
4. 保持向后兼容，现有功能不受影响

### 成功标准
- ✅ 用户可以基于角色创建Agent
- ✅ Agent遵守角色规则
- ✅ 智能模型路由工作正常
- ✅ 所有现有测试通过
- ✅ 新增集成测试通过

---

## 架构设计

### 1. AgentConfig扩展

**现有结构**:
```python
class AgentConfig(BaseModel):
    agent_id: str
    name: str
    role: str  # 当前是简单字符串
    model_id: str
    priority: int
    system_prompt: Optional[str]
```

**扩展方案**:
```python
class AgentConfig(BaseModel):
    agent_id: str
    name: str
    role: str  # 保持兼容
    role_type: Optional[str]  # 新增：角色类型（analyst/architect/developer等）
    model_id: str
    priority: int
    system_prompt: Optional[str]
    
    # 新增：角色配置引用
    role_config: Optional[Dict[str, Any]]  # 从角色系统加载的完整配置
```

**集成点**:
- 在ConfigManager中添加`load_role_config(role_type)`方法
- 创建Agent时可选择使用标准角色或自定义配置

### 2. 规则引擎集成

**目标**: ResponseCoordinator在选择和调度Agent时应用规则

**集成方案**:
```python
class ResponseCoordinator:
    def __init__(self):
        self.rule_engine = RuleEngine()  # 新增
        
    def select_agents(self, ...):
        # 现有逻辑
        selected = self._apply_qualification_rule(...)
        
        # 新增：规则检查
        violations = self.rule_engine.check_blocking_rules(
            scope='backend',
            context={'session': session_id, 'agents': selected}
        )
        if violations:
            # 处理规则违规
            pass
        
        return selected, stop_reason
```

**集成点**:
- 在`select_agents()`中添加规则检查
- 在`start_round()`中应用规则约束
- 添加规则违规的日志和处理

### 3. 模型路由集成

**目标**: Executor调用Agent时使用智能模型路由

**集成方案**:
```python
class Executor:
    def __init__(self):
        self.model_router = ModelRouter()  # 新增
        
    async def execute_agent(self, agent_config, ...):
        # 新增：智能路由决策
        decision = self.model_router.route(
            task_type=self._infer_task_type(agent_config),
            complexity=self._estimate_complexity(context),
            context_size=len(messages)
        )
        
        # 使用路由建议的模型（如果与配置不同，记录日志）
        selected_model = decision.selected_model
        
        # 现有执行逻辑
        result = await self._call_model(selected_model, ...)
        return result
```

**集成点**:
- 在`execute_agent()`中添加路由逻辑
- 支持模型切换和fallback
- 记录成本估算

---

## 实施步骤

### Step 1: 扩展AgentConfig（30分钟）
- [ ] 在src/core/models.py中扩展AgentConfig
- [ ] 添加role_type和role_config字段
- [ ] 更新ConfigManager支持角色加载

### Step 2: 集成规则引擎（45分钟）
- [ ] 在src/agents/coordinator.py中集成RuleEngine
- [ ] 在select_agents()中添加规则检查
- [ ] 添加规则违规处理逻辑

### Step 3: 集成模型路由（45分钟）
- [ ] 在src/agents/executor.py中集成ModelRouter
- [ ] 在execute_agent()中添加路由逻辑
- [ ] 支持模型切换和成本追踪

### Step 4: 创建集成测试（30分钟）
- [ ] 测试角色加载
- [ ] 测试规则检查
- [ ] 测试模型路由

### Step 5: 文档更新（15分钟）
- [ ] 更新README.md
- [ ] 创建集成使用指南

---

## 向后兼容性

**保证**:
- 现有Agent配置继续工作（role字段保持字符串）
- role_type为Optional，不影响现有代码
- 规则检查可选，不强制启用

**迁移路径**:
- 用户可以逐步将Agent迁移到使用角色系统
- 提供迁移脚本（可选）

---

## 风险和缓解

**风险1**: 集成影响现有功能
- **缓解**: 保持向后兼容，所有新功能可选

**风险2**: 性能影响
- **缓解**: 规则检查和路由决策都很轻量，缓存优化

**风险3**: 测试覆盖不足
- **缓解**: 创建完整的集成测试套件

---

## 时间估算

- 集成实施: 2.5小时
- 测试创建: 0.5小时
- 文档更新: 0.25小时
- **总计**: 约3.25小时

---

**状态**: 方案已制定，开始实施
**下一步**: Step 1 - 扩展AgentConfig
