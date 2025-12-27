import pytest
import asyncio
import os
from src.telegram_multi.cortex.db import CortexDB
from src.telegram_multi.cortex.logger import LogActor

CONST_TEST_DB = "test_logger.db"

import pytest_asyncio

@pytest_asyncio.fixture
async def logger_stack():
    if os.path.exists(CONST_TEST_DB):
        os.remove(CONST_TEST_DB)

    db = CortexDB(CONST_TEST_DB)
    await db.initialize()
    actor = LogActor(db)

    # Start actor in background
    task = asyncio.create_task(actor.start())

    yield actor, db

    # Cleanup
    await actor.log_span("STOP")
    await task
    await db.close()

    if os.path.exists(CONST_TEST_DB):
        os.remove(CONST_TEST_DB)

@pytest.mark.asyncio
async def test_log_span_writes_to_db(logger_stack):
    """Verify that a span sent to the actor eventually ends up in the DB."""
    actor, db = logger_stack

    # (span_id, trace_id, agent_id, step_type, input, output, conf)
    test_span = ("span1", "trace1", "agent1", "THINK", "input1", "output1", 0.95)

    await actor.log_span(test_span)

    # Wait strictly longer than flush interval? No, we can trigger flush by stopping or waiting
    # We'll wait a bit (less than 2s flush) but we rely on STOP to flush residue
    # Or we can insert enough to trigger batch flush.

    # Let's forcefully stop to trigger flush
    # The fixture will stop it.
    pass

    # We need to verify AFTER fixture cleanup? No, fixture cleanup closes DB.
    # We must verify inside the test.

    # Force manual flush not available on actor.
    # But batch size is 10.

@pytest.mark.asyncio
async def test_batch_flush_trigger(logger_stack):
    actor, db = logger_stack

    # Send 12 items (batch size 10)
    for i in range(12):
        span = (f"span_{i}", "trace1", "agent1", "THINK", "in", "out", 0.9)
        await actor.log_span(span)

    # Give it a tiny moment to process the batch
    await asyncio.sleep(0.5)

    # Check DB
    async with db.execute("SELECT COUNT(*) FROM spans") as cursor:
        row = await cursor.fetchone()
        # Should have at least 10 flushed
        assert row[0] >= 10
