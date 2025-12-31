"""
Blast Radius Analyzer - Impact-Aware Code Routing

Analyzes the impact of code changes by examining import dependencies.
Used to determine if a task requires full Council review (High impact)
or can be fast-tracked (Low impact).

Reference: doc/COUNCIL_2025_IMPLEMENTATION_POC.md - Section 4
"""

import ast
import os
from pathlib import Path
from typing import List, Set, Dict
from dataclasses import dataclass
from enum import Enum


class ImpactLevel(str, Enum):
    """Impact level for code changes"""

    LOW = "LOW (Leaf Node)"
    MEDIUM = "MEDIUM (Local Util)"
    HIGH = "HIGH (Core Interface)"


@dataclass
class ImpactAnalysis:
    """Result of impact analysis"""

    level: ImpactLevel
    incoming_deps: int
    outgoing_deps: int
    dependents: List[str]
    dependencies: List[str]


class BlastRadiusAnalyzer:
    """
    Analyzes the "blast radius" of code changes.

    Determines how many other files depend on the target files,
    enabling impact-aware routing decisions.

    Usage:
        analyzer = BlastRadiusAnalyzer("/path/to/project")
        impact = analyzer.calculate_impact(["council/core/agent.py"])
        print(impact.level)  # "HIGH (Core Interface)"
    """

    def __init__(self, root_dir: str):
        """
        Initialize the analyzer.

        Args:
            root_dir: Root directory of the project to analyze
        """
        self.root_dir = Path(root_dir).resolve()
        self._import_graph: Dict[str, Set[str]] = {}
        self._cached = False

    def _build_import_graph(self) -> None:
        """Build the import dependency graph for the project."""
        if self._cached:
            return

        self._import_graph = {}

        for py_file in self._get_all_python_files():
            imports = self._get_imports(py_file)
            rel_path = str(py_file.relative_to(self.root_dir))
            self._import_graph[rel_path] = imports

        self._cached = True

    def _get_all_python_files(self) -> List[Path]:
        """Get all Python files in the project."""
        python_files = []

        for root, dirs, files in os.walk(self.root_dir):
            # Skip hidden directories and common non-source directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ("__pycache__", "node_modules", ".venv", "venv", ".git")
            ]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        return python_files

    def _get_imports(self, file_path: Path) -> Set[str]:
        """
        Extract import statements from a Python file using AST.

        Returns module names that are imported.
        """
        imports = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])

        except (SyntaxError, FileNotFoundError, UnicodeDecodeError):
            pass

        return imports

    def _get_module_name(self, file_path: str) -> str:
        """Convert file path to module name."""
        # Remove .py extension and convert path separators to dots
        module = file_path.replace(".py", "").replace("/", ".").replace("\\", ".")
        return module.split(".")[0]  # Return top-level module

    def _find_dependents(self, target_files: List[str]) -> List[str]:
        """Find files that import any of the target files."""
        self._build_import_graph()

        # Convert target files to their module names
        target_modules = {self._get_module_name(f) for f in target_files}

        dependents = []
        for file_path, imports in self._import_graph.items():
            if file_path in target_files:
                continue

            # Check if this file imports any of our target modules
            if imports & target_modules:
                dependents.append(file_path)

        return dependents

    def _find_dependencies(self, target_files: List[str]) -> List[str]:
        """Find files that the target files import."""
        self._build_import_graph()

        dependencies = set()
        for file_path in target_files:
            if file_path in self._import_graph:
                dependencies.update(self._import_graph[file_path])

        return list(dependencies)

    def calculate_impact(self, target_files: List[str]) -> ImpactAnalysis:
        """
        Calculate the impact level of changing the target files.

        Args:
            target_files: List of file paths relative to root_dir

        Returns:
            ImpactAnalysis with level, dependency counts, and details
        """
        dependents = self._find_dependents(target_files)
        dependencies = self._find_dependencies(target_files)

        incoming_deps = len(dependents)
        outgoing_deps = len(dependencies)

        # Determine impact level
        if incoming_deps == 0:
            level = ImpactLevel.LOW
        elif incoming_deps < 5:
            level = ImpactLevel.MEDIUM
        else:
            level = ImpactLevel.HIGH

        return ImpactAnalysis(
            level=level,
            incoming_deps=incoming_deps,
            outgoing_deps=outgoing_deps,
            dependents=dependents,
            dependencies=dependencies,
        )

    def get_impact_level(self, target_files: List[str]) -> str:
        """
        Get just the impact level string for a set of files.

        Convenience method for quick checks.

        Args:
            target_files: List of file paths relative to root_dir

        Returns:
            Impact level string like "LOW (Leaf Node)"
        """
        return self.calculate_impact(target_files).level.value

    def should_fast_track(self, target_files: List[str]) -> bool:
        """
        Determine if changes to these files can skip full Council review.

        Returns True for LOW impact files (leaf nodes with no dependents).

        Args:
            target_files: List of file paths relative to root_dir

        Returns:
            True if changes can be fast-tracked
        """
        analysis = self.calculate_impact(target_files)
        return analysis.level == ImpactLevel.LOW

    def clear_cache(self) -> None:
        """Clear the cached import graph. Call after file changes."""
        self._import_graph = {}
        self._cached = False


# Export
__all__ = [
    "BlastRadiusAnalyzer",
    "ImpactAnalysis",
    "ImpactLevel",
]
