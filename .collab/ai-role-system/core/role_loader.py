#!/usr/bin/env python3
"""
AI角色系统 - 角色加载器

提供角色配置的加载、缓存和验证功能。
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoleLoader:
    """角色配置加载器"""

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化加载器

        Args:
            base_path: ai-role-system目录路径
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = Path(base_path)
        self.roles_dir = self.base_path / 'roles'
        self._cache: Dict[str, Dict[str, Any]] = {}

        if not self.roles_dir.exists():
            raise ValueError(f"Roles directory not found: {self.roles_dir}")

    def load_role(self, role_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        加载指定角色配置

        Args:
            role_id: 角色ID (例如: 'analyst', 'developer')
            use_cache: 是否使用缓存

        Returns:
            角色配置字典

        Raises:
            FileNotFoundError: 角色文件不存在
            ValueError: 配置格式错误
        """
        # 检查缓存
        if use_cache and role_id in self._cache:
            logger.debug(f"Loading role '{role_id}' from cache")
            return self._cache[role_id]

        # 加载文件
        role_file = self.roles_dir / f"{role_id}.yaml"
        if not role_file.exists():
            raise FileNotFoundError(f"Role file not found: {role_file}")

        try:
            with open(role_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 基本验证
            self._validate_role_config(config, role_id)

            # 缓存
            self._cache[role_id] = config
            logger.info(f"Loaded role: {role_id}")

            return config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {role_file}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading role {role_id}: {e}")

    def _validate_role_config(self, config: Dict[str, Any], role_id: str):
        """验证角色配置的基本结构"""
        required_fields = ['role', 'scope', 'inputs', 'workflow', 'output_contract']

        for field in required_fields:
            if field not in config:
                raise ValueError(
                    f"Role '{role_id}' missing required field: {field}"
                )

        # 验证role字段
        role = config['role']
        role_required = ['id', 'name', 'version', 'mission']
        for field in role_required:
            if field not in role:
                raise ValueError(
                    f"Role '{role_id}' missing role.{field}"
                )

    def load_all_roles(self) -> Dict[str, Dict[str, Any]]:
        """
        加载所有角色配置

        Returns:
            {role_id: config} 字典
        """
        roles = {}

        for role_file in self.roles_dir.glob('*.yaml'):
            role_id = role_file.stem
            try:
                roles[role_id] = self.load_role(role_id)
            except Exception as e:
                logger.error(f"Failed to load role {role_id}: {e}")

        logger.info(f"Loaded {len(roles)} roles")
        return roles

    def get_role_info(self, role_id: str) -> Dict[str, str]:
        """
        获取角色的基本信息

        Returns:
            {'id', 'name', 'version', 'mission'}
        """
        config = self.load_role(role_id)
        return config['role']

    def get_workflow(self, role_id: str) -> list:
        """获取角色的工作流步骤"""
        config = self.load_role(role_id)
        return config.get('workflow', [])

    def get_output_schema(self, role_id: str) -> Dict[str, Any]:
        """获取角色的输出schema"""
        config = self.load_role(role_id)
        return config.get('output_contract', {}).get('schema', {})

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("Role cache cleared")

    def reload_role(self, role_id: str) -> Dict[str, Any]:
        """强制重新加载角色（忽略缓存）"""
        if role_id in self._cache:
            del self._cache[role_id]
        return self.load_role(role_id, use_cache=False)


# 便捷函数
def create_loader(base_path: Optional[Path] = None) -> RoleLoader:
    """创建角色加载器实例"""
    return RoleLoader(base_path)


if __name__ == '__main__':
    # 测试代码
    loader = RoleLoader()

    print("=== 测试角色加载器 ===\n")

    # 测试1: 加载单个角色
    print("1. 加载developer角色:")
    developer = loader.load_role('developer')
    print(f"   - ID: {developer['role']['id']}")
    print(f"   - Name: {developer['role']['name']}")
    print(f"   - Mission: {developer['role']['mission']}")

    # 测试2: 获取角色信息
    print("\n2. 获取analyst角色信息:")
    info = loader.get_role_info('analyst')
    print(f"   {info}")

    # 测试3: 加载所有角色
    print("\n3. 加载所有角色:")
    all_roles = loader.load_all_roles()
    for role_id in all_roles.keys():
        print(f"   - {role_id}")

    print("\n✅ 角色加载器测试完成")
