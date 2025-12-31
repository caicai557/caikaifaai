"""
LLM Client - Unified Interface for Cognitive Capabilities

Wraps LiteLLM to provide:
1. Multi-provider support (Gemini, OpenAI, Anthropic)
2. Structured output enforcement (via JSON mode or tool calling)
3. Cost tracking and budget management
4. Observability hooks
"""

import json
import logging
from typing import Optional, Dict, Type, TypeVar, List

from pydantic import BaseModel
from litellm import completion

# Observability setup

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """
    Unified LLM Client for the Council Framework.

    Attributes:
        default_model (str): The default model to use.
        budget_limit (float): Optional daily budget limit in USD.
    """

    def __init__(self, default_model: str = "claude-4.5-sonnet", debug: bool = False):
        self.default_model = default_model
        self.debug = debug

        # Configure LiteLLM
        if self.debug:
            import litellm

            litellm.set_verbose = True

        # Register token tracker callback
        # success_callback.append(tracker.track_usage)

    def completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Standard chat completion.

        Args:
            messages: List of message dicts (role, content).
            model: Override default model.
            temperature: Creativity control.
            max_tokens: Limit output length.
            json_mode: Force JSON output (if supported by provider).

        Returns:
            str: The model's response content.
        """
        target_model = model or self.default_model

        try:
            response = completion(
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"} if json_mode else None,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"LLM Completion failed: {e}")
            # In a real system, we might implement fallback logic here
            raise

    def structured_completion(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        """
        Generate a response that adheres to a specific Pydantic model.

        Uses LiteLLM's `response_format` or instructor-like patching logic
        (depending on provider capabilities).

        Args:
            messages: input messages.
            response_model: Pydantic model class.

        Returns:
            Instance of response_model.
        """
        target_model = model or self.default_model

        try:
            # Using LiteLLM's `response_format` with Pydantic schema
            # Note: Provider support varies. For Gemini/OpenAI, this works well.
            json_schema = response_model.model_json_schema()

            # 1. Append instructions if model doesn't support native structure
            # (Simplification for robustness)
            system_msg = next((m for m in messages if m["role"] == "system"), None)
            instruction = f"\n\nOutput MUST be valid JSON adhering to this schema:\n{json.dumps(json_schema, indent=2)}"

            if system_msg:
                system_msg["content"] += instruction
            else:
                messages.insert(0, {"role": "system", "content": instruction})

            content = self.completion(
                messages=messages,
                model=target_model,
                temperature=temperature,
                json_mode=True,
            )

            # 2. Parse and validate
            return response_model.model_validate_json(content)

        except Exception as e:
            logger.error(f"Structured completion failed: {e}")
            raise

    def simple_query(self, prompt: str) -> str:
        """Helper for single-turn queries."""
        return self.completion(messages=[{"role": "user", "content": prompt}])


# Singleton instance
default_client = LLMClient()


class CachedLLMClient(LLMClient):
    """
    LLM Client with Automatic Context Caching (Gemini)

    Note: Gemini caching requires Google Cloud credentials.
    If not configured, falls back to standard completion.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_mgr = None
        self._gemini_available = self._check_gemini_credentials()

        if self._gemini_available:
            from council.context.gemini_cache import GeminiCacheManager
            self.cache_mgr = GeminiCacheManager()

    def _check_gemini_credentials(self) -> bool:
        """Check if Gemini/Google Cloud credentials are available"""
        import os

        # Check for API key
        if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"):
            return True

        # Check for Application Default Credentials
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            return True

        # Try to detect ADC
        try:
            from google.auth import default
            default()
            return True
        except Exception:
            return False

    def completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Completion with auto-caching support
        """
        target_model = model or self.default_model

        # Determine if we should attempt caching (Gemini only, requires credentials)
        if "gemini" in target_model.lower() and self._gemini_available and self.cache_mgr:
            # Extract system prompt as potential cacheable content
            system_msg = next((m for m in messages if m["role"] == "system"), None)

            if (
                system_msg and len(system_msg["content"]) > 10000
            ):  # Conservative threshold check before expensive token count
                # Try to cache
                cache_name = self.cache_mgr.create(
                    name="auto_cache_" + str(hash(system_msg["content"])),
                    content=system_msg["content"],
                    model=target_model,
                )

                if cache_name:
                    # Find user query (last message)
                    user_query = messages[-1]["content"]

                    logger.info(f"Using Gemini Cache: {cache_name}")
                    return self.cache_mgr.generate_with_cache(
                        cache_name=cache_name, query=user_query
                    )

        # Fallback to standard completion
        return super().completion(messages, model, temperature, max_tokens, json_mode)


# Replace default client if auto-caching is improved
default_client = CachedLLMClient()
