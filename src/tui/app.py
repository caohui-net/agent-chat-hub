"""
TUI应用 - 基于Textual的终端界面（增强版：Agent面板+状态栏）
"""
from typing import Optional
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, DataTable, Label, Button, TextArea
from textual.binding import Binding
from textual import work

from src.agents.session import SessionManager
from src.tui.config_screen import ConfigScreen
from src.tui.plugin_screen import PluginScreen
from src.tui.input_screen import PathInputScreen, ConfirmScreen
from src.core.file_storage import FileStorageManager
from src.tui.clipboard_service import get_clipboard_service


class ChatApp(App):
    """Agent Chat Hub TUI应用"""

    ENABLE_COMMAND_PALETTE = False  # 禁用命令面板避免冲突

    # 快捷键绑定
    BINDINGS = [
        Binding("ctrl+q", "quit", "退出", show=True),
        Binding("ctrl+shift+c", "copy_message", "复制消息", show=True),
        Binding("ctrl+t", "toggle_agent", "切换Agent", show=True),
        Binding("ctrl+r", "refresh_agents", "刷新Agent列表", show=True),
        Binding("ctrl+g", "open_config", "配置管理", show=True),
        Binding("ctrl+p", "open_plugins", "插件管理", show=True),
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

    #file_panel {
        width: 35;
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

    /* 对话框样式 */
    #dialog {
        width: 60;
        height: auto;
        border: solid $accent;
        background: $panel;
        padding: 1;
    }

    #dialog_title {
        text-align: center;
        margin-bottom: 1;
    }

    #dialog_message {
        text-align: center;
        margin: 1;
    }

    #dialog_buttons {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #path_input {
        width: 1fr;
        margin-bottom: 1;
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

        # 初始化文件存储管理器
        storage_base = Path.home() / ".agent-chat-hub" / "files"
        # 注意：session在on_mount时创建，初始化时使用临时ID
        self.file_storage = None  # 延迟初始化

    def compose(self) -> ComposeResult:
        """构建UI组件"""
        yield Header()

        # 主容器：水平布局（Agent面板 + 对话区 + 文件面板）
        with Horizontal(id="main_container"):
            # 左侧：Agent面板
            with Vertical(id="agent_panel"):
                yield Static("📋 Agents", classes="panel-title")
                yield DataTable(id="agent_table")

            # 中间：对话显示区（TextArea支持文本选择）
            yield ScrollableContainer(
                TextArea("", read_only=True, show_line_numbers=False, id="chat_display"),
                id="chat_container"
            )

            # 右侧：文件面板
            with Vertical(id="file_panel"):
                # 上部：文件列表
                with ScrollableContainer(id="file_list_container"):
                    yield Static("📁 文件列表", classes="panel-title")
                    yield DataTable(id="file_table")

                # 下部：文件操作区
                with Vertical(id="file_operations"):
                    yield Static("🔧 文件操作", classes="panel-title")
                    yield Button("📤 上传文件", id="upload_btn", variant="primary")
                    yield Button("📥 下载选中", id="download_btn")
                    yield Button("🗑️ 删除选中", id="delete_btn", variant="error")

        # 状态栏
        yield Label("", id="status_bar")

        # 输入框
        yield Input(placeholder="输入消息... (Ctrl+Q 退出)", id="input_box")

        yield Footer()

    def on_mount(self) -> None:
        """应用启动时初始化"""
        # 创建新会话
        self.session_manager.create_session("Agent Chat Hub")
        self.update_display("欢迎使用 Agent Chat Hub!\n请输入消息开始对话...")

        # 初始化文件存储管理器（会话创建后）
        if self.session_manager.current_session:
            storage_base = Path.home() / ".agent-chat-hub" / "files"
            session_id = self.session_manager.current_session.session_id
            self.file_storage = FileStorageManager(storage_base, session_id)

        # 初始化Agent表格
        table = self.query_one("#agent_table", DataTable)
        table.add_columns("Agent", "状态", "优先级")
        self.refresh_agent_panel()

        # 初始化文件表格
        file_table = self.query_one("#file_table", DataTable)
        file_table.add_columns("文件名", "大小", "类型")

        # 刷新文件列表（从存储读取）
        if self.file_storage:
            self.refresh_file_list()

        # 更新状态栏
        self.update_status_bar()

    async def on_unmount(self) -> None:
        """应用退出时清理资源"""
        # 关闭异步HTTP客户端
        await self.session_manager.executor.aclose()

    def update_display(self, content: str) -> None:
        """更新聊天显示区域（TextArea支持文本选择）

        Args:
            content: 要显示的内容
        """
        chat_display = self.query_one("#chat_display", TextArea)
        chat_display.load_text(content)

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

    def refresh_file_list(self) -> None:
        """刷新文件列表显示"""
        file_table = self.query_one("#file_table", DataTable)
        file_table.clear()

        # 防御性检查
        if not self.file_storage:
            file_table.add_row("文件系统未初始化", "-", "-")
            return

        # 获取文件列表
        try:
            files = self.file_storage.list_files()

            if not files:
                file_table.add_row("暂无文件", "-", "-")
            else:
                for file in files:
                    # 格式化文件大小
                    size_str = self._format_file_size(file.size)
                    # 显示范围标记
                    scope_mark = "🌐" if file.scope == "workspace" else "📁"
                    file_table.add_row(
                        f"{scope_mark} {file.filename}",
                        size_str,
                        file.file_type
                    )
        except Exception as e:
            file_table.add_row(f"错误: {e}", "-", "-")

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小显示

        Args:
            size_bytes: 字节数

        Returns:
            格式化的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"

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

    def action_copy_message(self) -> None:
        """复制聊天显示区的全部内容到剪贴板"""
        try:
            # 获取聊天显示区的内容
            chat_display = self.query_one("#chat_display", TextArea)
            content = chat_display.text

            if not content or not content.strip():
                self.notify("没有内容可复制", severity="warning", timeout=3)
                return

            # 使用剪贴板服务复制
            clipboard = get_clipboard_service()
            success, message = clipboard.copy(content)

            if success:
                self.notify(message, severity="information", timeout=3)
            else:
                # 失败时显示降级提示（多行消息）
                self.notify(
                    message,
                    severity="warning",
                    timeout=8  # 降级提示需要更长时间阅读
                )

        except Exception as e:
            self.notify(f"复制失败: {str(e)}", severity="error", timeout=5)

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

    def on_button_pressed(self, event) -> None:
        """处理按钮点击事件（分发到异步处理器）"""
        button_id = event.button.id

        if button_id == "upload_btn":
            self.handle_upload()
        elif button_id == "download_btn":
            self.handle_download()
        elif button_id == "delete_btn":
            self.handle_delete()

    @work(exclusive=False)
    async def handle_upload(self) -> None:
        """处理文件上传（异步）"""
        try:
            # 防御性检查
            if not self.file_storage:
                self.update_display("❌ 文件存储系统未初始化，请重启应用")
                return

            # 弹出路径输入对话框
            file_path = await self.push_screen_wait(
                PathInputScreen(
                    title="📤 上传文件",
                    placeholder="输入文件路径（例如：/home/user/file.txt）",
                    default_value=""
                )
            )

            # 用户取消
            if not file_path or file_path.strip() == "":
                self.update_display("⚠️ 上传已取消")
                return

            # 执行上传
            src_path = Path(file_path.strip())

            if not src_path.exists():
                self.update_display(f"❌ 文件不存在: {file_path}")
                return

            if not src_path.is_file():
                self.update_display(f"❌ 不是有效的文件: {file_path}")
                return

            metadata = self.file_storage.upload_file(src_path, scope="session")

            self.update_display(
                f"✅ 文件上传成功！\n\n"
                f"文件名: {metadata.filename}\n"
                f"大小: {self._format_file_size(metadata.size)}\n"
                f"类型: {metadata.file_type}\n"
                f"范围: {metadata.scope}"
            )

            # 刷新文件列表
            self.refresh_file_list()

        except Exception as e:
            self.update_display(f"❌ 上传失败: {e}")

    @work(exclusive=False)
    async def handle_download(self) -> None:
        """处理文件下载（异步）"""
        try:
            # 防御性检查
            if not self.file_storage:
                self.update_display("❌ 文件存储系统未初始化，请重启应用")
                return

            file_table = self.query_one("#file_table", DataTable)

            # 获取选中行
            if file_table.cursor_row is None or file_table.cursor_row < 0:
                self.update_display("⚠️ 请先在文件列表中选中要下载的文件")
                return

            # 获取文件列表
            files = self.file_storage.list_files()

            if not files or file_table.cursor_row >= len(files):
                self.update_display("⚠️ 文件列表为空或选中无效")
                return

            selected_file = files[file_table.cursor_row]

            # 弹出目标路径输入对话框
            default_dest = str(Path.home() / "Downloads" / selected_file.filename)
            dest_path = await self.push_screen_wait(
                PathInputScreen(
                    title=f"📥 下载文件: {selected_file.filename}",
                    placeholder="输入保存路径",
                    default_value=default_dest
                )
            )

            # 用户取消
            if not dest_path or dest_path.strip() == "":
                self.update_display("⚠️ 下载已取消")
                return

            # 执行下载
            dest = Path(dest_path.strip())
            success = self.file_storage.download_file(selected_file.file_id, dest)

            if success:
                self.update_display(f"✅ 文件已下载到: {dest}")
            else:
                self.update_display(f"❌ 下载失败: 文件不存在")

        except Exception as e:
            self.update_display(f"❌ 下载失败: {e}")

    @work(exclusive=False)
    async def handle_delete(self) -> None:
        """处理文件删除（异步）"""
        try:
            # 防御性检查
            if not self.file_storage:
                self.update_display("❌ 文件存储系统未初始化，请重启应用")
                return

            file_table = self.query_one("#file_table", DataTable)

            # 获取选中行
            if file_table.cursor_row is None or file_table.cursor_row < 0:
                self.update_display("⚠️ 请先在文件列表中选中要删除的文件")
                return

            # 获取文件列表
            files = self.file_storage.list_files()

            if not files or file_table.cursor_row >= len(files):
                self.update_display("⚠️ 文件列表为空或选中无效")
                return

            selected_file = files[file_table.cursor_row]

            # 弹出确认对话框
            confirmed = await self.push_screen_wait(
                ConfirmScreen(
                    message=f"🗑️ 确定要删除文件吗？\n\n文件名: {selected_file.filename}\n大小: {self._format_file_size(selected_file.size)}\n\n此操作不可恢复！"
                )
            )

            # 用户取消
            if not confirmed:
                self.update_display("⚠️ 删除已取消")
                return

            # 执行删除
            success = self.file_storage.delete_file(selected_file.file_id)

            if success:
                self.update_display(f"✅ 文件已删除: {selected_file.filename}")
                # 刷新文件列表
                self.refresh_file_list()
            else:
                self.update_display(f"❌ 删除失败: 文件不存在")

        except Exception as e:
            self.update_display(f"❌ 删除失败: {e}")

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
