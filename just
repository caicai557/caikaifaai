#!/usr/bin/env bash
# Wrapper to invoke a working `just` binary.
# Priority: system just (if installed) -> .venv/bin/just -> error.

set -e

this="$0"
sys_just="$(command -v just 2>/dev/null || true)"

if [ -n "$sys_just" ] && [ "$sys_just" != "$this" ]; then
  exec "$sys_just" "$@"
elif [ -x ".venv/bin/just" ]; then
  exec ".venv/bin/just" "$@"
fi

echo "just not found. Install with 'sudo apt-get install just' or ensure .venv/bin/just exists." >&2
exit 1
