# 检查点系统设计文档

**创建日期**: 2026-09-17  
**版本**: v1.0  
**状态**: 设计阶段

---

## 1. 概述

### 1.1 目标

实现细粒度的检查点机制，支持：
- Agent 响应级别的状态快照
- 崩溃后精确恢复到任意检查点
- 用户手动回滚到历史状态
- 调试时查看完整的执行历史

### 1.2 灵感来源

参考 Tutti 的 Durable Checkpoints 机制，但简化为单用户场景。

---

## 2. 核心概念

### 2.1 检查点类型 (CheckpointType)

```python
class CheckpointType(str, Enum):
    """检查点类型"""
    SESSION_START = "session_start"      # 会话开始
    USER_INPUT = "user_input"            # 用户输入
    AGENT_START = "agent_start"          # Agent 开始响应
    AGENT_COMPLETE = "agent_complete"    # Agent 完成响应
    AGENT_ERROR = "agent_error"          # Agent 错误
    TIMEOUT = "timeout"                  # 超时
    USER_COMMAND = "user_command"        # 用户显式命令
    ROUND_COMPLETE = "round_complete"    # 轮次完成
```

### 2.2 检查点状态 (CheckpointState)

```python
class CheckpointState(str, Enum):
    """检查点状态"""
    PENDING = "pending"      # 待激活
    ACTIVE = "active"        # 当前激活（每个会话只有一个）
    RESOLVED = "resolved"    # 已解决
    FAILED = "failed"        # 失败
```

### 2.3 检查点模型 (ResponseCheckpoint)

```python
@dataclass
class ResponseCheckpoint:
    """响应检查点"""
    
    # 标识
    checkpoint_id: str                  # UUID
    session_id: str                     # 会话 ID
    round_num: int                      # 轮次编号
    
    # 类型和状态
    checkpoint_type: CheckpointType
    state: CheckpointState
    
    # Agent 信息
    agent_id: Optional[str] = None      # 关联的 Agent ID
    
    # 快照数据
    response_data: Optional[str] = None # Agent 响应内容（JSON）
    session_snapshot: Optional[str] = None  # 会话状态快照（JSON）
    
    # 错误信息
    error: Optional[str] = None
    
    # 时间戳
    timestamp: float = field(default_factory=time.time)
    
    # 序列号（单调递增）
    sequence: int = 0
```

---

## 3. 检查点生命周期

### 3.1 状态转换

```
创建 → PENDING
   ↓
激活 → ACTIVE (每个会话只有一个)
   ↓
解决 → RESOLVED (完成)
   ↓ (失败)
   → FAILED
```

### 3.2 创建时机

| 事件 | 检查点类型 | 说明 |
|------|-----------|------|
| 会话开始 | SESSION_START | 初始检查点 |
| 用户输入 | USER_INPUT | 每次用户输入前 |
| Agent 开始 | AGENT_START | 每个 Agent 开始响应前 |
| Agent 完成 | AGENT_COMPLETE | 每个 Agent 完成响应后 |
| Agent 错误 | AGENT_ERROR | Agent 执行出错 |
| 超时 | TIMEOUT | 看门狗超时 |
| 用户命令 | USER_COMMAND | 用户执行显式命令 |
| 轮次完成 | ROUND_COMPLETE | 一轮响应全部完成 |

---

## 4. 数据库 Schema

### 4.1 checkpoints 表

```sql
CREATE TABLE checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    round_num INTEGER NOT NULL,
    checkpoint_type TEXT NOT NULL,
    state TEXT NOT NULL,
    agent_id TEXT,
    response_data TEXT,      -- JSON
    session_snapshot TEXT,   -- JSON
    error TEXT,
    timestamp REAL NOT NULL,
    sequence INTEGER NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    INDEX idx_session_sequence (session_id, sequence),
    INDEX idx_session_state (session_id, state)
);
```

### 4.2 session_snapshot JSON 结构

```json
{
  "messages": [...],           // 当前消息列表
  "active_agent_ids": [...],   // 激活的 agents
  "round_num": 5,              // 当前轮次
  "token_usage": {             // Token 使用情况
    "input_tokens": 1000,
    "output_tokens": 500
  },
  "metadata": {...}            // 其他元数据
}
```

---

## 5. CheckpointManager API

### 5.1 核心方法

