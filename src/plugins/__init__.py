"""插件系统模块

提供插件加载、管理、API等功能
"""
from .base import IPlugin, PluginHook, PluginEvent
from .models import PluginMetadata, PluginConfig, PluginState
from .registry import PluginRegistry
from .loader import PluginLoader

__all__ = [
    'IPlugin',
    'PluginHook',
    'PluginEvent',
    'PluginMetadata',
    'PluginConfig',
    'PluginState',
    'PluginRegistry',
    'PluginLoader',
]
