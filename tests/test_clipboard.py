#!/usr/bin/env python3
"""
ClipboardService测试脚本
验证剪贴板服务的各个降级策略
"""
import sys
from src.tui.clipboard_service import get_clipboard_service


def test_clipboard_service():
    """测试剪贴板服务"""
    print("=" * 60)
    print("ClipboardService功能测试")
    print("=" * 60)

    # 获取服务实例
    clipboard = get_clipboard_service()
    print(f"✓ 服务实例创建成功")
    print(f"  平台: {clipboard._platform}")
    print()

    # 测试文本
    test_texts = [
        ("简单文本", "Hello, World!"),
        ("中文文本", "你好，世界！"),
        ("多行文本", "第一行\n第二行\n第三行"),
        ("特殊字符", "Tab:\t Quote:\" Newline:\n"),
    ]

    results = []

    for name, text in test_texts:
        print(f"测试: {name}")
        print(f"  内容: {repr(text[:50])}")

        success, message = clipboard.copy(text)
        results.append((name, success))

        if success:
            print(f"  ✓ 成功: {message}")
        else:
            print(f"  ✗ 失败: {message}")
            if clipboard._last_error:
                print(f"  详细错误: {clipboard._last_error}")
        print()

    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    print(f"成功: {success_count}/{total_count}")

    for name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")

    print()

    if success_count > 0:
        print("✓ ClipboardService工作正常")
        print("  至少一种复制策略可用")
        return 0
    else:
        print("⚠ ClipboardService所有策略失败")
        print("  这是正常的，如果：")
        print("  - 在无头SSH会话中运行")
        print("  - 没有安装剪贴板工具")
        print("  - 终端不支持OSC 52")
        print()
        print("  用户仍可使用终端原生复制（Shift+拖拽）")
        return 1


if __name__ == "__main__":
    sys.exit(test_clipboard_service())
