# 创建你的第一个Agent - 教程

从零开始创建一个自定义Agent的完整教程

---

## 目标

在本教程中，你将学会：
1. 理解Agent的基本结构
2. 创建一个自定义Agent
3. 配置Agent的行为
4. 测试和调试Agent
5. 在TUI中使用Agent

**预计时间**: 15分钟

---

## 前置条件

- 已完成[快速开始](../user-guide/QUICKSTART.md)
- Agent Chat Hub正常运行
- 基本的JSON知识

---

## 步骤1: 理解Agent结构

### Agent配置文件

Agent配置存储在 `~/.agent-chat-hub/agents.json`：

```json
{
  "agents": [
    {
      "id": "agent_researcher",
      "name": "researcher",
      "role": "research",
      "model_id": "claude-sonnet-3-5",
      "provider": "anthropic",
      "system_prompt": "You are a research assistant...",
      "temperature": 0.7,
      "max_tokens": 4096,
      "enabled": true
    }
  ]
}
```

### 字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `id` | Agent唯一标识符 | `agent_translator` |
| `name` | Agent名称（@mention使用） | `translator` |
| `role` | Agent角色类型 | `translation` |
| `model_id` | 使用的模型 | `claude-sonnet-3-5` |
| `provider` | 模型提供商 | `anthropic` 或 `openai` |
| `system_prompt` | 系统提示词（定义Agent行为） | 见下文 |
| `temperature` | 创意程度（0.0-1.0） | `0.5` |
| `max_tokens` | 最大输出token数 | `4096` |
| `enabled` | 是否启用 | `true` |

---

## 步骤2: 设计你的Agent

### 场景: 创建一个翻译Agent

我们将创建一个专业的翻译Agent，能够：
- 在中英文之间互译
- 保持原文语气和风格
- 处理技术文档翻译

### Agent规划

| 属性 | 值 | 理由 |
|------|-----|------|
| **ID** | `agent_translator` | 唯一标识符 |
| **名称** | `translator` | 简短易记 |
| **角色** | `translation` | 明确职责 |
| **模型** | `claude-sonnet-3-5` | 多语言能力强 |
| **温度** | `0.3` | 翻译需要准确性 |
| **最大Token** | `8192` | 支持长文档 |

---

## 步骤3: 编写System Prompt

System Prompt是Agent的"灵魂"，定义其行为和能力。

### 基础模板

```
You are a [角色描述].

Your strengths include:
- [能力1]
- [能力2]
- [能力3]

Guidelines:
- [指导原则1]
- [指导原则2]

Always [期望行为].
```

### 翻译Agent的System Prompt

```
You are a professional translator specializing in Chinese-English translation.

Your strengths include:
- Accurate translation while preserving meaning and tone
- Handling technical terminology correctly
- Adapting style for different contexts (formal, casual, technical)
- Providing natural, fluent translations

Guidelines:
- Detect the source language automatically (Chinese or English)
- Translate to the opposite language
- Preserve formatting (markdown, code blocks, etc.)
- For technical terms, provide the original term in parentheses if helpful
- Maintain the same level of formality as the source text

Always provide clear, natural translations that read as if originally written in the target language.
```

### System Prompt最佳实践

✅ **好的做法**：
- 清晰定义角色和职责
- 具体列出能力和行为
- 提供明确的指导原则
- 使用祈使句（"Always...", "Do not..."）

❌ **避免**：
- 模糊的描述（"尽力而为"）
- 相互矛盾的指令
- 过于冗长（>500词）
- 包含示例对话（占用token）

---

## 步骤4: 创建Agent配置

### 方法1: 使用配置向导（推荐）

```bash
python init_config.py
```

选择"创建新Agent"，按提示输入：

```
Agent名称: translator
角色类型: translation
模型: claude-sonnet-3-5
温度: 0.3
最大Token: 8192
```

System Prompt可以在创建后手动编辑。

### 方法2: 手动编辑配置文件

```bash
# 编辑配置文件
nano ~/.agent-chat-hub/agents.json
```

添加新Agent配置：

