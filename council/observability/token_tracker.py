"""
Token Tracker - Observability for LLM Token Usage
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def track_usage(
    kwargs: Dict[str, Any], response_obj: Any, start_time: Any, end_time: Any
):
    """
    LiteLLM success callback to track token usage.
    """
    try:
        model = kwargs.get("model", "unknown")
        usage = getattr(response_obj, "usage", None)

        if usage:
            prompt_tokens = getattr(usage, "prompt_tokens", 0)
            completion_tokens = getattr(usage, "completion_tokens", 0)
            total_tokens = getattr(usage, "total_tokens", 0)
            cost = getattr(response_obj, "_hidden_params", {}).get("response_cost", 0.0)

            logger.info(
                f"LLM Usage [{model}]: {total_tokens} tokens "
                f"({prompt_tokens} in, {completion_tokens} out). "
                f"Est. Cost: ${cost:.6f}"
            )

            # Here we could record to a database, Prometheus, etc.
    except Exception as e:
        logger.warning(f"Failed to track token usage: {e}")
