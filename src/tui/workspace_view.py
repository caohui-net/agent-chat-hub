"""
工作空间视图 - TUI界面组件

提供工作空间的可视化界面：
- 文件树视图
- 任务列表视图
- 生成物列表视图
"""

from typing import Optional
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, DataTable, Tree, Button, Label, Input
from textual.screen import Screen
from textual.binding import Binding

from src.core.workspace import WorkspaceManager, Workspace, TaskStatus, ArtifactType


class WorkspaceView(Screen):
    """工作空间视图Screen"""

    BINDINGS = [
        Binding("escape", "dismiss", "关闭", show=True),
        Binding("f1", "show_files", "文件", show=True),
        Binding("f2", "show_tasks", "任务", show=True),
        Binding("f3", "show_artifacts", "生成物", show=True),
        Binding("ctrl+n", "new_task", "新建任务", show=True),
    ]

    CSS = """
    WorkspaceView {
        layout: vertical;
    }

    #workspace_header {
        dock: top;
        height: 3;
        background: $panel;
        border: solid $accent;
        padding: 0 1;
    }

    #workspace_content {
        layout: horizontal;
        height: 1fr;
    }

    #left_panel {
        width: 30%;
        border: solid $primary;
        padding: 1;
    }

    #right_panel {
        width: 70%;
        border: solid $primary;
        padding: 1;
    }

    #view_tabs {
        dock: top;
        height: 3;
        layout: horizontal;
    }

    .view_button {
        margin: 0 1;
    }

    Tree {
        height: 1fr;
    }

    DataTable {
        height: 1fr;
    }

    #status_bar {
        dock: bottom;
        height: 3;
        background: $panel;
        border: solid $accent;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        workspace: Workspace,
        name: Optional[str] = None
    ):
        """初始化工作空间视图

        Args:
            workspace_manager: 工作空间管理器
            workspace: 当前工作空间
            name: Screen名称
        """
        super().__init__(name=name)
        self.workspace_manager = workspace_manager
        self.workspace = workspace
        self.current_view = "files"  # files, tasks, artifacts

    def compose(self) -> ComposeResult:
        """构建UI组件"""
        # 顶部标题栏
        with Container(id="workspace_header"):
            yield Label(f"📦 工作空间: {self.workspace.title}")

        # 主内容区
        with Horizontal(id="workspace_content"):
            # 左侧面板：统计信息
            with Vertical(id="left_panel"):
                yield Static("📊 统计信息", classes="panel-title")
                yield Static("", id="stats_display")

                yield Static("")  # 间隔
                yield Static("🔧 操作", classes="panel-title")
                yield Button("➕ 新建任务", id="new_task_btn", variant="primary")
                yield Button("📁 添加文件", id="add_file_btn")
                yield Button("🔄 刷新", id="refresh_btn")

            # 右侧面板：内容视图
            with Vertical(id="right_panel"):
                # 视图切换标签
                with Horizontal(id="view_tabs"):
                    yield Button("📁 文件", id="view_files_btn", variant="primary", classes="view_button")
                    yield Button("✓ 任务", id="view_tasks_btn", classes="view_button")
                    yield Button("📦 生成物", id="view_artifacts_btn", classes="view_button")

                # 文件视图
                with ScrollableContainer(id="files_view", can_focus=True):
                    yield Tree("📁 文件", id="file_tree")

                # 任务视图（默认隐藏）
                with Container(id="tasks_view"):
                    yield DataTable(id="task_table", cursor_type="row")

                # 生成物视图（默认隐藏）
                with Container(id="artifacts_view"):
                    yield DataTable(id="artifact_table", cursor_type="row")

        # 底部状态栏
        with Container(id="status_bar"):
            yield Label("", id="status_label")

    def on_mount(self) -> None:
        """挂载时初始化"""
        # 初始化任务表格
        task_table = self.query_one("#task_table", DataTable)
        task_table.add_columns("ID", "标题", "状态", "分配给", "进度")

        # 初始化生成物表格
        artifact_table = self.query_one("#artifact_table", DataTable)
        artifact_table.add_columns("类型", "文件名", "创建者", "版本", "创建时间")

        # 加载数据
        self.refresh_all()

        # 显示文件视图
        self.show_view("files")

    def refresh_all(self) -> None:
        """刷新所有数据"""
        self.refresh_stats()
        self.refresh_files()
        self.refresh_tasks()
        self.refresh_artifacts()

    def refresh_stats(self) -> None:
        """刷新统计信息"""
        files = self.workspace_manager.list_files(self.workspace.workspace_id)
        tasks = self.workspace_manager.list_tasks(self.workspace.workspace_id)
        artifacts = self.workspace_manager.list_artifacts(self.workspace.workspace_id)

        # 统计任务状态
        task_stats = {
            TaskStatus.PENDING: 0,
            TaskStatus.RUNNING: 0,
            TaskStatus.DONE: 0,
            TaskStatus.FAILED: 0,
            TaskStatus.CANCELED: 0
        }
        for task in tasks:
            task_stats[task.status] = task_stats.get(task.status, 0) + 1

        stats_text = f"""
