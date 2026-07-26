"""文件存储管理器 - 混合架构（workspace + session隔离）"""

from __future__ import annotations

import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class FileMetadata(BaseModel):
    """文件元数据"""
    file_id: str = Field(..., description="文件唯一标识符")
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(default="unknown", description="文件类型")
    scope: Literal["session", "workspace"] = Field(default="session", description="存储范围")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="上传时间")
    path: Path = Field(..., description="文件实际存储路径")

    class Config:
        arbitrary_types_allowed = True


class FileStorageManager:
    """文件存储管理器

    混合架构：
    - workspace/: 全局共享区（工具文件、模板等）
    - sessions/{session_id}/: 会话隔离区
    """

    def __init__(self, base_dir: Path, session_id: str):
        """初始化文件存储管理器

        Args:
            base_dir: 存储根目录
            session_id: 当前会话ID
        """
        self.base_dir = Path(base_dir)
        self.session_id = session_id

        # 创建目录结构
        self.workspace_dir = self.base_dir / "workspace"
        self.session_dir = self.base_dir / "sessions" / session_id

        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "file_storage_initialized",
            workspace=str(self.workspace_dir),
            session_dir=str(self.session_dir)
        )

    def _generate_file_id(self, filepath: Path) -> str:
        """生成文件唯一标识符

        Args:
            filepath: 文件路径

        Returns:
            文件ID（基于内容哈希）
        """
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def _get_scope_dir(self, scope: Literal["session", "workspace"]) -> Path:
        """获取指定范围的存储目录

        Args:
            scope: 存储范围

        Returns:
            存储目录路径
        """
        return self.session_dir if scope == "session" else self.workspace_dir

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，防止路径穿越

        Args:
            filename: 原始文件名

        Returns:
            安全的文件名
        """
        # 移除路径分隔符和特殊字符
        safe_name = filename.replace('/', '_').replace('\\', '_')
        safe_name = safe_name.replace('..', '_')
        return safe_name

    def upload_file(
        self,
        src: Path,
        scope: Literal["session", "workspace"] = "session",
        custom_name: Optional[str] = None
    ) -> FileMetadata:
        """上传文件到存储

        Args:
            src: 源文件路径
            scope: 存储范围（session/workspace）
            custom_name: 自定义文件名（可选）

        Returns:
            文件元数据

        Raises:
            FileNotFoundError: 源文件不存在
            PermissionError: 无权限访问文件
        """
        if not src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")

        if not src.is_file():
            raise ValueError(f"不是有效的文件: {src}")

        # 确定目标文件名
        filename = custom_name if custom_name else src.name
        filename = self._sanitize_filename(filename)

        # 确定目标目录
        target_dir = self._get_scope_dir(scope)
        target_path = target_dir / filename

        # 处理同名文件冲突
        counter = 1
        original_stem = target_path.stem
        original_suffix = target_path.suffix
        while target_path.exists():
            filename = f"{original_stem}_{counter}{original_suffix}"
            target_path = target_dir / filename
            counter += 1

        # 复制文件
        shutil.copy2(src, target_path)

        # 生成元数据
        file_id = self._generate_file_id(target_path)
        metadata = FileMetadata(
            file_id=file_id,
            filename=filename,
            size=target_path.stat().st_size,
            file_type=target_path.suffix.lstrip('.') or 'unknown',
            scope=scope,
            path=target_path
        )

        logger.info(
            "file_uploaded",
            file_id=file_id,
            filename=filename,
            scope=scope,
            size=metadata.size
        )

        return metadata

    def download_file(self, file_id: str, dest: Path) -> bool:
        """下载文件到指定位置

        Args:
            file_id: 文件ID
            dest: 目标路径

        Returns:
            是否成功
        """
        # 查找文件
        all_files = self.list_files(scope="session") + self.list_files(scope="workspace")
        target_file = next((f for f in all_files if f.file_id == file_id), None)

        if not target_file:
            logger.warning("file_not_found", file_id=file_id)
            return False

        if not target_file.path.exists():
            logger.error("file_path_invalid", file_id=file_id, path=str(target_file.path))
            return False

        # 复制文件
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_file.path, dest)

        logger.info("file_downloaded", file_id=file_id, dest=str(dest))
        return True

    def delete_file(self, file_id: str) -> bool:
        """删除文件

        Args:
            file_id: 文件ID

        Returns:
            是否成功
        """
        # 查找文件
        all_files = self.list_files(scope="session") + self.list_files(scope="workspace")
        target_file = next((f for f in all_files if f.file_id == file_id), None)

        if not target_file:
            logger.warning("file_not_found_for_deletion", file_id=file_id)
            return False

        if not target_file.path.exists():
            logger.warning("file_already_deleted", file_id=file_id)
            return True

        # 删除文件
        target_file.path.unlink()

        logger.info("file_deleted", file_id=file_id, filename=target_file.filename)
        return True

    def list_files(self, scope: Optional[Literal["session", "workspace"]] = None) -> List[FileMetadata]:
        """列出文件

        Args:
            scope: 存储范围（None表示全部）

        Returns:
            文件元数据列表
        """
        files: List[FileMetadata] = []

        scopes = [scope] if scope else ["session", "workspace"]

        for s in scopes:
            scope_dir = self._get_scope_dir(s)  # type: ignore

            if not scope_dir.exists():
                continue

            for file_path in scope_dir.iterdir():
                if file_path.is_file():
                    try:
                        file_id = self._generate_file_id(file_path)
                        metadata = FileMetadata(
                            file_id=file_id,
                            filename=file_path.name,
                            size=file_path.stat().st_size,
                            file_type=file_path.suffix.lstrip('.') or 'unknown',
                            scope=s,  # type: ignore
                            path=file_path
                        )
                        files.append(metadata)
                    except Exception as e:
                        logger.warning("file_metadata_error", path=str(file_path), error=str(e))

        # 按上传时间排序
        files.sort(key=lambda f: f.uploaded_at, reverse=True)

        return files

    def get_file_by_id(self, file_id: str) -> Optional[FileMetadata]:
        """根据ID获取文件元数据

        Args:
            file_id: 文件ID

        Returns:
            文件元数据或None
        """
        all_files = self.list_files()
        return next((f for f in all_files if f.file_id == file_id), None)
