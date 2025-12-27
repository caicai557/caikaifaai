import aiosqlite

class CortexDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    async def initialize(self):
        """Initialize DB connection, enable WAL, and create schema."""
        self._conn = await aiosqlite.connect(self.db_path)

        # Enforce WAL mode for concurrency
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;") # Optimization

        await self._create_schema()
        await self._conn.commit()

    async def _create_schema(self):
        """Create the Cortex schema (Traces, Spans, Votes)."""
        # Traces: System-level sessions
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                goal TEXT
            );
        """)

        # Spans: Atomic thought steps
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                span_id TEXT PRIMARY KEY,
                trace_id TEXT,
                agent_id TEXT,
                step_type TEXT,
                input_text TEXT,
                output_text TEXT,
                confidence FLOAT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(trace_id) REFERENCES traces(trace_id)
            );
        """)

        # Votes: Wald math inputs
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                vote_id TEXT PRIMARY KEY,
                span_id TEXT,
                decision TEXT,
                confidence FLOAT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(span_id) REFERENCES spans(span_id)
            );
        """)

    def execute(self, sql: str, parameters=()):
        if not self._conn:
            raise RuntimeError("Database not initialized")
        return self._conn.execute(sql, parameters)

    async def commit(self):
        if self._conn:
            await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()
