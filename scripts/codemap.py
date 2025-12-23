#!/usr/bin/env python3
import subprocess
from pathlib import Path


def sh(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, errors="replace")


root = Path(".").resolve()

print("# CODEMAP\n")
print("## Repo Summary\n")
try:
    branch = sh("git rev-parse --abbrev-ref HEAD").strip()
    head = sh("git rev-parse --short HEAD").strip()
    print(f"- Branch: {branch}")
    print(f"- HEAD: {head}\n")
except Exception:
    print("- Not a git repo (or git not available)\n")

print("## Top-level Structure\n")
for p in sorted(
    [x for x in root.iterdir() if x.name not in [".git"]], key=lambda x: x.name.lower()
):
    if p.is_dir():
        print(f"- {p.name}/")
    else:
        print(f"- {p.name}")

print("\n## Largest Files (tracked)\n")
try:
    out = sh(
        "git ls-files -z | xargs -0 -I{} bash -lc 'wc -c \"{}\"' | sort -nr | head -n 25"
    )
    print("```")
    print(out.strip())
    print("```")
except Exception as e:
    print(f"(skip: {e})")

print("\n## Grep Hotspots (common entrypoints)\n")
patterns = [
    "main(",
    "createApp",
    "app.listen",
    "Router",
    "index.ts",
    "index.js",
    "Electron",
    "BrowserWindow",
    "BrowserView",
    "express(",
    "fastify",
]
print("```")
for pat in patterns:
    try:
        lines = sh(f'rg -n "{pat}" -S . | head -n 10')
        if lines.strip():
            print(f"\n# {pat}\n{lines.strip()}")
    except Exception:
        pass
print("```")

print("\n## Council Files\n")
print("- Governance: .council/AGENTS.md")
print("- Rules: .council/CLAUDE.md")
print("- Brief (SSOT): .council/BRIEF.md")
print("- Decisions: .council/DECISIONS.md")
print("- Notes: .council/NOTES.md")