```json
{
  "agents": [
    {
      "id": "agent_translator",
      "name": "translator",
      "role": "translation",
      "model_id": "claude-sonnet-3-5",
      "provider": "anthropic",
      "system_prompt": "You are a professional translator specializing in Chinese-English translation.\n\nYour strengths include:\n- Accurate translation while preserving meaning and tone\n- Handling technical terminology correctly\n- Adapting style for different contexts (formal, casual, technical)\n- Providing natural, fluent translations\n\nGuidelines:\n- Detect the source language automatically (Chinese or English)\n- Translate to the opposite language\n- Preserve formatting (markdown, code blocks, etc.)\n- For technical terms, provide the original term in parentheses if helpful\n- Maintain the same level of formality as the source text\n\nAlways provide clear, natural translations that read as if originally written in the target language.",
      "temperature": 0.3,
      "max_tokens": 8192,
      "enabled": true
    }
  ]
}
```

**注意**: JSON中的换行符需要使用 `\n`

---

## 步骤5: 验证配置

### 检查配置文件

```python
python -c "
import json
from pathlib import Path

config_path = Path.home() / '.agent-chat-hub' / 'agents.json'
with open(config_path) as f:
    config = json.load(f)

translator = next(
    (a for a in config['agents'] if a['id'] == 'agent_translator'),
    None
)

if translator:
    print('✅ Agent配置已创建')
    print(f'名称: {translator[\"name\"]}')
    print(f'模型: {translator[\"model_id\"]}')
    print(f'温度: {translator[\"temperature\"]}')
else:
    print('❌ Agent未找到')
"
```

### 测试Agent加载

```python
python -c "
from src.core.config import ConfigManager

config = ConfigManager()
agent = config.get_agent('agent_translator')

if agent:
    print('✅ Agent加载成功')
    print(f'ID: {agent.agent_id}')
    print(f'名称: {agent.name}')
    print(f'角色: {agent.role}')
else:
    print('❌ Agent加载失败')
"
```

---

## 步骤6: 测试Agent

### 方法1: 在TUI中测试

```bash
# 启动应用
./start.sh
```

在输入框中输入：

```
@translator 请翻译: Hello, how are you?
```

预期输出：

```
translator: 你好，你好吗？
```

### 方法2: 使用Python脚本测试

创建测试脚本 `test_translator.py`：

```python
import asyncio
from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager

async def test_translator():
    # 初始化
    config_manager = ConfigManager()
    coordinator = ResponseCoordinator()
    executor = AgentExecutor(config_manager)
    session_manager = SessionManager(config_manager, coordinator, executor)
    
    # 创建会话
    session_manager.create_session("翻译测试")
    
    # 测试用例
    test_cases = [
        "@translator Translate: 人工智能正在改变世界",
        "@translator Translate: Machine learning is a subset of AI",
        "@translator 翻译这段技术文档: The API endpoint returns a JSON response"
    ]
    
    for test_input in test_cases:
        print(f"\n{'='*60}")
        print(f"输入: {test_input}")
        print(f"{'-'*60}")
        
        responses = await session_manager.process_user_input(test_input)
        
        for response in responses:
            print(f"{response.agent_id}:")
            print(response.content)
            print(f"\nToken: {response.token_usage.total_tokens}")
    
    # 清理
    await executor.aclose()

if __name__ == "__main__":
    asyncio.run(test_translator())
```

运行测试：

```bash
python test_translator.py
```

---

## 步骤7: 调试和优化

### 常见问题和解决方案

#### 问题1: Agent无响应

**检查**：
```python
python -c "
from src.core.config import ConfigManager
config = ConfigManager()
agent = config.get_agent('agent_translator')
print(f'已启用: {agent.enabled if agent else \"Agent不存在\"}')
"
```

**解决**：确保 `enabled: true`

#### 问题2: 翻译质量不佳

**优化System Prompt**：
- 添加更多示例场景
- 明确输出格式
- 调整温度参数（降低到0.2）

#### 问题3: 响应过长

**解决**：
- 减少 `max_tokens`（如从8192减到4096）
- 在System Prompt中添加："Keep translations concise"

#### 问题4: Token消耗过多

