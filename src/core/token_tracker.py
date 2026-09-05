"""Token追踪与成本计算 - 追踪Agent的Token使用和成本"""

import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List

import structlog

logger = structlog.get_logger()


@dataclass
class AgentTokenUsage:
    """Agent的Token使用记录"""

    agent_id: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    timestamp: float = field(default_factory=time.time)

    @property
    def total_tokens(self) -> int:
        """计算总Token数"""
        return self.input_tokens + self.output_tokens

    def estimate_cost(self, price_table: Dict[str, Dict[str, float]]) -> float:
        """
        估算成本（美元）

        Args:
            price_table: 价格表 {model: {"input": price_per_1M, "output": price_per_1M}}

        Returns:
            估算成本（美元）
        """
        prices = price_table.get(self.model, {})
        input_price = prices.get("input", 0.0)
        output_price = prices.get("output", 0.0)

        input_cost = (self.input_tokens * input_price) / 1_000_000
        output_cost = (self.output_tokens * output_price) / 1_000_000

        return input_cost + output_cost


class TokenTracker:
    """追踪Token使用情况和成本"""

    # 模型价格表（美元/百万tokens）
    PRICE_TABLE = {
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "claude-opus-4-8": {"input": 15.0, "output": 75.0},
        "claude-sonnet-5": {"input": 3.0, "output": 15.0},
        "claude-sonnet-4": {"input": 3.0, "output": 15.0},
        "claude-haiku-4": {"input": 0.25, "output": 1.25},
        "claude-haiku-4-5": {"input": 0.25, "output": 1.25},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    }

    def __init__(self):
        self.usage_history: List[AgentTokenUsage] = []
        logger.info("token_tracker_initialized")

    def record_usage(self, usage: AgentTokenUsage) -> None:
        """
        记录Token使用

        Args:
            usage: Token使用记录
        """
        self.usage_history.append(usage)
        cost = usage.estimate_cost(self.PRICE_TABLE)

        logger.info(
            "token_usage_recorded",
            agent_id=usage.agent_id,
            model=usage.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            cost_usd=cost
        )

    def get_session_stats(self) -> Dict:
        """
        获取会话统计

        Returns:
            会话统计字典
        """
        if not self.usage_history:
            return {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "by_agent": {},
                "by_model": {},
            }

        total_input = sum(u.input_tokens for u in self.usage_history)
        total_output = sum(u.output_tokens for u in self.usage_history)
        total_cost = sum(u.estimate_cost(self.PRICE_TABLE) for u in self.usage_history)

        # 按Agent统计
        by_agent: Dict[str, Dict] = {}
        for usage in self.usage_history:
            if usage.agent_id not in by_agent:
                by_agent[usage.agent_id] = {
                    "input": 0,
                    "output": 0,
                    "total": 0,
                    "cost": 0.0
                }
            by_agent[usage.agent_id]["input"] += usage.input_tokens
            by_agent[usage.agent_id]["output"] += usage.output_tokens
            by_agent[usage.agent_id]["total"] += usage.total_tokens
            by_agent[usage.agent_id]["cost"] += usage.estimate_cost(self.PRICE_TABLE)

        # 按模型统计
        by_model: Dict[str, Dict] = {}
        for usage in self.usage_history:
            if usage.model not in by_model:
                by_model[usage.model] = {
                    "input": 0,
                    "output": 0,
                    "total": 0,
                    "cost": 0.0,
                    "count": 0
                }
            by_model[usage.model]["input"] += usage.input_tokens
            by_model[usage.model]["output"] += usage.output_tokens
            by_model[usage.model]["total"] += usage.total_tokens
            by_model[usage.model]["cost"] += usage.estimate_cost(self.PRICE_TABLE)
            by_model[usage.model]["count"] += 1

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": total_cost,
            "by_agent": by_agent,
            "by_model": by_model,
        }

    def get_daily_cost(self, date: datetime = None) -> float:
        """
        获取指定日期的成本

        Args:
            date: 日期，默认为今天

        Returns:
            当日成本（美元）
        """
        if date is None:
            date = datetime.now()

        target_date = date.date()
        daily_usage = [
            u for u in self.usage_history
            if datetime.fromtimestamp(u.timestamp).date() == target_date
        ]

        return sum(u.estimate_cost(self.PRICE_TABLE) for u in daily_usage)

    def get_agent_cost(self, agent_id: str) -> float:
        """
        获取特定Agent的总成本

        Args:
            agent_id: Agent ID

        Returns:
            该Agent的总成本（美元）
        """
        agent_usage = [u for u in self.usage_history if u.agent_id == agent_id]
        return sum(u.estimate_cost(self.PRICE_TABLE) for u in agent_usage)

    def get_recent_usage(self, limit: int = 10) -> List[AgentTokenUsage]:
        """
        获取最近的N条使用记录

        Args:
            limit: 返回记录数量

        Returns:
            最近的使用记录列表
        """
        return self.usage_history[-limit:]

    def clear_history(self) -> None:
        """清除所有历史记录"""
        self.usage_history.clear()
        logger.info("token_usage_history_cleared")

    def format_summary(self) -> str:
        """
        格式化输出统计摘要

        Returns:
            格式化的统计文本
        """
        stats = self.get_session_stats()

        lines = [
            "📊 Token使用统计:",
            f"├─ 输入: {stats['total_input_tokens']:,} tokens",
            f"├─ 输出: {stats['total_output_tokens']:,} tokens",
            f"├─ 总计: {stats['total_tokens']:,} tokens",
            f"└─ 成本: ${stats['total_cost_usd']:.4f}",
        ]

        if stats['by_agent']:
            lines.append("\n📋 按Agent统计:")
            for agent_id, agent_stats in stats['by_agent'].items():
                lines.append(
                    f"  {agent_id}: {agent_stats['total']:,} tokens, "
                    f"${agent_stats['cost']:.4f}"
                )

        daily_cost = self.get_daily_cost()
        lines.append(f"\n💰 今日成本: ${daily_cost:.2f}")

        return "\n".join(lines)
