# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> [!IMPORTANT]
> **Strictly follow the rules in [.council/AGENTS.md](./.council/AGENTS.md)**

## Project Overview

**Name**: cesi-telegram-multi
**Type**: Python backend application (telegram-web client with translation)
**Main Purpose**: Multi-instance Telegram Web A runner with bidirectional translation support
**Language**: Python 3.12+
**Architecture**: Async/await with message interception and translation pipeline

## Common Commands

### Development Commands

```bash
# Install dependencies
pip install -e ".[telegram]"        # Telegram features
pip install -e ".[dev]"              # Development tools (pytest, ruff)

# Testing
just test                            # Run pytest on tests/ directory
pytest tests/test_<module>.py        # Run single test file

# Code quality
just lint                            # Check code with ruff
just compile                         # Check syntax with py_compile

# Verification
just verify                          # Run compile + lint + test (gate keeper)
just ship                            # verify + codex review + show git log
```

### Development Workflow

```bash
just dev "<task description>"        # Full workflow: codemap → plan → audit/tdd/impl → verify
just tdd                             # TDD mode (write tests first)
just impl                            # Implementation mode (minimal patch + verify)
```

## Architecture & Code Organization

### Core Modules

```
src/
├── telegram_multi/           # Main Telegram multi-instance runner
│   ├── message_interceptor.py   # Message interception & translation injection
│   ├── translator.py            # Translation factory with provider pattern
│   ├── instance_manager.py      # Multi-instance lifecycle management
│   ├── browser_context.py       # Browser context setup (Playwright)
│   ├── config.py                # Configuration models (Pydantic)
│   └── translators/             # Translation provider implementations
│       └── google.py            # Google Translate provider
├── seabox/                   # API server module (FastAPI-based)
├── config.py                 # Global feature flags
└── calculator.py             # Utility module
```

### Key Classes & Patterns

**MessageInterceptor** (`message_interceptor.py`):
- Injects JavaScript to intercept Telegram messages
- Translates messages bidirectionally based on config
- Supports callbacks for message interception events
- Uses `get_injection_script()` to return browser-side code

**Translator** (`translator.py`):
- Factory pattern for creating translator instances
- Plugin system: `register_provider(name, provider_class)`
- Built-in Google Translate provider, extensible for DeepL/Argos
- Caches translations to avoid duplicate API calls

**InstanceManager** (`instance_manager.py`):
- Manages lifecycle of multiple Telegram Web A instances
- Coordinates browser context creation and cleanup
- Handles async startup/shutdown of instances

**TelegramConfig** (`config.py`):
- Pydantic models for instance, translation, and browser configuration
- Centralized configuration loading

### Entry Points

- `run_telegram.py`: CLI for launching multi-instance Telegram with translation
- `run_dashboard.py`: Dashboard server for monitoring instances
- Tests: `tests/test_*.py` files for each module

## Testing Strategy

- **Framework**: Pytest with coverage tracking
- **Test Structure**: One test file per source module (e.g., `test_message_interceptor.py`)
- **Mocking**: Use `unittest.mock` for translator and browser context mocks
- **Run**: `just test` or `pytest tests/` for all tests

Example: Running a single test
```bash
pytest tests/test_translator.py -v
pytest tests/test_translator.py::TestTranslator::test_translate -v
```

## Development Standards

- **Type Hints**: Required for all function signatures
- **Async/Await**: Used for Playwright browser operations and Translator batching
- **Config**: Use Pydantic models for configuration
- **Providers**: Use factory pattern for pluggable translators

## Batch Operations Protocol

For changes affecting 3+ files, write a Python script instead of manual edits:

```python
# Example: scripts/bulk_rename.py
import os, re, glob
for filepath in glob.glob("src/**/*.py", recursive=True):
    with open(filepath) as f:
        content = f.read()
    content = re.sub(r"old_name", "new_name", content)
    with open(filepath, "w") as f:
        f.write(content)
```

## Verification Gate (just verify)

This is the single arbiter of quality:
1. `compile`: Check Python syntax
2. `lint`: Check code style with ruff
3. `test`: Run pytest suite

All three must pass before shipping.

## Safety Boundaries

- ❌ **Forbidden**: `rm -rf`, `git push`, modifying `.env`, destructive file operations
- ✅ **Free**: `read`, `ls`, `grep`, `lint`, `pytest`, `python -m py_compile`
- ⚠️ **Confirm**: Git commits/pushes, file deletions, batch edits

## Related Documentation

- [.council/AGENTS.md](./.council/AGENTS.md): Agent governance and routing rules
- [CODEMAP.md](./CODEMAP.md): High-level project architecture
- [NOTES.md](./NOTES.md): Session notes and decisions
- [pyproject.toml](./pyproject.toml): Project metadata and dependencies
