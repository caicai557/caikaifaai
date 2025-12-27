---
description: 最小实现 — 通过测试的最小补丁 (Gemini Flash)
argument-hint: [任务或范围]
---

Follow the project rules and governance:

- Read and follow: .council/AGENTS.md and .council/CLAUDE.md
- Primary inputs (use if present): SPEC.md, AUDIT.md, CODEMAP.md, .council/BRIEF.md
- Assume tests already exist (run /tdd first if not).

Task / scope: $ARGUMENTS

Execution sequence:

1) Diff-first plan (very short): which files, what minimal change, what risk.
2) Implement the minimal code changes to satisfy tests and contract expectations.
3) Run `just verify` (this is the only final gate).
4) Update .council/NOTES.md with:
   - what changed
   - verification evidence (just verify pass)
   - remaining risks / follow-ups (or "none")

Output requirements:

- Paste the `just verify` summary result (short).
- List files changed.
- If contract/API behavior changed, add an entry to .council/DECISIONS.md.
