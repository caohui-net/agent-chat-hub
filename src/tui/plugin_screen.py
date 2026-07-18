"""插件管理界面

显示已安装插件列表、启用/禁用、查看详情
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Static, Button
from textual.containers import Vertical, Horizontal, Container
from textual.binding import Binding
import structlog

from src.plugins.registry import PluginRegistry
from src.plugins.loader import PluginLoader

logger = structlog.get_logger(__name__)


class PluginScreen(Screen):
    """插件管理界面"""

    BINDINGS = [
        Binding("escape", "back", "返回", show=True),
        Binding("e", "toggle_plugin", "启用/禁用", show=True),
        Binding("d", "show_details", "详情", show=True),
        Binding("r", "refresh", "刷新", show=True),
    ]

    def __init__(self, plugin_registry: PluginRegistry, plugin_loader: PluginLoader):
        """初始化插件管理界面

        Args:
            plugin_registry: 插件注册表实例
            plugin_loader: 插件加载器实例
        """
        super().__init__()
        self.plugin_registry = plugin_registry
        self.plugin_loader = plugin_loader
        self.selected_plugin_id = None

    def compose(self) -> ComposeResult:
        """组合界面组件"""
        yield Header()

        with Vertical(id="plugin_container"):
            yield Static("🔌 插件管理", classes="panel-title")
            yield DataTable(id="plugin_table")

            with Container(id="plugin_details"):
                yield Static("", id="detail_text")

        with Horizontal(id="button_bar"):
            yield Button("启用/禁用", id="btn_toggle", variant="primary")
            yield Button("刷新", id="btn_refresh")
            yield Button("返回", id="btn_back")

        yield Footer()

    def on_mount(self) -> None:
        """界面加载时调用"""
        # 设置表格
        table = self.query_one("#plugin_table", DataTable)
        table.add_columns("插件名称", "ID", "版本", "状态", "作者")
        table.cursor_type = "row"

        # 加载插件列表
        self.refresh_plugin_list()

    def refresh_plugin_list(self) -> None:
        """刷新插件列表"""
        table = self.query_one("#plugin_table", DataTable)
        table.clear()

        # 获取所有插件元数据
        all_metadata = self.plugin_registry.get_all_metadata()

        for plugin_id, metadata in all_metadata.items():
            # 获取插件状态
            state = self.plugin_registry.get_state(plugin_id)
            status = state.status if state else "unknown"

            # 添加行
            table.add_row(
                metadata.name,
                metadata.plugin_id,
                metadata.version,
                self._format_status(status),
                metadata.author,
                key=plugin_id
            )

        logger.info("plugin_list_refreshed", count=len(all_metadata))

    def _format_status(self, status: str) -> str:
        """格式化状态显示

        Args:
            status: 状态字符串

        Returns:
            str: 格式化的状态
        """
        status_map = {
            "loaded": "✓ 已加载",
            "enabled": "✓ 已启用",
            "disabled": "✗ 已禁用",
            "error": "✗ 错误",
            "unloaded": "- 未加载",
            "unknown": "? 未知"
        }
        return status_map.get(status, status)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """表格行选中时调用"""
        self.selected_plugin_id = event.row_key.value
        self.show_plugin_details(self.selected_plugin_id)

    def show_plugin_details(self, plugin_id: str) -> None:
        """显示插件详情

        Args:
            plugin_id: 插件ID
        """
        metadata = self.plugin_registry.get_metadata(plugin_id)
        state = self.plugin_registry.get_state(plugin_id)

        if not metadata:
            return

        details = [
            f"📦 {metadata.name}",
            f"",
            f"ID: {metadata.plugin_id}",
            f"版本: {metadata.version}",
            f"作者: {metadata.author}",
            f"状态: {self._format_status(state.status if state else 'unknown')}",
            f"",
            f"描述: {metadata.description}",
        ]

        if metadata.dependencies:
            details.append(f"")
            details.append(f"依赖: {', '.join(metadata.dependencies)}")

        if metadata.provides:
            details.append(f"提供: {', '.join(metadata.provides)}")

        detail_text = self.query_one("#detail_text", Static)
        detail_text.update("\n".join(details))

    def action_toggle_plugin(self) -> None:
        """切换插件启用/禁用状态"""
        if not self.selected_plugin_id:
            self.app.notify("请先选择一个插件", severity="warning")
            return

        plugin = self.plugin_registry.get_plugin(self.selected_plugin_id)
        state = self.plugin_registry.get_state(self.selected_plugin_id)

        if not plugin or not state:
            self.app.notify("插件未找到", severity="error")
            return

        try:
            if state.status == "enabled":
                # 禁用插件
                plugin.on_disable()
                self.plugin_registry.update_state(self.selected_plugin_id, "disabled")
                self.app.notify(f"插件 {self.selected_plugin_id} 已禁用")
            else:
                # 启用插件
                plugin.on_enable()
                self.plugin_registry.update_state(self.selected_plugin_id, "enabled")
                self.app.notify(f"插件 {self.selected_plugin_id} 已启用")

            # 刷新列表
            self.refresh_plugin_list()
            self.show_plugin_details(self.selected_plugin_id)

        except Exception as e:
            logger.error("toggle_plugin_failed", plugin_id=self.selected_plugin_id, error=str(e))
            self.app.notify(f"操作失败: {str(e)}", severity="error")

    def action_show_details(self) -> None:
        """显示插件详情"""
        if self.selected_plugin_id:
            self.show_plugin_details(self.selected_plugin_id)
        else:
            self.app.notify("请先选择一个插件", severity="warning")

    def action_refresh(self) -> None:
        """刷新插件列表"""
        self.refresh_plugin_list()
        self.app.notify("插件列表已刷新")

    def action_back(self) -> None:
        """返回主界面"""
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """按钮点击事件"""
        if event.button.id == "btn_toggle":
            self.action_toggle_plugin()
        elif event.button.id == "btn_refresh":
            self.action_refresh()
        elif event.button.id == "btn_back":
            self.action_back()
