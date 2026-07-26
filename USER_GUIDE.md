# Agent Chat Hub 用户手册

**版本**: 0.1.0  
**更新日期**: 2026-07-26

---

## 目录

- [快速开始](#快速开始)
- [基本操作](#基本操作)
- [高级功能](#高级功能)
- [快捷键参考](#快捷键参考)
- [常见问题](#常见问题)

---

## 快速开始

### 安装与启动

**1. 克隆项目**
```bash
git clone https://github.com/caohui-net/agent-chat-hub.git
cd agent-chat-hub
```

**2. 创建虚拟环境并安装**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

**3. 初始化配置**
```bash
python3 init_config.py
```

按照提示输入API密钥（至少配置一个模型）。

**4. 启动应用**
```bash
python3 main.py
```

---

## 基本操作

### 1. 启动应用

运行 `python3 main.py` 后，TUI界面会自动打开：

```
┌─ Agent Chat Hub ─────────────────────────────────────┐
│ 聊天区域                                              │
│                                                       │
│                                                       │
│                                                       │
│                                                       │
├─ 输入区 ─────────────────────────────────────────────┤
│ 输入消息...                                           │
└───────────────────────────────────────────────────────┘
```

### 2. 配置模型

**查看已配置的模型**：
- 按 `F2` 打开配置界面
- 选择 "查看模型配置"

**添加新模型**：
1. 按 `F2` 打开配置界面
2. 选择 "添加新模型"
3. 按提示输入：
   - 模型ID（如 `claude-3-sonnet`）
   - 提供商（如 `anthropic`）
   - 显示名称
   - API端点
   - API密钥名称

**支持的模型**：
- Anthropic Claude (claude-3-opus, claude-3-sonnet)
- OpenAI GPT (gpt-4, gpt-4-turbo)
- Google Gemini

### 3. 创建Agent

**步骤**：
1. 按 `F2` 打开配置界面
2. 选择 "添加新Agent"
3. 填写Agent信息：
   - Agent ID：唯一标识符（如 `technical_assistant`）
   - 名称：显示名称（如 `技术助手`）
   - 角色描述：Agent的职责
   - 选择关联的模型
   - 设置优先级（数值越小优先级越高）

**示例配置**：
```
Agent ID: code_reviewer
名称: 代码审查专家
角色: 专注于代码质量和最佳实践
模型: claude-3-opus
优先级: 100
```

### 4. 发送消息

**普通消息**：
1. 在输入框中输入消息
2. 按 `Enter` 发送
3. 默认情况下，总管角色（coordinator）会响应

**@提及特定Agent**：
```
@code_reviewer 请审查这段代码：
def hello():
    print("hello")
```

使用 `@agent_id` 或 `@agent_name` 可以指定哪个Agent响应。

### 5. 查看消息历史

- 所有消息都会自动保存
- 滚动聊天区域查看历史消息
- 按 `Ctrl+↑` / `Ctrl+↓` 快速滚动

### 6. 复制文本

**复制聊天内容**：
1. 在聊天区域中选择文本（鼠标拖拽）
2. 按 `Ctrl+Shift+C` 复制
3. 内容已复制到系统剪贴板

**注意**：
- 使用OSC 52协议（适用于终端）
- 如果OSC 52不可用，会回退到平台工具（xclip/xsel/pbcopy）

---

## 高级功能

### 1. 多Agent协作

**场景示例**：讨论技术方案

```
用户: @architect @developer 
我们需要设计一个高并发的消息队列系统，请给出建议。
```

**工作流程**：
1. `architect` Agent分析架构需求
2. `developer` Agent提供实现建议
3. 两个Agent的响应会按优先级顺序显示

**优先级规则**：
- 数值越小，优先级越高
- 相同优先级按Agent ID字典序

### 2. @mention路由规则

Agent Chat Hub使用智能路由机制：

**无@mention**：
- 只有**总管角色**（coordinator）会响应
- 适合一般性问题和引导对话

**有@mention**：
- 只有被@的Agents会响应
- 支持部分匹配（如 `@tech` 匹配 `technical_assistant`）
- 支持多个@mention

**示例**：
```bash
# 只有coordinator响应
"你好，介绍一下你的功能"

# 只有code_reviewer响应
"@code_reviewer 请审查这段代码"

# technical_assistant 和 code_reviewer都响应
"@technical @code_reviewer 讨论这个设计"
```

### 3. 会话管理

**创建新会话**：
- 按 `F3` 打开会话菜单
- 选择 "新建会话"
- 输入会话标题

**切换会话**：
- 按 `F3` 查看会话列表
- 使用方向键选择
- 按 `Enter` 切换

**会话持久化**：
- 所有会话自动保存到 `config/sessions/`
- 包含完整的消息历史和Agent状态

### 4. Agent间消息传递

Agents可以互相发送消息（高级功能）：

```python
# Agent A 发送消息给 Agent B
session_manager.send_agent_message(
    from_agent="agent_a",
    to_agent="agent_b",
    content="请协助处理这个任务"
)
```

**查看Agent消息**：
- Agent消息会在聊天区域以特殊格式显示
- 格式：`[Agent A → Agent B] 消息内容`

### 5. 插件系统

**查看已安装插件**：
1. 按 `F4` 打开插件管理界面
2. 查看插件列表和状态

**加载插件**：
- 插件目录：`plugins/`
- 系统自动加载符合规范的插件
- 重启应用以加载新插件

**开发插件**：
参见 `docs/plugins/plugin-development-guide.md`

---

## 快捷键参考

### 全局快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Q` | 退出应用 |
| `F1` | 显示帮助 |
| `F2` | 配置管理 |
| `F3` | 会话管理 |
| `F4` | 插件管理 |
| `Ctrl+Shift+C` | 复制选中文本 |

### 聊天区域

| 快捷键 | 功能 |
|--------|------|
| `↑` / `↓` | 滚动消息 |
| `Ctrl+↑` / `Ctrl+↓` | 快速滚动 |
| `Home` | 跳转到顶部 |
| `End` | 跳转到底部 |

### 输入框

| 快捷键 | 功能 |
|--------|------|
| `Enter` | 发送消息 |
| `Shift+Enter` | 换行 |
| `Ctrl+A` | 全选 |
| `Ctrl+C` | 复制（标准） |
| `Ctrl+V` | 粘贴 |

---

## 常见问题

### Q1: 如何修改API密钥？

**方法1：使用keyring命令行**
```bash
keyring set agent-chat-hub anthropic_api_key
```

**方法2：重新运行初始化**
```bash
python3 init_config.py
```

### Q2: Agent没有响应怎么办？

**检查清单**：
1. Agent是否设置为active=True？
2. 是否使用了@mention，但Agent不是coordinator角色？
3. 检查模型配置是否正确
4. 查看日志：`logs/agent-chat-hub.log`

### Q3: 如何设置coordinator角色？

在创建Agent时，设置 `role_type="coordinator"`：

```python
agent = AgentConfig(
    agent_id="coordinator",
    name="总管",
    role="协调和引导对话",
    role_type="coordinator",  # 关键设置
    model_id="claude-3-sonnet",
    priority=1
)
```

### Q4: 消息历史保存在哪里？

- 配置文件：`config/`
- 会话数据：`config/sessions/`
- 日志文件：`logs/agent-chat-hub.log`

### Q5: 如何备份配置？

```bash
# 备份配置目录
cp -r config/ config_backup_$(date +%Y%m%d)/

# 或者只备份关键文件
cp config/models.json config/models.json.bak
cp config/agents.json config/agents.json.bak
```

### Q6: 复制功能不工作？

**原因**：
- 终端不支持OSC 52协议
- 未安装平台复制工具

**解决方案**：
```bash
# Linux
sudo apt install xclip xsel

# macOS（通常已预装pbcopy）
# 无需额外安装

# 测试剪贴板
python3 tests/test_clipboard.py
```

参见 `TEST_GUIDE.md` 获取详细测试指南。

### Q7: 性能优化建议？

1. **减少并发Agent数**：默认最多3个
2. **使用更快的模型**：Haiku系列响应更快
3. **调整日志级别**：生产环境使用WARNING或ERROR
4. **定期清理会话**：删除不需要的历史会话

参见 `PERFORMANCE.md` 获取性能基准数据。

### Q8: 如何调试问题？

**启用详细日志**：
```bash
# 设置环境变量
export LOG_LEVEL=DEBUG
python3 main.py
```

**查看日志**：
```bash
tail -f logs/agent-chat-hub.log
```

**运行测试**：
```bash
pytest tests/ -v
```

---

## 进阶主题

### 自定义系统提示

为Agent设置自定义系统提示：

```python
agent = AgentConfig(
    agent_id="custom_agent",
    name="自定义Agent",
    role="专业角色",
    model_id="claude-3-opus",
    system_prompt="你是一个专业的XXX，专注于...",  # 自定义提示
    priority=100
)
```

### 配置响应预算

限制每轮对话的资源消耗：

```python
coordinator = ResponseCoordinator(
    budget_limits=BudgetLimits(
        max_agents=3,           # 最多3个Agent
        max_calls_per_round=5,  # 每轮最多5次调用
        max_tokens=15000,       # 最多15k tokens
        timeout_seconds=180.0   # 180秒超时
    )
)
```

### Agent优先级策略

**推荐配置**：
- Coordinator: 1-10（最高优先级）
- 专业Agent: 50-100（中等优先级）
- 辅助Agent: 200-500（较低优先级）

---

## 获取帮助

- **文档**：`docs/` 目录
- **问题追踪**：GitHub Issues
- **测试指南**：`TEST_GUIDE.md`
- **部署指南**：`DEPLOYMENT.md`
- **性能分析**：`PERFORMANCE.md`

---

**祝使用愉快！** 🚀
