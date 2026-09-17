"""
数据库模块 - SQLite数据库封装

提供检查点系统的持久化存储。
"""

import sqlite3
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger()


class Database:
    """SQLite数据库管理器

    特性：
    - 线程安全（每个线程独立连接）
    - 自动初始化schema
    - 事务支持
    """

    def __init__(self, db_path: str):
        """初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 线程本地存储（每个线程独立连接）
        self._local = threading.local()

        # 初始化schema
        self._init_schema()

        logger.info("database_initialized", db_path=str(self.db_path))

    def _get_connection(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接

        Returns:
            SQLite连接对象
        """
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row  # 支持字典访问
        return self._local.conn

    def _init_schema(self) -> None:
        """初始化数据库schema"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 创建checkpoints表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                round_num INTEGER NOT NULL,
                checkpoint_type TEXT NOT NULL,
                state TEXT NOT NULL,
                agent_id TEXT,
                response_data TEXT,
                session_snapshot TEXT,
                error TEXT,
                timestamp REAL NOT NULL,
                sequence INTEGER NOT NULL
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_sequence
            ON checkpoints(session_id, sequence)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_state
            ON checkpoints(session_id, state)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_round
            ON checkpoints(session_id, round_num)
        """)

        conn.commit()
        logger.info("database_schema_initialized")

    def execute(
        self,
        query: str,
        params: tuple = ()
    ) -> sqlite3.Cursor:
        """执行SQL查询

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            Cursor对象
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """执行查询并获取单条结果

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            字典形式的结果，如果无结果则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并获取所有结果

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            字典列表形式的结果
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        """关闭数据库连接"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            delattr(self._local, 'conn')
            logger.info("database_connection_closed")
