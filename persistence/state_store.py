"""
State Store - 状态存储

提供抽象接口和 SQLite 实现
"""

from abc import ABC, abstractmethod
from typing import Optional, List
import json

# 尝试导入 aiosqlite
try:
    import aiosqlite

    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False
    aiosqlite = None

from council.persistence.checkpoint import Checkpoint


class StateStore(ABC):
    """状态存储抽象基类"""

    @abstractmethod
    async def initialize(self) -> None:
        """初始化存储"""
        pass

    @abstractmethod
    async def save(self, checkpoint: Checkpoint) -> None:
        """保存检查点"""
        pass

    @abstractmethod
    async def load(self, thread_id: str) -> Optional[Checkpoint]:
        """加载最新检查点"""
        pass

    @abstractmethod
    async def load_at_step(self, thread_id: str, step: int) -> Optional[Checkpoint]:
        """加载特定步骤的检查点 (时间旅行)"""
        pass

    @abstractmethod
    async def list_checkpoints(self, thread_id: str) -> List[Checkpoint]:
        """列出所有检查点"""
        pass

    @abstractmethod
    async def delete_thread(self, thread_id: str) -> None:
        """删除线程所有检查点"""
        pass


class SqliteStateStore(StateStore):
    """
    SQLite 状态存储实现

    使用 aiosqlite 实现异步操作
    """

    def __init__(self, db_path: str = "state.db"):
        if not HAS_AIOSQLITE:
            raise ImportError(
                "aiosqlite is required for SqliteStateStore. "
                "Install with: pip install aiosqlite"
            )
        self.db_path = db_path
        self._initialized = False

    async def initialize(self) -> None:
        """创建表结构"""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_thread_id
                ON checkpoints(thread_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_thread_step
                ON checkpoints(thread_id, step)
            """)
            await db.commit()

        self._initialized = True

    async def save(self, checkpoint: Checkpoint) -> None:
        """保存检查点到 SQLite"""
        await self.initialize()

        # 验证 state 可序列化
        try:
            state_json = json.dumps(checkpoint.state, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Checkpoint state not JSON serializable: {e}")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO checkpoints (thread_id, state, step, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    checkpoint.thread_id,
                    state_json,
                    checkpoint.step,
                    checkpoint.timestamp.isoformat(),
                ),
            )
            await db.commit()

    async def load(self, thread_id: str) -> Optional[Checkpoint]:
        """加载最新检查点"""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT thread_id, state, step, timestamp
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY step DESC
                LIMIT 1
                """,
                (thread_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None

                return Checkpoint(
                    thread_id=row["thread_id"],
                    state=json.loads(row["state"]),
                    step=row["step"],
                    timestamp=row["timestamp"]
                    if isinstance(row["timestamp"], str)
                    else row["timestamp"],
                )

    async def load_at_step(self, thread_id: str, step: int) -> Optional[Checkpoint]:
        """加载特定步骤 (时间旅行)"""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT thread_id, state, step, timestamp
                FROM checkpoints
                WHERE thread_id = ? AND step = ?
                """,
                (thread_id, step),
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None

                return Checkpoint(
                    thread_id=row["thread_id"],
                    state=json.loads(row["state"]),
                    step=row["step"],
                    timestamp=row["timestamp"],
                )

    async def list_checkpoints(self, thread_id: str) -> List[Checkpoint]:
        """列出所有检查点"""
        await self.initialize()

        checkpoints = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT thread_id, state, step, timestamp
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY step ASC
                """,
                (thread_id,),
            ) as cursor:
                async for row in cursor:
                    checkpoints.append(
                        Checkpoint(
                            thread_id=row["thread_id"],
                            state=json.loads(row["state"]),
                            step=row["step"],
                            timestamp=row["timestamp"],
                        )
                    )

        return checkpoints

    async def delete_thread(self, thread_id: str) -> None:
        """删除线程所有检查点"""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,)
            )
            await db.commit()


__all__ = ["StateStore", "SqliteStateStore"]
