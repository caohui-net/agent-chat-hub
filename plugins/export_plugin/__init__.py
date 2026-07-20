"""Export Plugin - 对话导出插件

支持将对话历史导出为Markdown或JSON格式
"""
from src.plugins.base import IPlugin
from src.plugins.models import PluginMetadata
from typing import Dict, Any, Optional
import json
from datetime import datetime
from pathlib import Path


class ExportPlugin(IPlugin):
    """对话导出插件

    功能：
    - 导出对话为Markdown格式
    - 导出对话为JSON格式
    - 支持自定义导出路径
    """

    def get_metadata(self) -> PluginMetadata:
        """返回插件元数据"""
        return PluginMetadata(
            plugin_id="export_plugin",
            name="Export Plugin",
            version="1.0.0",
            description="将对话历史导出为Markdown或JSON格式",
            author="Agent Chat Hub Team",
            dependencies=[],
            provides=["export_markdown", "export_json"],
            hooks=["on_message_complete"],
            config_schema={
                "type": "object",
                "properties": {
                    "export_dir": {
                        "type": "string",
                        "description": "导出目录路径",
                        "default": "~/.agent-chat-hub/exports"
                    },
                    "auto_export": {
                        "type": "boolean",
                        "description": "是否自动导出",
                        "default": False
                    },
                    "format": {
                        "type": "string",
                        "description": "默认导出格式",
                        "enum": ["markdown", "json"],
                        "default": "markdown"
                    }
                }
            },
            default_config={
                "export_dir": "~/.agent-chat-hub/exports",
                "auto_export": False,
                "format": "markdown"
            }
        )

    def on_load(self) -> None:
        """插件加载时调用"""
        if self.plugin_api:
            self.plugin_api.logger.info("ExportPlugin loaded")

        # 确保导出目录存在
        export_dir = Path(self.get_config().get("export_dir", "~/.agent-chat-hub/exports")).expanduser()
        export_dir.mkdir(parents=True, exist_ok=True)

    def on_enable(self) -> None:
        """插件启用时调用"""
        if self.plugin_api:
            self.plugin_api.logger.info("ExportPlugin enabled")
            self.plugin_api.tui.show_notification(
                "对话导出插件已启用",
                severity="information",
                timeout=2
            )

    def on_disable(self) -> None:
        """插件禁用时调用"""
        if self.plugin_api:
            self.plugin_api.logger.info("ExportPlugin disabled")

    def export_to_markdown(self, session_id: str, output_path: Optional[str] = None) -> str:
        """导出会话为Markdown格式

        Args:
            session_id: 会话ID
            output_path: 输出路径（可选）

        Returns:
            str: 导出文件路径
        """
        # 获取会话数据
        if not self.plugin_api:
            raise RuntimeError("Plugin API not available")

        session_data = self.plugin_api.agent.get_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        # 生成Markdown内容
        markdown = self._generate_markdown(session_data)

        # 确定输出路径
        if output_path is None:
            export_dir = Path(self.get_config().get("export_dir", "~/.agent-chat-hub/exports")).expanduser()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(export_dir / f"session_{session_id}_{timestamp}.md")

        # 写入文件
        Path(output_path).write_text(markdown, encoding="utf-8")

        if self.plugin_api:
            self.plugin_api.logger.info("Session exported to Markdown", path=output_path)

        return output_path

    def export_to_json(self, session_id: str, output_path: Optional[str] = None) -> str:
        """导出会话为JSON格式

        Args:
            session_id: 会话ID
            output_path: 输出路径（可选）

        Returns:
            str: 导出文件路径
        """
        # 获取会话数据
        if not self.plugin_api:
            raise RuntimeError("Plugin API not available")

        session_data = self.plugin_api.agent.get_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")

        # 生成JSON内容
        json_data = self._generate_json(session_data)

        # 确定输出路径
        if output_path is None:
            export_dir = Path(self.get_config().get("export_dir", "~/.agent-chat-hub/exports")).expanduser()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(export_dir / f"session_{session_id}_{timestamp}.json")

        # 写入文件
        Path(output_path).write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")

        if self.plugin_api:
            self.plugin_api.logger.info("Session exported to JSON", path=output_path)

        return output_path

    def _generate_markdown(self, session_data: Dict[str, Any]) -> str:
        """生成Markdown格式内容"""
        lines = []

        # 标题
        lines.append(f"# 会话导出")
        lines.append(f"\n**会话ID**: {session_data.get('session_id', 'N/A')}")
        lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n---\n")

        # 对话历史
        messages = session_data.get('messages', [])
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')

            if role == 'user':
                lines.append(f"## 👤 用户")
            elif role == 'assistant':
                agent_name = msg.get('agent_name', 'Agent')
                lines.append(f"## 🤖 {agent_name}")
            else:
                lines.append(f"## {role}")

            if timestamp:
                lines.append(f"*{timestamp}*\n")

            lines.append(f"{content}\n")
            lines.append("---\n")

        return "\n".join(lines)

    def _generate_json(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成JSON格式内容"""
        return {
            "session_id": session_data.get('session_id'),
            "export_time": datetime.now().isoformat(),
            "messages": session_data.get('messages', []),
            "metadata": {
                "total_messages": len(session_data.get('messages', [])),
                "agents": list(set(msg.get('agent_name') for msg in session_data.get('messages', []) if msg.get('role') == 'assistant'))
            }
        }
