#!/usr/bin/env python3
"""文件操作功能集成验证脚本"""

import sys
from pathlib import Path

def verify_imports():
    """验证所有模块导入"""
    print("🔍 验证模块导入...")

    try:
        from src.core.file_storage import FileStorageManager, FileMetadata
        print("  ✓ FileStorageManager")

        from src.tui.input_screen import PathInputScreen, ConfirmScreen
        print("  ✓ PathInputScreen, ConfirmScreen")

        from src.tui.app import ChatApp
        print("  ✓ ChatApp")

        return True
    except ImportError as e:
        print(f"  ✗ 导入失败: {e}")
        return False

def verify_file_structure():
    """验证文件结构"""
    print("\n🔍 验证文件结构...")

    required_files = [
        "src/core/file_storage.py",
        "src/tui/input_screen.py",
        "src/tui/app.py",
        "docs/FILE_OPERATIONS.md",
    ]

    all_exist = True
    for filepath in required_files:
        path = Path(filepath)
        if path.exists():
            print(f"  ✓ {filepath}")
        else:
            print(f"  ✗ {filepath} 不存在")
            all_exist = False

    return all_exist

def verify_storage_operations():
    """验证存储操作"""
    print("\n🔍 验证存储操作...")

    import tempfile
    from src.core.file_storage import FileStorageManager

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_base = Path(tmpdir)
            manager = FileStorageManager(storage_base, "test_session")

            # 测试上传
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Test content")
            metadata = manager.upload_file(test_file, scope="session")
            print(f"  ✓ 上传: {metadata.filename}")

            # 测试列表
            files = manager.list_files()
            assert len(files) == 1, "文件列表数量错误"
            print(f"  ✓ 列表: {len(files)} 个文件")

            # 测试下载
            download_dest = Path(tmpdir) / "downloaded.txt"
            success = manager.download_file(metadata.file_id, download_dest)
            assert success and download_dest.exists(), "下载失败"
            print(f"  ✓ 下载: {download_dest.name}")

            # 测试删除
            success = manager.delete_file(metadata.file_id)
            assert success, "删除失败"
            files_after = manager.list_files()
            assert len(files_after) == 0, "删除后列表未清空"
            print(f"  ✓ 删除: 列表已清空")

        return True
    except Exception as e:
        print(f"  ✗ 操作失败: {e}")
        return False

def verify_dialog_components():
    """验证对话框组件"""
    print("\n🔍 验证对话框组件...")

    try:
        from src.tui.input_screen import PathInputScreen, ConfirmScreen
        from textual.screen import ModalScreen

        # 验证PathInputScreen是ModalScreen子类
        assert issubclass(PathInputScreen, ModalScreen), "PathInputScreen不是ModalScreen"
        print("  ✓ PathInputScreen 继承正确")

        # 验证ConfirmScreen是ModalScreen子类
        assert issubclass(ConfirmScreen, ModalScreen), "ConfirmScreen不是ModalScreen"
        print("  ✓ ConfirmScreen 继承正确")

        # 验证初始化
        path_screen = PathInputScreen(
            title="测试",
            placeholder="测试",
            default_value=""
        )
        print("  ✓ PathInputScreen 可初始化")

        confirm_screen = ConfirmScreen(message="测试")
        print("  ✓ ConfirmScreen 可初始化")

        return True
    except Exception as e:
        print(f"  ✗ 组件验证失败: {e}")
        return False

def main():
    """主验证流程"""
    print("=" * 60)
    print("文件操作功能集成验证")
    print("=" * 60)

    results = {
        "模块导入": verify_imports(),
        "文件结构": verify_file_structure(),
        "存储操作": verify_storage_operations(),
        "对话框组件": verify_dialog_components(),
    }

    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有验证通过！功能实现完整。")
        print("=" * 60)
        return 0
    else:
        print("❌ 部分验证失败，请检查上述错误。")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
