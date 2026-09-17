"""
测试显式协调命令系统

测试 Phase 1.1 新增的显式命令功能：
- SCHEDULE: 调度指定 agents
- DELEGATE: 委托任务给指定 agents
- ACKNOWLEDGE: 确认收到，不响应
- COMPLETE: 标记完成
"""
import pytest
from src.agents.coordinator import ResponseCoordinator, BudgetLimits
from src.core.models import (
    AgentConfig,
    CoordinationCommand,
    CoordinationMode,
    ExplicitCoordinationRequest
)


@pytest.fixture
def coordinator():
    """创建协调器实例"""
    return ResponseCoordinator(BudgetLimits())


@pytest.fixture
def test_agents():
    """创建测试用的 agent 配置"""
    return [
        AgentConfig(
            agent_id="claude",
            name="Claude",
            role="技术助手",
            role_type="worker",
            model_id="claude-opus-4",
            priority=100,
            active=True
        ),
        AgentConfig(
            agent_id="codex",
            name="Codex",
            role="代码助手",
            role_type="worker",
            model_id="gpt-4",
            priority=200,
            active=True
        ),
        AgentConfig(
            agent_id="gemini",
            name="Gemini",
            role="通用助手",
            role_type="worker",
            model_id="gemini-pro",
            priority=300,
            active=True
        ),
        AgentConfig(
            agent_id="coordinator",
            name="Coordinator",
            role="总管",
            role_type="coordinator",
            model_id="claude-opus-4",
            priority=50,
            active=True
        ),
    ]


class TestExplicitScheduleCommand:
    """测试 SCHEDULE 命令"""

    def test_schedule_single_agent(self, coordinator, test_agents):
        """测试调度单个 agent"""
        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.SCHEDULE,
            agent_ids=["claude"],
            context="测试任务",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            explicit_request=request
        )

        assert len(selected) == 1
        assert selected[0].agent_id == "claude"
        assert coordinator.coordination_mode == CoordinationMode.EXPLICIT

    def test_schedule_multiple_agents(self, coordinator, test_agents):
        """测试调度多个 agents"""
        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.SCHEDULE,
            agent_ids=["claude", "codex"],
            context="测试任务",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            explicit_request=request
        )

        assert len(selected) == 2
        agent_ids = [a.agent_id for a in selected]
        assert "claude" in agent_ids
        assert "codex" in agent_ids

    def test_schedule_nonexistent_agent(self, coordinator, test_agents):
        """测试调度不存在的 agent"""
        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.SCHEDULE,
            agent_ids=["nonexistent"],
            context="测试任务",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            explicit_request=request
        )

        # 不存在的 agent 应该被忽略
        assert len(selected) == 0

    def test_schedule_inactive_agent(self, coordinator, test_agents):
        """测试调度未激活的 agent"""
        # 将 claude 设为未激活
        for agent in test_agents:
            if agent.agent_id == "claude":
                agent.active = False

        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.SCHEDULE,
            agent_ids=["claude"],
            context="测试任务",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            explicit_request=request
        )

        # 未激活的 agent 不应该被选中
        assert len(selected) == 0


class TestExplicitDelegateCommand:
    """测试 DELEGATE 命令"""

    def test_delegate_to_single_agent(self, coordinator, test_agents):
        """测试委托给单个 agent"""
        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.DELEGATE,
            agent_ids=["codex"],
            context="请优化代码",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            explicit_request=request
        )

        assert len(selected) == 1
        assert selected[0].agent_id == "codex"

    def test_delegate_to_multiple_agents(self, coordinator, test_agents):
        """测试委托给多个 agents"""
        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.DELEGATE,
            agent_ids=["claude", "codex", "gemini"],
            context="请协作完成任务",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            explicit_request=request
        )

        assert len(selected) == 3
        agent_ids = [a.agent_id for a in selected]
        assert "claude" in agent_ids
        assert "codex" in agent_ids
        assert "gemini" in agent_ids


class TestExplicitAcknowledgeCommand:
    """测试 ACKNOWLEDGE 命令"""

    def test_acknowledge_returns_empty(self, coordinator, test_agents):
        """测试 ACKNOWLEDGE 返回空列表"""
        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.ACKNOWLEDGE,
            agent_ids=["claude"],
            context="收到",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            explicit_request=request
        )

        # ACKNOWLEDGE 不应该选中任何 agent
        assert len(selected) == 0


