# Project Engineering Rules (Enforced)

Strictly follow the rules in: ./.council/AGENTS.md

## Engineering Standards
- Prefer small PRs (<= 400 LOC net change) unless approved by a written decision.
- "Diff-first": propose plan, then patch, then verify.
- TDD preference: tests before logic for non-trivial changes.
- Deterministic commands: every workflow must be runnable from Justfile.

## Output Contracts
- Every task produces:
  1) Spec/Plan (what & why)
  2) Patch (code)
  3) Verification (tests/logs)
  4) Notes update (what changed)