文件数: {len(files)}
任务数: {len(tasks)}
  - 待处理: {task_stats[TaskStatus.PENDING]}
  - 进行中: {task_stats[TaskStatus.RUNNING]}
  - 已完成: {task_stats[TaskStatus.DONE]}
  - 失败: {task_stats[TaskStatus.FAILED]}
生成物: {len(artifacts)}
"""

        self.query_one("#stats_display", Static).update(stats_text.strip())

    def refresh_files(self) -> None:
        """刷新文件树"""
        tree = self.query_one("#file_tree", Tree)
        tree.clear()

        files = self.workspace_manager.list_files(self.workspace.workspace_id)

        if not files:
            tree.root.add_leaf("📭 暂无文件")
            return

        # 按文件类型分组
        files_by_type: dict = {}
        for file_ref in files:
            file_type = file_ref.file_type or "其他"
            if file_type not in files_by_type:
                files_by_type[file_type] = []
            files_by_type[file_type].append(file_ref)

        # 添加到树
        for file_type, file_list in sorted(files_by_type.items()):
            type_node = tree.root.add(f"📂 {file_type.upper()} ({len(file_list)})")
            for file_ref in file_list:
                # 格式化文件大小
                size_kb = file_ref.file_size / 1024
                if size_kb < 1024:
                    size_str = f"{size_kb:.1f}KB"
                else:
                    size_str = f"{size_kb / 1024:.1f}MB"

                type_node.add_leaf(f"📄 {file_ref.file_name} ({size_str})")

    def refresh_tasks(self) -> None:
        """刷新任务列表"""
        table = self.query_one("#task_table", DataTable)
        table.clear()

        tasks = self.workspace_manager.list_tasks(self.workspace.workspace_id)

        if not tasks:
            table.add_row("无任务", "", "", "", "")
            return

        for task in tasks:
            # 状态图标
            status_icon = {
                TaskStatus.PENDING: "⏸️",
                TaskStatus.RUNNING: "▶️",
                TaskStatus.DONE: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.CANCELED: "🚫"
            }.get(task.status, "❓")

            # 计算进度
            if task.status == TaskStatus.DONE:
                progress = "100%"
            elif task.status == TaskStatus.RUNNING:
                progress = "进行中"
            else:
                progress = "-"

            # 截断长ID
            task_id_short = task.task_id[:8]

            table.add_row(
                task_id_short,
                task.title[:30],
                f"{status_icon} {task.status.value}",
                task.assigned_to or "-",
                progress
            )

    def refresh_artifacts(self) -> None:
        """刷新生成物列表"""
        table = self.query_one("#artifact_table", DataTable)
        table.clear()

        artifacts = self.workspace_manager.list_artifacts(self.workspace.workspace_id)

        if not artifacts:
            table.add_row("无生成物", "", "", "", "")
            return

        for artifact in artifacts:
            from datetime import datetime

            # 类型图标
            type_icon = {
                ArtifactType.CODE: "💻",
                ArtifactType.DOCUMENT: "📄",
                ArtifactType.IMAGE: "🖼️",
                ArtifactType.DIAGRAM: "📊",
                ArtifactType.DATA: "📊",
                ArtifactType.OTHER: "📦"
            }.get(artifact.artifact_type, "📦")

            # 格式化时间
            created_time = datetime.fromtimestamp(artifact.created_at).strftime("%m-%d %H:%M")

            table.add_row(
                f"{type_icon} {artifact.artifact_type.value}",
                artifact.file_name[:40],
                artifact.created_by,
                f"v{artifact.version}",
                created_time
            )

    def show_view(self, view_name: str) -> None:
        """切换视图

        Args:
            view_name: 视图名称 (files, tasks, artifacts)
        """
        self.current_view = view_name

        # 隐藏所有视图
        self.query_one("#files_view").display = False
        self.query_one("#tasks_view").display = False
        self.query_one("#artifacts_view").display = False

        # 重置按钮样式
        self.query_one("#view_files_btn", Button).variant = "default"
        self.query_one("#view_tasks_btn", Button).variant = "default"
        self.query_one("#view_artifacts_btn", Button).variant = "default"

        # 显示选中的视图
        if view_name == "files":
            self.query_one("#files_view").display = True
            self.query_one("#view_files_btn", Button).variant = "primary"
        elif view_name == "tasks":
            self.query_one("#tasks_view").display = True
            self.query_one("#view_tasks_btn", Button).variant = "primary"
        elif view_name == "artifacts":
            self.query_one("#artifacts_view").display = True
            self.query_one("#view_artifacts_btn", Button).variant = "primary"

        self.update_status(f"当前视图: {view_name}")

    def update_status(self, message: str) -> None:
        """更新状态栏

        Args:
            message: 状态消息
        """
        self.query_one("#status_label", Label).update(message)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        button_id = event.button.id

        if button_id == "view_files_btn":
            self.show_view("files")
        elif button_id == "view_tasks_btn":
            self.show_view("tasks")
        elif button_id == "view_artifacts_btn":
            self.show_view("artifacts")
        elif button_id == "new_task_btn":
            self.action_new_task()
        elif button_id == "add_file_btn":
            self.update_status("添加文件功能即将推出")
        elif button_id == "refresh_btn":
            self.refresh_all()
            self.update_status("✅ 已刷新")

    def action_dismiss(self) -> None:
        """关闭视图"""
        self.dismiss()

    def action_show_files(self) -> None:
        """显示文件视图"""
        self.show_view("files")

    def action_show_tasks(self) -> None:
        """显示任务视图"""
        self.show_view("tasks")

    def action_show_artifacts(self) -> None:
        """显示生成物视图"""
        self.show_view("artifacts")

    def action_new_task(self) -> None:
        """新建任务"""
        # 推送任务创建对话框
        dialog = TaskCreationDialog(self.workspace_manager, self.workspace.workspace_id)
        self.app.push_screen(dialog, self.on_task_created)

    def on_task_created(self, task_id: Optional[str]) -> None:
        """任务创建完成回调

        Args:
            task_id: 创建的任务ID，如果取消则为None
        """
        if task_id:
            self.refresh_all()
            self.update_status(f"✅ 任务已创建: {task_id[:8]}")


class TaskCreationDialog(Screen):
    """任务创建对话框"""

    CSS = """
    TaskCreationDialog {
        align: center middle;
    }

    #dialog_container {
        width: 60;
        height: 20;
        background: $panel;
        border: thick $accent;
        padding: 1 2;
    }

    .input_label {
        margin-top: 1;
    }

    Input {
        margin-bottom: 1;
    }

    #button_bar {
        layout: horizontal;
        height: 3;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self, workspace_manager: WorkspaceManager, workspace_id: str):
        """初始化对话框

        Args:
            workspace_manager: 工作空间管理器
            workspace_id: 工作空间ID
        """
        super().__init__()
        self.workspace_manager = workspace_manager
        self.workspace_id = workspace_id

    def compose(self) -> ComposeResult:
        """构建UI"""
        with Container(id="dialog_container"):
            yield Static("➕ 新建任务", classes="panel-title")

            yield Static("标题:", classes="input_label")
            yield Input(placeholder="输入任务标题", id="title_input")

            yield Static("描述:", classes="input_label")
            yield Input(placeholder="输入任务描述", id="description_input")

            yield Static("分配给 (可选):", classes="input_label")
            yield Input(placeholder="agent_id", id="assigned_to_input")

            with Horizontal(id="button_bar"):
                yield Button("✓ 创建", id="create_btn", variant="primary")
                yield Button("✗ 取消", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        if event.button.id == "create_btn":
            # 获取输入
            title = self.query_one("#title_input", Input).value.strip()
            description = self.query_one("#description_input", Input).value.strip()
            assigned_to = self.query_one("#assigned_to_input", Input).value.strip() or None

            if not title:
                return  # 标题不能为空

            # 创建任务
            task = self.workspace_manager.create_task(
                workspace_id=self.workspace_id,
                title=title,
                description=description or "无描述",
                assigned_to=assigned_to
            )

            # 返回任务ID
            self.dismiss(task.task_id)

        elif event.button.id == "cancel_btn":
            # 取消
            self.dismiss(None)
