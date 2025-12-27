---
description: TDD 门禁 — 先写测试后实现 (Gemini Flash)
argument-hint: [任务或范围]
---

Follow the project rules and governance:

- Read and follow: .council/AGENTS.md and .council/CLAUDE.md
- Primary inputs (use if present): SPEC.md, AUDIT.md, CODEMAP.md, .council/BRIEF.md

Task / scope: $ARGUMENTS

Output requirements:

1) Test plan (bullet list mapped to acceptance criteria / contracts)
2) Create or update real test files (NOT tests.json). Prefer contract-style tests for API/error behavior.
3) Run tests to confirm RED where appropriate (or at least confirm the new test fails before the fix).
4) Print exactly:
   - files changed
   - commands executed
   - the failing test summary (short)

Rules:

- Do NOT implement production logic yet.
- If SPEC/AUDIT is missing or unclear, ask for the minimum missing info and propose assumptions explicitly.