**检查Token使用**：
```python
from src.agents.session import SessionManager

stats = session_manager.token_tracker.get_session_stats()
translator_stats = stats['by_agent'].get('agent_translator', {})

print(f"平均Token/请求: {translator_stats['total'] / num_requests}")
```

**优化**：
- 缩短System Prompt
- 降低 `max_tokens`
- 使用更小的模型（如claude-haiku-3）

---

## 步骤8: 高级配置

### 添加角色特定行为

为不同类型的翻译任务创建专门的Agent：

```json
{
  "id": "agent_tech_translator",
  "name": "tech_translator",
  "role": "technical_translation",
  "system_prompt": "You are a technical translator specializing in software documentation...",
  "temperature": 0.2
}
```

### 使用不同模型

比较不同模型的效果：

| 模型 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| claude-haiku-3 | 简单翻译 | 快速、便宜 | 质量一般 |
| claude-sonnet-3-5 | 通用翻译 | 平衡 | - |
| claude-opus-3 | 复杂文档 | 高质量 | 慢、贵 |
| gpt-4-turbo | 技术翻译 | 术语准确 | - |

### 添加上下文管理

在System Prompt中添加：

```
Context awareness:
- Remember terminology preferences from earlier in the conversation
- Maintain consistent translation choices for recurring terms
- Reference previous translations when asked
```

---

## 步骤9: 与其他Agent协作

### 场景: 翻译+审查工作流

创建一个审查Agent来检查翻译质量：

```json
{
  "id": "agent_translation_reviewer",
  "name": "translation_reviewer",
  "role": "review",
  "system_prompt": "You are a translation quality reviewer. Review translations for:\n- Accuracy\n- Natural flow\n- Terminology consistency\n- Grammar\n\nProvide constructive feedback.",
  "temperature": 0.5,
  "max_tokens": 4096,
  "enabled": true
}
```

### 使用协作流程

```bash
# 在TUI中
User: @translator 翻译: The quick brown fox jumps over the lazy dog
translator: 敏捷的棕色狐狸跳过懒狗

User: @translation_reviewer 审查上面的翻译
translation_reviewer: 翻译准确，建议将"懒狗"改为"懒洋洋的狗"以更好地传达原文语气
```

---

## 步骤10: 持续改进

### 收集反馈

记录Agent的表现：
- 成功的翻译案例
- 失败或不准确的案例
- 用户反馈

### 迭代System Prompt

根据反馈调整：

**版本1**（初始）：
```
You are a translator.
```

**版本2**（添加能力）：
```
You are a translator.
Translate accurately while preserving tone.
```

**版本3**（添加指导原则）：
```
You are a professional translator.
- Preserve tone and style
- Handle technical terms correctly
- Provide natural translations
```

**版本4**（当前最佳）：
```
You are a professional translator specializing in Chinese-English translation.
[完整版本见步骤3]
```

### 性能监控

定期检查：
```python
# Token使用趋势
stats = token_tracker.get_session_stats()

# 平均响应时间
avg_time = sum(times) / len(times)

# 错误率
error_rate = errors / total_requests
```

---

## 完整示例代码

### test_translator_complete.py

