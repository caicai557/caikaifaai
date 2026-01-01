import unittest
from unittest.mock import MagicMock, AsyncMock
import sys
import json

# Check if redis is available
import importlib.util

HAS_REDIS = importlib.util.find_spec("redis") is not None

from council.persistence import Checkpoint  # noqa: E402

# Mock redis module before importing RedisStateStore
mock_redis = MagicMock()
mock_redis.__spec__ = None  # Fix: pytest requires __spec__ to be set
mock_redis_asyncio = MagicMock()
mock_redis_asyncio.__spec__ = None
mock_redis_client = AsyncMock()
mock_redis_asyncio.Redis.from_url.return_value = mock_redis_client
sys.modules["redis"] = mock_redis
sys.modules["redis.asyncio"] = mock_redis_asyncio


@unittest.skipUnless(HAS_REDIS, "redis not installed")
class TestRedisStateStore(unittest.IsolatedAsyncioTestCase):
    async def test_save_load(self):
        # Setup Pipeline Mock
        mock_pipeline = AsyncMock()
        mock_pipeline.__aenter__ = AsyncMock(return_value=mock_pipeline)
        mock_pipeline.__aexit__ = AsyncMock(return_value=None)

        mock_client = AsyncMock()
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)

        # Patch redis.Redis (since we import redis.asyncio as redis, and call redis.Redis)
        # Actually, in redis_store.py: import redis.asyncio as redis
        # So we need to patch redis.asyncio.Redis
        # Import first
        from council.persistence.redis_store import RedisStateStore
        import council.persistence.redis_store

        # Patch the specific class method used in the module
        # redis_store.redis is the alias for redis.asyncio
        with unittest.mock.patch.object(
            council.persistence.redis_store.redis.Redis,
            "from_url",
            return_value=mock_client,
        ):
            from council.persistence.redis_store import RedisStateStore

            store = RedisStateStore("redis://localhost")

            # Test Save
            cp = Checkpoint("thread-1", {"a": 1}, step=1)
            await store.save(cp)

            # Verify set call
            expected_key = "council:checkpoints:thread-1:1"
            # pipe.set called twice
            self.assertEqual(mock_pipeline.set.call_count, 2)

            # Check first call (checkpoint data)
            args = mock_pipeline.set.call_args_list[0]
            self.assertEqual(args[0][0], expected_key)
            saved_data = json.loads(args[0][1])
            self.assertEqual(saved_data["thread_id"], "thread-1")

            # Test Load
            mock_client.get.return_value = json.dumps(cp.to_dict())
            loaded = await store.load_at_step("thread-1", 1)
            self.assertEqual(loaded.thread_id, "thread-1")
            self.assertEqual(loaded.state["a"], 1)


if __name__ == "__main__":
    unittest.main()
