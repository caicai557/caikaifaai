#!/usr/bin/env python3
"""
Tokenizer - PII De-identification and Data Masking.

2025 Best Practices:
- Regex-based PII detection for known patterns
- Deterministic tokenization for referential integrity
- Reversible mapping with secure token vault
- Support for structured and unstructured text

Usage:
  python scripts/tokenizer.py --tokenize "Contact me at john@example.com or 555-123-4567"
  python scripts/tokenizer.py --detokenize "[EMAIL_0] or [PHONE_0]" --vault token_vault.json
"""

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# PII Patterns based on 2025 best practices
PII_PATTERNS = {
    "email": {
        "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "template": "[EMAIL_{}]",
        "description": "Email addresses",
    },
    "phone_us": {
        "pattern": r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b",
        "template": "[PHONE_{}]",
        "description": "US phone numbers",
    },
    "ssn": {
        "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
        "template": "[SSN_{}]",
        "description": "Social Security Numbers",
    },
    "credit_card": {
        "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "template": "[CC_{}]",
        "description": "Credit card numbers",
    },
    "ip_address": {
        "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "template": "[IP_{}]",
        "description": "IPv4 addresses",
    },
    "api_key": {
        "pattern": r"\b(?:sk-|pk-|api[_-]?key[_-]?)[A-Za-z0-9]{20,}\b",
        "template": "[API_KEY_{}]",
        "description": "API keys and secrets",
    },
}


@dataclass
class TokenVault:
    """Secure storage for token-to-original mappings."""

    mappings: Dict[str, str] = field(default_factory=dict)
    reverse_mappings: Dict[str, str] = field(default_factory=dict)

    def add(self, token: str, original: str) -> None:
        """Add a token mapping."""
        self.mappings[token] = original
        self.reverse_mappings[original] = token

    def get_original(self, token: str) -> Optional[str]:
        """Get original value from token."""
        return self.mappings.get(token)

    def get_token(self, original: str) -> Optional[str]:
        """Get token from original value (for deterministic tokenization)."""
        return self.reverse_mappings.get(original)

    def save(self, path: str) -> None:
        """Save vault to file (should be encrypted in production)."""
        with open(path, "w") as f:
            json.dump(self.mappings, f, indent=2)

    def load(self, path: str) -> None:
        """Load vault from file."""
        if os.path.exists(path):
            with open(path) as f:
                self.mappings = json.load(f)
                self.reverse_mappings = {v: k for k, v in self.mappings.items()}


def generate_deterministic_token(
    original: str,
    category: str,
    template: str,
    salt: str = "",
) -> str:
    """
    Generate a deterministic token for consistent tokenization.

    This ensures the same input always produces the same token,
    which is crucial for maintaining referential integrity.
    """
    # Create a hash-based index
    hash_input = f"{salt}:{category}:{original}"
    hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
    return template.format(hash_value.upper())


def tokenize_pii(
    text: str,
    vault: Optional[TokenVault] = None,
    deterministic: bool = True,
    salt: str = "",
    patterns: Optional[Dict] = None,
) -> Tuple[str, TokenVault]:
    """
    Replace PII with tokens and return the tokenized text with mapping.

    Args:
        text: Input text containing potential PII
        vault: Existing token vault (for consistent tokenization)
        deterministic: If True, same input produces same token
        salt: Salt for deterministic hashing
        patterns: Custom PII patterns (uses default if None)

    Returns:
        Tuple of (tokenized_text, token_vault)
    """
    if vault is None:
        vault = TokenVault()

    if patterns is None:
        patterns = PII_PATTERNS

    counter = 0
    result = text

    for category, config in patterns.items():
        pattern = config["pattern"]
        template = config["template"]

        for match in re.finditer(pattern, result):
            original = match.group()

            # Check if already tokenized
            existing_token = vault.get_token(original)
            if existing_token:
                token = existing_token
            elif deterministic:
                token = generate_deterministic_token(original, category, template, salt)
            else:
                token = template.format(counter)
                counter += 1

            # Add to vault
            vault.add(token, original)

            # Replace in text
            result = result.replace(original, token, 1)

    return result, vault


def detokenize_pii(text: str, vault: TokenVault) -> str:
    """
    Restore original values from tokens.

    Args:
        text: Tokenized text
        vault: Token vault with mappings

    Returns:
        Original text with PII restored
    """
    result = text
    for token, original in vault.mappings.items():
        result = result.replace(token, original)
    return result


def detect_pii(
    text: str,
    patterns: Optional[Dict] = None,
) -> List[Dict]:
    """
    Detect PII in text without tokenizing.

    Returns list of detected PII with category and position.
    """
    if patterns is None:
        patterns = PII_PATTERNS

    detections = []
    for category, config in patterns.items():
        for match in re.finditer(config["pattern"], text):
            detections.append(
                {
                    "category": category,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "description": config["description"],
                }
            )

    return detections


def main():
    parser = argparse.ArgumentParser(description="Tokenizer - PII De-identification")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--tokenize",
        metavar="TEXT",
        help="Tokenize PII in the given text",
    )
    group.add_argument(
        "--detokenize",
        metavar="TEXT",
        help="Restore PII from tokens",
    )
    group.add_argument(
        "--detect",
        metavar="TEXT",
        help="Detect PII without tokenizing",
    )

    parser.add_argument(
        "--vault",
        default=".council/token_vault.json",
        help="Path to token vault file",
    )
    parser.add_argument(
        "--salt",
        default="",
        help="Salt for deterministic tokenization",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if args.tokenize:
        vault = TokenVault()
        if os.path.exists(args.vault):
            vault.load(args.vault)

        result, vault = tokenize_pii(args.tokenize, vault, salt=args.salt)

        # Save vault
        os.makedirs(os.path.dirname(args.vault), exist_ok=True)
        vault.save(args.vault)

        if args.json:
            output = {
                "tokenized": result,
                "vault_path": args.vault,
                "mappings_count": len(vault.mappings),
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"🔒 Tokenized: {result}")
            print(f"📁 Vault saved: {args.vault}")

    elif args.detokenize:
        vault = TokenVault()
        vault.load(args.vault)

        result = detokenize_pii(args.detokenize, vault)

        if args.json:
            print(json.dumps({"original": result}))
        else:
            print(f"🔓 Restored: {result}")

    elif args.detect:
        detections = detect_pii(args.detect)

        if args.json:
            print(json.dumps({"detections": detections}, indent=2))
        else:
            if detections:
                print(f"🔍 Found {len(detections)} PII:")
                for d in detections:
                    print(f"   [{d['category']}] {d['value']} ({d['description']})")
            else:
                print("✅ No PII detected")


if __name__ == "__main__":
    main()
