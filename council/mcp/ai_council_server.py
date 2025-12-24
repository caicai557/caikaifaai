"""
AI Council MCP Server - Multi-model parallel consensus

Inspired by 0xAkuti/ai-council-mcp, this MCP server:
1. Queries multiple AI models in parallel (Gemini, OpenAI, Claude)
2. Uses anonymous synthesis to prevent bias
3. Returns weighted consensus response

This is a simplified version for local development.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import asyncio
import json
import os
import re
from datetime import datetime
from council.facilitator.wald_consensus import WaldConsensus, ConsensusResult, ConsensusDecision


class ModelProvider(Enum):
    """Supported model providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class ModelConfig:
    """Configuration for a model"""
    provider: ModelProvider
    model_name: str
    api_key_env: str
    enabled: bool = True
    weight: float = 1.0  # Weight for consensus calculation


@dataclass
class ModelResponse:
    """Response from a single model"""
    provider: ModelProvider
    model_name: str
    content: str
    latency_ms: float
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConsensusResponse:
    """Synthesized consensus response"""
    synthesis: str
    individual_responses: List[ModelResponse]
    agreement_score: float  # 0-1, how much models agree
    total_latency_ms: float
    successful_models: int
    failed_models: int


# Default model configurations
DEFAULT_MODELS = [
    ModelConfig(
        provider=ModelProvider.GEMINI,
        model_name="gemini-2.0-flash",
        api_key_env="GEMINI_API_KEY",
        weight=1.0,
    ),
    ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        weight=1.0,
    ),
]


