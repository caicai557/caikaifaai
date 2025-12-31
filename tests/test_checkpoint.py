"""
Tests for State Persistence (Checkpointing)

TDD: 先写测试，后实现
"""

import pytest
import tempfile
import os


# =============================================================
# Test Fixtures
# =============================================================


@pytest.fixture
def temp_db():
    """临时数据库文件"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    os.unlink(f.name)


# =============================================================
# Test: Checkpoint Data Structure
# =============================================================


class TestCheckpoint:
    """Checkpoint 数据结构测试"""

    def test_checkpoint_creation(self):
        """测试创建 Checkpoint"""
        from council.persistence.checkpoint import Checkpoint

        cp = Checkpoint(
            thread_id="thread-123",
            state={"key": "value"},
            step=1,
        )

        assert cp.thread_id == "thread-123"
        assert cp.state == {"key": "value"}
        assert cp.step == 1
        assert cp.timestamp is not None

    def test_checkpoint_serialization(self):
        """测试 Checkpoint 序列化"""
        from council.persistence.checkpoint import Checkpoint

        cp = Checkpoint(
            thread_id="thread-123",
            state={"messages": ["hello", "world"]},
            step=5,
        )

        data = cp.to_dict()
        restored = Checkpoint.from_dict(data)

        assert restored.thread_id == cp.thread_id
        assert restored.state == cp.state
        assert restored.step == cp.step


# =============================================================
# Test: SQLite State Store
# =============================================================


# Check if aiosqlite is available
import importlib.util

HAS_AIOSQLITE = importlib.util.find_spec("aiosqlite") is not None


@pytest.mark.skipif(not HAS_AIOSQLITE, reason="aiosqlite not installed")
class TestSqliteStateStore:
    """SQLite 状态存储测试"""

    @pytest.mark.asyncio
    async def test_save_and_load(self, temp_db):
        """测试保存和加载"""
        from council.persistence.state_store import SqliteStateStore
        from council.persistence.checkpoint import Checkpoint

        store = SqliteStateStore(temp_db)
        await store.initialize()

        cp = Checkpoint(
            thread_id="thread-abc",
            state={"user": "Alice", "messages": []},
            step=1,
        )

        await store.save(cp)
        loaded = await store.load("thread-abc")

        assert loaded is not None
        assert loaded.thread_id == "thread-abc"
        assert loaded.state["user"] == "Alice"

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, temp_db):
        """测试加载不存在的 thread"""
        from council.persistence.state_store import SqliteStateStore

        store = SqliteStateStore(temp_db)
        await store.initialize()

        loaded = await store.load("nonexistent")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_multiple_checkpoints_same_thread(self, temp_db):
        """测试同一 thread 多个 checkpoint"""
        from council.persistence.state_store import SqliteStateStore
        from council.persistence.checkpoint import Checkpoint

        store = SqliteStateStore(temp_db)
        await store.initialize()

        for step in range(3):
            cp = Checkpoint(
                thread_id="thread-multi",
                state={"step": step},
                step=step,
            )
            await store.save(cp)

        # 加载最新的
        latest = await store.load("thread-multi")
        assert latest.step == 2

        # 列出所有
        history = await store.list_checkpoints("thread-multi")
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_time_travel(self, temp_db):
        """测试时间旅行 - 加载特定步骤"""
        from council.persistence.state_store import SqliteStateStore
        from council.persistence.checkpoint import Checkpoint

        store = SqliteStateStore(temp_db)
        await store.initialize()

        for step in range(5):
            cp = Checkpoint(
                thread_id="thread-travel",
                state={"value": step * 10},
                step=step,
            )
            await store.save(cp)

        # 加载第 2 步
        step2 = await store.load_at_step("thread-travel", step=2)
        assert step2.state["value"] == 20

    @pytest.mark.asyncio
    async def test_delete_thread(self, temp_db):
        """测试删除 thread 所有 checkpoint"""
        from council.persistence.state_store import SqliteStateStore
        from council.persistence.checkpoint import Checkpoint

        store = SqliteStateStore(temp_db)
        await store.initialize()

        cp = Checkpoint(thread_id="thread-del", state={}, step=0)
        await store.save(cp)

        await store.delete_thread("thread-del")
        loaded = await store.load("thread-del")
        assert loaded is None


# =============================================================
# Test: Thread Isolation
# =============================================================


@pytest.mark.skipif(not HAS_AIOSQLITE, reason="aiosqlite not installed")
class TestThreadIsolation:
    """Thread 隔离测试"""

    @pytest.mark.asyncio
    async def test_different_threads_isolated(self, temp_db):
        """测试不同 thread 相互隔离"""
        from council.persistence.state_store import SqliteStateStore
        from council.persistence.checkpoint import Checkpoint

        store = SqliteStateStore(temp_db)
        await store.initialize()

        await store.save(Checkpoint("thread-a", {"data": "A"}, 0))
        await store.save(Checkpoint("thread-b", {"data": "B"}, 0))

        a = await store.load("thread-a")
        b = await store.load("thread-b")

        assert a.state["data"] == "A"
        assert b.state["data"] == "B"
