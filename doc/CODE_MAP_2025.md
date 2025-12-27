# Cortex Agent Sandbox: Code Map (Dec 2025)

> **Context**: This project has evolved from a Telegram Client into an **Agent Development Sandbox**.
> **Core Architecture**: Async Actor Model + SQLite Blackboard + Real LLM Cognition.

## 1. Directory Structure

```
src/telegram_multi/
├── cortex/                       # [THE BRAIN] new!
│   ├── actors/                   # Actor Implementations
│   │   ├── base.py               # Actor primitives (mailbox, loop)
│   │   ├── agent.py              # The "Thinking" Agent (ReAct Loop)
│   │   └── council.py            # The Orchestrator
│   ├── intelligence/             # [THE SOUL]
│   │   ├── llm_factory.py        # Gemini/Claude Factory
│   │   └── prompts.py            # System Identity & Personas
│   ├── tools/                    # [THE HANDS]
│   │   └── browser_tool.py       # Browser Control Interface
│   ├── db.py                     # SQLite WAL 'Blackboard'
│   └── logger.py                 # Structured Tracing (Spans)
├── cli/
│   ├── commands/
│   │   └── council.py            # System Bootstrap
│   └── cli_main.py               # Entry Point
├── ... (Legacy components: browser_context, translators)
```

## 2. Key Components Breakdown

### A. The Cortex Layer (Infrastructure)
*   **`CortexDB` (`cortex/db.py`)**: The central nervous system. A shared, WAL-mode SQLite database that stores:
    *   `traces`: High-level task flows.
    *   `spans`: Granular steps (Thinking, Tool Calls, Logs).
    *   `votes`: (Phase 9) Council decisions.
*   **`BaseActor` (`cortex/actors/base.py`)**: The generated base class for all actors. Handles async message queues, error recovery, and shutdown signals.

### B. The Intelligence Layer (Cognition)
*   **`LLMFactory` (`cortex/intelligence/llm_factory.py`)**:
    *   Currently supports: **Google Gemini**.
    *   Features: Automatic Auth (ADC), Regex-based JSON Tool Parsing (for robustness).
*   **`AgentActor` (`cortex/actors/agent.py`)**:
    *   The "Entity" that lives in the sandbox.
    *   Runs a generic cognitive loop: `Msg -> Think (LLM) -> Action (Tool) -> Observe -> Reply`.

### C. The Interface Layer (Body)
*   **`BrowserTool` (`cortex/tools/browser_tool.py`)**:
    *   Exposes `BrowserContext` to the LLM.
    *   Actions: `read_title`, `click`, `type`, `navigate`.

## 3. Development Flows

### "The First Breath" (Debugging Agents)
To test an agent's ability to think and act:
```bash
# Set Key (if not using ADC)
export GEMINI_API_KEY="..."
# Run the E2E Test
pytest tests/cortex/test_awakening.py
```

### "The Council" (Running the System)
To launch the full visual environment:
```bash
python run_telegram.py council --config telegram.yaml
```

## 4. Phase Status
*   **Phase 1-5**: Foundation (Browser, Translation) [Legacy/Stable]
*   **Phase 6**: Cortex Layer (DB, Actors) [Complete]
*   **Phase 7**: Deep Integration (Wiring) [Complete]
*   **Phase 8**: The Awakening (Real LLM) [Complete]
*   **Phase 9**: Governance (Council Rules) [In Progress]
