#!/usr/bin/env python3
"""
Unit tests for rule_engine.py
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))

from rule_engine import RuleEngine, RuleViolation


class TestRuleEngine(unittest.TestCase):
    """Test cases for RuleEngine class"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = RuleEngine()

    def test_initialization(self):
        """Test engine initialization"""
        self.assertIsNotNone(self.engine)
        self.assertTrue(self.engine.rules_dir.exists())

    def test_load_rules(self):
        """Test loading all rules"""
        rules = self.engine.load_rules()

        self.assertGreater(len(rules), 0)
        self.assertEqual(len(rules), 13)

    def test_load_rules_by_scope(self):
        """Test loading rules filtered by scope"""
        backend_rules = self.engine.load_rules(scope='backend')

        self.assertGreater(len(backend_rules), 0)
        for rule in backend_rules:
            self.assertIn('backend', rule.get('scope', []))

    def test_get_rules_by_severity(self):
        """Test getting rules by severity level"""
        blocking_rules = self.engine.get_rules_by_severity('blocking')

        self.assertGreater(len(blocking_rules), 0)
        for rule in blocking_rules:
            self.assertEqual(rule['severity'], 'blocking')

    def test_check_blocking_rules(self):
        """Test checking blocking rules"""
        violations = self.engine.check_blocking_rules(
            scope='backend',
            context={'operation': 'test'}
        )

        self.assertIsInstance(violations, list)

    def test_get_rules_summary(self):
        """Test getting rule statistics"""
        summary = self.engine.get_rules_summary()

        self.assertIn('total', summary)
        self.assertIn('blocking', summary)
        self.assertEqual(summary['total'], 13)
        self.assertEqual(summary['blocking'], 11)


if __name__ == '__main__':
    unittest.main()