```python
class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self, db_path: str):
        """初始化"""
        
    def create_checkpoint(
        self,
        session_id: str,
        round_num: int,
        checkpoint_type: CheckpointType,
        agent_id: Optional[str] = None,
        response_data: Optional[Dict] = None,
        session_snapshot: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> ResponseCheckpoint:
        """创建检查点"""
        
    def activate_checkpoint(self, checkpoint_id: str) -> None:
        """激活检查点（将当前 ACTIVE 变为 RESOLVED）"""
        
    def resolve_checkpoint(self, checkpoint_id: str) -> None:
        """解决检查点"""
        
    def fail_checkpoint(self, checkpoint_id: str, error: str) -> None:
        """标记检查点失败"""
        
    def get_checkpoint(self, checkpoint_id: str) -> Optional[ResponseCheckpoint]:
        """获取检查点"""
        
    def get_active_checkpoint(self, session_id: str) -> Optional[ResponseCheckpoint]:
        """获取当前激活的检查点"""
        
    def list_checkpoints(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ResponseCheckpoint]:
        """列出检查点（按序列号倒序）"""
        
    def restore_from_checkpoint(
        self,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """从检查点恢复会话状态"""
        
    def rollback_to_checkpoint(
        self,
        checkpoint_id: str,
        create_new: bool = True
    ) -> ResponseCheckpoint:
        """回滚到检查点（可选创建新检查点记录回滚操作）"""
        
    def cleanup_old_checkpoints(
        self,
        session_id: str,
        keep_last_n: int = 100
    ) -> int:
        """清理旧检查点，保留最近 N 个"""
```

---

## 6. 与 SessionManager 集成

### 6.1 集成点

```python
class SessionManager:
    def __init__(self, ...):
        self.checkpoint_manager = CheckpointManager(db_path)
        
    async def handle_user_message(self, message: str):
        """处理用户消息"""
        # 1. 创建 USER_INPUT 检查点
        checkpoint = self.checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            round_num=self.current_round,
            checkpoint_type=CheckpointType.USER_INPUT,
            session_snapshot=self._capture_session_state()
        )
        
        # 2. 激活检查点
        self.checkpoint_manager.activate_checkpoint(checkpoint.checkpoint_id)
        
        try:
            # 3. 处理消息...
            await self._process_message(message)
            
            # 4. 解决检查点
            self.checkpoint_manager.resolve_checkpoint(checkpoint.checkpoint_id)
            
        except Exception as e:
            # 5. 失败时标记检查点
            self.checkpoint_manager.fail_checkpoint(
                checkpoint.checkpoint_id,
                error=str(e)
            )
            raise
            
    async def _execute_agent(self, agent_id: str, ...):
        """执行 Agent"""
        # 1. 创建 AGENT_START 检查点
        start_checkpoint = self.checkpoint_manager.create_checkpoint(
            session_id=self.session_id,
            round_num=self.current_round,
            checkpoint_type=CheckpointType.AGENT_START,
            agent_id=agent_id,
            session_snapshot=self._capture_session_state()
        )
        
        try:
            # 2. 执行 Agent
            response = await self.agent_executor.execute(...)
            
            # 3. 创建 AGENT_COMPLETE 检查点
            complete_checkpoint = self.checkpoint_manager.create_checkpoint(
                session_id=self.session_id,
                round_num=self.current_round,
                checkpoint_type=CheckpointType.AGENT_COMPLETE,
                agent_id=agent_id,
                response_data={"content": response},
                session_snapshot=self._capture_session_state()
            )
            
            # 4. 解决 START 检查点
            self.checkpoint_manager.resolve_checkpoint(start_checkpoint.checkpoint_id)
            
        except Exception as e:
            # 5. 创建 ERROR 检查点
            self.checkpoint_manager.create_checkpoint(
                session_id=self.session_id,
                round_num=self.current_round,
                checkpoint_type=CheckpointType.AGENT_ERROR,
                agent_id=agent_id,
                error=str(e)
            )
            raise
    
    def _capture_session_state(self) -> Dict[str, Any]:
        """捕获会话状态快照"""
        return {
            "messages": [msg.model_dump() for msg in self.messages],
            "active_agent_ids": self.active_agent_ids,
            "round_num": self.current_round,
            "token_usage": self.token_tracker.get_usage(),
            "metadata": {}
        }
```

---

## 7. 崩溃恢复流程

### 7.1 启动时恢复

```python
class SessionManager:
    async def recover_from_crash(self):
        """从崩溃中恢复"""
        # 1. 查找所有 ACTIVE 检查点（异常终止的会话）
        active_checkpoints = self.checkpoint_manager.find_active_checkpoints()
        
        for checkpoint in active_checkpoints:
            # 2. 标记为 FAILED
            self.checkpoint_manager.fail_checkpoint(
                checkpoint.checkpoint_id,
                error="Process crashed"
            )
            
            # 3. 查找上一个 RESOLVED 检查点
            last_resolved = self.checkpoint_manager.get_last_resolved_checkpoint(
                checkpoint.session_id
            )
            
            if last_resolved:
                # 4. 从上一个成功检查点恢复
                session_state = self.checkpoint_manager.restore_from_checkpoint(
                    last_resolved.checkpoint_id
                )
                
                # 5. 通知用户
                logger.info(
                    f"Recovered session {checkpoint.session_id} "
                    f"from checkpoint {last_resolved.checkpoint_id}"
                )
```

