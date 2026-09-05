"""Agent状态显示面板 - 实时显示Agent执行状态"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Label
from textual.reactive import reactive

from src.core.agent_status import AgentStatus, AgentStatusManager


class AgentStatusPanel(Container):
    """Agent状态显示面板

    显示所有Agent的实时执行状态：
    - ⏳ PENDING（等待中）
    - ⚙️ RUNNING（执行中）
    - ✅ COMPLETED（已完成）
    - ❌ ERROR（出错）
    """

    DEFAULT_CSS = """
    AgentStatusPanel {
        width: 100%;
        height: auto;
        border: solid $accent;
        padding: 1;
    }

    .status-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .status-item {
        margin: 0 0 0 2;
    }

    .status-pending {
        color: $warning;
    }

    .status-running {
        color: $accent;
    }

    .status-completed {
        color: $success;
    }

    .status-error {
        color: $error;
    }
    """

    # 响应式属性 - 当status_manager变化时自动更新显示
    status_data: reactive[str] = reactive("")

    def __init__(self, status_manager: AgentStatusManager, **kwargs):
        """初始化状态面板

        Args:
            status_manager: Agent状态管理器
        """
        super().__init__(**kwargs)
        self.status_manager = status_manager

    def compose(self) -> ComposeResult:
        """组合UI组件"""
        yield Label("📊 Agent执行状态", classes="status-title")
        yield Static(id="status_content", classes="status-item")

    def on_mount(self) -> None:
        """挂载时启动自动刷新"""
        self.set_interval(0.5, self.refresh_status)

    def refresh_status(self) -> None:
        """刷新状态显示"""
        statuses = self.status_manager.get_all_statuses()

        if not statuses:
            self.status_data = "无活动Agent"
            self.update_display(self.status_data)
            return

        lines = []
        for agent_id, state in statuses.items():
            # 状态图标
            icon = {
                AgentStatus.PENDING: "⏳",
                AgentStatus.RUNNING: "⚙️",
                AgentStatus.COMPLETED: "✅",
                AgentStatus.ERROR: "❌",
            }.get(state.status, "❓")

            # 计算耗时
            duration = ""
            if state.end_time and state.start_time:
                elapsed = state.end_time - state.start_time
                duration = f" ({elapsed:.1f}s)"
            elif state.start_time and state.status == AgentStatus.RUNNING:
                import time
                elapsed = time.time() - state.start_time
                duration = f" ({elapsed:.1f}s...)"

            # Token信息
            token_info = ""
            if state.total_tokens > 0:
                token_info = f" | {state.total_tokens} tokens"

            # 错误信息
            error_info = ""
            if state.error:
                error_info = f" | ⚠️ {state.error[:50]}"

            # 组装行
            line = f"{icon} {agent_id}: {state.status.value}{duration}{token_info}{error_info}"
            lines.append(line)

        self.status_data = "\n".join(lines)
        self.update_display(self.status_data)

    def update_display(self, content: str) -> None:
        """更新显示内容

        Args:
            content: 要显示的内容
        """
        try:
            static = self.query_one("#status_content", Static)
            static.update(content)
        except Exception:
            # 如果查询失败，可能是组件还未挂载
            pass


class TokenStatsPanel(Container):
    """Token统计面板 - 显示Token使用和成本"""

    DEFAULT_CSS = """
    TokenStatsPanel {
        width: 100%;
        height: auto;
        border: solid $success;
        padding: 1;
        margin-top: 1;
    }

    .stats-title {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
    }

    .stats-item {
        margin: 0 0 0 2;
    }
    """

    def __init__(self, token_tracker, **kwargs):
        """初始化统计面板

        Args:
            token_tracker: Token追踪器
        """
        super().__init__(**kwargs)
        self.token_tracker = token_tracker

    def compose(self) -> ComposeResult:
        """组合UI组件"""
        yield Label("💰 Token统计", classes="stats-title")
        yield Static(id="stats_content", classes="stats-item")

    def on_mount(self) -> None:
        """挂载时启动自动刷新"""
        self.set_interval(1.0, self.refresh_stats)

    def refresh_stats(self) -> None:
        """刷新统计显示"""
        stats = self.token_tracker.get_session_stats()

        lines = [
            f"📥 输入: {stats['total_input_tokens']:,} tokens",
            f"📤 输出: {stats['total_output_tokens']:,} tokens",
            f"📊 总计: {stats['total_tokens']:,} tokens",
            f"💵 成本: ${stats['total_cost_usd']:.4f}",
        ]

        # 按Agent统计
        if stats['by_agent']:
            lines.append("")
            lines.append("按Agent统计:")
            for agent_id, agent_stats in stats['by_agent'].items():
                lines.append(
                    f"  • {agent_id}: "
                    f"{agent_stats['input']} + {agent_stats['output']} = "
                    f"{agent_stats['input'] + agent_stats['output']} tokens "
                    f"(${agent_stats['cost']:.4f})"
                )

        content = "\n".join(lines)
        self.update_display(content)

    def update_display(self, content: str) -> None:
        """更新显示内容

        Args:
            content: 要显示的内容
        """
        try:
            static = self.query_one("#stats_content", Static)
            static.update(content)
        except Exception:
            pass
