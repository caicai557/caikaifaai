from typing import Optional, List
import json

from council.persistence.checkpoint import Checkpoint
from council.persistence.state_store import StateStore

try:
    import redis.asyncio as redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class RedisStateStore(StateStore):
    """
    Redis 状态存储实现

    Schema:
    - Checkpoint: council:checkpoints:{thread_id}:{step} -> JSON
    - Latest: council:latest:{thread_id} -> step
    """

    def __init__(self, url: str = "redis://localhost:6379/0"):
        if not HAS_REDIS:
            raise ImportError(
                "redis is required for RedisStateStore. Install with: pip install redis"
            )
        self.url = url
        self.client = None

    async def initialize(self) -> None:
        if not self.client:
            self.client = redis.asyncio.Redis.from_url(self.url, decode_responses=True)

    async def save(self, checkpoint: Checkpoint) -> None:
        await self.initialize()

        key = f"council:checkpoints:{checkpoint.thread_id}:{checkpoint.step}"
        latest_key = f"council:latest:{checkpoint.thread_id}"

        data = json.dumps(checkpoint.to_dict(), ensure_ascii=False)

        async with self.client.pipeline() as pipe:
            await pipe.set(key, data)
            await pipe.set(latest_key, checkpoint.step)
            await pipe.execute()

    async def load(self, thread_id: str) -> Optional[Checkpoint]:
        """加载最新检查点"""
        return await self.load_latest(thread_id)

    async def load_at_step(self, thread_id: str, step: int) -> Optional[Checkpoint]:
        """加载特定步骤"""
        await self.initialize()
        key = f"council:checkpoints:{thread_id}:{step}"
        data = await self.client.get(key)
        if not data:
            return None
        return Checkpoint.from_dict(json.loads(data))

    async def load_latest(self, thread_id: str) -> Optional[Checkpoint]:
        await self.initialize()
        latest_key = f"council:latest:{thread_id}"
        step = await self.client.get(latest_key)
        if not step:
            return None
        return await self.load_at_step(thread_id, int(step))

    async def list_checkpoints(self, thread_id: str) -> List[Checkpoint]:
        await self.initialize()
        # Scan for keys (inefficient for large sets, but simple for now)
        # Better: use a Sorted Set for indexing
        pattern = f"council:checkpoints:{thread_id}:*"
        keys = await self.client.keys(pattern)

        checkpoints = []
        for key in keys:
            data = await self.client.get(key)
            if data:
                checkpoints.append(Checkpoint.from_dict(json.loads(data)))

        return sorted(checkpoints, key=lambda x: x.step)

    async def delete_thread(self, thread_id: str) -> None:
        await self.initialize()
        pattern = f"council:*:{thread_id}*"
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)


__all__ = ["RedisStateStore", "RedisDistributedLock"]


class RedisDistributedLock:
    """
    Redis 分布式锁实现 (基于 Redlock 算法)

    支持：获取/释放/续期/Context Manager
    """

    def __init__(self, client):
        self.client = client
        self._locks: dict = {}

    async def acquire(self, key: str, ttl: int = 30) -> bool:
        import uuid
        token = str(uuid.uuid4())
        lock_key = f"council:lock:{key}"
        result = await self.client.set(lock_key, token, nx=True, ex=ttl)
        if result:
            self._locks[key] = token
            return True
        return False

    async def release(self, key: str) -> bool:
        token = self._locks.get(key)
        if not token:
            return False
        lock_key = f"council:lock:{key}"
        current_token = await self.client.get(lock_key)
        if current_token != token:
            return False
        await self.client.delete(lock_key)
        del self._locks[key]
        return True

    async def extend(self, key: str, ttl: int = 30) -> bool:
        token = self._locks.get(key)
        if not token:
            return False
        lock_key = f"council:lock:{key}"
        current_token = await self.client.get(lock_key)
        if current_token != token:
            return False
        await self.client.expire(lock_key, ttl)
        return True

    def lock(self, key: str, ttl: int = 30):
        return _LockContext(self, key, ttl)


class _LockContext:
    def __init__(self, lock: RedisDistributedLock, key: str, ttl: int):
        self.lock = lock
        self.key = key
        self.ttl = ttl
        self.acquired = False

    async def __aenter__(self) -> bool:
        self.acquired = await self.lock.acquire(self.key, self.ttl)
        return self.acquired

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.acquired:
            await self.lock.release(self.key)
        return False

