# PRD: 审核问题证据矩阵.md（位于.collab/artifacts/），包含14个问题的完整信息（文件路径、行号、复现步骤、影响范围），请基于此矩阵进行P0-P3正式分类，并达成最终优先级共识

## 决策


## 证据
- The 'Token预算控制完全失效' issue accurately identifies a critical flaw in cost control, justifying its P0 status.
- The 'Agent排序逻辑错误' issue highlights a direct violation of ADR-0001, also justifying P0.

## 行动项
- {'owner': 'team', 'task': 'Begin implementation of fixes starting with P0-001 and P0-002.', 'due': None, 'verification': 'All P0 issues must have corresponding passing tests before closing.'}
- {'owner': 'team', 'task': 'Establish baseline regression tests as outlined in the matrix.', 'due': None, 'verification': 'Test suite must pass locally and in CI.'}

## 验收标准
- [ ] 所有行动项完成
- [ ] 证据充分支持决策
- [ ] 无未解决的blocking问题

## 参考artifacts
- .collab/artifacts/DISCUSS-审核问题证据矩阵-MD-位于-1784438567-discuss-r0-claude-20260719-052247.md
- .collab/artifacts/DISCUSS-审核问题证据矩阵-MD-位于-1784438567-discuss-r3-gemini-20260719-053241.md


## 增量实施计划

**决策：** ...

### Phase 3: 实现
- [ ] {'owner': 'team', 'task': 'Begin implementation of fixes starting with P0-001 and P0-002.', 'due': None, 'verification': 'All P0 issues must have corresponding passing tests before closing.'}

### Phase 4: 验证
- [ ] {'owner': 'team', 'task': 'Establish baseline regression tests as outlined in the matrix.', 'due': None, 'verification': 'Test suite must pass locally and in CI.'}

### 实施建议
- 按phase顺序执行
- 每完成一个phase验证后再继续
- 遇到blocking及时回退讨论
