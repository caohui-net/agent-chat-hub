#!/usr/bin/env python3
"""
文件浏览器功能测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from textual.app import App
from src.tui.file_browser_screen import FileBrowserScreen


class TestFileBrowserApp(App):
    """测试文件浏览器的简单应用"""

    def on_mount(self):
        """启动时打开文件浏览器"""
        def on_file_selected(file_path):
            print(f"\n✅ 文件已选择: {file_path}")
            self.exit(file_path)

        browser = FileBrowserScreen(
            callback=on_file_selected,
            initial_path=Path.home()
        )
        self.push_screen(browser)


if __name__ == "__main__":
    print("🔍 文件浏览器测试")
    print("=" * 50)
    print("功能测试:")
    print("1. ✓ 显示文件系统目录列表")
    print("2. ✓ 双击或Enter进入目录")
    print("3. ✓ Backspace返回上一级")
    print("4. ✓ 输入框支持复制粘贴路径")
    print("5. ✓ 选择文件后自动返回主界面")
    print("6. ✓ Esc键取消并返回")
    print("=" * 50)
    print("\n启动文件浏览器测试...")

    app = TestFileBrowserApp()
    result = app.run()

    if result:
        print(f"\n✅ 测试完成！选择的文件: {result}")
    else:
        print("\n❌ 测试取消")
