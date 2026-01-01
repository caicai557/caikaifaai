"""
Persistence Phase - 状态持久化与清理阶段

记忆分离架构 (2026最佳实践):
- 长期记忆: NOTES.md - 跨会话持久化的情节记忆
- 短期记忆: SessionCache - 当前会话的工作上下文

会话快照、归档、上下文清理。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json


@dataclass
class SessionSnapshot:
    """
    会话快照 (/rewind)
    
    备份当前会话状态以便回滚
    """
    snapshot_id: str
    task_summary: str
    files_modified: List[str]
    context: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    
    def save(self, output_dir: str = ".council/snapshots") -> str:
        """保存快照"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{self.snapshot_id}_{self.created_at.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_path / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "snapshot_id": self.snapshot_id,
                "task_summary": self.task_summary,
                "files_modified": self.files_modified,
                "context": self.context,
                "created_at": self.created_at.isoformat(),
            }, f, ensure_ascii=False, indent=2)
        
        return str(filepath)
    
    @classmethod
    def load(cls, filepath: str) -> "SessionSnapshot":
        """加载快照"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls(
            snapshot_id=data["snapshot_id"],
            task_summary=data["task_summary"],
            files_modified=data["files_modified"],
            context=data["context"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class NotesArchiver:
    """
    NOTES.md 归档器
    
    总结当前会话的"情节记忆"并归档
    """
    
    def __init__(self, notes_path: str = "NOTES.md"):
        self.notes_path = Path(notes_path)
    
    def archive(
        self,
        session_summary: str,
        decisions: List[str],
        files_changed: List[str]
    ) -> str:
        """
        归档会话记录
        
        Args:
            session_summary: 会话摘要
            decisions: 决策列表
            files_changed: 变更文件列表
            
        Returns:
            归档内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        content = f"""
## [{timestamp}] 会话记录

### 摘要
{session_summary}

### 决策
{chr(10).join(f'- {d}' for d in decisions)}

### 变更文件
{chr(10).join(f'- `{f}`' for f in files_changed)}

---
"""
        
        # 追加到 NOTES.md
        with open(self.notes_path, "a", encoding="utf-8") as f:
            f.write(content)
        
        return content


class ContextCleaner:
    """
    上下文清理器 (/clear)
    
    清理陈旧日志，确保下一次任务敏捷性
    """
    
    def clear(
        self,
        keep_snapshots: int = 5,
        snapshot_dir: str = ".council/snapshots"
    ) -> Dict[str, Any]:
        """
        清理上下文
        
        Args:
            keep_snapshots: 保留的快照数量
            snapshot_dir: 快照目录
            
        Returns:
            清理结果
        """
        snapshot_path = Path(snapshot_dir)
        if not snapshot_path.exists():
            return {"deleted": 0, "kept": 0}
        
        snapshots = sorted(snapshot_path.glob("*.json"))
        to_delete = snapshots[:-keep_snapshots] if len(snapshots) > keep_snapshots else []
        
        for f in to_delete:
            f.unlink()
        
        return {
            "deleted": len(to_delete),
            "kept": len(snapshots) - len(to_delete),
        }


class SessionCache:
    """
    短期会话缓存 (2026最佳实践)
    
    与 NOTES.md (长期记忆) 区分:
    - SessionCache: 当前会话工作上下文，会话结束后清理
    - NOTES.md: 跨会话持久化的情节记忆
    """
    
    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self._cache: Dict[str, Any] = {}
        self._access_order: List[str] = []
    
    def set(self, key: str, value: Any):
        """设置缓存项"""
        if key in self._cache:
            self._access_order.remove(key)
        self._cache[key] = value
        self._access_order.append(key)
        
        # LRU 淘汰
        while len(self._access_order) > self.max_entries:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存项"""
        return self._cache.get(key, default)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()


class TokenSanitizer:
    """
    Token化脱敏器 (2026最佳实践)
    
    沙盒输出脱敏，保护敏感信息
    """
    
    SENSITIVE_PATTERNS = [
        (r'password[=:]\s*[\'"]?[^\s\'"]+', 'password=***REDACTED***'),
        (r'api[_-]?key[=:]\s*[\'"]?[^\s\'"]+', 'api_key=***REDACTED***'),
        (r'secret[=:]\s*[\'"]?[^\s\'"]+', 'secret=***REDACTED***'),
        (r'token[=:]\s*[\'"]?[^\s\'"]+', 'token=***REDACTED***'),
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***EMAIL***'),
    ]
    
    def sanitize(self, text: str) -> str:
        """脱敏文本"""
        import re
        result = text
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result


__all__ = [
    "SessionSnapshot",
    "NotesArchiver",
    "ContextCleaner",
    "SessionCache",
    "TokenSanitizer",
]
