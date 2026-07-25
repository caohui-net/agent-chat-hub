#!/usr/bin/env python3
"""
Unit tests for role_loader.py
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))

from role_loader import RoleLoader, create_loader


class TestRoleLoader(unittest.TestCase):
    """Test cases for RoleLoader class"""

    def setUp(self):
        """Set up test fixtures"""
        self.loader = RoleLoader()

    def test_initialization(self):
        """Test loader initialization"""
        self.assertIsNotNone(self.loader)
        self.assertTrue(self.loader.roles_dir.exists())

    def test_load_role(self):
        """Test loading a single role"""
        developer = self.loader.load_role('developer')

        self.assertIsNotNone(developer)
        self.assertIn('role', developer)
        self.assertEqual(developer['role']['id'], 'developer')

    def test_load_all_roles(self):
        """Test loading all roles"""
        roles = self.loader.load_all_roles()

        self.assertEqual(len(roles), 6)
        self.assertIn('analyst', roles)
        self.assertIn('developer', roles)

    def test_get_role_info(self):
        """Test getting role information"""
        info = self.loader.get_role_info('analyst')

        self.assertIn('id', info)
        self.assertIn('name', info)
        self.assertEqual(info['id'], 'analyst')

    def test_cache_mechanism(self):
        """Test caching works correctly"""
        # First load
        role1 = self.loader.load_role('reviewer')
        # Second load (should use cache)
        role2 = self.loader.load_role('reviewer')

        self.assertEqual(id(role1), id(role2))

    def test_create_loader_function(self):
        """Test create_loader convenience function"""
        loader = create_loader()
        self.assertIsInstance(loader, RoleLoader)


if __name__ == '__main__':
    unittest.main()