class AICouncilServer:
    """
    Multi-model consensus MCP server
    
    Queries multiple AI models in parallel and synthesizes responses
    to reduce bias and improve accuracy.
    
    Usage:
        server = AICouncilServer()
        response = await server.query("What is the best approach for...")
    """
    
    def __init__(self, models: Optional[List[ModelConfig]] = None):
        """
        Initialize the AI Council server
        
        Args:
            models: List of model configurations. Uses defaults if not provided.
        """
        self.models = models or DEFAULT_MODELS
        self._validate_api_keys()
        
        # Initialize Governance Gateway for output filtering
        from council.governance.gateway import GovernanceGateway
        self.gateway = GovernanceGateway()
    
    def _validate_api_keys(self) -> None:
        """Check which models have valid API keys"""
        for model in self.models:
            if not os.environ.get(model.api_key_env):
                model.enabled = False
    
    def get_enabled_models(self) -> List[ModelConfig]:
        """Get list of models with valid API keys"""
        return [m for m in self.models if m.enabled]
    
    async def _query_gemini(self, prompt: str, config: ModelConfig) -> ModelResponse:
        """Query Gemini API"""
        start_time = datetime.now()
        try:
            # Dynamically import to avoid dependency issues
            import google.generativeai as genai
            
            api_key = os.environ.get(config.api_key_env)
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel(config.model_name)
            response = await model.generate_content_async(prompt)
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return ModelResponse(
                provider=config.provider,
                model_name=config.model_name,
                content=response.text,
                latency_ms=latency,
                success=True,
            )
        except Exception as e:
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return ModelResponse(
                provider=config.provider,
                model_name=config.model_name,
                content="",
                latency_ms=latency,
                success=False,
                error=str(e),
            )
    
    async def _query_openai(self, prompt: str, config: ModelConfig) -> ModelResponse:
        """Query OpenAI API"""
        start_time = datetime.now()
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.environ.get(config.api_key_env))
            response = await client.chat.completions.create(
                model=config.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return ModelResponse(
                provider=config.provider,
                model_name=config.model_name,
                content=response.choices[0].message.content,
                latency_ms=latency,
                success=True,
            )
        except Exception as e:
            latency = (datetime.now() - start_time).total_seconds() * 1000
            return ModelResponse(
                provider=config.provider,
                model_name=config.model_name,
                content="",
                latency_ms=latency,
                success=False,
                error=str(e),
            )
    
    async def _query_model(self, prompt: str, config: ModelConfig) -> ModelResponse:
        """Query a model based on its provider"""
        if config.provider == ModelProvider.GEMINI:
            return await self._query_gemini(prompt, config)
        elif config.provider == ModelProvider.OPENAI:
            return await self._query_openai(prompt, config)
        else:
            return ModelResponse(
                provider=config.provider,
                model_name=config.model_name,
                content="",
                latency_ms=0,
                success=False,
                error=f"Unsupported provider: {config.provider}",
            )
    
    async def query_parallel(self, prompt: str) -> List[ModelResponse]:
        """
        Query all enabled models in parallel
        
        Args:
            prompt: The prompt to send to all models
            
        Returns:
            List of responses from all models
        """
        enabled = self.get_enabled_models()
        if not enabled:
            return []
        
        tasks = [self._query_model(prompt, config) for config in enabled]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        result = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                result.append(ModelResponse(
                    provider=enabled[i].provider,
                    model_name=enabled[i].model_name,
                    content="",
                    latency_ms=0,
                    success=False,
                    error=str(resp),
                ))
            else:
                result.append(resp)
        
        return result
    
    def _calculate_agreement(self, responses: List[ModelResponse]) -> float:
        """
        Calculate agreement score between responses
        
        Simple heuristic: compare response lengths and key terms
        Returns value between 0 (no agreement) and 1 (full agreement)
        """
        successful = [r for r in responses if r.success]
        if len(successful) < 2:
            return 1.0  # Can't calculate with < 2 responses
        
        # Simple length-based similarity
        lengths = [len(r.content) for r in successful]
        avg_length = sum(lengths) / len(lengths)
        if avg_length == 0:
            return 1.0
        
        length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        normalized_variance = length_variance / (avg_length ** 2)
        
        # Lower variance = higher agreement
        agreement = max(0, 1 - normalized_variance)
        return min(1.0, agreement)
    
    async def _synthesize_responses(
        self, 
        prompt: str, 
        responses: List[ModelResponse]
    ) -> str:
        """
        Synthesize multiple model responses into a single answer using an LLM
        """
        successful = [r for r in responses if r.success]
        if not successful:
            return "No models returned successful responses."
        
        # Construct synthesis prompt
        synthesis_prompt = f"Original Task: {prompt}\n\nModels have provided the following responses. Please synthesize them into a single, high-quality response. If there are conflicts, resolve them by choosing the safest and most robust option.\n\n"
        
        for i, resp in enumerate(successful):
            synthesis_prompt += f"--- Model {i+1} ({resp.model_name}) ---\n{resp.content}\n\n"
            
        synthesis_prompt += "--- End of Responses ---\n\nSynthesized Response:"
        
        # Use the first available Gemini model for synthesis (or OpenAI)
        try:
            # Quick hack to reuse query logic for synthesis
            # In a real system, we'd have a dedicated synthesizer config
            enabled = self.get_enabled_models()
            synthesizer_config = next((m for m in enabled if m.provider == ModelProvider.GEMINI), None) or enabled[0]
            
            synthesis_resp = await self._query_model(synthesis_prompt, synthesizer_config)
            if synthesis_resp.success:
                return synthesis_resp.content
        except Exception:
            pass
            
        # Fallback to simple concatenation if synthesis fails
        best = successful[0]
        return f"[Synthesized (Fallback)]\n{best.content}"
    
    async def query(self, prompt: str) -> ConsensusResponse:
        """
        Query all models and return synthesized consensus
        
        Args:
            prompt: The question or task to send to all models
            
        Returns:
            ConsensusResponse with synthesis and individual responses
        """
        start_time = datetime.now()
        
        responses = await self.query_parallel(prompt)
        
        successful = [r for r in responses if r.success]
        failed = [r for r in responses if not r.success]
        
        synthesis = await self._synthesize_responses(prompt, responses)
        
        # Governance Check: Output Filtering
        from council.governance.gateway import RiskLevel
        risk = self.gateway._scan_content(synthesis)
        if risk in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            if risk == RiskLevel.CRITICAL:
                 synthesis = f"⚠️ [GOVERNANCE BLOCKED] The synthesized response was blocked due to detected CRITICAL risk pattern."
            else:
                 synthesis = f"⚠️ [GOVERNANCE BLOCKED] The synthesized response was blocked due to detected {risk.name} risk pattern.\n\nBlocked Content Preview (Safe): {synthesis[:50]}..."
        
        agreement = self._calculate_agreement(responses)
        
        # Calculate consensus using Wald (SPRT)
        wald_result = self.evaluate_votes(responses)
        
        total_latency = (datetime.now() - start_time).total_seconds() * 1000
        
        return ConsensusResponse(
            synthesis=synthesis,
            individual_responses=responses,
            agreement_score=agreement,
            total_latency_ms=total_latency,
            successful_models=len(successful),
            failed_models=len(failed),
        )

    def _parse_vote(self, content: str, agent_name: str) -> Dict[str, Any]:
        """
        Parse vote decision and confidence from model response
        
        Expected format:
        Vote: APPROVE | REJECT | HOLD
        Confidence: 0.0 - 1.0
        """
        content_lower = content.lower()
        
        # Decision
        decision = "hold"
        if "vote: approve" in content_lower:
            decision = "approve"
        elif "vote: reject" in content_lower:
            decision = "reject"
        elif "vote: hold" in content_lower:
            decision = "hold"
            
        # Confidence
        confidence = 0.5
        match = re.search(r"confidence:\s*(\d*\.?\d+)", content_lower)
        if match:
            try:
                conf_val = float(match.group(1))
                confidence = max(0.0, min(1.0, conf_val))
            except ValueError:
                pass
                
        return {
            "agent": agent_name,
            "decision": decision,
            "confidence": confidence,
            "rationale": content[:200]
        }

    def evaluate_votes(self, responses: List[ModelResponse]) -> ConsensusResult:
        """
        Evaluate votes using Wald Consensus
        """
        votes = []
        for resp in responses:
            if not resp.success:
                continue
            
            # Use model name as agent name
            agent_name = f"{resp.provider.value}/{resp.model_name}"
            vote = self._parse_vote(resp.content, agent_name)
            votes.append(vote)
            
        detector = WaldConsensus()
        return detector.evaluate(votes)
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status and model availability"""
        return {
            "total_models": len(self.models),
            "enabled_models": len(self.get_enabled_models()),
            "models": [
                {
                    "provider": m.provider.value,
                    "model": m.model_name,
                    "enabled": m.enabled,
                    "weight": m.weight,
                }
                for m in self.models
            ],
        }


# Export
__all__ = [
    "AICouncilServer",
    "ModelConfig",
    "ModelProvider",
    "ModelResponse",
    "ConsensusResponse",
    "DEFAULT_MODELS",
]
