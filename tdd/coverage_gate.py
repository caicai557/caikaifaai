"""
TDD Coverage Gate - Programmatic test coverage enforcement

Blocks code changes from proceeding if coverage falls below threshold.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
import subprocess
import re


@dataclass
class CoverageReport:
    """Test coverage report"""

    total_coverage: float  # Percentage 0-100
    files_coverage: Dict[str, float]  # Per-file coverage
    uncovered_lines: Dict[str, List[int]]  # Per-file uncovered lines
    passed: bool
    error: Optional[str] = None


class CoverageGateError(Exception):
    """Raised when coverage is below threshold"""

    def __init__(self, current: float, required: float):
        self.current = current
        self.required = required
        super().__init__(f"Coverage {current:.1f}% is below required {required:.1f}%")


class CoverageGate:
    """
    TDD Coverage Gate

    Ensures test coverage meets minimum threshold before allowing
    code changes to proceed.

    Usage:
        gate = CoverageGate(min_coverage=90)
        if gate.check():
            print("Coverage OK!")
        else:
            gate.block_if_below()  # Raises CoverageGateError
    """

    def __init__(
        self,
        min_coverage: float = 90.0,
        test_command: str = "python3 -m pytest --cov=council --cov-report=term-missing",
        working_dir: str = ".",
    ):
        """
        Initialize coverage gate

        Args:
            min_coverage: Minimum required coverage percentage (0-100)
            test_command: Command to run tests with coverage
            working_dir: Working directory for tests
        """
        self.min_coverage = min_coverage
        self.test_command = test_command
        self.working_dir = working_dir
        self._last_report: Optional[CoverageReport] = None

    def run_coverage(self) -> CoverageReport:
        """
        Run tests and collect coverage report

        Returns:
            CoverageReport with coverage data
        """
        try:
            result = subprocess.run(
                self.test_command.split(),
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )

            output = result.stdout + result.stderr

            # Parse coverage output
            total_coverage = self._parse_total_coverage(output)
            files_coverage = self._parse_file_coverage(output)
            uncovered = self._parse_uncovered_lines(output)

            self._last_report = CoverageReport(
                total_coverage=total_coverage,
                files_coverage=files_coverage,
                uncovered_lines=uncovered,
                passed=total_coverage >= self.min_coverage,
            )

            return self._last_report

        except subprocess.TimeoutExpired:
            return CoverageReport(
                total_coverage=0,
                files_coverage={},
                uncovered_lines={},
                passed=False,
                error="Test execution timed out",
            )
        except Exception as e:
            return CoverageReport(
                total_coverage=0,
                files_coverage={},
                uncovered_lines={},
                passed=False,
                error=str(e),
            )

    def _parse_total_coverage(self, output: str) -> float:
        """Extract total coverage percentage from pytest-cov output"""
        # Look for "TOTAL ... XX%" pattern
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if match:
            return float(match.group(1))

        # Alternative pattern
        match = re.search(r"(\d+)%\s*$", output, re.MULTILINE)
        if match:
            return float(match.group(1))

        return 0.0

    def _parse_file_coverage(self, output: str) -> Dict[str, float]:
        """Extract per-file coverage from output"""
        files = {}
        # Match lines like: council/auth/rbac.py    220    20    91%
        pattern = r"^([\w/\._]+\.py)\s+\d+\s+\d+\s+(\d+)%"
        for match in re.finditer(pattern, output, re.MULTILINE):
            files[match.group(1)] = float(match.group(2))
        return files

    def _parse_uncovered_lines(self, output: str) -> Dict[str, List[int]]:
        """Extract uncovered line numbers from output"""
        uncovered = {}
        # Match lines like: council/auth/rbac.py    220    20    91%   42-45, 78
        pattern = r"^([\w/\._]+\.py)\s+\d+\s+\d+\s+\d+%\s+([\d\-,\s]+)"
        for match in re.finditer(pattern, output, re.MULTILINE):
            file_path = match.group(1)
            lines_str = match.group(2).strip()
            if lines_str:
                lines = self._parse_line_ranges(lines_str)
                uncovered[file_path] = lines
        return uncovered

    def _parse_line_ranges(self, lines_str: str) -> List[int]:
        """Parse line ranges like '42-45, 78' into [42, 43, 44, 45, 78]"""
        lines = []
        for part in lines_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                lines.extend(range(int(start), int(end) + 1))
            elif part.isdigit():
                lines.append(int(part))
        return lines

    def check(self) -> bool:
        """
        Check if current coverage meets threshold

        Returns:
            True if coverage >= min_coverage
        """
        report = self.run_coverage()
        return report.passed

    def block_if_below(self) -> None:
        """
        Block execution if coverage is below threshold

        Raises:
            CoverageGateError: If coverage is below min_coverage
        """
        report = self.run_coverage()
        if not report.passed:
            raise CoverageGateError(report.total_coverage, self.min_coverage)

    def get_last_report(self) -> Optional[CoverageReport]:
        """Get the last coverage report"""
        return self._last_report

    def get_uncovered_summary(self) -> str:
        """Get a summary of uncovered code"""
        if not self._last_report:
            return "No coverage report available"

        lines = []
        for file_path, uncovered in self._last_report.uncovered_lines.items():
            if uncovered:
                lines.append(f"{file_path}: lines {uncovered[:5]}...")

        if not lines:
            return "All code covered!"

        return "\n".join(lines)


# Export
__all__ = ["CoverageGate", "CoverageReport", "CoverageGateError"]
