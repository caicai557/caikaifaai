# MCP Context Optimization: Best Practices

> **Core Philosophy**: "Progressive Disclosure" - prevent context pollution by loading tools only when needed.

## 1. The "Default Loadout" (Zero-Cost Baseline)

Your environment should default to the **minimal viable toolset** to prevent cognitive drift and token waste.

**Default Loadout (.mcp.json)**:
- ✅ **Filesystem**: Essential for reading/writing code.
- ✅ **Codex/Memory**: Essential for project history.
- ❌ **GitHub**: **DISABLED** by default (eats massive context).
- ❌ **Web Browser**: **DISABLED** by default (unless needed).

## 2. The "Just-in-Time" Workflow (JIT)

Enable heavy tools only for the specific task duration, then immediately disable them.

### Workflow: Handling a PR

1.  **Activator**:
    - Open Claude Code settings (`/mcp`).
    - Enable **GitHub**.
    - Run `/doctor` to verify connection.

2.  **Execution**:
    - Task: "Review PR #123"
    - Task: "Create issue for bug X"

3.  **Deactivator** (Crucial Step):
    - **Immediately** disable **GitHub** in settings.
    - Run `/doctor` to clear context cache.

> **Why?** Keeping GitHub open injects thousands of tokens of schema definitions into *every single prompt*, degrading reasoning quality for non-GitHub tasks.

## 3. Configuration Layering

We follow the standard scoping precedence:

| Scope | File | Purpose | Content |
|-------|------|---------|---------|
| **Project** | `.mcp.json` | Team-shared, immutable infrastructure | Filesystem, Build tools |
| **User** | `~/.claude.json` | Personal, experimental, heavy tools | GitHub (token required), Postgres |

### Action Item
Copy the heavy tool configs from `config/mcp_user_config.template.json` to your local `~/.claude.json` only if you frequently need them, but keep them `disabled` by default.
