"""Agent Chat Hub - 程序入口点"""

import sys
from pathlib import Path
from src.tui.app import run_app


def main():
    """主函数"""
    # 默认配置目录
    config_dir = Path.home() / ".agent-chat-hub"

    # 启动TUI应用
    try:
        run_app(config_dir=config_dir)
    except KeyboardInterrupt:
        print("\n应用已退出")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
