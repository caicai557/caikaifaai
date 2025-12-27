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

## Token Saving Rules (MANDATORY)

> [!CAUTION]
> **违反以下规则将被视为严重错误。每次 Edit ≈ 3k tokens，批量工具 ≈ 0.5k tokens。**

### 强制规则

1. **Lint 错误必须用自动修复**:

   ```bash
   ruff check --fix .                    # 不要逐个 Edit
   ruff check --select E501 --fix .      # line-too-long
   black .                               # 格式化
   isort .                               # import 排序
   ```

2. **修改 ≥3 处相同代码必须用批量脚本**:

   ```bash
   python scripts/batch_replace.py -p "old" -r "new" -g "src/**/*.py"
   ```

3. **不确定方案时必须先本地验证**:

   ```bash
   # 创建 repro.py 验证方案，确认可行后再 Edit
   python repro.py
   ```

### 检查清单 (每次 Edit 前)

- [ ] 这是 lint 错误吗？ → **用 ruff/black**
- [ ] 需要修改 ≥3 处吗？ → **用批量脚本**
- [ ] 我确定方案能工作吗？ → **先本地验证**

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

# 理事会层级监督指令集 (2025.12.26)

## 编排协议 (Orchestration)

- 优先查阅 `Task Ledger`，所有决策需锚定在 `AGENTS.md` 定义的规则之内。
- 在大型重构前，强制调用 `gemini-think` 进行 2M 上下文全库审计。

## 执行约束 (Execution)

- 涉及 3 步以上的操作必须使用 PTC 脚本编排，禁用逐条自然语言确认。
- 代码实施前必须先在 `/tests/` 目录下建立 Red 状态的测试用例。

## 记忆管理 (Persistence)

- 会话接近上限时，自动调用 `/compact` 总结架构决策并归档至 `NOTES.md`。
- 任务结束前，必须提供一段包含逻辑差异与风险提示的最终总结。

--------------------------------------------------------------------------------
比喻理解： 这种层级化监督模式就像是顶级医疗专家组进行手术：Codex 5.2 是主刀医生（主席），手握手术方案（Task Ledger）进行全局调度；Gemini 3 Pro 是翻阅过病人几十年所有病历档案的资深顾问（Advisor）；Claude Code 则是拿着精密手术刀的执行医生。他们在 AGENTS.md 规定的无菌手术室（Docker 沙盒）内通过 MCP 统一接口 协作。而你作为董事长（人类用户），平时只需通过仪表板监控手术进展，仅在“主刀医生”请求时介入。
