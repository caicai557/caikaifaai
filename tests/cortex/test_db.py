import pytest
import os
from src.telegram_multi.cortex.db import CortexDB

CONST_TEST_DB = "test_cortex.db"

import pytest_asyncio

@pytest_asyncio.fixture
async def cortex_db():
    if os.path.exists(CONST_TEST_DB):
        os.remove(CONST_TEST_DB)

    db = CortexDB(CONST_TEST_DB)
    await db.initialize()
    yield db
    await db.close()

    if os.path.exists(CONST_TEST_DB):
        os.remove(CONST_TEST_DB)

@pytest.mark.asyncio
async def test_wal_mode_enabled(cortex_db):
    """Verify that WAL mode is actually enabled."""
    async with cortex_db.execute("PRAGMA journal_mode;") as cursor:
        row = await cursor.fetchone()
        assert row[0].upper() == "WAL", "Database must be in WAL mode"

@pytest.mark.asyncio
async def test_schema_tables_exist(cortex_db):
    """Verify tables are created."""
    tables = ["traces", "spans", "votes"]
    for table in tables:
        async with cortex_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,)
        ) as cursor:
            row = await cursor.fetchone()
            assert row is not None, f"Table {table} not created"