```python
"""
完整的翻译Agent测试脚本
展示创建、配置、测试的完整流程
"""
import asyncio
import json
from pathlib import Path
from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager

async def main():
    print("🚀 开始测试翻译Agent\n")
    
    # 1. 检查Agent是否存在
    config_manager = ConfigManager()
    agent = config_manager.get_agent("agent_translator")
    
    if not agent:
        print("❌ Agent未找到，请先创建Agent")
        return
    
    print(f"✅ Agent已加载")
    print(f"   名称: {agent.name}")
    print(f"   模型: {agent.model_id}")
    print(f"   温度: {agent.temperature}\n")
    
    # 2. 初始化会话
    coordinator = ResponseCoordinator()
    executor = AgentExecutor(config_manager)
    session_manager = SessionManager(config_manager, coordinator, executor)
    session_manager.create_session("翻译测试")
    
    # 3. 测试用例
    test_cases = [
        {
            "name": "中译英 - 简单句子",
            "input": "@translator 翻译: 今天天气很好",
            "expected": "英文翻译"
        },
        {
            "name": "英译中 - 技术术语",
            "input": "@translator Translate: Machine learning models require training data",
            "expected": "中文翻译"
        },
        {
            "name": "中译英 - 长文本",
            "input": "@translator 翻译这段话: 人工智能技术正在快速发展，深度学习和神经网络已经在图像识别、自然语言处理等领域取得了显著成果。",
            "expected": "英文翻译"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{'='*70}")
        print(f"测试 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'-'*70}")
        print(f"输入: {test_case['input']}\n")
        
        try:
            responses = await session_manager.process_user_input(test_case['input'])
            
            for response in responses:
                print(f"✅ {response.agent_id}:")
                print(f"   {response.content}\n")
                print(f"   📊 Token使用: {response.token_usage.total_tokens}")
                print(f"   ⏱️  响应时间: {response.timestamp:.2f}s\n")
                
                results.append({
                    "test": test_case['name'],
                    "success": True,
                    "tokens": response.token_usage.total_tokens
                })
        
        except Exception as e:
            print(f"❌ 测试失败: {e}\n")
            results.append({
                "test": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    # 4. 统计报告
    print(f"{'='*70}")
    print("📊 测试总结\n")
    
    success_count = sum(1 for r in results if r.get('success'))
    total_tokens = sum(r.get('tokens', 0) for r in results)
    
    print(f"成功: {success_count}/{len(results)}")
    print(f"总Token: {total_tokens:,}")
    print(f"平均Token/请求: {total_tokens // len(results)}\n")
    
    # 5. Token统计
    stats = session_manager.token_tracker.get_session_stats()
    print(f"会话Token统计:")
    print(f"  输入: {stats['total_input_tokens']:,}")
    print(f"  输出: {stats['total_output_tokens']:,}")
    print(f"  总计: {stats['total_tokens']:,}")
    print(f"  成本: ${stats['total_cost_usd']:.4f}\n")
    
    # 6. 清理
    await executor.aclose()
    print("✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python test_translator_complete.py
```

---

## 下一步

恭喜！你已经成功创建了第一个自定义Agent。

继续探索：
1. **创建更多Agent** - 尝试其他角色（代码审查、文档写作等）
2. **Agent协作** - 设计多Agent工作流
3. **集成插件** - 为Agent添加工具能力
4. **性能优化** - 调整参数以平衡质量和成本

---

## 相关文档

- [配置指南](../user-guide/CONFIGURATION.md) - 详细配置说明
- [API参考](../api-reference/API.md) - API文档
- [故障排除](../user-guide/TROUBLESHOOTING.md) - 常见问题

---

## 附录: Agent角色模板

### 研究分析Agent

```
You are a research analyst specializing in information synthesis and insight extraction.

Your strengths include:
- Breaking down complex topics into understandable components
- Identifying patterns and connections across information
- Summarizing key findings with supporting evidence
- Providing balanced, well-reasoned analysis

Guidelines:
- Cite sources when making factual claims
- Present multiple perspectives on controversial topics
- Use clear structure (intro, analysis, conclusion)
- Highlight key insights and actionable recommendations

Always provide thorough, well-structured analysis backed by evidence.
```

### 代码编写Agent

```
You are a software engineer specializing in writing clean, maintainable code.

Your strengths include:
- Writing production-ready code following best practices
- Clear documentation and helpful comments
- Error handling and edge case consideration
- Performance optimization

Guidelines:
- Follow language-specific conventions
- Write self-documenting code with clear variable names
- Include docstrings for functions and classes
- Handle errors gracefully with try-except blocks
- Test your code mentally before outputting

Always write code that is readable, maintainable, and follows industry standards.
```

### 文档写作Agent

```
You are a technical writer specializing in clear, user-friendly documentation.

Your strengths include:
- Explaining complex concepts in simple terms
- Structured, scannable content with clear headings
- Appropriate use of examples and code snippets
- Consistent style and terminology

Guidelines:
- Start with a clear overview
- Use active voice and present tense
- Include practical examples
- Format for readability (bullets, code blocks, tables)
- Define technical terms on first use

Always create documentation that is clear, complete, and easy to follow.
```

---

**版本**: v1.0  
**更新日期**: 2026-09-06  
**预计完成时间**: 15分钟