---

## 8. 回滚功能

### 8.1 用户触发回滚

```python
# TUI 命令: /rollback <checkpoint_id>
async def rollback_command(self, checkpoint_id: str):
    """回滚到指定检查点"""
    # 1. 验证检查点存在
    checkpoint = self.checkpoint_manager.get_checkpoint(checkpoint_id)
    if not checkpoint:
        raise ValueError(f"Checkpoint {checkpoint_id} not found")
    
    # 2. 恢复状态
    session_state = self.checkpoint_manager.restore_from_checkpoint(checkpoint_id)
    
    # 3. 应用状态
    self.messages = [Message(**msg) for msg in session_state["messages"]]
    self.current_round = session_state["round_num"]
    
    # 4. 创建回滚记录检查点
    rollback_checkpoint = self.checkpoint_manager.create_checkpoint(
        session_id=self.session_id,
        round_num=self.current_round,
        checkpoint_type=CheckpointType.USER_COMMAND,
        session_snapshot=session_state,
        response_data={"rollback_to": checkpoint_id}
    )
    
    # 5. 通知用户
    return f"已回滚到检查点 {checkpoint_id}"
```

---

## 9. 性能优化

### 9.1 异步写入

```python
class CheckpointManager:
    def __init__(self, db_path: str):
        self.db = Database(db_path)
        self.write_queue = asyncio.Queue()
        self.writer_task = asyncio.create_task(self._async_writer())
        
    async def create_checkpoint_async(self, ...):
        """异步创建检查点（不阻塞主流程）"""
        await self.write_queue.put((checkpoint_type, data))
        
    async def _async_writer(self):
        """后台写入任务"""
        while True:
            checkpoint_type, data = await self.write_queue.get()
            # 批量写入数据库
            self._batch_write([data])
```

### 9.2 定期清理

```python
async def periodic_cleanup():
    """定期清理任务（每小时运行）"""
    while True:
        await asyncio.sleep(3600)  # 1 小时
        
        for session_id in active_sessions:
            # 保留最近 100 个检查点
            deleted = checkpoint_manager.cleanup_old_checkpoints(
                session_id,
                keep_last_n=100
            )
            logger.info(f"Cleaned {deleted} old checkpoints for {session_id}")
```

---

## 10. 测试策略

### 10.1 单元测试

```python
# tests/test_checkpoint.py

def test_create_checkpoint():
    """测试创建检查点"""
    
def test_activate_checkpoint():
    """测试激活检查点（自动解决上一个 ACTIVE）"""
    
def test_resolve_checkpoint():
    """测试解决检查点"""
    
def test_fail_checkpoint():
    """测试失败检查点"""
    
def test_restore_from_checkpoint():
    """测试从检查点恢复"""
    
def test_rollback_to_checkpoint():
    """测试回滚"""
    
def test_cleanup_old_checkpoints():
    """测试清理旧检查点"""
```

### 10.2 集成测试

```python
# tests/integration/test_checkpoint_recovery.py

async def test_crash_during_agent_response():
    """测试 Agent 响应中途崩溃恢复"""
    
async def test_crash_during_multiple_agents():
    """测试多 Agent 并发时崩溃恢复"""
    
async def test_rollback_after_error():
    """测试错误后回滚"""
    
async def test_checkpoint_sequence():
    """测试检查点序列完整性"""
```

---

## 11. 未来扩展

### 11.1 压缩历史检查点

```python
# 将多个连续的 RESOLVED 检查点压缩为一个
def compress_checkpoints(session_id: str, keep_every_n: int = 10):
    """压缩历史检查点"""
```

### 11.2 检查点分支

```python
# 支持从同一检查点创建多个分支（类似 Git）
def create_branch_from_checkpoint(
    checkpoint_id: str,
    branch_name: str
) -> str:
    """从检查点创建分支"""
```

---

## 12. 总结

### 12.1 核心价值

- ✅ 精确的崩溃恢复（恢复到任意 Agent 响应前）
- ✅ 用户可控的回滚（撤销错误操作）
- ✅ 完整的执行历史（调试利器）
- ✅ 增强系统可靠性

### 12.2 实施优先级

1. **高优先级**: CheckpointManager 核心 API
2. **高优先级**: 与 SessionManager 集成
3. **中优先级**: 崩溃恢复流程
4. **中优先级**: 回滚功能
5. **低优先级**: 性能优化和清理

---

**文档版本**: v1.0  
**下一步**: 实施 CheckpointManager
