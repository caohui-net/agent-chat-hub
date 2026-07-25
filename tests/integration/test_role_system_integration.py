"""
AI角色系统集成测试

测试RuleChecker和ModelRouter与ResponseCoordinator/Executor的集成
"""
import pytest
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.core.models import AgentConfig
from src.core.config import ConfigManager


class TestRoleSystemIntegration:
    """AI角色系统集成测试"""

    def test_coordinator_with_rule_checker(self):
        """测试ResponseCoordinator集成RuleChecker"""
        coordinator = ResponseCoordinator()

        # 验证rule_checker已初始化
        assert hasattr(coordinator, 'rule_checker')
        assert coordinator.rule_checker is not None

    def test_executor_with_model_router(self, tmp_path):
        """测试Executor集成ModelRouter"""
        config_manager = ConfigManager(config_dir=tmp_path)
        executor = AgentExecutor(config_manager)

        # 验证model_router属性存在
        assert hasattr(executor, 'model_router')
        # ModelRouter可能不可用（取决于AI角色系统是否存在）

    def test_agent_with_role_type(self):
        """测试AgentConfig支持role_type和role_config"""
        agent = AgentConfig(
            agent_id="test-001",
            name="测试Agent",
            model_id="claude-3-opus",
            role="developer",
            role_type="developer",  # 新增字段
            role_config={  # 新增字段
                "task_type": "code_review",
                "complexity": "medium"
            }
        )

        assert agent.role_type == "developer"
        assert agent.role_config["task_type"] == "code_review"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
