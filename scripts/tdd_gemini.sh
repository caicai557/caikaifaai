#!/usr/bin/env bash
set -euo pipefail

if ! command -v gemini >/dev/null 2>&1; then
  echo "gemini not found in PATH" >&2
  exit 1
fi

if [[ ! -f SPEC.md ]]; then
  echo "SPEC.md missing. Run: just plan \"<task>\" first." >&2
  exit 1
fi

SPEC="$(cat SPEC.md)"
CONTRACTS="$(cat .council/CONTRACTS.md 2>/dev/null || true)"

gemini --prompt "
You are a TDD expert.
Based on SPEC.md and CONTRACTS.md, write tests first.

SPEC:
${SPEC}

CONTRACTS:
${CONTRACTS}

Rules:
- Output ONLY Python test code (pytest style)
- Cover acceptance criteria and contracts
- Do NOT implement production logic
- Tests should FAIL initially (red state)

Output the test file content:
" > tests/test_new.py

echo "Wrote tests/test_new.py (review and rename)"
