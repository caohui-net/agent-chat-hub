# Troubleshooting Guide - 故障排除指南

常见问题解决方案和诊断命令

---

## 快速诊断

运行诊断脚本自动检测问题：

```bash
python diagnose_issues.py
```

输出示例：
```
🔍 开始诊断...
✅ Python版本: 3.10.12
✅ 虚拟环境: 已激活
✅ 依赖包: 已安装
✅ 配置文件: 存在
✅ API密钥: 已配置
❌ 网络连接: 超时

🚨 发现1个问题
```

---

## 安装问题

### 问题1: 虚拟环境不存在

**错误消息**：
```
错误: 虚拟环境不存在
请运行: python3 -m venv venv
```

**原因**：未创建虚拟环境

**解决方案**：
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -e .
```

✅ **验证**：
```bash
which python
# 应输出: /path/to/agent-chat-hub/venv/bin/python
```

---

### 问题2: 依赖安装失败

**错误消息**：
```
ERROR: Could not install packages due to an EnvironmentError
```

**原因**：权限不足或网络问题

**解决方案**：
```bash
# 方案1: 使用--user标志
pip install --user -e .

# 方案2: 升级pip
pip install --upgrade pip

# 方案3: 清理缓存重试
pip cache purge
pip install -e .
```

---

### 问题3: ModuleNotFoundError

**错误消息**：
```
ModuleNotFoundError: No module named 'textual'
```

**原因**：依赖未安装或虚拟环境未激活

**解决方案**：
```bash
# 1. 确认虚拟环境已激活
source venv/bin/activate

# 2. 重新安装依赖
pip install -e .

# 3. 验证安装
pip list | grep textual
```

---

## 配置问题

### 问题4: API密钥未配置

**错误消息**：
```
错误: API密钥未配置
请运行: python init_config.py
```

**原因**：首次运行未配置API密钥

**解决方案**：
```bash
# 运行配置向导
python init_config.py
```

按提示输入：
1. 选择模型提供商（Anthropic/OpenAI）
2. 输入API密钥
3. 创建第一个Agent

✅ **验证**：
```python
python -c "
from src.core.config import ConfigManager
config = ConfigManager()
print('✅ API密钥已配置' if config.get_api_key() else '❌ API密钥未配置')
"
```

---

### 问题5: 配置文件不存在

**错误消息**：
```
FileNotFoundError: [Errno 2] No such file or directory: '/home/user/.agent-chat-hub/models.json'
```

**原因**：配置文件未创建

**解决方案**：
```bash
# 方案1: 运行配置向导（推荐）
python init_config.py

# 方案2: 手动创建配置目录
mkdir -p ~/.agent-chat-hub
```

然后运行 `python init_config.py` 生成配置文件

---

### 问题6: 配置文件格式错误

**错误消息**：
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**原因**：配置文件格式错误或损坏

**解决方案**：
```bash
# 1. 备份现有配置
cp ~/.agent-chat-hub/models.json ~/.agent-chat-hub/models.json.bak

# 2. 重新生成配置
python init_config.py --reset

# 3. 验证JSON格式
python -c "import json; json.load(open('~/.agent-chat-hub/models.json'))"
```

---

## 运行时问题

### 问题7: Agent无响应

**症状**：发送消息后Agent长时间无响应

**可能原因**：
1. API密钥无效
2. 网络连接问题
3. API限流
4. 模型ID错误

**诊断步骤**：

```bash
# 1. 检查API密钥
python -c "
from src.core.config import ConfigManager
config = ConfigManager()
key = config.get_api_key()
print(f'API密钥: {key[:10]}...' if key else 'API密钥未配置')
"

# 2. 测试网络连接
curl -I https://api.anthropic.com
# 或
curl -I https://api.openai.com

# 3. 查看日志
tail -f ~/.agent-chat-hub/logs/agent-chat-hub.log

# 4. 验证模型ID
python -c "
from src.core.config import ConfigManager
config = ConfigManager()
print('可用模型:')
for model in config.models:
    print(f'  - {model[\"id\"]}')