class TestExplicitCompleteCommand:
    """测试 COMPLETE 命令"""

    def test_complete_returns_empty_and_marks_complete(self, coordinator, test_agents):
        """测试 COMPLETE 返回空列表并标记轮次完成"""
        coordinator.start_round("test-session", 1)

        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.COMPLETE,
            agent_ids=["claude"],
            context="任务完成",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            explicit_request=request
        )

        # COMPLETE 不应该选中任何 agent
        assert len(selected) == 0

        # 应该标记轮次完成
        from src.agents.coordinator import StopReason
        assert coordinator.current_round.stop_reason == StopReason.ROUND_COMPLETE


class TestExplicitModeOverridesAuto:
    """测试显式模式覆盖自动模式"""

    def test_explicit_overrides_mention_routing(self, coordinator, test_agents):
        """测试显式命令覆盖 @mention 路由"""
        # 提供 @mentions，但同时提供显式请求
        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.SCHEDULE,
            agent_ids=["codex"],  # 显式指定 codex
            context="测试任务",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            mentions=["claude"],  # @mentions 指定 claude
            explicit_request=request  # 但显式请求指定 codex
        )

        # 应该使用显式请求，忽略 @mentions
        assert len(selected) == 1
        assert selected[0].agent_id == "codex"

    def test_explicit_overrides_coordinator_default(self, coordinator, test_agents):
        """测试显式命令覆盖默认 coordinator 规则"""
        # 在自动模式下，无 @mentions 时只选择 coordinator
        # 但显式模式应该可以选择任意 agent

        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.SCHEDULE,
            agent_ids=["claude", "codex"],  # 显式指定 worker agents
            context="测试任务",
            round_num=1,
            session_id="test-session"
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            mentions=None,  # 无 @mentions
            explicit_request=request
        )

        # 应该选择显式指定的 agents，而不是 coordinator
        assert len(selected) == 2
        agent_ids = [a.agent_id for a in selected]
        assert "claude" in agent_ids
        assert "codex" in agent_ids
        assert "coordinator" not in agent_ids

    def test_auto_mode_without_explicit_request(self, coordinator, test_agents):
        """测试无显式请求时使用自动模式"""
        # 无显式请求，无 @mentions，应该只选择 coordinator
        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            mentions=None,
            explicit_request=None
        )

        assert len(selected) == 1
        assert selected[0].agent_id == "coordinator"


class TestExplicitRequestValidation:
    """测试显式请求数据验证"""

    def test_empty_agent_ids_raises_error(self):
        """测试空 agent_ids 列表抛出错误"""
        with pytest.raises(ValueError, match="agent_ids 不能为空"):
            ExplicitCoordinationRequest(
                command=CoordinationCommand.SCHEDULE,
                agent_ids=[],  # 空列表
                context="测试任务",
                round_num=1,
                session_id="test-session"
            )

    def test_valid_commands(self):
        """测试所有有效命令类型"""
        commands = [
            CoordinationCommand.SCHEDULE,
            CoordinationCommand.DELEGATE,
            CoordinationCommand.ACKNOWLEDGE,
            CoordinationCommand.COMPLETE
        ]

        for cmd in commands:
            request = ExplicitCoordinationRequest(
                command=cmd,
                agent_ids=["claude"],
                context="测试任务",
                round_num=1,
                session_id="test-session"
            )
            assert request.command == cmd


class TestExplicitWithPriorityOverride:
    """测试优先级覆盖功能"""

    def test_priority_override_metadata(self, coordinator, test_agents):
        """测试优先级覆盖作为元数据传递"""
        request = ExplicitCoordinationRequest(
            command=CoordinationCommand.SCHEDULE,
            agent_ids=["claude", "codex"],
            context="测试任务",
            round_num=1,
            session_id="test-session",
            priority_override=10  # 覆盖优先级
        )

        selected = coordinator.qualify_agents(
            available_agents=test_agents,
            explicit_request=request
        )

        # 应该选中指定的 agents
        assert len(selected) == 2
        # priority_override 当前不改变实际排序，只作为元数据存在
        assert request.priority_override == 10
