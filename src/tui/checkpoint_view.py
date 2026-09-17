"""检查点视图 - 显示检查点列表并支持回滚操作"""

from datetime import datetime
from typing import Optional, Callable
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import DataTable, Button, Static, Label
from textual.binding import Binding

from src.core.checkpoint import CheckpointManager, ResponseCheckpoint, CheckpointType, CheckpointState


class CheckpointView(Screen):
    """检查点视图Screen

    显示检查点列表，支持：
    - 查看检查点详情
    - 选择检查点回滚
    - 实时刷新
    """

    BINDINGS = [
        Binding("escape", "dismiss", "返回", show=True),
        Binding("r", "refresh", "刷新", show=True),
        Binding("enter", "rollback", "回滚", show=True),
    ]

    CSS = """
    CheckpointView {
        align: center middle;
    }

    #checkpoint_container {
        width: 90%;
        height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #checkpoint_title {
        dock: top;
        width: 100%;
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $accent;
    }

    #checkpoint_table {
        height: 1fr;
        border: solid $accent;
    }

    #checkpoint_details {
        dock: bottom;
        width: 100%;
        height: 8;
        border: solid $success;
        padding: 1;
    }

    #button_bar {
        dock: bottom;
        width: 100%;
        height: 3;
        align: center middle;
    }

    .detail-label {
        color: $text-muted;
    }
    """

    def __init__(
        self,
        checkpoint_manager: CheckpointManager,
        session_id: str,
        on_rollback: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """初始化检查点视图

        Args:
            checkpoint_manager: 检查点管理器
            session_id: 当前会话ID
            on_rollback: 回滚回调函数(checkpoint_id) -> None
        """
        super().__init__(**kwargs)
        self.checkpoint_manager = checkpoint_manager
        self.session_id = session_id
        self.on_rollback = on_rollback
        self.checkpoints = []
        self.selected_checkpoint: Optional[ResponseCheckpoint] = None

    def compose(self) -> ComposeResult:
        """组合UI组件"""
        with Vertical(id="checkpoint_container"):
            yield Label("📜 检查点历史", id="checkpoint_title")

            # 检查点表格
            yield DataTable(id="checkpoint_table", cursor_type="row")

            # 检查点详情
            with Container(id="checkpoint_details"):
                yield Static("选择一个检查点查看详情...", id="detail_content")

            # 按钮栏
            with Horizontal(id="button_bar"):
                yield Button("↩️ 回滚", id="rollback_btn", variant="primary")
                yield Button("🔄 刷新", id="refresh_btn", variant="default")
                yield Button("❌ 关闭", id="close_btn", variant="error")

    def on_mount(self) -> None:
        """挂载时初始化"""
        # 初始化表格列
        table = self.query_one("#checkpoint_table", DataTable)
        table.add_columns("序号", "类型", "状态", "轮次", "时间", "Agent")

        # 加载检查点数据
        self.refresh_checkpoints()

    def refresh_checkpoints(self) -> None:
        """刷新检查点列表"""
        # 获取检查点列表（最近100个）
        self.checkpoints = self.checkpoint_manager.list_checkpoints(
            self.session_id,
            limit=100
        )

        # 更新表格
        table = self.query_one("#checkpoint_table", DataTable)
        table.clear()

        if not self.checkpoints:
            table.add_row("无检查点", "-", "-", "-", "-", "-")
            return

        for checkpoint in self.checkpoints:
            # 格式化时间
            timestamp = datetime.fromtimestamp(checkpoint.timestamp)
            time_str = timestamp.strftime("%H:%M:%S")

            # 类型图标
            type_icon = self._get_type_icon(checkpoint.checkpoint_type)

            # 状态图标
            state_icon = self._get_state_icon(checkpoint.state)

            # Agent名称（截断）
            agent_name = checkpoint.agent_id[:12] if checkpoint.agent_id else "-"

            table.add_row(
                str(checkpoint.sequence),
                f"{type_icon} {checkpoint.checkpoint_type.value}",
                f"{state_icon} {checkpoint.state.value}",
                str(checkpoint.round_num),
                time_str,
                agent_name,
                key=checkpoint.checkpoint_id
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """处理行选择事件"""
        # 获取选中的检查点ID
        checkpoint_id = event.row_key.value if event.row_key else None

        if not checkpoint_id:
            return

        # 查找检查点对象
        self.selected_checkpoint = next(
            (cp for cp in self.checkpoints if cp.checkpoint_id == checkpoint_id),
            None
        )

        if self.selected_checkpoint:
            self.update_details(self.selected_checkpoint)

    def update_details(self, checkpoint: ResponseCheckpoint) -> None:
        """更新检查点详情显示

        Args:
            checkpoint: 检查点对象
        """
        details = []
        details.append(f"🆔 ID: {checkpoint.checkpoint_id[:16]}...")
        details.append(f"📍 序号: {checkpoint.sequence}")
        details.append(f"🔢 轮次: {checkpoint.round_num}")
        details.append(f"📅 时间: {datetime.fromtimestamp(checkpoint.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")

        if checkpoint.agent_id:
            details.append(f"🤖 Agent: {checkpoint.agent_id}")

        if checkpoint.error:
            details.append(f"❌ 错误: {checkpoint.error[:50]}...")

        # 更新显示
        detail_widget = self.query_one("#detail_content", Static)
        detail_widget.update("\n".join(details))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击事件"""
        button_id = event.button.id

        if button_id == "rollback_btn":
            self.action_rollback()
        elif button_id == "refresh_btn":
            self.action_refresh()
        elif button_id == "close_btn":
            self.action_dismiss()

    def action_rollback(self) -> None:
        """执行回滚操作"""
        if not self.selected_checkpoint:
            self.notify("请先选择一个检查点", severity="warning")
            return

        # 确认回滚
        checkpoint_id = self.selected_checkpoint.checkpoint_id

        # 调用回滚回调
        if self.on_rollback:
            try:
                self.on_rollback(checkpoint_id)
                self.notify(f"已回滚到检查点 {checkpoint_id[:8]}...", severity="information")
                self.dismiss()
            except Exception as e:
                self.notify(f"回滚失败: {str(e)}", severity="error")

    def action_refresh(self) -> None:
        """刷新检查点列表"""
        self.refresh_checkpoints()
        self.notify("检查点列表已刷新", severity="information")

    def action_dismiss(self) -> None:
        """关闭视图"""
        self.dismiss()

    @staticmethod
    def _get_type_icon(checkpoint_type: CheckpointType) -> str:
        """获取检查点类型图标

        Args:
            checkpoint_type: 检查点类型

        Returns:
            图标字符串
        """
        icons = {
            CheckpointType.SESSION_START: "🎬",
            CheckpointType.USER_INPUT: "👤",
            CheckpointType.AGENT_START: "🚀",
            CheckpointType.AGENT_COMPLETE: "✅",
            CheckpointType.AGENT_ERROR: "❌",
            CheckpointType.TIMEOUT: "⏱️",
            CheckpointType.USER_COMMAND: "⚙️",
            CheckpointType.ROUND_COMPLETE: "🏁",
        }
        return icons.get(checkpoint_type, "❓")

    @staticmethod
    def _get_state_icon(state: CheckpointState) -> str:
        """获取检查点状态图标

        Args:
            state: 检查点状态

        Returns:
            图标字符串
        """
        icons = {
            CheckpointState.PENDING: "⏳",
            CheckpointState.ACTIVE: "▶️",
            CheckpointState.RESOLVED: "✔️",
            CheckpointState.FAILED: "💥",
        }
        return icons.get(state, "❓")