"
```

**解决方案**：

根据诊断结果：
- API密钥无效 → 重新配置 `python init_config.py`
- 网络问题 → 检查代理设置或防火墙
- API限流 → 等待一段时间或升级API计划
- 模型ID错误 → 修改 `~/.agent-chat-hub/agents.json`

---

### 问题8: Token超限错误

**错误消息**：
```
Error: maximum context length exceeded
```

**原因**：上下文token数超过模型限制

**解决方案**：

```bash
# 方案1: 减少max_tokens
# 编辑 ~/.agent-chat-hub/agents.json
nano ~/.agent-chat-hub/agents.json
# 将max_tokens改为更小的值（如2048）

# 方案2: 清理会话历史
python -c "
from src.agents.session import SessionManager
# 创建新会话（丢弃旧上下文）
"

# 方案3: 使用更大上下文的模型
# 切换到claude-opus-3或gpt-4-turbo
```

---

### 问题9: 重试失败

**错误消息**：
```
Error: Max retries (3) exceeded
```

**原因**：网络持续不稳定或API服务异常

**解决方案**：

```bash
# 1. 检查网络稳定性
ping -c 5 api.anthropic.com

# 2. 检查API服务状态
curl https://status.anthropic.com

# 3. 增加重试次数（临时）
# 编辑 src/agents/executor.py
# 修改 max_retries = 3 为 max_retries = 5

# 4. 等待后重试
# API服务恢复后自动正常
```

---

### 问题10: @mention不匹配

**症状**：输入 `@res` 无法匹配到 `researcher`

**原因**：Agent名称不匹配或Agent未启用

**诊断**：

```python
python -c "
from src.core.config import ConfigManager
config = ConfigManager()
print('可用Agent:')
for agent in config.agents:
    status = '✅' if agent.get('enabled', True) else '❌'
    print(f'{status} {agent[\"name\"]} (id: {agent[\"id\"]})')
"
```

**解决方案**：

```bash
# 1. 确认Agent已启用
# 编辑 ~/.agent-chat-hub/agents.json
nano ~/.agent-chat-hub/agents.json
# 确保 "enabled": true

# 2. 检查Agent名称拼写
# 确保输入的名称与配置文件中的name字段匹配

# 3. 重启应用
./start.sh
```

---

## 界面问题

### 问题11: TUI界面显示异常

**症状**：界面乱码或布局错误

**原因**：终端不支持或终端尺寸过小

**解决方案**：

```bash
# 1. 检查终端类型
echo $TERM
# 推荐: xterm-256color

# 2. 设置终端类型
export TERM=xterm-256color

# 3. 检查终端尺寸
tput cols  # 列数应≥80
tput lines # 行数应≥24

# 4. 调整终端窗口大小
# 推荐: 至少100x30
```

---

### 问题12: 无法输入中文

**症状**：输入中文显示为乱码

**原因**：终端编码设置问题

**解决方案**：

```bash
# 1. 检查locale
locale | grep LANG
# 应显示: LANG=en_US.UTF-8 或 zh_CN.UTF-8

# 2. 设置UTF-8编码
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# 3. 重启应用
./start.sh
```

---

### 问题13: 快捷键不工作

**症状**：按Ctrl+C无法退出

**原因**：快捷键被终端或其他程序占用

**解决方案**：

```bash
# 1. 检查快捷键绑定
# Ctrl+C - 退出
# Ctrl+N - 新会话
# Tab - 切换焦点

# 2. 如果Ctrl+C不工作，尝试：
# Ctrl+D (EOF)
# Ctrl+Z (挂起) 然后 kill %1

# 3. 强制终止
ps aux | grep "python main.py"
kill -9 <PID>
```

---

## 性能问题

### 问题14: 响应速度慢

**症状**：Agent响应时间超过10秒

**可能原因**：
1. 网络延迟
2. 模型负载高
3. Token数过多

**诊断**：

```bash
# 1. 测试API延迟
time curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-3-5","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}'

# 2. 查看Token统计
# 在TUI中查看Token统计面板

