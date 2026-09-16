"""
文件浏览器界面 - 支持文件系统导航和选择
"""
from pathlib import Path
from typing import Optional, Callable
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button, DataTable, Label, Footer
from textual.binding import Binding


class FileBrowserScreen(Screen):
    """文件浏览器界面 - 类似文件管理器"""

    BINDINGS = [
        Binding("escape", "cancel", "取消", show=True),
        Binding("enter", "select_file", "选择", show=True),
        Binding("backspace", "go_parent", "上一级", show=True),
    ]

    CSS = """
    FileBrowserScreen {
        background: $surface;
    }

    #browser_container {
        width: 100%;
        height: 100%;
        border: thick $primary;
        padding: 1;
    }

    .dialog-title {
        width: 100%;
        text-style: bold;
        margin-bottom: 1;
        color: $accent;
    }

    #current_path {
        width: 100%;
        margin-bottom: 1;
        color: $text;
    }

    #file_table {
        height: 1fr;
        margin-bottom: 1;
    }

    #path_input_container {
        height: auto;
        margin-bottom: 1;
    }

    #button_row {
        width: 100%;
        height: auto;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }

    #status_msg {
        width: 100%;
        height: 2;
        content-align: center middle;
        color: $warning;
    }

    #help_text {
        width: 100%;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self, callback: Optional[Callable] = None, initial_path: Optional[Path] = None):
        """初始化文件浏览器

        Args:
            callback: 文件选择后的回调函数
            initial_path: 初始目录路径
        """
        super().__init__()
        self.callback = callback
        self.current_path = initial_path or Path.home()
        self.selected_file: Optional[Path] = None

    def compose(self) -> ComposeResult:
        """构建UI组件"""
        with Vertical(id="browser_container"):
            yield Static("📁 文件浏览器", classes="dialog-title")
            yield Static(f"当前路径: {self.current_path}", id="current_path")

            # 文件列表表格
            yield DataTable(id="file_table", cursor_type="row")

            # 路径输入区
            with Horizontal(id="path_input_container"):
                yield Static("路径: ")
                yield Input(
                    placeholder="输入或粘贴文件路径...",
                    id="path_input"
                )

            # 操作按钮
            with Horizontal(id="button_row"):
                yield Button("✓ 选择文件", id="select_btn", variant="primary")
                yield Button("📁 进入目录", id="enter_dir_btn")
                yield Button("⬆️ 上一级", id="parent_btn")
                yield Button("✗ 取消", id="cancel_btn")

            yield Label("", id="status_msg")
            yield Static(
                "提示: Enter=选择 | Backspace=上一级 | Esc=取消 | 双击目录=进入",
                id="help_text"
            )

        yield Footer()

    def on_mount(self) -> None:
        """挂载时初始化"""
        # 初始化表格
        table = self.query_one("#file_table", DataTable)
        table.add_columns("类型", "名称", "大小", "修改时间")
        table.cursor_type = "row"

        # 加载当前目录
        self.load_directory(self.current_path)

        # 聚焦到表格
        table.focus()

    def load_directory(self, path: Path) -> None:
        """加载目录内容

        Args:
            path: 要加载的目录路径
        """
        try:
            if not path.exists():
                self.show_error(f"路径不存在: {path}")
                return

            if not path.is_dir():
                self.show_error(f"不是目录: {path}")
                return

            self.current_path = path.resolve()

            # 更新路径显示
            self.query_one("#current_path", Static).update(f"当前路径: {self.current_path}")

            # 清空并重新加载表格
            table = self.query_one("#file_table", DataTable)
            table.clear()

            # 添加父目录入口（如果不是根目录）
            if self.current_path.parent != self.current_path:
                table.add_row("📁", "..", "-", "-")

            # 列出目录内容
            items = sorted(
                path.iterdir(),
                key=lambda x: (not x.is_dir(), x.name.lower())
            )

            for item in items:
                try:
                    icon = "📁" if item.is_dir() else "📄"
                    name = item.name

                    if item.is_file():
                        size = item.stat().st_size
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f}KB"
                        else:
                            size_str = f"{size / (1024 * 1024):.1f}MB"
                    else:
                        size_str = "-"

                    # 修改时间
                    mtime = item.stat().st_mtime
                    from datetime import datetime
                    mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

                    table.add_row(icon, name, size_str, mtime_str)
                except PermissionError:
                    continue

        except PermissionError:
            self.show_error(f"权限不足: {path}")
        except Exception as e:
            self.show_error(f"加载失败: {e}")

    def show_error(self, message: str) -> None:
        """显示错误消息"""
        self.query_one("#status_msg", Label).update(f"❌ {message}")

    def show_success(self, message: str) -> None:
        """显示成功消息"""
        self.query_one("#status_msg", Label).update(f"✅ {message}")

    def get_selected_item(self) -> Optional[Path]:
        """获取当前选中的项目"""
        table = self.query_one("#file_table", DataTable)
        if table.cursor_row is None or table.cursor_row < 0:
            return None

        # 获取选中行的名称
        row = table.get_row_at(table.cursor_row)
        name = row[1]  # 名称列

        if name == "..":
            return self.current_path.parent

        return self.current_path / name

    def action_select_file(self) -> None:
        """选择当前高亮的文件"""
        item = self.get_selected_item()
        if item is None:
            return

        if item.is_dir():
            self.load_directory(item)
        elif item.is_file():
            self.confirm_file(item)

    def action_go_parent(self) -> None:
        """返回上一级目录"""
        if self.current_path.parent != self.current_path:
            self.load_directory(self.current_path.parent)

    def action_cancel(self) -> None:
        """取消并关闭"""
        self.dismiss(None)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """处理表格行选择（双击）"""
        item = self.get_selected_item()
        if item is None:
            return

        if item.is_dir():
            self.load_directory(item)
        elif item.is_file():
            self.confirm_file(item)

    def on_button_pressed(self, event) -> None:
        """处理按钮点击"""
        button_id = event.button.id

        if button_id == "select_btn":
            item = self.get_selected_item()
            if item and item.is_file():
                self.confirm_file(item)
            else:
                self.show_error("请选择一个文件")

        elif button_id == "enter_dir_btn":
            item = self.get_selected_item()
            if item and item.is_dir():
                self.load_directory(item)
            else:
                self.show_error("请选择一个目录")

        elif button_id == "parent_btn":
            self.action_go_parent()

        elif button_id == "cancel_btn":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """处理路径输入提交"""
        if event.input.id == "path_input":
            path_str = event.input.value.strip()
            if not path_str:
                return

            # 展开~和环境变量
            path = Path(path_str).expanduser().resolve()

            if path.is_dir():
                self.load_directory(path)
                event.input.value = ""
            elif path.is_file():
                self.confirm_file(path)
            else:
                self.show_error(f"路径无效: {path}")

    def confirm_file(self, file_path: Path) -> None:
        """确认选择文件

        Args:
            file_path: 选中的文件路径
        """
        # 检查文件大小
        try:
            file_size = file_path.stat().st_size
            if file_size > 10 * 1024 * 1024:
                self.show_error(f"文件过大: {file_size / 1024 / 1024:.1f}MB (最大10MB)")
                return

            # 调用回调
            if self.callback:
                self.callback(str(file_path.absolute()))

            self.dismiss(str(file_path.absolute()))

        except Exception as e:
            self.show_error(f"文件访问失败: {e}")
