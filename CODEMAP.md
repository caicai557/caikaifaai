# CODEMAP

## Repo Summary

- Branch: main
- HEAD: acfba72

## Top-level Structure

- .council/
- CODEMAP.md
- Justfile
- scripts/
- src/
- tests/

## Largest Files (tracked)

```
7257 scripts/council_bootstrap.sh
1640 scripts/codemap.py
1361 .council/BRIEF.md
1047 src/config.py
1031 Justfile
870 tests/test_calculator.py
856 .council/AGENTS.md
543 .council/CLAUDE.md
489 src/calculator.py
381 .council/CHECKLIST.md
346 .council/prompts/audit_gemini.md
294 .council/prompts/plan_codex.md
275 .council/prompts/implement_claude.md
253 .council/prompts/tdd_claude.md
129 .council/NOTES.md
117 .council/DECISIONS.md
72 src/__init__.py
32 tests/__init__.py
0 CODEMAP.md
```

## Grep Hotspots (common entrypoints)

```

# createApp
./scripts/codemap.py:38:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",
./scripts/council_bootstrap.sh:226:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",

# app.listen
./scripts/council_bootstrap.sh:226:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",
./scripts/codemap.py:38:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",

# Router
./scripts/council_bootstrap.sh:226:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",
./scripts/codemap.py:38:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",

# index.ts
./scripts/council_bootstrap.sh:226:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",
./scripts/codemap.py:38:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",

# index.js
./scripts/council_bootstrap.sh:226:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",
./scripts/codemap.py:38:    "main(", "createApp", "app.listen", "Router", "index.ts", "index.js",

# Electron
./scripts/council_bootstrap.sh:227:    "Electron", "BrowserWindow", "BrowserView", "express(", "fastify"
./scripts/codemap.py:39:    "Electron", "BrowserWindow", "BrowserView", "express(", "fastify"

# BrowserWindow
./scripts/council_bootstrap.sh:227:    "Electron", "BrowserWindow", "BrowserView", "express(", "fastify"
./scripts/codemap.py:39:    "Electron", "BrowserWindow", "BrowserView", "express(", "fastify"

# BrowserView
./scripts/council_bootstrap.sh:227:    "Electron", "BrowserWindow", "BrowserView", "express(", "fastify"
./scripts/codemap.py:39:    "Electron", "BrowserWindow", "BrowserView", "express(", "fastify"

# fastify
./scripts/council_bootstrap.sh:227:    "Electron", "BrowserWindow", "BrowserView", "express(", "fastify"
./scripts/codemap.py:39:    "Electron", "BrowserWindow", "BrowserView", "express(", "fastify"
```

## Council Files

- Governance: .council/AGENTS.md
- Rules: .council/CLAUDE.md
- Brief (SSOT): .council/BRIEF.md
- Decisions: .council/DECISIONS.md
- Notes: .council/NOTES.md
