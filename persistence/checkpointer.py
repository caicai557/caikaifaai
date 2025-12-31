"""
Checkpointer - 状态持久化

参考: LangGraph Checkpointer 最佳实践
功能: 保存状态快照，支持恢复和时间旅行调试
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import json
import sqlite3
import time
from pathlib import Path


@dataclass
class Checkpoint:
    """状态检查点"""
    thread_id: str
    step: int
    state_json: str
    timestamp: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def from_state(cls, thread_id: str, step: int, state: Any) -> "Checkpoint":
        """从状态对象创建检查点"""
        if hasattr(state, 'model_dump'):
            state_dict = state.model_dump()
        elif hasattr(state, '__dict__'):
            state_dict = state.__dict__
        else:
            state_dict = {"value": state}
        
        return cls(
            thread_id=thread_id,
            step=step,
            state_json=json.dumps(state_dict, ensure_ascii=False, default=str),
            timestamp=time.time()
        )
    
    def to_state_dict(self) -> Dict[str, Any]:
        """转换回状态字典"""
        return json.loads(self.state_json)


class BaseCheckpointer(ABC):
    """检查点保存器基类"""
    
    @abstractmethod
    def put(self, checkpoint: Checkpoint) -> None:
        """保存检查点"""
        pass
    
    @abstractmethod
    def get(self, thread_id: str, step: int = -1) -> Optional[Checkpoint]:
        """获取检查点 (step=-1 获取最新)"""
        pass
    
    @abstractmethod
    def list(self, thread_id: str, limit: int = 10) -> List[Checkpoint]:
        """列出检查点历史"""
        pass
    
    @abstractmethod
    def delete_thread(self, thread_id: str) -> int:
        """删除线程的所有检查点"""
        pass


class InMemoryCheckpointer(BaseCheckpointer):
    """内存检查点保存器 (开发测试用)"""
    
    def __init__(self):
        self.checkpoints: Dict[str, List[Checkpoint]] = {}
    
    def put(self, checkpoint: Checkpoint) -> None:
        if checkpoint.thread_id not in self.checkpoints:
            self.checkpoints[checkpoint.thread_id] = []
        self.checkpoints[checkpoint.thread_id].append(checkpoint)
    
    def get(self, thread_id: str, step: int = -1) -> Optional[Checkpoint]:
        cps = self.checkpoints.get(thread_id, [])
        if not cps:
            return None
        if step == -1:
            return cps[-1]
        for cp in cps:
            if cp.step == step:
                return cp
        return None
    
    def list(self, thread_id: str, limit: int = 10) -> List[Checkpoint]:
        cps = self.checkpoints.get(thread_id, [])
        return cps[-limit:]
    
    def delete_thread(self, thread_id: str) -> int:
        if thread_id in self.checkpoints:
            count = len(self.checkpoints[thread_id])
            del self.checkpoints[thread_id]
            return count
        return 0


class SQLiteCheckpointer(BaseCheckpointer):
    """SQLite 检查点保存器 (生产推荐)"""
    
    def __init__(self, db_path: str = ".council/checkpoints.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    state_json TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT,
                    UNIQUE(thread_id, step)
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_thread 
                ON checkpoints(thread_id, step DESC)
            ''')
    
    def put(self, checkpoint: Checkpoint) -> None:
        """保存检查点"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO checkpoints 
                (thread_id, step, state_json, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                checkpoint.thread_id,
                checkpoint.step,
                checkpoint.state_json,
                checkpoint.timestamp,
                json.dumps(checkpoint.metadata) if checkpoint.metadata else None
            ))
    
    def get(self, thread_id: str, step: int = -1) -> Optional[Checkpoint]:
        """获取检查点"""
        with sqlite3.connect(self.db_path) as conn:
            if step == -1:
                row = conn.execute('''
                    SELECT thread_id, step, state_json, timestamp, metadata
                    FROM checkpoints WHERE thread_id = ?
                    ORDER BY step DESC LIMIT 1
                ''', (thread_id,)).fetchone()
            else:
                row = conn.execute('''
                    SELECT thread_id, step, state_json, timestamp, metadata
                    FROM checkpoints WHERE thread_id = ? AND step = ?
                ''', (thread_id, step)).fetchone()
            
            if row:
                return Checkpoint(
                    thread_id=row[0],
                    step=row[1],
                    state_json=row[2],
                    timestamp=row[3],
                    metadata=json.loads(row[4]) if row[4] else {}
                )
            return None
    
    def list(self, thread_id: str, limit: int = 10) -> List[Checkpoint]:
        """列出检查点"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute('''
                SELECT thread_id, step, state_json, timestamp, metadata
                FROM checkpoints WHERE thread_id = ?
                ORDER BY step DESC LIMIT ?
            ''', (thread_id, limit)).fetchall()
            
            return [
                Checkpoint(
                    thread_id=r[0], step=r[1], state_json=r[2],
                    timestamp=r[3], metadata=json.loads(r[4]) if r[4] else {}
                )
                for r in reversed(rows)
            ]
    
    def delete_thread(self, thread_id: str) -> int:
        """删除线程"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'DELETE FROM checkpoints WHERE thread_id = ?', 
                (thread_id,)
            )
            return cursor.rowcount


def get_checkpointer(provider: str = "sqlite", **kwargs) -> BaseCheckpointer:
    """获取检查点保存器"""
    if provider == "memory":
        return InMemoryCheckpointer()
    elif provider == "sqlite":
        return SQLiteCheckpointer(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# 导出
__all__ = [
    "Checkpoint",
    "BaseCheckpointer",
    "InMemoryCheckpointer",
    "SQLiteCheckpointer",
    "get_checkpointer",
]
