import pytest
import pytest_asyncio
import asyncio
from src.telegram_multi.cortex.actors.base import BaseActor

class MockActor(BaseActor):
    def __init__(self, name="mock"):
        super().__init__(name)
        self.processed_messages = []

    async def handle(self, msg):
        if msg == "CRASH":
            raise ValueError("Intentional Crash")
        if msg == "SLOW":
            await asyncio.sleep(0.2) # Longer than timeout? No, timeout is 5s usually.
            # We'll mock timeout logic in test params if possible, or override.
        self.processed_messages.append(msg)

@pytest_asyncio.fixture
async def actor():
    a = MockActor()
    # Override timeout for testing speed
    a._timeout = 0.1
    t = asyncio.create_task(a.start())
    yield a
    await a.tell("STOP")
    await t

@pytest.mark.asyncio
async def test_actor_processes_messages(actor):
    await actor.tell("hello")
    await asyncio.sleep(0.01)
    assert "hello" in actor.processed_messages

@pytest.mark.asyncio
async def test_actor_survives_crash(actor):
    """Ensure actor loop continues after an exception in handle."""
    await actor.tell("CRASH")
    await actor.tell("recovery")
    await asyncio.sleep(0.01)
    assert "recovery" in actor.processed_messages

@pytest.mark.asyncio
async def test_actor_timeout_resilience(actor):
    """Ensure actor keeps running even if no messages (timeout triggers)."""
    # Wait longer than _timeout (0.1s)
    await asyncio.sleep(0.2)
    assert actor.running
    await actor.tell("after_timeout")
    await asyncio.sleep(0.01)
    assert "after_timeout" in actor.processed_messages
