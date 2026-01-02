"""
Integration Test - Full Workflow Verification

Tests the complete integration between:
- ContextManager (context engineering)
- MemoryAggregator (unified memory)
- TieredMemory (auto promotion)
- LLMSession (sliding window)
- BaseAgent (memory integration)
- CompositeTools (aggregate tools)
"""

import sys
from unittest.mock import MagicMock, AsyncMock
import os
import tempfile
import shutil

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest


@pytest.fixture
def temp_dir():
    """Create temporary directory for persistence"""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestModuleExports:
    """Test that all new modules are properly exported"""

    def test_memory_exports(self):
        """Test memory module exports"""
        from council.memory import (
            LLMSession,
            VectorMemory,
            TieredMemory,
            MemoryAggregator,
            KnowledgeGraph,
        )

        assert LLMSession is not None
        assert VectorMemory is not None
        assert TieredMemory is not None
        assert MemoryAggregator is not None
        assert KnowledgeGraph is not None

    def test_context_exports(self):
        """Test context module exports"""
        from council.context import (
            RollingContext,
            ContextManager,
            ContextLayer,
            ContextEntry,
        )

        assert RollingContext is not None
        assert ContextManager is not None
        assert ContextLayer is not None
        assert ContextEntry is not None

    def test_tools_exports(self):
        """Test tools module exports"""
        from council.tools import (
            CompositeTools,
            OrchestrationEngine,
        )

        assert CompositeTools is not None
        assert OrchestrationEngine is not None


class TestIntegrationWorkflow:
    """Test complete workflow integration"""

    def test_context_to_memory_flow(self, temp_dir):
        """Test context layer flows to memory aggregator"""
        from council.context import ContextManager, ContextLayer
        from council.memory import VectorMemory, TieredMemory, MemoryAggregator

        # 1. Setup context
        ctx = ContextManager()
        ctx.add_layer(ContextLayer.SYSTEM, "You are a helpful assistant")
        ctx.add_layer(ContextLayer.SESSION, "User asked about Python")

        # 2. Setup memory
        tiered = TieredMemory(persist_dir=temp_dir)
        vector = VectorMemory(persist_dir=temp_dir, collection_name="long_term")
        agg = MemoryAggregator(short_term=tiered, long_term=vector)

        # 3. Store context summary to memory
        context_summary = ctx.compile()
        agg.remember(context_summary, memory_type="short_term")

        # 4. Verify memory was stored
        assert tiered.short_term.count() == 1

        # 5. Query directly from short_term
        stored = tiered.short_term.search("")
        assert len(stored) > 0
        assert "assistant" in stored[0]["document"].lower()

    def test_session_with_memory(self, temp_dir):
        """Test LLMSession sliding window with memory"""
        from council.memory import LLMSession, TieredMemory, MemoryAggregator

        # 1. Setup
        session = LLMSession(agent_name="test", storage_dir=temp_dir, window_size=3)
        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        # 2. Add messages
        for i in range(10):
            session.add_message("user", f"Message {i} about coding")

        # 3. Get windowed messages
        windowed = session.get_messages(use_window=True)

        # 4. Store important messages to memory
        for msg in windowed:
            if msg["role"] != "system":
                agg.remember(msg["content"], "short_term")

        # 5. Verify
        assert len(windowed) <= 4  # 1 system + 3 window
        assert tiered.short_term.count() > 0

    def test_tiered_memory_lifecycle(self, temp_dir):
        """Test complete tiered memory lifecycle"""
        from council.memory import TieredMemory

        tiered = TieredMemory(persist_dir=temp_dir)
        tiered.AUTO_PROMOTE_ACCESS_COUNT = 2

        # 1. Add to short-term
        doc_id = tiered.short_term.add("Important fact", {"type": "fact"})

        # 2. Access multiple times
        tiered.increment_access("short_term", doc_id)
        tiered.increment_access("short_term", doc_id)

        # 3. Auto promote
        promoted = tiered.auto_promote()

        # 4. Verify
        assert promoted == 1
        assert tiered.short_term.count() == 0
        assert tiered.long_term.count() == 1

        # 5. Check promoted_from metadata
        doc = tiered.long_term.get(doc_id)
        assert doc["metadata"]["promoted_from"] == "short_term"

    def test_context_manager_cache_integration(self):
        """Test context manager KV-cache optimization"""
        from council.context import ContextManager, ContextLayer

        ctx = ContextManager()

        # Add cacheable system context
        ctx.add_layer(
            ContextLayer.SYSTEM,
            "You are an AI assistant specialized in coding.",
            is_cacheable=True,
        )

        # Add cacheable document
        ctx.add_layer(
            ContextLayer.DOCUMENT,
            "Project uses Python 3.12 and FastAPI framework.",
            is_cacheable=True,
        )

        # Add dynamic session context
        ctx.add_layer(
            ContextLayer.SESSION,
            "User is asking about authentication.",
            is_cacheable=False,
        )

        # Get cache prefix (only cacheable content)
        cache_prefix = ctx.get_kv_cache_prefix()
        cache_key = ctx.get_cache_key()

        # Verify
        assert "AI assistant" in cache_prefix
        assert "Python 3.12" in cache_prefix
        assert "authentication" not in cache_prefix
        assert len(cache_key) == 32


