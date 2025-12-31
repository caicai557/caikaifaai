# Programmatic Tool Calling - 批量工具调用
"""基于 Anthropic PTC 最佳实践: 沙箱执行 LLM 生成的 Python 代码"""

import asyncio
import ast
from typing import Dict, Any, List, Callable, Optional


class ToolExecutionError(Exception):
    """工具执行错误"""
    pass


class SandboxViolationError(Exception):
    """沙箱安全违规"""
    pass


FORBIDDEN_IMPORTS = {"os", "sys", "subprocess", "shutil", "pathlib", "importlib", "builtins", "__builtins__", "eval", "exec", "compile", "open", "file", "input", "globals", "locals", "vars", "dir", "getattr", "setattr", "delattr", "hasattr"}
FORBIDDEN_NAMES = {"__import__", "__loader__", "__spec__", "__builtins__", "__file__", "__name__"}


class ToolsProxy:
    def __init__(self, tools: Dict[str, Callable]):
        self._tools = tools

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(f"Private attribute access not allowed: {name}")
        if name not in self._tools:
            raise AttributeError(f"Tool not found: {name}")
        return self._tools[name]


class CodeValidator(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split(".")[0] in FORBIDDEN_IMPORTS:
                self.violations.append(f"Forbidden import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split(".")[0] in FORBIDDEN_IMPORTS:
            self.violations.append(f"Forbidden import: {node.module}")
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in FORBIDDEN_NAMES:
            self.violations.append(f"Forbidden name: {node.id}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "compile", "open", "__import__"}:
                self.violations.append(f"Forbidden function: {node.func.id}")
        self.generic_visit(node)

    def validate(self, code: str) -> List[str]:
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            self.violations.append(f"Syntax error: {e}")
        return self.violations


class ProgrammaticToolExecutor:
    """沙箱执行 LLM 生成的工具调用代码"""

    def __init__(self, tools: Optional[Dict[str, Callable]] = None, timeout: float = 30.0, max_iterations: int = 1000):
        self.tools = tools or {}
        self.timeout = timeout
        self.max_iterations = max_iterations
        self._validator = CodeValidator()

    async def execute_batch(self, code: str) -> Any:
        violations = self._validator.validate(code)
        if violations:
            raise SandboxViolationError(f"Security violations: {violations}")

        tools_proxy = ToolsProxy(self.tools)
        safe_builtins = {
            "len": len, "range": range, "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
            "list": list, "dict": dict, "set": set, "tuple": tuple, "str": str, "int": int, "float": float,
            "bool": bool, "True": True, "False": False, "None": None, "print": print, "isinstance": isinstance,
            "type": type, "sorted": sorted, "reversed": reversed, "min": min, "max": max, "sum": sum,
            "abs": abs, "round": round, "any": any, "all": all,
        }

        wrapped_code = f"""
async def __execute(tools):
{chr(10).join('    ' + line for line in code.strip().split(chr(10)))}
    return output
"""
        try:
            namespace: Dict[str, Any] = {"__builtins__": safe_builtins}
            compiled = compile(wrapped_code, "<sandbox>", "exec")
            exec(compiled, namespace, namespace)
            execute_fn = namespace["__execute"]
            result = await asyncio.wait_for(execute_fn(tools_proxy), timeout=self.timeout)
            return result
        except asyncio.TimeoutError:
            raise ToolExecutionError(f"Execution timed out after {self.timeout}s")
        except Exception as e:
            raise ToolExecutionError(f"Execution failed: {e}")


__all__ = ["ProgrammaticToolExecutor", "ToolExecutionError", "SandboxViolationError"]