# 3. 检查系统资源
top -p $(pgrep -f "python main.py")
```

**优化方案**：

```bash
# 1. 减少max_tokens
# 编辑 ~/.agent-chat-hub/agents.json
# "max_tokens": 2048  # 从4096减少到2048

# 2. 降低temperature
# "temperature": 0.5  # 从0.7降低到0.5

# 3. 使用更快的模型
# claude-sonnet-3-5 → claude-haiku-3
```

---

### 问题15: 内存占用过高

**症状**：应用占用超过500MB内存

**原因**：会话历史过长

**解决方案**：

```bash
# 1. 创建新会话
# 在TUI中按 Ctrl+N

# 2. 清理旧会话
rm ~/.agent-chat-hub/sessions/*.json

# 3. 限制会话消息数
# 编辑 src/agents/session.py
# 添加消息数限制（如最多保留100条）
```

---

## 日志分析

### 查看错误日志

```bash
# 查看所有错误
grep "ERROR" ~/.agent-chat-hub/logs/agent-chat-hub.log

# 查看最近的错误
tail -n 100 ~/.agent-chat-hub/logs/agent-chat-hub.log | grep "ERROR"

# 实时监控错误
tail -f ~/.agent-chat-hub/logs/agent-chat-hub.log | grep --color "ERROR"
```

### 常见错误消息

#### 1. Authentication failed

```
ERROR: Authentication failed: Invalid API key
```

**解决**：重新配置API密钥

```bash
python init_config.py
```

#### 2. Connection timeout

```
ERROR: Connection timeout after 30s
```

**解决**：检查网络连接或增加超时时间

#### 3. Rate limit exceeded

```
ERROR: Rate limit exceeded. Retry after 60s
```

**解决**：等待限流解除或升级API计划

---

## 常用诊断命令

### 系统信息

```bash
# Python版本
python --version

# 虚拟环境
which python

# 已安装包
pip list

# 配置文件
ls -la ~/.agent-chat-hub/
```

### 网络测试

```bash
# 测试Anthropic API
curl -I https://api.anthropic.com

# 测试OpenAI API
curl -I https://api.openai.com

# DNS解析
nslookup api.anthropic.com
```

### 进程管理

```bash
# 查找进程
ps aux | grep "python main.py"

# 终止进程
pkill -f "python main.py"

# 查看端口占用
lsof -i :8000
```

---

## 错误代码对照表

| 错误代码 | 说明 | 解决方案 |
|----------|------|----------|
| `ERR_API_KEY_MISSING` | API密钥未配置 | 运行 `python init_config.py` |
| `ERR_CONFIG_NOT_FOUND` | 配置文件不存在 | 运行 `python init_config.py` |
| `ERR_AGENT_NOT_FOUND` | Agent不存在 | 检查 `agents.json` |
| `ERR_MODEL_NOT_FOUND` | 模型ID错误 | 检查 `models.json` |
| `ERR_NETWORK_TIMEOUT` | 网络超时 | 检查网络连接 |
| `ERR_RATE_LIMIT` | API限流 | 等待或升级计划 |
| `ERR_TOKEN_LIMIT` | Token超限 | 减少max_tokens |
| `ERR_AUTH_FAILED` | 认证失败 | 重新配置API密钥 |

---

## 获取帮助

如果以上方案无法解决问题：

1. **查看完整日志**：
   ```bash
   cat ~/.agent-chat-hub/logs/agent-chat-hub.log
   ```

2. **运行诊断**：
   ```bash
   python diagnose_issues.py > diagnostic_report.txt
   ```

3. **提交Issue**：
   - GitHub Issues: [github.com/yourusername/agent-chat-hub/issues](https://github.com/yourusername/agent-chat-hub/issues)
   - 附上诊断报告和错误日志

---

## 相关文档

- [快速开始](QUICKSTART.md)
- [配置指南](CONFIGURATION.md)
- [API参考](../api-reference/API.md)

---

**版本**: v1.0  
**更新日期**: 2026-09-06
