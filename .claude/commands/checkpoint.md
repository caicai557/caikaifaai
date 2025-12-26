---
description: Council record — finalize task, commit changes, and update notes. (Claude)
argument-hint: [task-label]
---

Follow the project rules and governance:

- Read and follow: .council/AGENTS.md and .council/CLAUDE.md
- Primary outputs: Git commit, .council/NOTES.md update

Task / label: $ARGUMENTS

Execution sequence:

1) Run `just verify` one last time to ensure green state.
2) If verify passes:
   - Git add all relevant changes
   - Git commit with message: "feat: $ARGUMENTS" (or suitable type)
3) Update `.council/NOTES.md` with a summary of the completed task.
4) (Optional) Update `.last_checkpoint` with current commit hash.

Output requirements:

- Commit hash
- Summary of changes
- Verification status (PASS)
