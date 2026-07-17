"""TUI主应用 - 基于Textual的终端界面"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input
from textual.binding import Binding


class ChatApp(App):
    """Agent Chat Hub TUI主应用"""

    # CSS样式定义
    CSS = """
    Screen {
        layout: vertical;
    }

    #message_container {
        height: 1fr;
        border: solid $primary;
    }

    #input_box {
        dock: bottom;
        height: 3;
    }
    """

    # 键盘绑定
    BINDINGS = [
        Binding("ctrl+c", "quit", "退出", priority=True),
        Binding("ctrl+s", "toggle_sidebar", "切换侧边栏"),
    ]

    def __init__(self, config_dir=None):
        """初始化应用

        Args:
            config_dir: 配置目录路径
        """
        super().__init__()
        self.config_dir = config_dir
        self.title = "Agent Chat Hub"
        self.sub_title = "多模型Agent聊天系统"

    def compose(self) -> ComposeResult:
        """构建UI组件"""
        yield Header()

        # 消息容器（中部）
        yield Container(
            Static("欢迎使用 Agent Chat Hub!", id="message_container"),
            id="chat_area"
        )

        # 输入框（底部）
        yield Input(placeholder="输入消息...", id="input_box")

        yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """处理用户输入

        Args:
            event: 输入提交事件
        """
        message = event.value
        if message.strip():
            # TODO: 处理消息发送逻辑
            self.query_one("#message_container", Static).update(
                f"已发送: {message}"
            )
            event.input.value = ""

    def action_toggle_sidebar(self) -> None:
        """切换侧边栏显示"""
        # TODO: 实现侧边栏切换逻辑
        pass


def run_app(config_dir=None):
    """启动TUI应用

    Args:
        config_dir: 配置目录路径
    """
    app = ChatApp(config_dir=config_dir)
    app.run()


if __name__ == "__main__":
    run_app()
