# Agent Council Governance (SSOT)

## Hard Safety Boundaries (Non-negotiable)
- DO NOT read, print, or exfiltrate secrets: .env, *.pem, *key*, credentials files.
- DO NOT run destructive commands (rm -rf, format disk, chmod -R on system paths).
- Any dependency installation must be explicit and minimal.
- All changes must be reviewable (diff-first), reversible (git), and test-verified.

## Definition of Done (DoD)
- Tests added/updated.
- Lint/typecheck pass (if applicable).
- Clear rollback plan (git commit history is clean).
- Updates documented in .council/NOTES.md and .council/DECISIONS.md (when architectural).

## Roles (Default)
- Codex: Orchestrator (PRD → task tree → acceptance criteria).
- Gemini: Auditor (cross-file conflicts, edge cases, design review).
- Claude Code: Executor (apply patches, write tests, run commands, iterate).
