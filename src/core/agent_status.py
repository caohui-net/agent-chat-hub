"""Agent状态追踪 - 实时追踪Agent的执行状态"""

import time
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

import structlog

logger = structlog.get_logger()


class AgentStatus(Enum):
    """Agent执行状态枚举"""

    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    ERROR = "error"          # 出错


@dataclass
class AgentState:
    """Agent状态数据"""

    agent_id: str
    status: AgentStatus
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    error: Optional[str] = None

    @property
    def elapsed_seconds(self) -> float:
        """计算已执行时间（秒）"""
        if not self.start_time:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def total_tokens(self) -> int:
        """计算总token数"""
        return self.input_tokens + self.output_tokens


class AgentStatusManager:
    """追踪所有Agent的实时状态"""

    def __init__(self):
        self.states: Dict[str, AgentState] = {}
        logger.info("agent_status_manager_initialized")

    def mark_pending(self, agent_id: str) -> None:
        """标记Agent为等待状态"""
        self.states[agent_id] = AgentState(
            agent_id=agent_id,
            status=AgentStatus.PENDING
        )
        logger.debug("agent_status_pending", agent_id=agent_id)

    def mark_running(self, agent_id: str) -> None:
        """标记Agent为执行中状态"""
        state = self.states.get(agent_id)
        if state:
            state.status = AgentStatus.RUNNING
            state.start_time = time.time()
        else:
            self.states[agent_id] = AgentState(
                agent_id=agent_id,
                status=AgentStatus.RUNNING,
                start_time=time.time()
            )
        logger.info("agent_status_running", agent_id=agent_id)

    def mark_completed(
        self,
        agent_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> None:
        """标记Agent为已完成状态"""
        state = self.states.get(agent_id)
        if state:
            state.status = AgentStatus.COMPLETED
            state.end_time = time.time()
            state.input_tokens = input_tokens
            state.output_tokens = output_tokens

            logger.info(
                "agent_status_completed",
                agent_id=agent_id,
                elapsed_seconds=state.elapsed_seconds,
                total_tokens=state.total_tokens
            )
        else:
            logger.warning("agent_status_not_found", agent_id=agent_id)

    def mark_error(self, agent_id: str, error: str) -> None:
        """标记Agent为错误状态"""
        state = self.states.get(agent_id)
        if state:
            state.status = AgentStatus.ERROR
            state.end_time = time.time()
            state.error = error

            logger.error(
                "agent_status_error",
                agent_id=agent_id,
                error=error,
                elapsed_seconds=state.elapsed_seconds
            )
        else:
            logger.warning("agent_status_not_found", agent_id=agent_id)

    def get_status(self, agent_id: str) -> Optional[AgentState]:
        """获取Agent的状态"""
        return self.states.get(agent_id)

    def get_all_statuses(self) -> Dict[str, AgentState]:
        """获取所有Agent的状态"""
        return dict(self.states)

    def get_running_agents(self) -> Dict[str, AgentState]:
        """获取所有正在执行的Agent"""
        return {
            agent_id: state
            for agent_id, state in self.states.items()
            if state.status == AgentStatus.RUNNING
        }

    def get_completed_agents(self) -> Dict[str, AgentState]:
        """获取所有已完成的Agent"""
        return {
            agent_id: state
            for agent_id, state in self.states.items()
            if state.status == AgentStatus.COMPLETED
        }

    def get_failed_agents(self) -> Dict[str, AgentState]:
        """获取所有失败的Agent"""
        return {
            agent_id: state
            for agent_id, state in self.states.items()
            if state.status == AgentStatus.ERROR
        }

    def clear_agent_status(self, agent_id: str) -> bool:
        """清除Agent的状态"""
        if agent_id in self.states:
            del self.states[agent_id]
            logger.debug("agent_status_cleared", agent_id=agent_id)
            return True
        return False

    def clear_all_statuses(self) -> None:
        """清除所有Agent的状态"""
        self.states.clear()
        logger.info("all_agent_statuses_cleared")

    def get_summary(self) -> Dict[str, int]:
        """获取状态统计摘要"""
        summary = {
            "total": len(self.states),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "error": 0
        }

        for state in self.states.values():
            if state.status == AgentStatus.PENDING:
                summary["pending"] += 1
            elif state.status == AgentStatus.RUNNING:
                summary["running"] += 1
            elif state.status == AgentStatus.COMPLETED:
                summary["completed"] += 1
            elif state.status == AgentStatus.ERROR:
                summary["error"] += 1

        return summary
