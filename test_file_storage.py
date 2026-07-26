#!/usr/bin/env python3
"""文件存储管理器基础测试"""

from pathlib import Path
import tempfile
from src.core.file_storage import FileStorageManager

def test_file_storage():
    """测试文件存储基本功能"""
    print("🧪 测试文件存储管理器\n")

    # 使用临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_base = Path(tmpdir)
        session_id = "test_session"

        manager = FileStorageManager(storage_base, session_id)
        print(f"✓ 初始化成功")
        print(f"  - Workspace: {manager.workspace_dir}")
        print(f"  - Session: {manager.session_dir}\n")

        # 测试1: 创建测试文件
        test_file = Path(tmpdir) / "test_upload.txt"
        test_file.write_text("Hello, World!")
        print(f"✓ 创建测试文件: {test_file}")

        # 测试2: 上传文件
        metadata = manager.upload_file(test_file, scope="session")
        print(f"\n✓ 上传成功:")
        print(f"  - File ID: {metadata.file_id}")
        print(f"  - Filename: {metadata.filename}")
        print(f"  - Size: {metadata.size} bytes")
        print(f"  - Scope: {metadata.scope}")

        # 测试3: 列出文件
        files = manager.list_files()
        print(f"\n✓ 文件列表: {len(files)} 个文件")
        for f in files:
            print(f"  - {f.filename} ({f.size} bytes, {f.scope})")

        # 测试4: 下载文件
        download_dest = Path(tmpdir) / "downloaded.txt"
        success = manager.download_file(metadata.file_id, download_dest)
        print(f"\n✓ 下载成功: {success}")
        if download_dest.exists():
            content = download_dest.read_text()
            print(f"  - 内容: {content}")

        # 测试5: 删除文件
        success = manager.delete_file(metadata.file_id)
        print(f"\n✓ 删除成功: {success}")

        files_after = manager.list_files()
        print(f"✓ 删除后文件列表: {len(files_after)} 个文件")

    print("\n✅ 所有测试通过！")

if __name__ == "__main__":
    test_file_storage()
