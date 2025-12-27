import asyncio
import logging
from typing import List
from .db import CortexDB

class LogActor:
    """
    Dedicated Actor for writing logs to SQLite.
    Prevents database locking by serializing all writes through a single queue.
    """
    def __init__(self, db: CortexDB):
        self.db = db
        self.inbox = asyncio.Queue()
        self.running = False
        self._batch: List[tuple] = []
        self._batch_size = 10
        self._flush_interval = 2.0 # seconds

    async def start(self):
        """Main actor loop."""
        self.running = True
        while self.running:
            try:
                # Wait for message with timeout to allow periodic flushing
                msg = await asyncio.wait_for(self.inbox.get(), timeout=self._flush_interval)

                if msg == "STOP":
                    await self._flush_spans()
                    self.running = False
                    self.inbox.task_done()
                    break

                # Assume msg is a Span tuple: (span_id, trace_id, agent_id, step_type, input, output, conf)
                self._batch.append(msg)

                if len(self._batch) >= self._batch_size:
                    await self._flush_spans()

                self.inbox.task_done()

            except asyncio.TimeoutError:
                # Flush on timeout
                await self._flush_spans()
            except Exception as e:
                logging.error(f"LogActor crashed: {e}")
                # We don't want to crash the logger loop, just log the error and continue
                await asyncio.sleep(1)

    async def log_span(self, span_data: tuple):
        """Public method to send log to actor."""
        await self.inbox.put(span_data)

    async def _flush_spans(self):
        """Write batch to DB."""
        if not self._batch:
            return

        try:
            # Atomic batch insert
            await self.db.execute("BEGIN TRANSACTION")
            for span in self._batch:
                # (span_id, trace_id, agent_id, step_type, input, output, conf)
                await self.db.execute(
                    """INSERT INTO spans (span_id, trace_id, agent_id, step_type, input_text, output_text, confidence)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    span
                )
            await self.db.execute("COMMIT")
            self._batch = []
        except Exception as e:
            logging.error(f"Failed to flush logs: {e}")
            try:
                await self.db.execute("ROLLBACK")
            except:
                pass
