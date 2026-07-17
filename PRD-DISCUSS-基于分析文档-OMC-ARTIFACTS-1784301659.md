# PRD: 基于分析文档(.omc/artifacts/new-requirements-analysis.md)，对5个未达成一致的内容进行细化讨论直到达成共识：1. HTTP/WebSocket传输层去留决策（Codex要求证据驱动 vs Gemini主张移除简化）2. LangGraph使用强制性（Codex不锁定框架 vs Gemini确认使用）3. Agent响应控制的6个精确标准（资格、排序、去重、取消、预算、停止）4. API密钥安全的4个具体方案（存储、显示、日志、传输）5. 历史技术选型冲突的正式处理方式。允许反驳，要求每个点提供可执行的决策和验证标准

## 决策


## 证据
- new-requirements-analysis.md确认TUI替代Web界面，但没有提出远程客户端或必须保留网络API的需求。
- 分析文档明确将历史React、FastAPI、HTTP/WebSocket和API-first选择列为与新需求冲突的事项，必须正式取代或缩小范围。
- DISCUSS-基于分析文档-OMC-ARTIFACTS-1784301659-r2-gemini已接受LangGraph封装和证据驱动的传输决策，双方分歧可通过消费者契约门槛消除。
- 同一Agent每轮一次、稳定顺序、幂等键和禁止Agent输出自动续轮共同形成可测试的消息轰炸上界。
- 性能数据无法识别外部消费者；消费者盘点和契约测试可以直接验证删除传输层是否造成兼容性破坏。

## 行动项
- {'owner': '架构负责人', 'task': '盘点HTTP/WebSocket调用方、集成测试、部署入口和公开文档，并据此执行移除或制定适配层迁移计划。', 'due': '实现TUI前', 'verification': '提交消费者清单；清单为空时现有非Web测试全部通过，非空时每个消费者均有契约测试、迁移负责人和删除日期。'}
- {'owner': 'Agent协调机制负责人', 'task': '冻结六项响应控制规则及MVP硬预算，并建立与LangGraph实现解耦的行为测试套件。', 'due': '协调器实现前', 'verification': '替换为测试替身协调器后，同一套资格、排序、去重、取消、预算和停止测试仍能执行并通过。'}
- {'owner': '安全负责人', 'task': '落实密钥环存储、固定遮罩、日志出口脱敏和远程TLS强制策略。', 'due': '模型配置功能验收前', 'verification': '诱饵密钥零命中检查通过，远程明文、无效证书和密钥持久化测试均被拒绝。'}
- {'owner': '技术负责人和产品负责人', 'task': '批准并发布技术选型替代ADR，同步需求、架构说明、阶段计划和任务列表。', 'due': '进入实现前', 'verification': '所有有效文档引用同一ADR，旧React及强制网络层决策标记为部分取代或已取代，且不存在相互矛盾的MVP范围描述。'}

## 验收标准
- [ ] 所有行动项完成
- [ ] 证据充分支持决策
- [ ] 无未解决的blocking问题

## 参考artifacts
- .collab/artifacts/DISCUSS-基于分析文档-OMC-ARTIFACTS-1784301659-discuss-r0-claude-20260717-152059.md
- .collab/artifacts/DISCUSS-基于分析文档-OMC-ARTIFACTS-1784301659-discuss-r1-gemini-20260717-152133.md
- .collab/artifacts/DISCUSS-基于分析文档-OMC-ARTIFACTS-1784301659-discuss-r1-codex-20260717-152335.md
- .collab/artifacts/DISCUSS-基于分析文档-OMC-ARTIFACTS-1784301659-discuss-r2-gemini-20260717-152400.md
- .collab/artifacts/DISCUSS-基于分析文档-OMC-ARTIFACTS-1784301659-discuss-r5-codex-20260717-153352.md


## 增量实施计划

**决策：** ...

### Phase 2: 配置
- [ ] {'owner': '安全负责人', 'task': '落实密钥环存储、固定遮罩、日志出口脱敏和远程TLS强制策略。', 'due': '模型配置功能验收前', 'verification': '诱饵密钥零命中检查通过，远程明文、无效证书和密钥持久化测试均被拒绝。'}

### Phase 3: 实现
- [ ] {'owner': '架构负责人', 'task': '盘点HTTP/WebSocket调用方、集成测试、部署入口和公开文档，并据此执行移除或制定适配层迁移计划。', 'due': '实现TUI前', 'verification': '提交消费者清单；清单为空时现有非Web测试全部通过，非空时每个消费者均有契约测试、迁移负责人和删除日期。'}
- [ ] {'owner': 'Agent协调机制负责人', 'task': '冻结六项响应控制规则及MVP硬预算，并建立与LangGraph实现解耦的行为测试套件。', 'due': '协调器实现前', 'verification': '替换为测试替身协调器后，同一套资格、排序、去重、取消、预算和停止测试仍能执行并通过。'}
- [ ] {'owner': '技术负责人和产品负责人', 'task': '批准并发布技术选型替代ADR，同步需求、架构说明、阶段计划和任务列表。', 'due': '进入实现前', 'verification': '所有有效文档引用同一ADR，旧React及强制网络层决策标记为部分取代或已取代，且不存在相互矛盾的MVP范围描述。'}

### 实施建议
- 按phase顺序执行
- 每完成一个phase验证后再继续
- 遇到blocking及时回退讨论
