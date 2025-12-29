# Tests for Model Router
import pytest


class TestModelRouter:
    @pytest.mark.asyncio
    async def test_router_initialization(self):
        from council.orchestration.model_router import ModelRouter
        router = ModelRouter()
        assert router is not None
        assert hasattr(router, "route")

    @pytest.mark.asyncio
    async def test_route_coding_task(self):
        from council.orchestration.model_router import ModelRouter
        router = ModelRouter()
        result = await router.route("Write a Python function to sort a list")
        assert result is not None
        assert hasattr(result, "model_name")

    @pytest.mark.asyncio
    async def test_route_planning_task(self):
        from council.orchestration.model_router import ModelRouter
        router = ModelRouter()
        result = await router.route("Design the architecture for a microservices system")
        assert result is not None

    @pytest.mark.asyncio
    async def test_route_with_fallback(self):
        from council.orchestration.model_router import ModelRouter
        router = ModelRouter()
        result = await router.route_with_fallback("Complex refactoring task")
        assert result is not None
        assert hasattr(result, "primary")
        assert hasattr(result, "fallback")

    @pytest.mark.asyncio
    async def test_route_batch(self):
        from council.orchestration.model_router import ModelRouter
        router = ModelRouter()
        tasks = ["task1", "task2"]
        results = await router.route_batch(tasks)
        assert len(results) == 2

    def test_model_specs_consistency(self):
        from council.orchestration.task_classifier import MODEL_SPECS
        from council.orchestration.model_router import ROUTER_MODEL_CONFIGS
        assert len(MODEL_SPECS) > 0
        assert len(ROUTER_MODEL_CONFIGS) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
