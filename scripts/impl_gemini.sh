#!/usr/bin/env bash
set -euo pipefail

if ! command -v gemini >/dev/null 2>&1; then
  echo "gemini not found in PATH" >&2
  exit 1
fi

SPEC="$(cat SPEC.md 2>/dev/null || true)"
TESTS="$(cat tests/test_*.py 2>/dev/null | head -200 || true)"

gemini --prompt "
You are an implementation expert.
Implement minimal change to pass the tests.

SPEC:
${SPEC}

EXISTING TESTS:
${TESTS}

Rules:
- Output ONLY the implementation code
- Minimal change principle
- Make tests pass (green state)
- Follow existing code style

After implementation, run: just verify
"

echo "Review the output and apply changes manually"
echo "Then run: just verify"
