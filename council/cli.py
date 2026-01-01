"""
Council CLI - 命令行工具

提供日常开发常用命令:
- council classify <task>   分类任务并推荐模型
- council route <task>      快速路由
- council status            查看系统状态

六步工作流命令:
- council init              生成 CLAUDE.md
- council plan <task>       只读计划模式
- council audit             全库审计
- council tdd <feature>     TDD测试生成
- council execute <task>    沙箱执行
- council rewind            快照备份
- council clear             会话清理
"""

import argparse
import sys
import os
import importlib.util
from typing import Optional

try:
    from rich.console import Console
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


def dev_command(task: str, verbose: bool = True) -> None:
    """开发任务 - 全能力编排器"""
    import asyncio
    from council.dev_orchestrator import DevOrchestrator, DevStatus

    console = None
    if HAS_RICH:
        console = Console()
        console.print("\n[bold blue]🚀 Council Dev[/bold blue] - 多模型编程智能体")
        console.print(f"[dim]任务: {task}[/dim]\n")

    orchestrator = DevOrchestrator(verbose=verbose)

    # 运行编排器
    result = asyncio.run(orchestrator.dev(task))

    # 输出结果
    if HAS_RICH and console:
        if result.status == DevStatus.COMPLETED:
            console.print("\n[bold green]✅ 完成![/bold green]")
        elif result.status == DevStatus.FAILED:
            console.print("\n[bold red]❌ 失败[/bold red]")
        else:
            console.print(f"\n[bold yellow]⚠️ {result.status.value}[/bold yellow]")

        console.print(f"[dim]耗时: {result.duration_ms:.0f}ms[/dim]")
        console.print(f"[dim]{result.message}[/dim]")

        if result.consensus:
            console.print(f"\n[bold]共识:[/bold] π={result.consensus.pi_approve:.3f}")
    else:
        print(f"\n{result.message}")
        print(f"状态: {result.status.value}")
        print(f"耗时: {result.duration_ms:.0f}ms")


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

    # dev 命令 (1.0.0 核心)
    dev_parser = subparsers.add_parser("dev", help="开发任务 (全能力编排器)")
    dev_parser.add_argument("task", help="开发任务描述")
    dev_parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    # === 六步工作流命令 ===
    
    # init 命令
    init_parser = subparsers.add_parser("init", help="生成 CLAUDE.md")
    init_parser.add_argument("--output", "-o", default="CLAUDE.md", help="输出文件路径")
    
    # plan 命令
    plan_parser = subparsers.add_parser("plan", help="只读计划模式")
    plan_parser.add_argument("task", help="任务描述")
    
    # audit 命令
    audit_parser = subparsers.add_parser("audit", help="全库审计 (Gemini Pro)")
    audit_parser.add_argument("--dir", "-d", default=".", help="目标目录")
    
    # tdd 命令
    tdd_parser = subparsers.add_parser("tdd", help="TDD测试生成 (Claude Sonnet)")
    tdd_parser.add_argument("feature", help="功能描述")
    
    # execute 命令
    execute_parser = subparsers.add_parser("execute", help="沙箱执行")
    execute_parser.add_argument("task", help="任务描述")
    execute_parser.add_argument("--sandbox", "-s", default="docker", help="沙箱类型")
    
    # rewind 命令
    rewind_parser = subparsers.add_parser("rewind", help="快照备份")
    rewind_parser.add_argument("--id", help="快照ID (默认自动生成)")
    
    # clear 命令
    clear_parser = subparsers.add_parser("clear", help="会话清理")
    clear_parser.add_argument("--keep", "-k", type=int, default=5, help="保留快照数量")
    
    # codemap 命令
    codemap_parser = subparsers.add_parser("codemap", help="生成代码地图")
    codemap_parser.add_argument("--dir", "-d", default=".", help="目标目录")
    codemap_parser.add_argument("--output", "-o", default="CODEMAP.md", help="输出文件")
    
    # tripartite 命令
    tripartite_parser = subparsers.add_parser("tripartite", help="三权分立执行")
    tripartite_parser.add_argument("task", help="任务描述")

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
    elif parsed.command == "dev":
        try:
            dev_command(parsed.task, verbose=getattr(parsed, "verbose", True))
        except Exception as e:
            print(f"Error in dev: {e}")
            return 1
    # === 六步工作流命令 ===
    elif parsed.command == "init":
        from council.workflow.commands import init_command
        init_command(output_path=parsed.output)
    elif parsed.command == "plan":
        from council.workflow.commands import plan_command
        plan_command(parsed.task)
    elif parsed.command == "audit":
        from council.workflow.commands import audit_command
        audit_command(target_dir=parsed.dir)
    elif parsed.command == "tdd":
        from council.workflow.commands import tdd_command
        tdd_command(parsed.feature)
    elif parsed.command == "execute":
        from council.workflow.commands import execute_command
        execute_command(parsed.task, sandbox=parsed.sandbox)
    elif parsed.command == "rewind":
        from council.workflow.commands import rewind_command
        rewind_command(snapshot_id=parsed.id)
    elif parsed.command == "clear":
        from council.workflow.commands import clear_command
        clear_command(keep=parsed.keep)
    elif parsed.command == "codemap":
        from council.workflow.codemap import CodeMapGenerator
        generator = CodeMapGenerator(root_dir=parsed.dir)
        output_path = generator.save(parsed.output)
        print(f"✅ 代码地图已生成: {output_path}")
    elif parsed.command == "tripartite":
        from council.orchestration.tripartite import TripartiteOrchestrator
        orchestrator = TripartiteOrchestrator()
        result = orchestrator.run(parsed.task)
        print(f"✅ 三权分立执行完成, Token节省: {result.token_saved:.1%}")
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
