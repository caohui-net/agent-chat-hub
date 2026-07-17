"""
Agent Chat Hub - 主入口
"""
import sys
from pathlib import Path

from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator, BudgetLimits
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager
from src.tui.app import run_app


def main():
    """应用主入口"""
    # 配置目录
    config_dir = Path.home() / ".agent-chat-hub"
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 初始化配置管理器
        config_manager = ConfigManager(config_dir=config_dir)
        config_manager.load_configs()

        # 初始化响应协调器（使用MVP预算限制）
        coordinator = ResponseCoordinator(
            budget_limits=BudgetLimits(
                max_agents=3,
                max_calls_per_round=3,
                max_tokens=12000,
                timeout_seconds=120.0
            )
        )

        # 初始化agent执行器
        executor = AgentExecutor(config_manager)

        # 初始化会话管理器
        session_manager = SessionManager(
            config_manager=config_manager,
            coordinator=coordinator,
            executor=executor,
            session_dir=config_dir / "sessions"
        )

        # 运行TUI应用
        print("正在启动 Agent Chat Hub...")
        run_app(session_manager)

    except KeyboardInterrupt:
        print("\n应用已退出")
        sys.exit(0)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
