#!/usr/bin/env python3
"""验证P1-002修复：Agent排序逻辑"""

import sys
sys.path.insert(0, '.')

from src.agents.coordinator import ResponseCoordinator, BudgetLimits
from src.core.models import AgentConfig

# 创建测试agents（不同priority）
agents = [
    AgentConfig(agent_id="c", name="C", role="assistant", model_id="m1", priority=300, active=True),
    AgentConfig(agent_id="a", name="A", role="assistant", model_id="m1", priority=100, active=True),
    AgentConfig(agent_id="b", name="B", role="assistant", model_id="m1", priority=200, active=True),
    AgentConfig(agent_id="d", name="D", role="assistant", model_id="m1", priority=150, active=True),
    AgentConfig(agent_id="e", name="E", role="assistant", model_id="m1", priority=250, active=True),
]

# 创建coordinator（max_agents=3）
coord = ResponseCoordinator(BudgetLimits(max_agents=3, max_calls_per_round=3, max_tokens=10000))

# 调用qualify_agents
qualified = coord.qualify_agents(agents, max_agents=3)

# 验证结果
print("输入agents（未排序）:")
for a in agents:
    print(f"  {a.agent_id}: priority={a.priority}")

print(f"\n返回的qualified agents（应按priority升序，取前3个）:")
for a in qualified:
    print(f"  {a.agent_id}: priority={a.priority}")

# 验证
expected_ids = ["a", "d", "b"]  # priority: 100, 150, 200
actual_ids = [a.agent_id for a in qualified]

print(f"\n预期: {expected_ids}")
print(f"实际: {actual_ids}")

if actual_ids == expected_ids:
    print("\n✅ 测试通过：排序逻辑正确")
    sys.exit(0)
else:
    print("\n❌ 测试失败：排序逻辑错误")
    sys.exit(1)
