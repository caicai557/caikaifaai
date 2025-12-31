"""
Unit tests for AI Council MCP Server

Tests cover:
- Model configuration and validation
- API key detection
- Parallel query execution
- Agreement score calculation
- Response synthesis
"""

import pytest
import os
from unittest.mock import patch
from council.mcp.ai_council_server import (
    AICouncilServer,
    ModelConfig,
    ModelProvider,
    ModelResponse,
    ConsensusResponse,
    DEFAULT_MODELS,
)


class TestModelConfiguration:
    """Tests for model configuration"""

    def test_default_models_exist(self):
        """Should have default model configurations"""
        assert len(DEFAULT_MODELS) >= 1
        assert any(m.provider == ModelProvider.GEMINI for m in DEFAULT_MODELS)

    def test_model_config_creation(self):
        """Should create model config with all fields"""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            api_key_env="OPENAI_API_KEY",
            weight=0.8,
        )
        assert config.provider == ModelProvider.OPENAI
        assert config.model_name == "gpt-4"
        assert config.weight == 0.8
        assert config.enabled is True


class TestAPIKeyValidation:
    """Tests for API key detection"""

    def test_models_disabled_without_api_key(self):
        """Models without API keys should be disabled"""
        with patch.dict(os.environ, {}, clear=True):
            server = AICouncilServer()
            enabled = server.get_enabled_models()
            assert len(enabled) == 0

    def test_models_enabled_with_api_key(self):
        """Models with API keys should be enabled"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
            models = [
                ModelConfig(
                    provider=ModelProvider.GEMINI,
                    model_name="gemini-2.0-flash",
                    api_key_env="GEMINI_API_KEY",
                )
            ]
            server = AICouncilServer(models=models)
            enabled = server.get_enabled_models()
            assert len(enabled) == 1
            assert enabled[0].provider == ModelProvider.GEMINI


class TestServerStatus:
    """Tests for server status reporting"""

    def test_get_status_structure(self):
        """Status should have correct structure"""
        server = AICouncilServer()
        status = server.get_status()

        assert "total_models" in status
        assert "enabled_models" in status
        assert "models" in status
        assert isinstance(status["models"], list)

    def test_status_model_details(self):
        """Status should include model details"""
        models = [
            ModelConfig(
                provider=ModelProvider.GEMINI,
                model_name="gemini-flash",
                api_key_env="GEMINI_API_KEY",
                weight=1.5,
            )
        ]
        server = AICouncilServer(models=models)
        status = server.get_status()

        assert status["total_models"] == 1
        assert status["models"][0]["provider"] == "gemini"
        assert status["models"][0]["weight"] == 1.5


class TestAgreementCalculation:
    """Tests for agreement score calculation"""

    def test_agreement_with_single_response(self):
        """Single response should have perfect agreement"""
        server = AICouncilServer()
        responses = [
            ModelResponse(
                provider=ModelProvider.GEMINI,
                model_name="gemini-flash",
                content="Hello world",
                latency_ms=100,
                success=True,
            )
        ]
        agreement = server._calculate_agreement(responses)
        assert agreement == 1.0

    def test_agreement_with_similar_responses(self):
        """Similar length responses should have high agreement"""
        server = AICouncilServer()
        responses = [
            ModelResponse(
                provider=ModelProvider.GEMINI,
                model_name="gemini",
                content="This is a test response.",
                latency_ms=100,
                success=True,
            ),
            ModelResponse(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                content="This is a test answer.",
                latency_ms=150,
                success=True,
            ),
        ]
        agreement = server._calculate_agreement(responses)
        assert agreement > 0.8  # High agreement for similar lengths

    def test_agreement_with_failed_responses(self):
        """Failed responses should be ignored in agreement"""
        server = AICouncilServer()
        responses = [
            ModelResponse(
                provider=ModelProvider.GEMINI,
                model_name="gemini",
                content="Success",
                latency_ms=100,
                success=True,
            ),
            ModelResponse(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                content="",
                latency_ms=50,
                success=False,
                error="API Error",
            ),
        ]
        agreement = server._calculate_agreement(responses)
        assert agreement == 1.0  # Only one successful, so full agreement


class TestResponseSynthesis:
    """Tests for response synthesis"""

    def test_synthesis_with_no_responses(self):
        """Should handle no successful responses"""
        server = AICouncilServer()
        synthesis = server._synthesize_responses("test", [])
        assert "No models" in synthesis

    def test_synthesis_includes_model_count(self):
        """Synthesis should mention number of models"""
        server = AICouncilServer()
        responses = [
            ModelResponse(
                provider=ModelProvider.GEMINI,
                model_name="gemini",
                content="Test response content",
                latency_ms=100,
                success=True,
            ),
        ]
        synthesis = server._synthesize_responses("test", responses)
        assert "1 model" in synthesis
        assert "Test response content" in synthesis


class TestModelResponse:
    """Tests for ModelResponse dataclass"""

    def test_response_with_error(self):
        """Should capture error information"""
        response = ModelResponse(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            content="",
            latency_ms=50,
            success=False,
            error="Rate limited",
        )
        assert response.success is False
        assert response.error == "Rate limited"

    def test_response_timestamp(self):
        """Should have timestamp"""
        response = ModelResponse(
            provider=ModelProvider.GEMINI,
            model_name="gemini",
            content="test",
            latency_ms=100,
            success=True,
        )
        assert response.timestamp is not None


class TestConsensusResponse:
    """Tests for ConsensusResponse dataclass"""

    def test_consensus_response_creation(self):
        """Should create ConsensusResponse with all fields"""
        responses = [
            ModelResponse(
                provider=ModelProvider.GEMINI,
                model_name="gemini",
                content="test",
                latency_ms=100,
                success=True,
            ),
        ]
        consensus = ConsensusResponse(
            synthesis="Synthesized answer",
            individual_responses=responses,
            agreement_score=0.95,
            total_latency_ms=150,
            successful_models=1,
            failed_models=0,
        )
        assert consensus.agreement_score == 0.95
        assert len(consensus.individual_responses) == 1


class TestParallelQuery:
    """Tests for parallel query execution"""

    @pytest.mark.asyncio
    async def test_query_returns_empty_when_no_models(self):
        """Should return empty list when no models enabled"""
        with patch.dict(os.environ, {}, clear=True):
            server = AICouncilServer()
            responses = await server.query_parallel("test prompt")
            assert responses == []

    @pytest.mark.asyncio
    async def test_query_handles_unsupported_provider(self):
        """Should handle unsupported provider gracefully"""
        # Create a mock provider
        server = AICouncilServer(models=[])

        class FakeProvider:
            value = "fake"

        config = ModelConfig(
            provider=FakeProvider,
            model_name="fake-model",
            api_key_env="FAKE_KEY",
        )

        response = await server._query_model("test", config)
        assert response.success is False
        assert "Unsupported" in response.error
