import asyncio
import logging
from typing import Optional

class BaseActor:
    """
    Abstract Actor class implementing the Async Actor Pattern.
    Features:
    - Bounded/Unbounded Inbox (asyncio.Queue)
    - Safe Message Loop with Timeout
    - Crash Recovery (catches Exceptions in handle)
    """
    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.inbox = asyncio.Queue()
        self.running = False
        self._timeout = timeout
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the actor loop as a background task."""
        self.running = True
        # In production we might want to return the task to allow awaiting?
        # or just run the loop if awaited directly.
        # The test awaits start(), so let's run the loop here.
        # But usually start() should be non-blocking? 
        # The test does `asyncio.create_task(a.start())`. Correct.
        await self._loop()

    async def _loop(self):
        while self.running:
            try:
                msg = await asyncio.wait_for(self.inbox.get(), timeout=self._timeout)
                
                if msg == "STOP":
                    self.running = False
                    self.inbox.task_done()
                    break
                
                await self.handle(msg)
                self.inbox.task_done()
                
            except asyncio.TimeoutError:
                # Heartbeat or Idle
                pass
            except Exception as e:
                logging.error(f"Actor {self.name} crashed processing message: {e}")
                # We continue the loop! (Crash Recovery)

    async def handle(self, msg):
        """Override this method to process messages."""
        raise NotImplementedError

    async def tell(self, msg):
        """Send a message to this actor."""
        await self.inbox.put(msg)

    async def ask(self, msg):
        """Request-Response pattern (TODO)."""
        pass
