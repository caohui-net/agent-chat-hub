#!/usr/bin/env python3
"""
验证TUI文本选择功能
"""
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Static
from textual.containers import Container

class TextSelectionDemo(App):
    """演示TextArea文本选择功能"""

    CSS = """
    Screen {
        layout: vertical;
    }

    Container {
        height: 1fr;
        border: solid green;
        padding: 1;
    }

    TextArea {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        """构建界面"""
        with Container():
            yield Static("📝 TextArea文本选择测试（只读模式）", id="title")
            yield TextArea(
                "这是一段测试文本。\n\n"
                "请尝试以下操作：\n"
                "1. 使用鼠标拖拽选择文本\n"
                "2. 按Ctrl+C复制选中的文本\n"
                "3. 在其他应用中粘贴验证\n\n"
                "✅ 如果能成功选择和复制，说明文本选择功能正常工作！\n\n"
                "按Ctrl+Q退出。",
                read_only=True,
                show_line_numbers=False,
                id="demo_text"
            )

    def on_mount(self) -> None:
        """应用启动后"""
        self.title = "TextArea文本选择验证"

if __name__ == "__main__":
    app = TextSelectionDemo()
    app.run()
