#!/usr/bin/env python3
"""
AI角色系统 - 规则引擎

提供原子规则的加载、检查和触发机制。
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RuleSeverity(Enum):
    """规则严重级别"""
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


@dataclass
class RuleViolation:
    """规则违规记录"""
    rule_id: str
    rule_name: str
    severity: RuleSeverity
    message: str
    context: Dict[str, Any]

    def __str__(self):
        emoji = "🚫" if self.severity == RuleSeverity.BLOCKING else "⚠️"
        return f"{emoji} [{self.rule_id}] {self.rule_name}: {self.message}"


class RuleEngine:
    """规则引擎核心"""

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化规则引擎

        Args:
            base_path: ai-role-system目录路径
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = Path(base_path)
        self.rules_dir = self.base_path / 'rules'
        self._rules_cache: Dict[str, List[Dict[str, Any]]] = {}

        if not self.rules_dir.exists():
            raise ValueError(f"Rules directory not found: {self.rules_dir}")

    def load_rules(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        加载规则

        Args:
            scope: 规则范围（如 'backend', 'database', 'testing'）
                  None表示加载所有规则

        Returns:
            规则列表
        """
        if scope and scope in self._rules_cache:
            return self._rules_cache[scope]

        rules = []

        for rule_file in self.rules_dir.glob('*.yaml'):
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    file_rules = yaml.safe_load(f)

                if not isinstance(file_rules, list):
                    logger.warning(f"Invalid rules format in {rule_file}")
                    continue

                # 过滤scope
                if scope:
                    file_rules = [r for r in file_rules if r.get('scope') == scope]

                rules.extend(file_rules)

            except Exception as e:
                logger.error(f"Failed to load rules from {rule_file}: {e}")

        # 缓存
        if scope:
            self._rules_cache[scope] = rules

        logger.info(f"Loaded {len(rules)} rules" + (f" for scope '{scope}'" if scope else ""))
        return rules

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取规则"""
        all_rules = self.load_rules()
        for rule in all_rules:
            if rule.get('id') == rule_id:
                return rule
        return None

    def check_blocking_rules(self, scope: str, context: Dict[str, Any]) -> List[RuleViolation]:
        """
        检查阻塞级别规则

        Args:
            scope: 检查范围
            context: 上下文信息（用于条件判断）

        Returns:
            违规列表
        """
        rules = self.load_rules(scope)
        violations = []

        for rule in rules:
            if rule.get('severity') != 'blocking':
                continue

            # 简化的条件检查（实际应用中需要更复杂的逻辑）
            if self._should_check_rule(rule, context):
                violation = self._check_rule(rule, context)
                if violation:
                    violations.append(violation)

        return violations

    def _should_check_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        判断是否应该检查此规则

        Args:
            rule: 规则定义
            context: 上下文

        Returns:
            是否应该检查
        """
        # 简化实现：检查context中是否包含触发关键字
        condition = rule.get('condition', '')

        # 如果context包含operation字段，检查是否匹配
        if 'operation' in context:
            operation = context['operation'].lower()
            condition_lower = condition.lower()

            # 简单的关键字匹配
            if 'api' in condition_lower and 'api' in operation:
                return True
            if 'database' in condition_lower and ('database' in operation or 'db' in operation):
                return True
            if 'deploy' in condition_lower and 'deploy' in operation:
                return True
            if 'test' in condition_lower and 'test' in operation:
                return True

        # 默认检查所有规则（在实际应用中应该更智能）
        return True

    def _check_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> Optional[RuleViolation]:
        """
        检查单个规则是否违反

        Args:
            rule: 规则定义
            context: 上下文

        Returns:
            违规记录（如果违反）
        """
        # 这是一个简化的实现
        # 实际应用中需要根据verification字段实现更复杂的检查逻辑

        rule_id = rule.get('id', 'unknown')
        rule_name = rule.get('name', 'Unknown Rule')
        severity = RuleSeverity(rule.get('severity', 'warning'))

        # 示例：检查context中是否有violation标记
        if context.get('check_violations', True):
            # 在真实场景中，这里应该根据verification字段执行实际检查
            # 现在返回None表示未违反
            return None

        return None

    def get_rules_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """获取指定严重级别的所有规则"""
        all_rules = self.load_rules()
        return [r for r in all_rules if r.get('severity') == severity]

    def get_rules_summary(self) -> Dict[str, int]:
        """获取规则统计摘要"""
        all_rules = self.load_rules()
        summary = {
            'total': len(all_rules),
            'blocking': 0,
            'warning': 0,
            'info': 0
        }

        for rule in all_rules:
            severity = rule.get('severity', 'info')
            if severity in summary:
                summary[severity] += 1

        return summary

    def clear_cache(self):
        """清空规则缓存"""
        self._rules_cache.clear()
        logger.info("Rules cache cleared")


# 便捷函数
def create_engine(base_path: Optional[Path] = None) -> RuleEngine:
    """创建规则引擎实例"""
    return RuleEngine(base_path)


if __name__ == '__main__':
    # 测试代码
    engine = RuleEngine()

    print("=== 测试规则引擎 ===\n")

    # 测试1: 加载所有规则
    print("1. 加载所有规则:")
    all_rules = engine.load_rules()
    print(f"   Total rules: {len(all_rules)}")

    # 测试2: 按scope加载
    print("\n2. 按scope加载规则:")
    backend_rules = engine.load_rules('backend')
    print(f"   Backend rules: {len(backend_rules)}")

    # 测试3: 获取规则摘要
    print("\n3. 规则统计:")
    summary = engine.get_rules_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    # 测试4: 获取单个规则
    print("\n4. 获取规则API-001:")
    rule = engine.get_rule_by_id('API-001')
    if rule:
        print(f"   Name: {rule.get('name')}")
        print(f"   Severity: {rule.get('severity')}")

    print("\n✅ 规则引擎测试完成")

