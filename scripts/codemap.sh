#!/usr/bin/env bash
set -euo pipefail

{
  echo "# CODEMAP"
  echo
  echo "## Repo files (tracked)"
  echo
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files | sed 's/^/- /'
  else
    find . -maxdepth 3 -type f \
      -not -path "./.venv/*" -not -path "./.git/*" \
      | sed 's#^\./#- #'
  fi
  echo
  echo "## Entry candidates"
  echo
  rg -n "if __name__ == .__main__." -S src tests 2>/dev/null || true
} > CODEMAP.md

echo "Wrote CODEMAP.md"
