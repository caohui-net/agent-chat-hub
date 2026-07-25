"""AI角色系统集成示例

演示如何使用AI角色系统创建基于角色的Agent。
"""
from src.core.models import AgentConfig
from src.core.role_integration import load_role_config, get_available_roles
from src.agents.rule_checker import RuleChecker


def create_role_based_agent_example():
    """示例：创建基于标准角色的Agent"""

    # 1. 查看可用角色
    available_roles = get_available_roles()
    print(f"可用角色: {available_roles}")

    # 2. 加载角色配置
    developer_config = load_role_config('developer')

    # 3. 创建Agent
    agent = AgentConfig(
        agent_id="dev-001",
        name="Python开发工程师",
        role="实现工程师",
        role_type="developer",
        role_config=developer_config,
        model_id="claude-opus-4.8",
        priority=100
    )

    print(f"✅ 创建Agent: {agent.name}")
    print(f"   角色类型: {agent.role_type}")
    print(f"   模型: {agent.model_id}")

    return agent


def rule_check_example():
    """示例：规则检查"""

    checker = RuleChecker()

    if not checker.is_available():
        print("⚠️ 规则引擎不可用")
        return

    # 检查agent选择
    violations = checker.check_agent_selection(
        session_id="example-session",
        selected_agents=["dev-001", "reviewer-001"],
        context={"operation": "code_review"}
    )

    if violations:
        print(f"❌ 规则违规: {len(violations)}个")
    else:
        print("✅ 规则检查通过")


if __name__ == '__main__':
    print("=== AI角色系统集成示例 ===\n")

    # 示例1: 创建基于角色的Agent
    print("示例1: 创建基于角色的Agent")
    agent = create_role_based_agent_example()
    print()

    # 示例2: 规则检查
    print("示例2: 规则检查")
    rule_check_example()
