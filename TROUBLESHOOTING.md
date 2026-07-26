# 故障排除指南

**版本**: 0.1.0  
**更新**: 2026-07-26

---

## 常见问题

### 1. 模块导入错误

**错误信息**：
```
ModuleNotFoundError: No module named 'src'
```

**原因**：项目未安装或PYTHONPATH未设置

**解决方案**：
```bash
# 方案1：安装项目（推荐）
pip install -e .

# 方案2：设置PYTHONPATH
export PYTHONPATH=.
python3 main.py
```

---

### 2. API密钥错误

**错误信息**：
```
KeyError: 'anthropic_api_key'
```

**原因**：API密钥未配置

**解决方案**：
```bash
# 重新初始化配置
python3 init_config.py

# 或手动设置
keyring set agent-chat-hub anthropic_api_key
```

---

### 3. Agent无响应

**症状**：发送消息后没有响应

**可能原因**：
- Agent未激活（active=False）
- 使用@mention但Agent不是coordinator角色
- 模型配置错误

**排查步骤**：
```bash
# 1. 检查Agent配置
cat config/agents.json | jq '.[] | {agent_id, active, role_type}'

# 2. 检查日志
tail -f logs/agent-chat-hub.log

# 3. 测试模型连接
# 查看错误信息
```

---

### 4. 测试失败

**错误信息**：
```
8 failed, 48 passed
```

**原因**：Coordinator路由规则变更后测试未更新

**解决方案**：
```bash
# 检查测试中的Agent是否有role_type字段
# 添加role_type='coordinator'到测试Agent配置

# 运行测试
pytest tests/ -v
```

---

### 5. 性能问题

**症状**：响应速度慢

**排查清单**：
1. 检查并发Agent数量（默认最多3个）
2. 查看日志级别（DEBUG会影响性能）
3. 检查网络延迟
4. 运行性能基准测试

**优化建议**：
```python
# 减少并发Agent数
coordinator = ResponseCoordinator(
    budget_limits=BudgetLimits(max_agents=2)
)

# 调整日志级别（生产环境）
import logging
logging.basicConfig(level=logging.WARNING)
```

---

### 6. 配置文件损坏

**症状**：启动失败，JSON解析错误

**解决方案**：
```bash
# 备份当前配置
cp config/models.json config/models.json.bak

# 重新初始化
python3 init_config.py

# 或手动修复JSON格式
```

---

### 7. 会话历史丢失

**原因**：会话文件被删除或损坏

**预防措施**：
```bash
# 定期备份
cp -r config/sessions/ backup/sessions_$(date +%Y%m%d)/

# 检查会话文件
ls -lh config/sessions/
```

---

### 8. 复制功能不工作

**原因**：终端不支持OSC 52或缺少复制工具

**解决方案**：
```bash
# Linux安装复制工具
sudo apt install xclip xsel

# 测试剪贴板
python3 tests/test_clipboard.py

# 查看测试指南
cat TEST_GUIDE.md
```

---

### 9. 权限错误

**错误信息**：
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**：
```bash
# 检查文件权限
ls -l config/

# 修复权限
chmod 755 config/
chmod 644 config/*.json

# 检查目录所有权
ls -ld config/
```

---

### 10. 内存占用过高

**症状**：应用占用大量内存

**排查**：
```bash
# 查看内存使用
ps aux | grep python3

# 检查会话数量
ls config/sessions/ | wc -l

# 清理旧会话
rm config/sessions/old_session_*.json
```

---

## 调试技巧

### 启用详细日志

```bash
# 设置环境变量
export LOG_LEVEL=DEBUG

# 启动应用
python3 main.py 2>&1 | tee debug.log
```

### 查看实时日志

```bash
# 跟踪日志文件
tail -f logs/agent-chat-hub.log

# 过滤错误
grep "ERROR" logs/agent-chat-hub.log
```

### 运行测试套件

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_coordinator.py -v

# 显示详细输出
pytest tests/ -v -s
```

---

## 日志位置

- **应用日志**: `logs/agent-chat-hub.log`
- **测试日志**: `pytest`输出
- **系统日志**: `/var/log/syslog`（如使用systemd）

---

## 获取支持

如果问题仍未解决：

1. **查看文档**: `docs/`目录
2. **运行测试**: `pytest tests/ -v`
3. **检查GitHub Issues**: 搜索已知问题
4. **提交Issue**: 提供日志和错误信息

---

**提示**: 大多数问题可通过查看日志文件解决！
