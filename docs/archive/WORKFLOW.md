# Windows AI Dev Workflow (Claude + Codex + Gemini)

## Division of labor (token-saving)
- Gemini: fast research + examples, short outputs.
- Claude: architecture + plan + guardrails + review.
- Codex: heavy implementation + refactors + local runs.

## Suggested loop
1) Claude: /intake <idea>
2) Gemini: /delegate-gemini <what to look up> -> run: tools\aiw.ps1 gemini -p "..."
3) Claude: integrate findings -> update docs/03_plan.md
4) Codex: /delegate-codex <implementation> -> run codex in repo
5) Claude: /ship-check <release> -> final review
