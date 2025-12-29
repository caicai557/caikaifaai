# Tests for Redis Distributed Lock
import pytest
from unittest.mock import AsyncMock, MagicMock
import sys

mock_redis = MagicMock()
sys.modules.setdefault("redis", mock_redis)
sys.modules.setdefault("redis.asyncio", mock_redis)


class TestRedisDistributedLock:
    @pytest.fixture
    def mock_redis_client(self):
        client = AsyncMock()
        client.set = AsyncMock(return_value=True)
        client.get = AsyncMock(return_value=None)
        client.delete = AsyncMock(return_value=1)
        client.expire = AsyncMock(return_value=True)
        return client

    @pytest.mark.asyncio
    async def test_acquire_success(self, mock_redis_client):
        from council.persistence.redis_store import RedisDistributedLock
        lock = RedisDistributedLock(mock_redis_client)
        mock_redis_client.set.return_value = True
        result = await lock.acquire("test-lock", ttl=30)
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_failure(self, mock_redis_client):
        from council.persistence.redis_store import RedisDistributedLock
        lock = RedisDistributedLock(mock_redis_client)
        mock_redis_client.set.return_value = False
        result = await lock.acquire("test-lock", ttl=30)
        assert result is False

    @pytest.mark.asyncio
    async def test_release_success(self, mock_redis_client):
        from council.persistence.redis_store import RedisDistributedLock
        lock = RedisDistributedLock(mock_redis_client)
        lock._locks["test-lock"] = "token-123"
        mock_redis_client.get.return_value = "token-123"
        result = await lock.release("test-lock")
        assert result is True

    @pytest.mark.asyncio
    async def test_release_wrong_owner(self, mock_redis_client):
        from council.persistence.redis_store import RedisDistributedLock
        lock = RedisDistributedLock(mock_redis_client)
        lock._locks["test-lock"] = "my-token"
        mock_redis_client.get.return_value = "other-token"
        result = await lock.release("test-lock")
        assert result is False

    @pytest.mark.asyncio
    async def test_extend(self, mock_redis_client):
        from council.persistence.redis_store import RedisDistributedLock
        lock = RedisDistributedLock(mock_redis_client)
        lock._locks["test-lock"] = "token"
        mock_redis_client.get.return_value = "token"
        result = await lock.extend("test-lock", ttl=60)
        assert result is True

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_redis_client):
        from council.persistence.redis_store import RedisDistributedLock
        lock = RedisDistributedLock(mock_redis_client)
        mock_redis_client.set.return_value = True
        async with lock.lock("test-resource", ttl=10) as acquired:
            assert acquired is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
