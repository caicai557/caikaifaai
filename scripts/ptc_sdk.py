#!/usr/bin/env python3
"""
PTC SDK - Simulated SDK for PTC V2 Sandbox Demo

This module provides mock functions that simulate external services
for use in the PTC V2 self-refining execution loop demo.

In production, these would be replaced with real API calls.
"""

from typing import List, Dict, Any
import json
import os
from datetime import datetime


def fetch_market_data(symbol: str) -> List[Dict[str, Any]]:
    """
    Fetch market data for a given symbol.

    Args:
        symbol: The trading symbol (e.g., "BTC", "ETH")

    Returns:
        List of market data dictionaries with 'symbol', 'price', 'timestamp'
    """
    # Simulated market data
    mock_data = {
        "BTC": [
            {"symbol": "BTC", "price": 450.2, "timestamp": "2025-12-27T00:00:00Z"},
            {"symbol": "BTC", "price": 452.1, "timestamp": "2025-12-27T01:00:00Z"},
            {"symbol": "BTC", "price": 448.5, "timestamp": "2025-12-27T02:00:00Z"},
        ],
        "ETH": [
            {"symbol": "ETH", "price": 32.5, "timestamp": "2025-12-27T00:00:00Z"},
            {"symbol": "ETH", "price": 33.1, "timestamp": "2025-12-27T01:00:00Z"},
            {"symbol": "ETH", "price": 31.8, "timestamp": "2025-12-27T02:00:00Z"},
        ],
    }

    return mock_data.get(
        symbol.upper(),
        [
            {"symbol": symbol, "price": 100.0, "timestamp": datetime.now().isoformat()},
        ],
    )


def save_result(filename: str, content: str) -> bool:
    """
    Save result to a file in the sandbox output directory.

    Args:
        filename: Name of the output file
        content: Content to write

    Returns:
        True if successful, False otherwise
    """
    output_dir = os.environ.get("PTC_OUTPUT_DIR", "/sandbox/output")
    os.makedirs(output_dir, exist_ok=True)

    try:
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[PTC SDK] Result saved to: {filepath}")
        return True
    except Exception as e:
        print(f"[PTC SDK] Error saving result: {e}")
        return False


def log_action(action: str, details: Dict[str, Any] = None) -> None:
    """
    Log an action for audit purposes.

    Args:
        action: Description of the action
        details: Additional details as a dictionary
    """
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "action": action,
        "details": details or {},
    }
    print(f"[PTC SDK LOG] {json.dumps(log_entry)}")


# Virtual SDK Documentation (injected into LLM context)
VIRTUAL_SDK_DOCS = """
LIBRARY: ptc_sdk (PTC Sandbox SDK)

FUNCTIONS:
- fetch_market_data(symbol: str) -> List[Dict]
  Returns a list of price records: [{"symbol": str, "price": float, "timestamp": str}, ...]

- save_result(filename: str, content: str) -> bool
  Saves content to a file. Returns True on success.

- log_action(action: str, details: Dict = None) -> None
  Logs an action for audit purposes.

USAGE EXAMPLE:
```python
import ptc_sdk

data = ptc_sdk.fetch_market_data("BTC")
avg = sum(d["price"] for d in data) / len(data)
ptc_sdk.save_result("result.txt", f"Average: {avg}")
```
"""

__all__ = ["fetch_market_data", "save_result", "log_action", "VIRTUAL_SDK_DOCS"]
