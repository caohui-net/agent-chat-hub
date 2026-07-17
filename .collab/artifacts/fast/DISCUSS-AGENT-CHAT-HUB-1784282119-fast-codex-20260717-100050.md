基于报告，Phase 1 建议采用“薄校验层 + 会话协调层 + LangGraph 适配层”。其中 `SessionManager` 的最小版本必须提前到 Phase 1，否则无法真正验证报告要求的跨会话状态持久化。

报告当前有两处需要修正：

- 风险部分称 LangGraph 持久化“未验证”，验证清单却标记为完成：[技术选型分析报告.md](/home/caohui/projects/agent-chat-hub/docs/技术选型分析报告.md:196)
- Phase 1 要求交付状态持久化，但 Session 管理和历史存储被排到 Phase 2：[技术选型分析报告.md](/home/caohui/projects/agent-chat-hub/docs/技术选型分析报告.md:211)

**推荐边界**

```text
FastAPI / WebSocket
        |
MessageValidator
        |
SessionManager
        |
LangGraphRuntimeAdapter
        |
LangGraph + ModelProvider
```

WebSocket 连接、模型 SDK 和 LangGraph 原始事件都不应进入核心领域模型。

**MessageValidator**

不要设计成一个试图“修复所有 Agent 输出”的大类。建议拆成两条明确路径：

```python
validate_command(raw) -> UserMessageCommand
normalize_agent_event(raw) -> DomainEvent
```

输入命令使用 Pydantic 判别联合，至少包含：

- `schema_version`
- `request_id`：重试和幂等键
- `session_id`
- `type`
- `content`
- `client_timestamp`，可选
- `metadata`，限制大小和允许类型

服务端事件建议统一为：

- `message.started`
- `message.delta`
- `message.completed`
- `message.failed`
- `session.status`
- 后续扩展 `tool.started/completed`、`interrupt.requested`

校验分三层：

1. 结构校验：类型、必填字段、长度、枚举、UUID。
2. 语义校验：消息类型与角色是否匹配、delta 是否允许为空、session 是否可写。
3. 规范化：供应商输出转换成统一文本块、工具调用块和错误事件。

“自动修复”只允许确定性操作，例如去掉 JSON Markdown fence、补充服务端生成的 ID、统一空白和 content block 形式。不能猜测缺失的工具参数、角色或正文。修复结果必须带 `warnings`，便于日志和测试追踪。

对前端输入采用严格模式，对模型供应商输出采用“规范化后校验”模式。错误返回稳定的错误码和字段路径，不把 Pydantic 原始错误直接暴露给客户端。

**SessionManager**

`SessionManager` 是用例协调器，不是全局状态字典，也不负责 WebSocket 连接管理。Phase 1 最小接口可以是：

```python
create_session(agent_id) -> Session
send_message(session_id, request_id, content) -> AsyncIterator[DomainEvent]
get_session(session_id) -> Session
list_messages(session_id) -> list[Message]
cancel_run(session_id, run_id) -> None
```

核心规则：

- Phase 1 使用 `session_id == LangGraph thread_id` 的一对一映射。
- 同一会话同一时间只允许一个 active run；不同会话可以并发。
- `request_id` 建唯一约束，网络重试不能触发两次模型调用。
- 流式 delta 只广播，最终消息才持久化，避免每个 token 写 SQLite。
- 断开 WebSocket 不应自动取消模型运行；取消必须是显式命令。
- Session 状态至少包括 `idle/running/cancelling/failed/closed`。

存储职责必须分开：

| 数据 | 所有者 |
|---|---|
| 会话标题、Agent、状态、时间 | SessionRepository |
| 用户和助手最终消息 | MessageRepository |
| Graph 节点状态、interrupt、恢复点 | LangGraph Checkpointer |
| WebSocket 连接和订阅关系 | ConnectionManager |

LangGraph checkpoint 不能替代消息历史数据库。Checkpoint 是执行状态，不是稳定的聊天查询模型；未来升级图结构后也不适合作为 UI 历史接口。

MVP 可以让业务表和 checkpointer 都落到 SQLite，但保持逻辑隔离。LangGraph 本地参考实现已经提供异步 `AsyncSqliteSaver` 和基于 `thread_id` 的读取方式：[checkpoint-sqlite README](/home/caohui/projects/agent-chat-hub/references/langgraph/libs/checkpoint-sqlite/README.md:1)。同时应启用严格 MessagePack 反序列化配置。

**LangGraph PoC**

PoC 不应从真实 Claude/Codex/Gemini 接口开始。先用确定性 fake streaming model 验证状态和基础设施，再做一个真实模型 smoke test。

最小图只需要：

```text
START -> load/context -> agent -> END
```

多轮聊天通过同一个 `thread_id` 重复调用实现，不必为了展示 LangGraph 而人为增加复杂节点。

PoC 必须自动化验证以下场景：

1. 多轮连续性  
   第一轮告诉 Agent 一个随机值，第二轮要求复述，确认状态被保留。

2. 进程重启恢复  
   关闭 checkpointer 和 graph，重新实例化后使用相同 `thread_id` 完成第二轮。仅在内存中连续调用不算持久化验证。

3. 会话隔离  
   两个 thread 并发写入不同信息，断言状态没有串线。

4. 流式事件  
   验证 `started -> delta* -> completed` 顺序、序号单调且最终文本等于 delta 聚合结果。

5. 幂等与并发  
   相同 `request_id` 重发只产生一条用户消息和一次 run；同一 session 的并发请求被拒绝或排队。

6. 失败恢复  
   模型在流中抛异常后产生 `message.failed`，session 回到可继续状态，下一次请求能够正常运行。

7. Human-in-the-loop  
   增加一个可选 interrupt 节点，验证暂停、进程重启和恢复。这是选择 LangGraph 的核心理由之一，不能只测普通聊天。

8. 性能基线  
   用 fake model 测 20 个并发 session，重点记录框架首事件延迟、事件丢失和 SQLite lock 错误；真实模型延迟不作为框架性能指标。

FastAPI 层只消费适配后的领域事件，不直接把 `astream` 或 `astream_events` 的原始结构发送给前端。这样 LangGraph API 或 stream mode 变化不会破坏 WebSocket 合约。

**Phase 1 通过标准**

- 重启进程后能够继续同一会话。
- 20 个并发会话无状态串线、无 SQLite 锁失败。
- 重复 `request_id` 不产生重复模型调用。
- 流式完成、失败、取消都有确定的终态。
- LangGraph 被封装在 `LangGraphRuntimeAdapter` 后面。
- 单元测试不依赖外部模型，真实模型仅保留一个可选集成测试。
- OpenAPI/WebSocket Schema 有明确版本号。

此外，当前 [pyproject.toml](/home/caohui/projects/agent-chat-hub/.claude/worktrees/session-init/pyproject.toml:1) 尚未声明 LangGraph、SQLite checkpointer 和模型适配依赖。进入实现前应锁定具体版本，并实际验证 Python 3.14 环境，而不是仅依赖包声明的 `>=3.10`。
