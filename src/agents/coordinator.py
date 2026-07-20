"""
响应协调器 - 实现6条响应控制规则

根据 ADR-0001 规范：
1. Qualification Rule: 确定性路由，基于配置
2. Ordering Rule: 配置优先级升序 + agent_id字典序
3. Deduplication Rule: (session, round, agent) 三元组去重
4. Cancellation Rule: 取消后禁止新调用，标记延迟输出
5. Budget Rule: MVP限额（3 agents, 3 calls, 12k tokens, 120s）
6. Stop Rule: 6种停止条件，禁止agent自动续轮
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Set, Tuple
from time import time

from src.core.models import AgentConfig, Message


class StopReason(Enum):
    """停止原因枚举"""
    USER_CANCEL = "user_cancel"          # 用户取消
    BUDGET_EXCEEDED = "budget_exceeded"   # 超出预算
    TIMEOUT = "timeout"                   # 超时
    MAX_CALLS = "max_calls"               # 达到最大调用次数
    NO_AGENTS = "no_agents"               # 无可用agent
    ROUND_COMPLETE = "round_complete"     # 轮次完成


@dataclass
class CallRecord:
    """调用记录 - 用于去重"""
    session_id: str
    round_num: int
    agent_id: str
    timestamp: float = field(default_factory=time)

    def as_tuple(self) -> Tuple[str, int, str]:
        """返回去重用的三元组"""
        return (self.session_id, self.round_num, self.agent_id)


@dataclass
class BudgetLimits:
    """预算限制配置"""
    max_agents: int = 3           # 最大并发agent数
    max_calls_per_round: int = 3  # 每轮最大调用次数
    max_tokens: int = 12000       # 最大token数
    timeout_seconds: float = 120.0  # 超时时间（秒）


@dataclass
class RoundState:
    """轮次状态"""
    round_num: int
    session_id: str
    start_time: float = field(default_factory=time)
    call_records: Set[Tuple[str, int, str]] = field(default_factory=set)
    total_calls: int = 0
    total_tokens: int = 0
    cancelled: bool = False
    stop_reason: Optional[StopReason] = None


class ResponseCoordinator:
    """
    响应协调器 - 多agent响应控制核心

    职责：
    - 实现6条响应控制规则
    - 管理轮次状态
    - 协调agent调用顺序
    - 监控预算和超时
    """

    def __init__(self, budget_limits: Optional[BudgetLimits] = None):
        """初始化协调器

        Args:
            budget_limits: 预算限制配置，默认使用MVP限额
        """
        self.budget_limits = budget_limits or BudgetLimits()
        self.current_round: Optional[RoundState] = None

    def start_round(self, session_id: str, round_num: int) -> None:
        """开始新的一轮对话

        Args:
            session_id: 会话ID
            round_num: 轮次编号
        """
        self.current_round = RoundState(
            round_num=round_num,
            session_id=session_id
        )

    def cancel_round(self) -> None:
        """取消当前轮次（Rule 4: Cancellation）"""
        if self.current_round:
            self.current_round.cancelled = True
            self.current_round.stop_reason = StopReason.USER_CANCEL

    def sort_agents(self, agents: List[AgentConfig]) -> List[AgentConfig]:
        """Rule 2: Ordering - 对agents排序

        排序规则：
        1. 优先级升序（priority字段，数值越小越优先）
        2. 相同优先级按agent_id字典序

        Args:
            agents: 待排序的agent列表

        Returns:
            排序后的agent列表
        """
        return sorted(agents, key=lambda a: (a.priority, a.agent_id))

    def is_duplicate_call(self, agent_id: str) -> bool:
        """Rule 3: Deduplication - 检查是否重复调用

        去重规则：(session_id, round_num, agent_id) 三元组唯一

        Args:
            agent_id: 要检查的agent ID

        Returns:
            True if 重复，False if 不重复
        """
        if not self.current_round:
            return False

        call_tuple = (
            self.current_round.session_id,
            self.current_round.round_num,
            agent_id
        )
        return call_tuple in self.current_round.call_records

    def record_call(self, agent_id: str, tokens_used: int = 0) -> None:
        """记录agent调用

        Args:
            agent_id: agent ID
            tokens_used: 本次调用使用的token数
        """
        if not self.current_round:
            return

        call_tuple = (
            self.current_round.session_id,
            self.current_round.round_num,
            agent_id
        )
        self.current_round.call_records.add(call_tuple)
        self.current_round.total_calls += 1
        self.current_round.total_tokens += tokens_used

    def check_budget(self) -> Optional[StopReason]:
        """Rule 5: Budget - 检查预算限制

        检查项：
        1. 超时：round运行时间 > timeout_seconds
        2. 调用次数：total_calls >= max_calls_per_round
        3. Token数：total_tokens >= max_tokens

        Returns:
            StopReason if 超出预算，None if 未超出
        """
        if not self.current_round:
            return None

        # 检查超时
        elapsed = time() - self.current_round.start_time
        if elapsed >= self.budget_limits.timeout_seconds:
            return StopReason.TIMEOUT

        # 检查调用次数
        if self.current_round.total_calls >= self.budget_limits.max_calls_per_round:
            return StopReason.MAX_CALLS

        # 检查token数
        if self.current_round.total_tokens >= self.budget_limits.max_tokens:
            return StopReason.BUDGET_EXCEEDED

        return None

    def qualify_agents(
        self,
        available_agents: List[AgentConfig],
        max_agents: Optional[int] = None
    ) -> List[AgentConfig]:
        """Rule 1: Qualification - 资格判定

        确定性路由规则：
        1. 仅选择active=True的agents
        2. 最多选择max_agents个（默认使用budget限制）
        3. 不依赖agent自报资格，完全基于配置

        Args:
            available_agents: 可用的agent配置列表
            max_agents: 最大agent数，默认使用预算限制

        Returns:
            合格的agent列表
        """
        max_count = max_agents if max_agents is not None else self.budget_limits.max_agents

        # 过滤active agents
        qualified = [a for a in available_agents if a.active]

        # 按priority升序排序，相同priority按agent_id字典序（与sort_agents保持一致）
        qualified_sorted = sorted(qualified, key=lambda a: (a.priority, a.agent_id))

        # 限制数量（应用在排序后）
        return qualified_sorted[:max_count] if len(qualified_sorted) > max_count else qualified_sorted

    def should_stop(self) -> Tuple[bool, Optional[StopReason]]:
        """Rule 6: Stop - 检查是否应该停止

        停止条件（满足任一即停止）：
        1. 用户取消（cancelled=True）
        2. 超出预算（check_budget返回非None）
        3. 无可用agents（qualified agents为空）
        4. 轮次已完成（round_complete标记）

        Returns:
            (should_stop, reason) 元组
        """
        if not self.current_round:
            return (True, StopReason.NO_AGENTS)

        # 检查取消
        if self.current_round.cancelled:
            return (True, StopReason.USER_CANCEL)

        # 检查预算
        budget_reason = self.check_budget()
        if budget_reason:
            self.current_round.stop_reason = budget_reason
            return (True, budget_reason)

        # 检查是否已标记完成
        if self.current_round.stop_reason == StopReason.ROUND_COMPLETE:
            return (True, StopReason.ROUND_COMPLETE)

        return (False, None)

    def select_agents(
        self,
        available_agents: List[AgentConfig]
    ) -> Tuple[List[AgentConfig], Optional[StopReason]]:
        """选择本轮应该调用的agents（整合所有规则）

        执行流程：
        1. 检查停止条件（Rule 6）
        2. 资格判定（Rule 1）
        3. 排序（Rule 2）
        4. 去重过滤（Rule 3）
        5. 应用预算限制（Rule 5）

        Args:
            available_agents: 可用的agent配置列表

        Returns:
            (selected_agents, stop_reason) 元组
            - selected_agents: 选中的agents（空列表if应该停止）
            - stop_reason: 停止原因（None if未停止）
        """
        # Rule 6: 检查停止条件
        should_stop, stop_reason = self.should_stop()
        if should_stop:
            return ([], stop_reason)

        # Rule 1: 资格判定
        qualified = self.qualify_agents(available_agents)
        if not qualified:
            self.current_round.stop_reason = StopReason.NO_AGENTS
            return ([], StopReason.NO_AGENTS)

        # Rule 2: 排序
        sorted_agents = self.sort_agents(qualified)

        # Rule 3: 去重过滤
        non_duplicate = [
            agent for agent in sorted_agents
            if not self.is_duplicate_call(agent.agent_id)
        ]

        if not non_duplicate:
            # 所有agents都已调用过，标记轮次完成
            self.current_round.stop_reason = StopReason.ROUND_COMPLETE
            return ([], StopReason.ROUND_COMPLETE)

        return (non_duplicate, None)

    def mark_round_complete(self) -> None:
        """标记当前轮次完成"""
        if self.current_round:
            self.current_round.stop_reason = StopReason.ROUND_COMPLETE

    def get_round_stats(self) -> dict:
        """获取当前轮次统计信息

        Returns:
            包含统计信息的字典
        """
        if not self.current_round:
            return {}

        elapsed = time() - self.current_round.start_time
        return {
            "round_num": self.current_round.round_num,
            "session_id": self.current_round.session_id,
            "total_calls": self.current_round.total_calls,
            "total_tokens": self.current_round.total_tokens,
            "elapsed_seconds": elapsed,
            "cancelled": self.current_round.cancelled,
            "stop_reason": self.current_round.stop_reason.value if self.current_round.stop_reason else None,
            "budget_usage": {
                "calls": f"{self.current_round.total_calls}/{self.budget_limits.max_calls_per_round}",
                "tokens": f"{self.current_round.total_tokens}/{self.budget_limits.max_tokens}",
                "time": f"{elapsed:.1f}/{self.budget_limits.timeout_seconds}",
            }
        }

