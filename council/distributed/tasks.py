import importlib.util
import sys
from typing import Dict, Any

from council.distributed.celery_app import make_celery_app, HAS_CELERY

if HAS_CELERY:
    app = make_celery_app()

    @app.task(name="council.run_agent")
    def run_agent_task(script_path: str, task: str) -> Dict[str, Any]:
        if not script_path:
            raise ValueError("script_path is required")

        spec = importlib.util.spec_from_file_location("agent_module", script_path)
        if not spec or not spec.loader:
            raise ImportError(f"Could not load script: {script_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["agent_module"] = module
        spec.loader.exec_module(module)

        agent = getattr(module, "agent", None)
        if not agent:
            from council.agents.base_agent import BaseAgent

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, BaseAgent):
                    agent = attr
                    break

        if not agent:
            raise ValueError(f"No agent instance found in {script_path}")

        result = agent.execute(task)
        return {
            "success": result.success,
            "output": result.output,
            "changes_made": result.changes_made,
            "errors": result.errors,
        }
else:
    app = None

    def run_agent_task(*_args, **_kwargs):
        raise ImportError("celery is required. Install with: pip install celery")
