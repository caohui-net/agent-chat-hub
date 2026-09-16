"""测试插件加载器功能"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from src.plugins.loader import PluginLoader
from src.plugins.registry import PluginRegistry
from src.plugins.base import IPlugin
from src.plugins.models import PluginMetadata


class MockPlugin(IPlugin):
    """模拟插件类用于测试"""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="mock_plugin",
            name="Mock Plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author"
        )


@pytest.fixture
def temp_plugins_dir(tmp_path):
    """创建临时插件目录"""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    return plugins_dir


@pytest.fixture
def registry():
    """创建插件注册表"""
    return PluginRegistry()


@pytest.fixture
def loader(temp_plugins_dir, registry):
    """创建插件加载器"""
    return PluginLoader(temp_plugins_dir, registry)


def test_scan_empty_plugins_dir(loader):
    """测试扫描空插件目录"""
    plugins = loader.scan_plugins()
    assert plugins == []


def test_scan_plugins_dir_with_valid_plugin(loader, temp_plugins_dir):
    """测试扫描包含有效插件的目录"""
    # 创建插件目录
    plugin_dir = temp_plugins_dir / "test_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("")

    plugins = loader.scan_plugins()
    assert "test_plugin" in plugins


def test_scan_plugins_dir_ignores_files(loader, temp_plugins_dir):
    """测试扫描忽略文件"""
    # 创建文件（不是目录）
    (temp_plugins_dir / "not_a_plugin.py").write_text("")

    plugins = loader.scan_plugins()
    assert "not_a_plugin.py" not in plugins


def test_validate_metadata_valid(loader):
    """测试验证有效的元数据"""
    metadata = PluginMetadata(
        plugin_id="test",
        name="Test",
        version="1.0.0",
        description="Test",
        author="Author"
    )
    assert loader._validate_metadata(metadata) is True


def test_validate_metadata_missing_id(loader):
    """测试验证缺少ID的元数据"""
    metadata = PluginMetadata(
        plugin_id="",
        name="Test",
        version="1.0.0",
        description="Test",
        author="Author"
    )
    assert loader._validate_metadata(metadata) is False


def test_check_dependencies_no_deps(loader):
    """测试检查无依赖的插件"""
    metadata = PluginMetadata(
        plugin_id="test",
        name="Test",
        version="1.0.0",
        description="Test",
        author="Author",
        dependencies=[]
    )
    assert loader.check_dependencies(metadata) is True


def test_check_dependencies_missing_dep(loader, registry):
    """测试检查缺少依赖的插件"""
    metadata = PluginMetadata(
        plugin_id="test",
        name="Test",
        version="1.0.0",
        description="Test",
        author="Author",
        dependencies=["missing_plugin"]
    )
    assert loader.check_dependencies(metadata) is False


def test_check_dependencies_satisfied(loader, registry):
    """测试检查依赖满足的插件"""
    # 先注册依赖插件
    dep_plugin = MockPlugin(plugin_api=None)
    registry.register(dep_plugin)

    metadata = PluginMetadata(
        plugin_id="test",
        name="Test",
        version="1.0.0",
        description="Test",
        author="Author",
        dependencies=["mock_plugin"]
    )
    assert loader.check_dependencies(metadata) is True


def test_unload_plugin_success(loader, registry):
    """测试成功卸载插件"""
    # 先注册插件
    plugin = MockPlugin(plugin_api=None)
    registry.register(plugin)

    # 卸载插件
    result = loader.unload_plugin("mock_plugin")
    assert result is True
    assert not registry.has_plugin("mock_plugin")


def test_unload_plugin_not_found(loader):
    """测试卸载不存在的插件"""
    result = loader.unload_plugin("nonexistent")
    assert result is False
