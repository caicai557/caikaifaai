#!/usr/bin/env bash
set -euo pipefail

if ! command -v just >/dev/null 2>&1; then
  echo "just not found in PATH; cannot run verify gate" >&2
  exit 127
fi

status=0
if just verify; then
  result="PASS"
else
  status=$?
  result="FAIL"
  echo "== verify: FAIL ==" >&2
fi

# 自动更新 NOTES.md
mkdir -p .council
{
  echo ""
  echo "## $(date +%Y-%m-%d) Verify"
  echo "- Status: ${result}"
  echo '```'
  git diff --stat HEAD 2>/dev/null | head -10 || true
  echo '```'
} >> .council/NOTES.md

exit "$status"
