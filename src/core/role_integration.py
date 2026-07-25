"""AI角色系统集成辅助工具

提供从AI角色系统加载角色配置的工具函数。
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# 添加AI角色系统到路径
ROLE_SYSTEM_PATH = Path(__file__).parent.parent.parent / '.collab' / 'ai-role-system'
sys.path.insert(0, str(ROLE_SYSTEM_PATH))

try:
    from core.role_loader import RoleLoader
    ROLE_SYSTEM_AVAILABLE = True
except ImportError:
    ROLE_SYSTEM_AVAILABLE = False


def load_role_config(role_type: str) -> Optional[Dict[str, Any]]:
    """从AI角色系统加载角色配置

    Args:
        role_type: 角色类型，如 'analyst', 'developer'等

    Returns:
        角色配置字典，如果加载失败返回None
    """
    if not ROLE_SYSTEM_AVAILABLE:
        return None

    try:
        loader = RoleLoader()
        config = loader.load_role(role_type)
        return config
    except Exception as e:
        # 静默失败，不影响主流程
        return None


def get_available_roles() -> list[str]:
    """获取所有可用的标准角色

    Returns:
        角色类型列表
    """
    if not ROLE_SYSTEM_AVAILABLE:
        return []

    return ['analyst', 'architect', 'developer', 'reviewer', 'qa', 'devops']
