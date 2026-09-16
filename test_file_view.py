#!/usr/bin/env python3
"""
测试文件预览功能
"""
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def create_test_files():
    """创建测试文件"""
    test_dir = Path(tempfile.gettempdir()) / "agent_chat_hub_test"
    test_dir.mkdir(exist_ok=True)

    # 测试文件1: 正常文本文件
    normal_file = test_dir / "test_normal.txt"
    normal_file.write_text("这是一个测试文件\n包含多行内容\n第三行")

    # 测试文件2: 长文件（超过50行）
    long_file = test_dir / "test_long.txt"
    long_content = "\n".join([f"第 {i} 行内容" for i in range(100)])
    long_file.write_text(long_content)

    # 测试文件3: 空文件
    empty_file = test_dir / "test_empty.txt"
    empty_file.write_text("")

    # 测试文件4: 大文件（>1MB）
    large_file = test_dir / "test_large.txt"
    large_content = "x" * (2 * 1024 * 1024)  # 2MB
    large_file.write_text(large_content)

    return test_dir, [normal_file, long_file, empty_file, large_file]

def verify_imports():
    """验证导入"""
    try:
        from src.tui.app import ChatApp
        print("✓ ChatApp 导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def main():
    print("🧪 文件预览功能测试")
    print("=" * 50)

    # 验证导入
    if not verify_imports():
        return

    # 创建测试文件
    test_dir, test_files = create_test_files()
    print(f"\n📁 测试文件已创建在: {test_dir}")

    for f in test_files:
        size = f.stat().st_size
        if size < 1024:
            size_str = f"{size}B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f}KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f}MB"
        print(f"  - {f.name}: {size_str}")

    print("\n" + "=" * 50)
    print("📋 测试步骤:")
    print("1. 运行: ./start.sh")
    print("2. 点击 '📤 浏览上传'")
    print(f"3. 导航到: {test_dir}")
    print("4. 依次上传并预览以下文件:")
    print("   - test_normal.txt (正常文本)")
    print("   - test_long.txt (100行文本)")
    print("   - test_empty.txt (空文件)")
    print("   - test_large.txt (大文件>1MB)")
    print("5. 每次预览后按 Ctrl+B 返回聊天")
    print("\n✅ 如果应用没有崩溃，说明修复成功！")
    print("=" * 50)

if __name__ == "__main__":
    main()
