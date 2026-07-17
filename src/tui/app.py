"""
TUI应用 - 基于Textual的终端界面
"""
from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static
from textual.binding import Binding

from src.agents.session import SessionManager


class ChatApp(App):
    """Agent Chat Hub TUI应用"""

    CSS = """
    Screen {
        layout: vertical;
    }

    #chat_container {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #input_box {
        dock: bottom;
        height: 3;
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
        yield ScrollableContainer(
            Static("", id="chat_display"),
            id="chat_container"
        )
        yield Input(placeholder="输入消息... (Ctrl+C 退出)", id="input_box")
        yield Footer()

    def on_mount(self) -> None:
        """应用启动时初始化"""
        # 创建新会话
        self.session_manager.create_session("Agent Chat Hub")
        self.update_display("欢迎使用 Agent Chat Hub!\n请输入消息开始对话...")

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
            self.update_display(display_content)

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
