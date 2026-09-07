"""
文件上传界面 - 支持路径输入和文件选择
"""
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button, Label


class FileUploadScreen(Screen):
    """文件上传界面"""

    CSS = """
    FileUploadScreen {
        align: center middle;
    }

    #upload_dialog {
        width: 80;
        height: 20;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    .dialog-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        margin-bottom: 1;
    }

    .input-label {
        margin-top: 1;
        margin-bottom: 1;
    }

    #button_row {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    Button {
        margin: 0 2;
    }

    #status_msg {
        width: 100%;
        height: 3;
        margin-top: 1;
        content-align: center middle;
        color: $warning;
    }
    """

    def __init__(self, callback=None):
        """初始化文件上传界面

        Args:
            callback: 上传成功后的回调函数，接收文件路径作为参数
        """
        super().__init__()
        self.callback = callback

    def compose(self) -> ComposeResult:
        """构建UI组件"""
        with Vertical(id="upload_dialog"):
            yield Static("📤 上传文件", classes="dialog-title")
            yield Static("请输入文件路径（支持相对路径和绝对路径）:", classes="input-label")
            yield Input(placeholder="/path/to/file.txt 或 ./file.txt", id="file_path_input")

            yield Static("提示：", classes="input-label")
            yield Static("• 支持通配符: ~/documents/*.pdf")
            yield Static("• 支持Tab补全（部分终端）")
            yield Static("• 拖拽文件到终端可自动粘贴路径")

            with Horizontal(id="button_row"):
                yield Button("✓ 确认上传", id="confirm_btn", variant="primary")
                yield Button("✗ 取消", id="cancel_btn")

            yield Label("", id="status_msg")

    def on_mount(self) -> None:
        """挂载时聚焦输入框"""
        self.query_one("#file_path_input", Input).focus()

    def on_button_pressed(self, event) -> None:
        """处理按钮点击"""
        button_id = event.button.id

        if button_id == "confirm_btn":
            self.handle_upload()
        elif button_id == "cancel_btn":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """处理回车提交"""
        if event.input.id == "file_path_input":
            self.handle_upload()

    def handle_upload(self) -> None:
        """处理文件上传逻辑"""
        file_path_input = self.query_one("#file_path_input", Input)
        status_msg = self.query_one("#status_msg", Label)

        file_path_str = file_path_input.value.strip()

        if not file_path_str:
            status_msg.update("⚠️ 请输入文件路径")
            return

        # 展开~和环境变量
        file_path = Path(file_path_str).expanduser()

        # 检查文件是否存在
        if not file_path.exists():
            status_msg.update(f"❌ 文件不存在: {file_path}")
            return

        if not file_path.is_file():
            status_msg.update(f"❌ 不是文件: {file_path}")
            return

        # 检查文件大小（限制10MB）
        file_size = file_path.stat().st_size
        if file_size > 10 * 1024 * 1024:
            status_msg.update(f"❌ 文件过大: {file_size / 1024 / 1024:.1f}MB (最大10MB)")
            return

        # 成功：调用回调并关闭对话框
        if self.callback:
            self.callback(str(file_path.absolute()))

        self.dismiss(str(file_path.absolute()))
