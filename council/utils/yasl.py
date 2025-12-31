"""
YASL (YAML Agent State Language) Utilities

Provides serialization and deserialization for agent context handover using YAML.
"""

import yaml
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class YASLSerializer:
    """
    Serializer for YASL (YAML Agent State Language).

    Ensures safe loading and consistent dumping of agent context.
    """

    @staticmethod
    def dump(context: Dict[str, Any]) -> str:
        """
        Serialize context dictionary to YASL string.

        Args:
            context: Dictionary containing agent state/context

        Returns:
            YAML formatted string
        """
        try:
            # allow_unicode=True ensures Chinese characters are readable
            # sort_keys=False preserves insertion order (Python 3.7+)
            return yaml.safe_dump(
                context, allow_unicode=True, sort_keys=False, default_flow_style=False
            )
        except Exception as e:
            logger.error(f"Failed to dump YASL: {e}")
            raise ValueError(f"YASL serialization failed: {e}")

    @staticmethod
    def load(yasl_str: str) -> Dict[str, Any]:
        """
        Deserialize YASL string to context dictionary.

        Args:
            yasl_str: YAML formatted string

        Returns:
            Dictionary containing agent state/context
        """
        try:
            data = yaml.safe_load(yasl_str)
            if not isinstance(data, dict):
                # Handle empty string or scalar values gracefully
                if data is None:
                    return {}
                raise ValueError(f"YASL root must be a dictionary, got {type(data)}")
            return data
        except yaml.YAMLError as e:
            logger.error(f"Failed to load YASL: {e}")
            raise ValueError(f"YASL deserialization failed: {e}")
