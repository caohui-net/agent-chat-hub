"""规则引擎集成辅助模块

为ResponseCoordinator提供规则检查功能。
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加AI角色系统到路径
ROLE_SYSTEM_PATH = Path(__file__).parent.parent.parent / '.collab' / 'ai-role-system'
sys.path.insert(0, str(ROLE_SYSTEM_PATH))

try:
    from core.rule_engine import RuleEngine, RuleViolation
    RULE_ENGINE_AVAILABLE = True
except ImportError:
    RULE_ENGINE_AVAILABLE = False
    RuleViolation = None


class RuleChecker:
    """规则检查器 - 封装规则引擎功能"""

    def __init__(self):
        """初始化规则检查器"""
        self.engine = None
        if RULE_ENGINE_AVAILABLE:
            try:
                self.engine = RuleEngine()
            except Exception:
                pass

    def check_agent_selection(
        self,
        session_id: str,
        selected_agents: List[str],
        context: Dict[str, Any]
    ) -> List[Any]:
        """检查agent选择是否违反规则

        Args:
            session_id: 会话ID
            selected_agents: 选中的agent列表
            context: 上下文信息

        Returns:
            违规列表，如果没有违规返回空列表
        """
        if not self.engine:
            return []

        try:
            violations = self.engine.check_blocking_rules(
                scope='backend',
                context={
                    'session': session_id,
                    'agents': selected_agents,
                    **context
                }
            )
            return violations
        except Exception:
            return []

    def is_available(self) -> bool:
        """检查规则引擎是否可用"""
        return self.engine is not None
