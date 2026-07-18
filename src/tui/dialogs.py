"""
配置对话框 - 用于添加/编辑配置项
"""
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Button, Input, Label, Static
from textual.binding import Binding


class AddModelDialog(ModalScreen):
    """添加模型对话框"""

    BINDINGS = [
        Binding("escape", "cancel", "取消", show=True),
    ]

    CSS = """
    AddModelDialog {
        align: center middle;
    }

    #dialog_container {
        width: 60;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1;
    }

    .dialog_title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }

    .input_row {
        height: 3;
        margin: 1;
    }

    .button_row {
        height: 3;
        align: center middle;
    }
    """

    def __init__(self):
        """初始化对话框"""
        super().__init__()
        self.result = None

    def compose(self) -> ComposeResult:
        """构建对话框界面"""
        with Container(id="dialog_container"):
            yield Static("➕ 添加模型配置", classes="dialog_title")

            yield Label("模型ID:", classes="input_row")
            yield Input(placeholder="如: claude-opus-4", id="input_model_id", classes="input_row")

            yield Label("显示名称:", classes="input_row")
            yield Input(placeholder="如: Claude Opus 4", id="input_display_name", classes="input_row")

            yield Label("提供商:", classes="input_row")
            yield Input(placeholder="anthropic/openai/google", id="input_provider", classes="input_row")

            yield Label("API端点:", classes="input_row")
            yield Input(
                placeholder="https://api.anthropic.com/v1/messages",
                id="input_base_url",
                classes="input_row"
            )

            yield Label("API Key名称:", classes="input_row")
            yield Input(placeholder="如: anthropic_api_key", id="input_api_key_name", classes="input_row")

            with Container(classes="button_row"):
                yield Button("确认", id="btn_confirm", variant="primary")
                yield Button("取消", id="btn_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "btn_confirm":
            # 收集输入数据
            self.result = {
                "model_id": self.query_one("#input_model_id", Input).value.strip(),
                "display_name": self.query_one("#input_display_name", Input).value.strip(),
                "provider": self.query_one("#input_provider", Input).value.strip(),
                "base_url": self.query_one("#input_base_url", Input).value.strip(),
                "api_key_name": self.query_one("#input_api_key_name", Input).value.strip(),
            }
            self.dismiss(self.result)
        else:
            self.action_cancel()

    def action_cancel(self) -> None:
        """取消操作"""
        self.dismiss(None)