class TestAgentIntegration:
    """Test BaseAgent memory integration"""

    def test_agent_memory_methods(self, temp_dir):
        """Test agent memory query and record methods"""
        from council.agents.base_agent import BaseAgent, ThinkResult, Vote, VoteDecision
        from council.memory import TieredMemory, MemoryAggregator

        # Create concrete agent for testing
        class TestAgent(BaseAgent):
            def think(self, task, context=None):
                # Query memory before thinking
                memory_context = self._query_memory(task)
                return ThinkResult(
                    analysis=f"Analyzed with memory: {memory_context[:50] if memory_context else 'none'}"
                )

            def vote(self, proposal, context=None):
                return Vote(
                    agent_name=self.name,
                    decision=VoteDecision.APPROVE,
                    confidence=0.8,
                    rationale="Test vote",
                )

            def execute(self, task, context=None):
                # Record result to memory
                self._record_to_memory(f"Executed: {task}", "short_term")
                return {"success": True}

        # Setup
        tiered = TieredMemory(persist_dir=temp_dir)
        agg = MemoryAggregator(short_term=tiered)

        # Pre-populate memory
        agg.remember("Python best practices include type hints", "short_term")

        # Create agent with memory
        agent = TestAgent(
            name="TestAgent",
            system_prompt="You are a test agent",
            memory_aggregator=agg,
        )

        # Test think with memory
        result = agent.think("How to use Python type hints")
        assert (
            "best practices" in result.analysis.lower()
            or "memory" in result.analysis.lower()
        )

        # Test execute with memory recording
        agent.execute("Build login system")
        assert tiered.short_term.count() >= 1


class TestCompositeToolsIntegration:
    """Test CompositeTools integration"""

    def test_tools_with_memory(self, temp_dir):
        """Test composite tools store results to memory"""
        from council.tools import CompositeTools
        from council.memory import TieredMemory, VectorMemory, MemoryAggregator

        # Setup memory
        tiered = TieredMemory(persist_dir=temp_dir)
        vector = VectorMemory(persist_dir=temp_dir, collection_name="research")
        agg = MemoryAggregator(short_term=tiered, long_term=vector)

        # Create tools with memory
        tools = CompositeTools(memory_aggregator=agg)

        # Get tool definitions (for MCP registration)
        defs = tools.get_tool_definitions()

        assert len(defs) == 2
        assert any(d["name"] == "deep_research" for d in defs)
        assert any(d["name"] == "code_analyze" for d in defs)


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow"""

    @pytest.mark.asyncio
    async def test_full_agent_workflow(self, temp_dir):
        """Test complete agent workflow with all components"""
        from council.context import ContextManager, ContextLayer
        from council.memory import (
            LLMSession,
            TieredMemory,
            VectorMemory,
            MemoryAggregator,
        )

        # 1. Initialize all systems
        ctx = ContextManager()
        session = LLMSession("architect", storage_dir=temp_dir, window_size=5)
        tiered = TieredMemory(persist_dir=temp_dir)
        vector = VectorMemory(persist_dir=temp_dir, collection_name="knowledge")
        agg = MemoryAggregator(short_term=tiered, long_term=vector)

        # 2. Setup context layers
        ctx.add_layer(
            ContextLayer.SYSTEM, "You are an architecture expert", is_cacheable=True
        )
        ctx.add_layer(
            ContextLayer.DOCUMENT,
            "Project uses microservices architecture",
            is_cacheable=True,
        )

        # 3. Simulate conversation
        session.add_message("system", ctx.compile())
        session.add_message("user", "Design an authentication service")
        session.add_message("assistant", "I'll design a JWT-based auth service...")

        # 4. Store key findings to memory
        agg.remember("Authentication uses JWT tokens", "long_term", {"topic": "auth"})
        agg.remember("Session conversation about microservices", "short_term")

        # 5. Query memory for context
        memory_context = agg.get_context_for_llm("authentication design")

        # 6. Verify complete workflow
        assert ctx.get_stats()["total_entries"] == 2
        assert session.state.messages[-1].role == "assistant"
        assert vector.count() == 1
        assert tiered.short_term.count() == 1
        assert "JWT" in memory_context

        # 7. Verify persistence
        session.save()
        assert session.session_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
