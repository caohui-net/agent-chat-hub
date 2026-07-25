#!/usr/bin/env python3
"""
Unit tests for model_router.py
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))

from model_router import ModelRouter, TaskComplexity


class TestModelRouter(unittest.TestCase):
    """Test cases for ModelRouter class"""

    def setUp(self):
        """Set up test fixtures"""
        self.router = ModelRouter()

    def test_initialization(self):
        """Test router initialization"""
        self.assertIsNotNone(self.router)
        self.assertTrue(self.router.models_dir.exists())
        self.assertEqual(len(self.router.models), 4)

    def test_route_simple_task(self):
        """Test routing for simple complexity task"""
        decision = self.router.route(
            task_type='code_review',
            complexity=TaskComplexity.SIMPLE
        )

        self.assertIsNotNone(decision.selected_model)
        self.assertGreater(decision.confidence, 0)

    def test_route_with_context_constraint(self):
        """Test routing with context size constraint"""
        decision = self.router.route(
            task_type='implementation',
            complexity=TaskComplexity.MEDIUM,
            context_size=50000
        )

        self.assertIsNotNone(decision)

    def test_route_with_cost_budget(self):
        """Test routing with cost budget constraint"""
        decision = self.router.route(
            task_type='analysis',
            complexity=TaskComplexity.COMPLEX,
            cost_budget=0.05
        )

        self.assertLessEqual(decision.estimated_cost, 0.05)

    def test_get_model_info(self):
        """Test getting model information"""
        info = self.router.get_model_info('claude-opus-4.8')

        self.assertIsNotNone(info)
        self.assertEqual(info.vendor, 'Anthropic')

    def test_fallback_mechanism(self):
        """Test fallback suggestions"""
        decision = self.router.route(
            task_type='implementation',
            complexity=TaskComplexity.SIMPLE
        )

        # Should have selected a model
        self.assertIsNotNone(decision.selected_model)
        # Fallback models list should exist (may be empty)
        self.assertIsInstance(decision.fallback_models, list)


if __name__ == '__main__':
    unittest.main()
