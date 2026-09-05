"""智能@mention匹配 - 支持精确、前缀、包含和模糊匹配"""

from difflib import SequenceMatcher
from typing import List, Optional, Tuple

import structlog

from ..core.models import AgentConfig

logger = structlog.get_logger()


class MentionMatcher:
    """智能@mention匹配器"""

    @staticmethod
    def similarity_ratio(a: str, b: str) -> float:
        """
        计算两个字符串的相似度比例（0-1）

        Args:
            a: 第一个字符串
            b: 第二个字符串

        Returns:
            相似度比例，1.0表示完全相同，0.0表示完全不同
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    @staticmethod
    def match_agent(
        agents: List[AgentConfig],
        mention: str,
        threshold: float = 0.6
    ) -> Optional[AgentConfig]:
        """
        匹配Agent，支持多种策略：
        1. 精确匹配 (agent_id或name完全相同)
        2. 前缀匹配 ("res" 匹配 "researcher")
        3. 包含匹配 ("search" 在 "researcher" 中)
        4. 模糊匹配 (相似度 > threshold)

        Args:
            agents: 可用的Agent列表
            mention: @mention文本（不包含@符号）
            threshold: 模糊匹配的相似度阈值，默认0.6

        Returns:
            匹配的AgentConfig，如果未找到返回None
        """
        if not mention or not agents:
            return None

        mention_lower = mention.lower()
        candidates: List[Tuple[AgentConfig, float]] = []

        # 1. 精确匹配 - 最高优先级
        for agent in agents:
            if agent.agent_id.lower() == mention_lower or agent.name.lower() == mention_lower:
                logger.info(
                    "mention_exact_match",
                    mention=mention,
                    agent_id=agent.agent_id,
                    agent_name=agent.name
                )
                return agent

        # 2. 前缀匹配
        for agent in agents:
            if agent.agent_id.lower().startswith(mention_lower) or \
               agent.name.lower().startswith(mention_lower):
                candidates.append((agent, 1.0))

        if candidates:
            matched_agent = candidates[0][0]
            logger.info(
                "mention_prefix_match",
                mention=mention,
                agent_id=matched_agent.agent_id,
                agent_name=matched_agent.name
            )
            return matched_agent

        # 3. 包含匹配
        for agent in agents:
            if mention_lower in agent.agent_id.lower() or \
               mention_lower in agent.name.lower():
                candidates.append((agent, 0.9))

        if candidates:
            matched_agent = candidates[0][0]
            logger.info(
                "mention_contains_match",
                mention=mention,
                agent_id=matched_agent.agent_id,
                agent_name=matched_agent.name
            )
            return matched_agent

        # 4. 模糊匹配
        for agent in agents:
            ratio1 = MentionMatcher.similarity_ratio(mention, agent.agent_id)
            ratio2 = MentionMatcher.similarity_ratio(mention, agent.name)
            max_ratio = max(ratio1, ratio2)

            if max_ratio > threshold:
                candidates.append((agent, max_ratio))

        if candidates:
            # 返回相似度最高的
            candidates.sort(key=lambda x: x[1], reverse=True)
            matched_agent = candidates[0][0]
            similarity = candidates[0][1]
            logger.info(
                "mention_fuzzy_match",
                mention=mention,
                agent_id=matched_agent.agent_id,
                agent_name=matched_agent.name,
                similarity=similarity
            )
            return matched_agent

        logger.warning("mention_no_match", mention=mention, available_agents=len(agents))
        return None

    @staticmethod
    def match_multiple(
        agents: List[AgentConfig],
        mentions: List[str],
        threshold: float = 0.6
    ) -> List[AgentConfig]:
        """
        批量匹配多个@mentions

        Args:
            agents: 可用的Agent列表
            mentions: @mention文本列表
            threshold: 模糊匹配的相似度阈值

        Returns:
            匹配的AgentConfig列表（去重）
        """
        matched_agents = []
        seen_agent_ids = set()

        for mention in mentions:
            agent = MentionMatcher.match_agent(agents, mention, threshold)
            if agent and agent.agent_id not in seen_agent_ids:
                matched_agents.append(agent)
                seen_agent_ids.add(agent.agent_id)

        return matched_agents
