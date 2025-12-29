"""
Council CLI - 命令行工具

提供日常开发常用命令:
- council classify <task>   分类任务并推荐模型
- council route <task>      快速路由
- council status            查看系统状态
"""

import argparse
import sys
import os
import importlib.util
from typing import Optional

print("DEBUG: CLI Loaded")

try:
    from rich.console import Console
    from rich.status import Status
    from rich.markdown import Markdown

    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def classify_command(task: str) -> None:
    """分类任务并显示推荐模型"""
    from council.orchestration.task_classifier import TaskClassifier, MODEL_SPECS

    tc = TaskClassifier()
    result = tc.classify(task)
    spec = MODEL_SPECS[result.recommended_model]

    print(f"""
╔════════════════════════════════════════════════════════════╗
║  Council Task Classifier                                   ║
╠════════════════════════════════════════════════════════════╣
║  任务: {task[:50]:50s}║
╠════════════════════════════════════════════════════════════╣
║  类型: {result.task_type.value:20s}置信度: {result.confidence:.0%}       ║
║  推荐: {spec.name:20s}SWE-bench: {spec.swe_bench}%    ║
║  备选: {result.fallback_model.value:50s}║
║  原因: {result.reason[:50]:50s}║
╚════════════════════════════════════════════════════════════╝
""")


def route_command(task: str) -> None:
    """快速路由 - 仅输出模型名称"""
    from council.orchestration.task_classifier import TaskClassifier

    tc = TaskClassifier()
    model = tc.recommend_model(task)
    print(model.value)


def status_command() -> None:
    """显示系统状态"""
    from council.orchestration.task_classifier import MODEL_SPECS

    print("""
╔════════════════════════════════════════════════════════════╗
║  Council System Status - December 2025                     ║
╠════════════════════════════════════════════════════════════╣
║  Available Models:                                         ║
""")

    for model, spec in MODEL_SPECS.items():
        status = "✅"
        print(
            f"║  {status} {spec.name:25s} {spec.swe_bench:5.1f}% SWE  {spec.context_window:>10,} ctx ║"
        )

    print("""╠════════════════════════════════════════════════════════════╣
║  Task Routing:                                             ║
║    planning     → gpt-5.2-codex                            ║
║    coding       → claude-4.5-sonnet                        ║
║    review       → gemini-3-pro                             ║
║    refactoring  → claude-4.5-opus                          ║
║    testing      → gemini-3-flash                           ║
╚════════════════════════════════════════════════════════════╝
""")


def models_command() -> None:
    """列出所有可用模型"""
    from council.orchestration.task_classifier import MODEL_SPECS

    print("\n可用模型 (December 2025):\n")
    print(f"{'模型':<25} {'SWE-bench':>10} {'上下文':>12} {'成本':>8} {'延迟':>8}")
    print("-" * 70)

    for model, spec in MODEL_SPECS.items():
        print(
            f"{spec.name:<25} {spec.swe_bench:>9.1f}% {spec.context_window:>11,} {spec.relative_cost:>7.1f}x {spec.latency:>8}"
        )


def run_agent(script_path: str, task: str) -> None:
    """运行 Agent 脚本"""
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")

    # 动态加载模块
    spec = importlib.util.spec_from_file_location("agent_module", script_path)
    if not spec or not spec.loader:
        raise ImportError(f"Could not load script: {script_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_module"] = module
    spec.loader.exec_module(module)

    # 查找 Agent 实例
    agent = getattr(module, "agent", None)
    if not agent:
        # 尝试查找 BaseAgent 子类实例
        from council.agents.base_agent import BaseAgent

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, BaseAgent):
                agent = attr
                break

    if not agent:
        print(f"Error: No 'agent' instance found in {script_path}")
        return

    print(f"Running agent: {agent.name}...")

    if HAS_RICH:
        console = Console()
        with console.status(
            f"[bold green]{agent.name} is thinking...[/bold green]", spinner="dots"
        ):
            result = agent.execute(task)

        console.print("\n[bold]Result:[/bold]")
        if result.success:
            console.print(Markdown(result.output))
        else:
            console.print(f"[bold red]Error:[/bold red] {result.output}")
            if result.errors:
                console.print(result.errors)
    else:
        print("Thinking...")
        result = agent.execute(task)
        print("\nResult:")
        print(result.output)
        if not result.success and result.errors:
            print(f"Errors: {result.errors}")


def main(args: Optional[list] = None) -> int:
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        prog="council",
        description="Council CLI - 多智能体理事会命令行工具",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # classify 命令
    classify_parser = subparsers.add_parser("classify", help="分类任务并推荐模型")
    classify_parser.add_argument("task", help="任务描述")

    # route 命令
    route_parser = subparsers.add_parser("route", help="快速路由 (仅输出模型名)")
    route_parser.add_argument("task", help="任务描述")

    # status 命令
    subparsers.add_parser("status", help="显示系统状态")

    # models 命令
    subparsers.add_parser("models", help="列出所有可用模型")

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行 Agent 脚本")
    run_parser.add_argument("script", help="Agent 脚本路径 (.py)")
    run_parser.add_argument("task", help="任务描述")

    parsed = parser.parse_args(args)

    if parsed.command == "classify":
        classify_command(parsed.task)
    elif parsed.command == "route":
        route_command(parsed.task)
    elif parsed.command == "status":
        status_command()
    elif parsed.command == "models":
        models_command()
    elif parsed.command == "run":
        try:
            run_agent(parsed.script, parsed.task)
        except Exception as e:
            print(f"Error running agent: {e}")
            return 1
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
