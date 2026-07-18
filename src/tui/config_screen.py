"""
配置管理界面 - 管理模型、Agent、API Key等配置
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Static, DataTable, Input, Label
from textual.binding import Binding

from src.core.config import ConfigManager
from src.core.models import ModelConfig
from src.tui.dialogs import AddModelDialog


class ConfigScreen(Screen):
    """配置管理界面

    提供模型、Agent、API Key等配置的管理功能
    """

    BINDINGS = [
        Binding("escape", "back", "返回", show=True),
        Binding("ctrl+s", "save", "保存", show=True),
        Binding("a", "add_item", "添加", show=True),
    ]

    CSS = """
    ConfigScreen {
        layout: vertical;
    }

    #config_menu {
        width: 25;
        border: solid $accent;
        padding: 1;
    }

    #config_content {
        width: 1fr;
        border: solid $primary;
        padding: 1;
    }

    .menu_item {
        padding: 1;
        margin: 1;
    }

    .menu_item:hover {
        background: $accent;
    }
    """

    def __init__(self, config_manager: ConfigManager):
        """初始化配置界面

        Args:
            config_manager: 配置管理器
        """
        super().__init__()
        self.config_manager = config_manager
        self.current_view = "models"  # 当前视图：models, agents, apikeys, budget

    def compose(self) -> ComposeResult:
        """构建界面"""
        yield Header()

        with Horizontal():
            # 左侧菜单
            with Vertical(id="config_menu"):
                yield Static("⚙️  配置管理", classes="panel-title")
                yield Button("模型配置", id="btn_models", classes="menu_item")
                yield Button("Agent配置", id="btn_agents", classes="menu_item")
                yield Button("API Key管理", id="btn_apikeys", classes="menu_item")
                yield Button("预算配置", id="btn_budget", classes="menu_item")

            # 右侧内容区
            with Vertical(id="config_content"):
                yield Static("", id="content_display")

        yield Footer()

    def on_mount(self) -> None:
        """界面挂载时初始化"""
        self.show_models_view()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击"""
        button_id = event.button.id

        if button_id == "btn_models":
            self.show_models_view()
        elif button_id == "btn_agents":
            self.show_agents_view()
        elif button_id == "btn_apikeys":
            self.show_apikeys_view()
        elif button_id == "btn_budget":
            self.show_budget_view()

    def show_models_view(self) -> None:
        """显示模型配置视图"""
        self.current_view = "models"
        content = self.query_one("#content_display", Static)

        # 获取所有模型
        models = self.config_manager.list_models()

        if not models:
            content.update("📋 模型配置\n\n暂无模型配置\n\n按 'a' 添加新模型")
        else:
            lines = ["📋 模型配置\n"]
            for model in models:
                lines.append(f"\n🔹 {model.display_name}")
                lines.append(f"   ID: {model.model_id}")
                lines.append(f"   提供商: {model.provider}")
                lines.append(f"   URL: {model.base_url}")

            content.update("\n".join(lines))

    def show_agents_view(self) -> None:
        """显示Agent配置视图"""
        self.current_view = "agents"
        content = self.query_one("#content_display", Static)

        # 获取所有Agent
        agents = self.config_manager.list_agents()

        if not agents:
            content.update("🤖 Agent配置\n\n暂无Agent配置\n\n按 'a' 添加新Agent")
        else:
            lines = ["🤖 Agent配置\n"]
            for agent in agents:
                status = "✓ 活跃" if agent.active else "✗ 禁用"
                lines.append(f"\n🔹 {agent.name} [{status}]")
                lines.append(f"   角色: {agent.role}")
                lines.append(f"   模型: {agent.model_id}")
                lines.append(f"   优先级: {agent.priority}")

            content.update("\n".join(lines))

    def show_apikeys_view(self) -> None:
        """显示API Key管理视图"""
        self.current_view = "apikeys"
        content = self.query_one("#content_display", Static)

        lines = ["🔑 API Key管理\n"]
        lines.append("\n注意：API Key存储在系统密钥环中，此处仅显示是否已设置\n")

        # 列出所有模型的API Key状态
        models = self.config_manager.list_models()
        for model in models:
            key_name = model.api_key_name
            has_key = self.config_manager.get_api_key(key_name) is not None
            status = "✓ 已设置" if has_key else "✗ 未设置"
            lines.append(f"\n🔹 {model.display_name}: {key_name}")
            lines.append(f"   状态: {status}")

        content.update("\n".join(lines))

    def show_budget_view(self) -> None:
        """显示预算配置视图"""
        self.current_view = "budget"
        content = self.query_one("#content_display", Static)

        content.update("💰 预算配置\n\n此功能即将推出...")

    def action_back(self) -> None:
        """返回主界面"""
        self.app.pop_screen()

    def action_save(self) -> None:
        """保存配置"""
        # 配置在修改时已自动保存
        self.app.pop_screen()

    async def action_add_item(self) -> None:
        """添加配置项（根据当前视图）"""
        if self.current_view == "models":
            await self.add_model()
        elif self.current_view == "agents":
            # 将来实现
            pass

    async def add_model(self) -> None:
        """添加模型配置"""
        result = await self.app.push_screen_wait(AddModelDialog())

        if result:
            # 验证必填字段
            if not all([result["model_id"], result["display_name"], result["provider"],
                       result["base_url"], result["api_key_name"]]):
                return

            # 创建模型配置
            model_config = ModelConfig(
                model_id=result["model_id"],
                provider=result["provider"],
                display_name=result["display_name"],
                base_url=result["base_url"],
                api_key_name=result["api_key_name"]
            )

            # 保存配置
            self.config_manager.add_model(model_config)

            # 刷新显示
            self.show_models_view()
