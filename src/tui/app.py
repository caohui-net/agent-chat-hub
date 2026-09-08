"""
TUI应用 - 基于Textual的终端界面（增强版：Agent面板+状态栏）
"""
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, DataTable, Label, Button
from textual.binding import Binding

from src.agents.session import SessionManager
from src.tui.config_screen import ConfigScreen
from src.tui.plugin_screen import PluginScreen
from src.tui.agent_status_panel import AgentStatusPanel, TokenStatsPanel
from src.tui.file_browser_screen import FileBrowserScreen


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
        min-width: 20;
        max-width: 50;
        border: solid $accent;
        padding: 1;
    }

    #chat_container {
        width: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #file_panel {
        width: 35;
        min-width: 25;
        max-width: 60;
        layout: vertical;
        border: solid $success;
    }

    #file_list_container {
        height: 2fr;
        border: solid $success;
        padding: 1;
    }

    #file_operations {
        height: 1fr;
        border: solid $success;
        padding: 1;
    }

    #status_panels {
        dock: bottom;
        height: auto;
        layout: vertical;
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

    /* 分隔符样式 */
    .splitter {
        background: $accent;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "退出", priority=True),
        Binding("ctrl+n", "new_session", "新会话"),
        Binding("ctrl+b", "restore_chat", "返回聊天", show=True),
    ]

    def __init__(self, session_manager: SessionManager):
        """初始化应用

        Args:
            session_manager: 会话管理器
        """
        super().__init__()
        self.session_manager = session_manager
        self.uploaded_files = []  # 存储已上传的文件路径
        self.chat_history_backup = ""  # 备份聊天历史，用于从文件预览返回

    def compose(self) -> ComposeResult:
        """构建UI组件"""
        yield Header()

        # 主容器：水平布局（Agent面板 + 对话区 + 文件面板）
        with Horizontal(id="main_container"):
            # 左侧：Agent面板
            with Vertical(id="agent_panel"):
                yield Static("📋 Agents", classes="panel-title")
                yield DataTable(id="agent_table")

            # 中间：对话显示区（添加滚动支持）
            yield ScrollableContainer(
                Static("", id="chat_display"),
                id="chat_container",
                can_focus=True  # 允许聚焦以支持滚动
            )

            # 右侧：文件面板
            with Vertical(id="file_panel"):
                # 上部：文件列表
                with ScrollableContainer(id="file_list_container", can_focus=True):
                    yield Static("📁 已上传文件", classes="panel-title")
                    yield DataTable(id="file_table", cursor_type="row")

                # 下部：文件操作区
                with Vertical(id="file_operations"):
                    yield Static("🔧 文件操作", classes="panel-title")
                    yield Button("📤 浏览上传", id="upload_btn", variant="primary")
                    yield Button("📝 查看内容", id="view_btn")
                    yield Button("↩️ 返回聊天", id="restore_btn", variant="success")
                    yield Button("🗑️ 移除选中", id="delete_btn", variant="error")
                    yield Static("", id="file_count_label")

        # 状态面板容器（底部）
        with Vertical(id="status_panels"):
            # Agent状态面板
            yield AgentStatusPanel(self.session_manager.status_manager)
            # Token统计面板
            yield TokenStatsPanel(self.session_manager.token_tracker)

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

        # 初始化文件表格
        file_table = self.query_one("#file_table", DataTable)
        file_table.add_columns("文件名", "大小", "类型")
        self.refresh_file_table()

        # 更新状态栏
        self.update_status_bar()

    async def on_unmount(self) -> None:
        """应用退出时清理资源"""
        # 关闭异步HTTP客户端
        await self.session_manager.executor.aclose()

    def refresh_file_table(self) -> None:
        """刷新文件列表显示"""
        from pathlib import Path

        file_table = self.query_one("#file_table", DataTable)
        file_table.clear()

        if not self.uploaded_files:
            file_table.add_row("📭 暂无文件", "-", "-")
            self.query_one("#file_count_label", Static).update("共 0 个文件")
            return

        for file_path_str in self.uploaded_files:
            file_path = Path(file_path_str)
            file_name = file_path.name

            # 检查文件是否还存在
            if not file_path.exists():
                file_table.add_row(f"⚠️ {file_name}", "已删除", "-")
                continue

            file_size = file_path.stat().st_size

            # 格式化文件大小
            if file_size < 1024:
                size_str = f"{file_size}B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f}KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f}MB"

            # 获取文件类型
            file_type = file_path.suffix[1:].upper() if file_path.suffix else "TXT"

            file_table.add_row(f"📄 {file_name}", size_str, file_type)

        # 更新文件计数
        self.query_one("#file_count_label", Static).update(f"共 {len(self.uploaded_files)} 个文件")

    def on_file_uploaded(self, file_path: str) -> None:
        """文件上传成功回调

        Args:
            file_path: 上传的文件路径
        """
        from pathlib import Path

        # 添加到文件列表
        if file_path not in self.uploaded_files:
            self.uploaded_files.append(file_path)

        # 刷新文件表格
        self.refresh_file_table()

        # 显示成功消息
        file_name = Path(file_path).name
        self.update_display(f"✅ 文件已上传: {file_name}\n路径: {file_path}")

    def update_display(self, content: str) -> None:
        """更新聊天显示区域

        Args:
            content: 要显示的内容
        """
        chat_display = self.query_one("#chat_display", Static)
        chat_display.update(content)

    def refresh_agent_panel(self) -> None:
        """刷新Agent面板显示（增强：显示角色类型）"""
        table = self.query_one("#agent_table", DataTable)
        table.clear()

        # 定义列（如果还没定义）
        if not table.columns:
            table.add_column("名称", width=12)
            table.add_column("角色", width=15)
            table.add_column("状态", width=8)

        agents = self.session_manager.config_manager.list_agents()
        for agent in agents:
            status = "✓ 活跃" if agent.active else "✗ 禁用"
            # 显示角色类型，coordinator特别标注
            role_display = agent.role
            if hasattr(agent, 'role_type') and agent.role_type == 'coordinator':
                role_display = f"🎯 {agent.role}"

            table.add_row(
                agent.name,
                role_display,
                status
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
            # 立即显示用户输入的消息
            current_history = self.session_manager.get_message_history()
            current_history.append(f"👤 用户: {user_input}")
            display_content = "\n\n".join(current_history)
            self.update_display(display_content)

            # 添加"处理中"提示
            display_content += "\n\n⏳ 处理中..."
            self.update_display(display_content)

            # 处理用户输入并获取响应（异步并发）
            responses = await self.session_manager.process_user_input(user_input)

            # 更新显示（包含AI响应）
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

    def on_button_pressed(self, event) -> None:
        """处理按钮点击事件"""
        button_id = event.button.id

        if button_id == "upload_btn":
            # 打开文件浏览器
            from pathlib import Path
            browser = FileBrowserScreen(
                callback=self.on_file_uploaded,
                initial_path=Path.home()
            )
            self.push_screen(browser)

        elif button_id == "view_btn":
            # 查看选中文件的内容
            file_table = self.query_one("#file_table", DataTable)
            if file_table.cursor_row is not None and 0 <= file_table.cursor_row < len(self.uploaded_files):
                file_path = self.uploaded_files[file_table.cursor_row]
                from pathlib import Path
                path = Path(file_path)

                if not path.exists():
                    self.update_display(f"❌ 文件不存在: {path.name}")
                    return

                # 备份当前聊天历史
                chat_display = self.query_one("#chat_display", Static)
                self.chat_history_backup = chat_display.renderable

                # 读取文件内容（限制大小）
                try:
                    if path.stat().st_size > 1024 * 1024:  # 1MB
                        preview_content = f"📄 文件过大，仅显示路径:\n{file_path}\n\n"
                        preview_content += f"💡 提示: 按Ctrl+B返回聊天历史"
                        self.update_display(preview_content)
                    else:
                        content = path.read_text(encoding='utf-8', errors='ignore')
                        lines = content.split('\n')
                        preview = '\n'.join(lines[:50])  # 只显示前50行
                        if len(lines) > 50:
                            preview += f"\n\n... (共 {len(lines)} 行，仅显示前50行)"

                        preview_content = f"📄 {path.name}:\n\n{preview}\n\n"
                        preview_content += f"{'─' * 40}\n💡 提示: 按Ctrl+B返回聊天历史"
                        self.update_display(preview_content)
                except Exception as e:
                    error_content = f"❌ 读取失败: {e}\n路径: {file_path}\n\n"
                    error_content += f"💡 提示: 按Ctrl+B返回聊天历史"
                    self.update_display(error_content)
            else:
                self.update_display("📄 请先在文件列表中选择要查看的文件")

        elif button_id == "delete_btn":
            # 从列表移除选中的文件
            file_table = self.query_one("#file_table", DataTable)
            if file_table.cursor_row is not None and 0 <= file_table.cursor_row < len(self.uploaded_files):
                file_path = self.uploaded_files.pop(file_table.cursor_row)
                self.refresh_file_table()
                from pathlib import Path
                self.update_display(f"🗑️ 已从列表移除: {Path(file_path).name}\n(文件本身未删除)")
            else:
                self.update_display("🗑️ 请先在文件列表中选择要移除的文件")

        elif button_id == "restore_btn":
            # 返回聊天历史
            self.action_restore_chat()

    def action_new_session(self) -> None:
        """创建新会话"""
        self.session_manager.create_session("新对话")
        self.update_display("新会话已创建！\n请输入消息开始对话...")

    def action_restore_chat(self) -> None:
        """恢复聊天历史（从文件预览返回）"""
        if self.chat_history_backup:
            chat_display = self.query_one("#chat_display", Static)
            chat_display.update(self.chat_history_backup)
            self.chat_history_backup = ""  # 清空备份
        else:
            # 如果没有备份，显示当前会话历史
            history = self.session_manager.get_message_history()
            if history:
                display_content = "\n\n".join(history)
                self.update_display(display_content)
            else:
                self.update_display("欢迎使用 Agent Chat Hub!\n请输入消息开始对话...")


def run_app(session_manager: SessionManager) -> None:
    """运行TUI应用

    Args:
        session_manager: 会话管理器
    """
    app = ChatApp(session_manager)
    app.run()
