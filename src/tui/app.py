"""
TUI应用 - 基于Textual的终端界面（增强版：Agent面板+状态栏）
"""
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, DataTable, Label
from textual.binding import Binding

from src.agents.session import SessionManager
from src.tui.config_screen import ConfigScreen
from src.tui.plugin_screen import PluginScreen


class ChatApp(App):
    """Agent Chat Hub TUI应用"""

    # 快捷键绑定
    BINDINGS = [
        Binding("ctrl+t", "toggle_agent", "切换Agent", show=True),
        Binding("ctrl+r", "refresh_agents", "刷新Agent列表", show=True),
        Binding("ctrl+g", "open_config", "配置管理", show=True),
        Binding("ctrl+p", "open_plugins", "插件管理", show=True),
        Binding("ctrl+q", "quit", "退出", show=True),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    #main_container {
        layout: horizontal;
        height: 1fr;
    }

    #agent_panel {
        width: 30;
        border: solid $accent;
        padding: 1;
    }

    #chat_container {
        width: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #status_bar {
        dock: bottom;
        height: 3;
        background: $panel;
        border: solid $accent;
        padding: 0 1;
    }

    #input_box {
        dock: bottom;
        height: 3;
    }

    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "退出", priority=True),
        Binding("ctrl+n", "new_session", "新会话"),
    ]

    def __init__(self, session_manager: SessionManager):
        """初始化应用

        Args:
            session_manager: 会话管理器
        """
        super().__init__()
        self.session_manager = session_manager

    def compose(self) -> ComposeResult:
        """构建UI组件"""
        yield Header()

        # 主容器：水平布局（Agent面板 + 对话区）
        with Horizontal(id="main_container"):
            # Agent面板
            with Vertical(id="agent_panel"):
                yield Static("📋 Agents", classes="panel-title")
                yield DataTable(id="agent_table")

            # 对话显示区
            yield ScrollableContainer(
                Static("", id="chat_display"),
                id="chat_container"
            )

        # 状态栏
        yield Label("", id="status_bar")

        # 输入框
        yield Input(placeholder="输入消息... (Ctrl+C 退出)", id="input_box")

        yield Footer()

    def on_mount(self) -> None:
        """应用启动时初始化"""
        # 创建新会话
        self.session_manager.create_session("Agent Chat Hub")
        self.update_display("欢迎使用 Agent Chat Hub!\n请输入消息开始对话...")

        # 初始化Agent表格
        table = self.query_one("#agent_table", DataTable)
        table.add_columns("Agent", "状态", "优先级")
        self.refresh_agent_panel()

        # 更新状态栏
        self.update_status_bar()

    async def on_unmount(self) -> None:
        """应用退出时清理资源"""
        # 关闭异步HTTP客户端
        await self.session_manager.executor.aclose()

    def update_display(self, content: str) -> None:
        """更新聊天显示区域

        Args:
            content: 要显示的内容
        """
        chat_display = self.query_one("#chat_display", Static)
        chat_display.update(content)

    def refresh_agent_panel(self) -> None:
        """刷新Agent面板显示"""
        table = self.query_one("#agent_table", DataTable)
        table.clear()

        agents = self.session_manager.config_manager.list_agents()
        for agent in agents:
            status = "✓ 活跃" if agent.active else "✗ 禁用"
            table.add_row(
                agent.name,
                status,
                str(agent.priority)
            )

    def update_status_bar(self) -> None:
        """更新状态栏显示"""
        status_label = self.query_one("#status_bar", Label)

        # 获取预算统计
        if self.session_manager.coordinator.current_round:
            stats = self.session_manager.coordinator.get_round_stats()
            status_text = (
                f"轮次: {stats['round_num']} | "
                f"调用: {stats['budget_usage']['calls']} | "
                f"Token: {stats['budget_usage']['tokens']} | "
                f"时间: {stats['budget_usage']['time']}"
            )
        else:
            status_text = "就绪 | 等待输入..."

        status_label.update(status_text)

    def action_toggle_agent(self) -> None:
        """切换选中agent的激活状态"""
        table = self.query_one("#agent_table", DataTable)
        if table.cursor_row is not None and table.cursor_row >= 0:
            agents = self.session_manager.config_manager.list_agents()
            if table.cursor_row < len(agents):
                agent = agents[table.cursor_row]
                # 切换激活状态
                agent.active = not agent.active
                self.session_manager.config_manager.update_agent(agent)
                # 刷新显示
                self.refresh_agent_panel()
                self.update_status_bar()

    def action_refresh_agents(self) -> None:
        """刷新agent面板"""
        self.refresh_agent_panel()

    def action_open_config(self) -> None:
        """打开配置管理界面"""
        config_screen = ConfigScreen(self.session_manager.config_manager)
        self.push_screen(config_screen)

    def action_open_plugins(self) -> None:
        """打开插件管理界面"""
        from pathlib import Path
        from src.plugins.registry import PluginRegistry
        from src.plugins.loader import PluginLoader

        # 初始化插件系统（如果还没有初始化）
        if not hasattr(self, 'plugin_registry'):
            plugins_dir = Path(__file__).parent.parent.parent / "plugins"
            self.plugin_registry = PluginRegistry()
            self.plugin_loader = PluginLoader(plugins_dir, self.plugin_registry)

            # 加载所有插件
            self.plugin_loader.load_all_plugins()

        # 打开插件管理界面
        plugin_screen = PluginScreen(self.plugin_registry, self.plugin_loader)
        self.push_screen(plugin_screen)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """处理用户输入（异步，支持并发agent调用）

        Args:
            event: 输入提交事件
        """
        user_input = event.value.strip()
        if not user_input:
            return

        # 清空输入框
        event.input.value = ""

        try:
            # 处理用户输入并获取响应（异步并发）
            responses = await self.session_manager.process_user_input(user_input)

            # 更新显示
            history = self.session_manager.get_message_history()
            display_content = "\n\n".join(history)

            # 添加agent间消息历史（如果有）
            agent_messages = self.session_manager.get_agent_message_history(limit=10)
            if agent_messages:
                display_content += "\n\n" + "─" * 40
                display_content += "\n\n💬 Agent间通信:\n\n"
                display_content += "\n".join(agent_messages)

            self.update_display(display_content)

            # 更新状态栏
            self.update_status_bar()

            # 保存会话
            self.session_manager.save_session()

        except Exception as e:
            self.update_display(f"错误: {e}")

    def action_new_session(self) -> None:
        """创建新会话"""
        self.session_manager.create_session("新对话")
        self.update_display("新会话已创建！\n请输入消息开始对话...")


def run_app(session_manager: SessionManager) -> None:
    """运行TUI应用

    Args:
        session_manager: 会话管理器
    """
    app = ChatApp(session_manager)
    app.run()
