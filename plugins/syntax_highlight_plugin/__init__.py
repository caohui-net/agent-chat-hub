"""Syntax Highlight Plugin - 代码语法高亮插件

为TUI中的代码块提供语法高亮显示
"""
from src.plugins.base import IPlugin
from src.plugins.models import PluginMetadata
from typing import Dict, Any, Optional
from rich.syntax import Syntax
from rich.console import Console


class SyntaxHighlightPlugin(IPlugin):
    """代码语法高亮插件

    功能：
    - 自动检测代码语言
    - 语法高亮显示
    - 支持多种主题
    - 集成到TUI消息显示
    """

    def get_metadata(self) -> PluginMetadata:
        """返回插件元数据"""
        return PluginMetadata(
            plugin_id="syntax_highlight_plugin",
            name="Syntax Highlight Plugin",
            version="1.0.0",
            description="为代码块提供语法高亮显示功能",
            author="Agent Chat Hub Team",
            dependencies=["rich", "pygments"],
            provides=["highlight_code", "detect_language"],
            hooks=["on_message_render"],
            config_schema={
                "type": "object",
                "properties": {
                    "theme": {
                        "type": "string",
                        "description": "语法高亮主题",
                        "enum": ["monokai", "github-dark", "nord", "dracula"],
                        "default": "monokai"
                    },
                    "line_numbers": {
                        "type": "boolean",
                        "description": "是否显示行号",
                        "default": True
                    },
                    "auto_detect": {
                        "type": "boolean",
                        "description": "自动检测代码语言",
                        "default": True
                    }
                }
            },
            default_config={
                "theme": "monokai",
                "line_numbers": True,
                "auto_detect": True
            }
        )

    def on_load(self) -> None:
        """插件加载时调用"""
        if self.plugin_api:
            self.plugin_api.logger.info("SyntaxHighlightPlugin loaded")

    def on_enable(self) -> None:
        """插件启用时调用"""
        if self.plugin_api:
            self.plugin_api.logger.info("SyntaxHighlightPlugin enabled")
            self.plugin_api.tui.show_notification(
                "代码语法高亮插件已启用",
                severity="information",
                timeout=2
            )

    def on_disable(self) -> None:
        """插件禁用时调用"""
        if self.plugin_api:
            self.plugin_api.logger.info("SyntaxHighlightPlugin disabled")

    def highlight_code(self, code: str, language: Optional[str] = None) -> Syntax:
        """对代码进行语法高亮

        Args:
            code: 代码文本
            language: 编程语言（可选，会自动检测）

        Returns:
            Syntax: Rich Syntax对象，可直接在TUI中显示
        """
        config = self.get_config()
        theme = config.get("theme", "monokai")
        line_numbers = config.get("line_numbers", True)
        auto_detect = config.get("auto_detect", True)

        # 自动检测语言
        if language is None and auto_detect:
            language = self.detect_language(code)

        # 创建Syntax对象
        syntax = Syntax(
            code,
            language or "text",
            theme=theme,
            line_numbers=line_numbers,
            word_wrap=False
        )

        return syntax

    def detect_language(self, code: str) -> str:
        """检测代码语言

        Args:
            code: 代码文本

        Returns:
            str: 检测到的语言名称
        """
        # 简单的启发式检测
        code_lower = code.lower().strip()

        # Python特征
        if any(keyword in code for keyword in ["def ", "import ", "class ", "print("]):
            return "python"

        # JavaScript/TypeScript特征
        if any(keyword in code for keyword in ["const ", "let ", "var ", "function ", "=>"]):
            if "interface " in code or ": string" in code:
                return "typescript"
            return "javascript"

        # Shell特征
        if code.startswith("#!") or any(keyword in code for keyword in ["#!/bin/bash", "echo ", "export "]):
            return "bash"

        # JSON特征
        if code.strip().startswith("{") or code.strip().startswith("["):
            return "json"

        # 默认纯文本
        return "text"
