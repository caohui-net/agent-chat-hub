#!/usr/bin/env python3
"""简化测试：只测试mention匹配"""

import json
from pathlib import Path
from src.core.models import AgentConfig
from src.core.mention_matcher import MentionMatcher
from src.core.mention_parser import parse_mentions

# 1. 加载agents配置
config_path = Path.home() / ".agent-chat-hub" / "agents.json"
with open(config_path) as f:
    agents_data = json.load(f)

agents = [AgentConfig(**data) for data in agents_data.values()]

# 2. 测试输入
test_input = "@gemini 在不在？"
print(f"用户输入: {test_input}")

# 3. 解析mentions
mentions = parse_mentions(test_input)
print(f"解析mentions: {mentions}")

# 4. 匹配
print("\n匹配结果:")
for mention in mentions:
    matched = MentionMatcher.match_agent(agents, mention, threshold=0.6)
    if matched:
        print(f"  @{mention} -> ✅ {matched.agent_id} ({matched.name})")
    else:
        print(f"  @{mention} -> ❌ 未匹配")
