# caicai

## MCP Tooling

Project-shared MCP servers live in `.mcp.json` and must only include standard
MCP server fields (`type`, `command`, `args`, `env`).

- Betas should be enabled via CLI flags (e.g., `claude --betas <name>`) or a
  shell alias/wrapper, not in `.mcp.json`.
- Version metadata lives in `docs/mcp.meta.json`.
- Optional or personal servers should use `--scope user` or local scope instead
  of being added to `.mcp.json`.
