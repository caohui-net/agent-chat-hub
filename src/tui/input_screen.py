"""路径输入对话框 - 用于文件上传/下载路径选择"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Label
from textual.containers import Vertical, Horizontal


class PathInputScreen(ModalScreen[str]):
    """路径输入对话框（模态）"""

    def __init__(self, title: str, placeholder: str, default_value: str = ""):
        """初始化路径输入对话框

        Args:
            title: 对话框标题
            placeholder: 输入框占位符
            default_value: 默认值
        """
        super().__init__()
        self.title_text = title
        self.placeholder_text = placeholder
        self.default_value = default_value

    def compose(self) -> ComposeResult:
        """构建对话框UI"""
        with Vertical(id="dialog"):
            yield Label(self.title_text, id="dialog_title")
            yield Input(
                placeholder=self.placeholder_text,
                value=self.default_value,
                id="path_input"
            )
            with Horizontal(id="dialog_buttons"):
                yield Button("确认", variant="primary", id="confirm_btn")
                yield Button("取消", id="cancel_btn")

    def on_mount(self) -> None:
        """对话框挂载时聚焦输入框"""
        self.query_one("#path_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "confirm_btn":
            input_widget = self.query_one("#path_input", Input)
            self.dismiss(input_widget.value)
        elif event.button.id == "cancel_btn":
            self.dismiss("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """处理回车提交"""
        self.dismiss(event.value)


class ConfirmScreen(ModalScreen[bool]):
    """确认对话框（模态）"""

    def __init__(self, message: str):
        """初始化确认对话框

        Args:
            message: 确认消息
        """
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        """构建对话框UI"""
        with Vertical(id="dialog"):
            yield Label(self.message, id="dialog_message")
            with Horizontal(id="dialog_buttons"):
                yield Button("确认", variant="error", id="confirm_btn")
                yield Button("取消", variant="primary", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "confirm_btn":
            self.dismiss(True)
        elif event.button.id == "cancel_btn":
            self.dismiss(False)
