#!/usr/bin/env python3
"""调试@mention匹配问题"""

import json
from pathlib import Path
from src.core.models import AgentConfig
from src.core.mention_matcher import MentionMatcher
from src.core.mention_parser import parse_mentions

# 加载agents配置
config_path = Path.home() / ".agent-chat-hub" / "agents.json"
with open(config_path) as f:
    agents_data = json.load(f)

# 构造AgentConfig列表
agents = [AgentConfig(**data) for data in agents_data.values()]

print("=" * 60)
print("🔍 调试@mention匹配")
print("=" * 60)

# 测试用户输入
test_input = "@gemini 在不在？"
print(f"\n用户输入: {test_input}")

# 1. 解析mentions
mentions = parse_mentions(test_input)
print(f"\n步骤1 - 解析mentions: {mentions}")

# 2. 显示可用agents
print(f"\n步骤2 - 可用agents:")
for agent in agents:
    print(f"  - agent_id: {agent.agent_id}")
    print(f"    name: {agent.name}")
    print(f"    active: {agent.active}")

# 3. 尝试匹配每个mention
print(f"\n步骤3 - 匹配结果:")
for mention in mentions:
    print(f"\n  @{mention}:")
    matched = MentionMatcher.match_agent(agents, mention, threshold=0.6)
    if matched:
        print(f"    ✅ 匹配成功: {matched.agent_id} ({matched.name})")
    else:
        print(f"    ❌ 未匹配")

        # 详细检查
        print(f"\n    详细检查:")
        for agent in agents:
            mention_lower = mention.lower()
            agent_id_lower = agent.agent_id.lower()
            name_lower = agent.name.lower()

            # 精确匹配
            if agent_id_lower == mention_lower or name_lower == mention_lower:
                print(f"      {agent.agent_id}: ✅ 精确匹配")
            # 前缀匹配
            elif agent_id_lower.startswith(mention_lower) or name_lower.startswith(mention_lower):
                print(f"      {agent.agent_id}: ✅ 前缀匹配")
            # 包含匹配
            elif mention_lower in agent_id_lower or mention_lower in name_lower:
                print(f"      {agent.agent_id}: ✅ 包含匹配 ('{mention_lower}' in '{agent_id_lower}')")
            else:
                print(f"      {agent.agent_id}: ❌ 不匹配")

print("\n" + "=" * 60)
