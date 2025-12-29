# Tests for Programmatic Tool Calling
import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock


class TestProgrammaticToolExecutor:
    @pytest.fixture
    def sample_tools(self) -> Dict[str, Any]:
        return {
            "get_weather": AsyncMock(return_value={"temp": 25, "condition": "sunny"}),
            "get_stock": AsyncMock(return_value={"price": 150.50}),
        }

    @pytest.mark.asyncio
    async def test_executor_initialization(self):
        from council.tools.programmatic_tools import ProgrammaticToolExecutor
        executor = ProgrammaticToolExecutor()
        assert executor is not None

    @pytest.mark.asyncio
    async def test_single_tool_call(self, sample_tools):
        from council.tools.programmatic_tools import ProgrammaticToolExecutor
        executor = ProgrammaticToolExecutor(tools=sample_tools)
        code = """
result = await tools.get_weather(city="Beijing")
output = result
"""
        results = await executor.execute_batch(code)
        assert results["temp"] == 25

    @pytest.mark.asyncio
    async def test_batch_tool_calls(self, sample_tools):
        from council.tools.programmatic_tools import ProgrammaticToolExecutor
        executor = ProgrammaticToolExecutor(tools=sample_tools)
        code = """
cities = ["Beijing", "Shanghai"]
results = []
for city in cities:
    data = await tools.get_weather(city=city)
    results.append(data)
output = results
"""
        results = await executor.execute_batch(code)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_sandbox_security(self):
        from council.tools.programmatic_tools import ProgrammaticToolExecutor, SandboxViolationError
        executor = ProgrammaticToolExecutor(tools={})
        dangerous_code = """
import os
os.system("rm -rf /")
"""
        with pytest.raises(SandboxViolationError):
            await executor.execute_batch(dangerous_code)

    @pytest.mark.asyncio
    async def test_timeout(self, sample_tools):
        from council.tools.programmatic_tools import ProgrammaticToolExecutor, ToolExecutionError
        import asyncio

        async def slow_tool(**kwargs):
            await asyncio.sleep(10)
            return {"result": "slow"}

        sample_tools["slow_tool"] = slow_tool
        executor = ProgrammaticToolExecutor(tools=sample_tools, timeout=0.1)
        code = """
result = await tools.slow_tool()
output = result
"""
        with pytest.raises((ToolExecutionError, asyncio.TimeoutError)):
            await executor.execute_batch(code)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
