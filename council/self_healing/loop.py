"""
Self-Healing Loop - Core engine for automated code repair

Implements the "Perceive → Reason → Act → Observe → Repeat" cycle:
1. Run tests
2. If fail → diagnose → generate patch
3. Apply patch → re-run tests
4. Check Wald consensus
5. Return result or escalate to human
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
from datetime import datetime
import asyncio
from enum import Enum
import subprocess


class HealingStatus(Enum):
    """Status of the healing process"""
    SUCCESS = "success"
    PARTIAL = "partial"  # Some tests fixed, some remain
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"
    HUMAN_REQUIRED = "human_required"


@dataclass
class TestResult:
    """Result from running tests"""
    passed: bool
    total_tests: int
    passed_count: int
    failed_count: int
    error_output: str
    duration_ms: float
    failed_tests: List[str] = field(default_factory=list)


@dataclass
class Diagnosis:
    """Diagnosis of a test failure"""
    failed_test: str
    error_type: str
    error_message: str
    suspected_file: Optional[str] = None
    suspected_line: Optional[int] = None
    root_cause: str = ""
    suggested_fix: str = ""


@dataclass
class Patch:
    """A code patch to fix an issue"""
    file_path: str
    original_content: str
    patched_content: str
    diagnosis: Diagnosis
    confidence: float = 0.5


@dataclass
class HealingIteration:
    """Record of a single healing iteration"""
    iteration: int
    test_result: TestResult
    diagnosis: Optional[Diagnosis] = None
    patch: Optional[Patch] = None
    patch_applied: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HealingReport:
    """Final report from the healing loop"""
    status: HealingStatus
    iterations: List[HealingIteration]
    total_iterations: int
    initial_failures: int
    final_failures: int
    patches_applied: List[Patch]
    duration_ms: float
    requires_human: bool = False
    recommendation: str = ""


class SelfHealingLoop:
    """
    Self-healing loop engine

    Automatically attempts to fix failing tests through iterative
    diagnosis and patching.

    Usage:
        loop = SelfHealingLoop(
            test_command="python -m pytest tests/",
            max_iterations=5,
        )
        report = loop.run()
        if report.status == HealingStatus.SUCCESS:
            print("All tests fixed!")
    """

    def __init__(
        self,
        test_command: str = "python3 -m pytest",
        max_iterations: int = 5,
        working_dir: str = ".",
        diagnose_fn: Optional[Callable[[TestResult], Diagnosis]] = None,
        patch_fn: Optional[Callable[[Diagnosis], Patch]] = None,
    ):
        """
        Initialize the self-healing loop

        Args:
            test_command: Command to run tests
            max_iterations: Maximum repair attempts
            working_dir: Working directory for tests
            diagnose_fn: Custom diagnosis function
            patch_fn: Custom patch generation function
        """
        self.test_command = test_command
        self.max_iterations = max_iterations
        self.working_dir = working_dir
        self.diagnose_fn = diagnose_fn or self._default_diagnose
        self.patch_fn = patch_fn or self._default_patch

        self.iterations: List[HealingIteration] = []
        self.patches_applied: List[Patch] = []

    def run_tests(self) -> TestResult:
        """
        Run the test suite

        Returns:
            TestResult with pass/fail information
        """
        start_time = datetime.now()

        try:
            result = subprocess.run(
                self.test_command.split(),
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            duration = (datetime.now() - start_time).total_seconds() * 1000

            # Parse pytest output
            output = result.stdout + result.stderr
            passed = result.returncode == 0

            # Simple parsing - extract test counts
            total = 0
            passed_count = 0
            failed_count = 0
            failed_tests = []

            for line in output.split("\n"):
                if "passed" in line.lower() and "=" in line:
                    # Try to extract counts from summary line
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed":
                            try:
                                passed_count = int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                        elif part == "failed":
                            try:
                                failed_count = int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                elif "FAILED" in line:
                    # Extract failed test name
                    if "::" in line:
                        test_name = line.split("FAILED")[1].strip() if "FAILED" in line else line
                        failed_tests.append(test_name.strip())

            total = passed_count + failed_count

            return TestResult(
                passed=passed,
                total_tests=total,
                passed_count=passed_count,
                failed_count=failed_count,
                error_output=output,
                duration_ms=duration,
                failed_tests=failed_tests,
            )

        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return TestResult(
                passed=False,
                total_tests=0,
                passed_count=0,
                failed_count=0,
                error_output="Test execution timed out",
                duration_ms=duration,
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return TestResult(
                passed=False,
                total_tests=0,
                passed_count=0,
                failed_count=0,
                error_output=str(e),
                duration_ms=duration,
            )

    def _default_diagnose(self, test_result: TestResult) -> Diagnosis:
        """
        Default diagnosis function

        Analyzes test output to identify the root cause.
        In production, this would use an LLM.
        """
        # Simple error type detection - always check error_output
        error_type = "unknown"
        if "AssertionError" in test_result.error_output:
            error_type = "assertion"
        elif "ImportError" in test_result.error_output:
            error_type = "import"
        elif "ModuleNotFoundError" in test_result.error_output:
            error_type = "import"
        elif "TypeError" in test_result.error_output:
            error_type = "type"
        elif "AttributeError" in test_result.error_output:
            error_type = "attribute"

        if not test_result.failed_tests:
            return Diagnosis(
                failed_test="unknown",
                error_type=error_type,
                error_message=test_result.error_output[:500],
            )

        failed_test = test_result.failed_tests[0]

        return Diagnosis(
            failed_test=failed_test,
            error_type=error_type,
            error_message=test_result.error_output[:1000],
            root_cause=f"Test '{failed_test}' failed with {error_type} error",
        )

    def _default_patch(self, diagnosis: Diagnosis) -> Patch:
        """
        Default patch generation function

        Attempts LLM patch generation when available.
        """
        try:
            from council.self_healing.patch_generator import PatchGenerator
        except Exception:
            return Patch(
                file_path="",
                original_content="",
                patched_content="",
                diagnosis=diagnosis,
                confidence=0.0,
            )

        generator = PatchGenerator()
        if generator._has_gemini or generator._has_openai:
            try:
                return asyncio.run(generator.generate_patch_with_llm(diagnosis))
            except RuntimeError:
                return generator.generate_patch(diagnosis)
        return generator.generate_patch(diagnosis)

    def apply_patch(self, patch: Patch) -> bool:
        """
        Apply a patch to a file

        Args:
            patch: The patch to apply

        Returns:
            True if patch was applied successfully
        """
        if not patch.file_path or patch.confidence < 0.5:
            return False

        try:
            with open(patch.file_path, 'r') as f:
                current = f.read()

            if patch.original_content not in current:
                return False

            new_content = current.replace(
                patch.original_content,
                patch.patched_content,
                1
            )

            with open(patch.file_path, 'w') as f:
                f.write(new_content)

            self.patches_applied.append(patch)
            return True

        except Exception:
            return False

    def rollback_patches(self) -> int:
        """
        Rollback all applied patches

        Returns:
            Number of patches rolled back
        """
        rolled_back = 0
        for patch in reversed(self.patches_applied):
            try:
                with open(patch.file_path, 'r') as f:
                    current = f.read()

                if patch.patched_content in current:
                    new_content = current.replace(
                        patch.patched_content,
                        patch.original_content,
                        1
                    )
                    with open(patch.file_path, 'w') as f:
                        f.write(new_content)
                    rolled_back += 1
            except Exception:
                pass

        self.patches_applied = []
        return rolled_back

    def run(self) -> HealingReport:
        """
        Execute the self-healing loop

        Returns:
            HealingReport with results
        """
        start_time = datetime.now()
        initial_result = self.run_tests()
        initial_failures = initial_result.failed_count

        # If tests pass, nothing to heal
        if initial_result.passed:
            return HealingReport(
                status=HealingStatus.SUCCESS,
                iterations=[HealingIteration(iteration=0, test_result=initial_result)],
                total_iterations=0,
                initial_failures=0,
                final_failures=0,
                patches_applied=[],
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

        # Healing loop
        for i in range(1, self.max_iterations + 1):
            test_result = self.run_tests() if i > 1 else initial_result

            if test_result.passed:
                # Fixed!
                duration = (datetime.now() - start_time).total_seconds() * 1000
                return HealingReport(
                    status=HealingStatus.SUCCESS,
                    iterations=self.iterations,
                    total_iterations=i - 1,
                    initial_failures=initial_failures,
                    final_failures=0,
                    patches_applied=self.patches_applied,
                    duration_ms=duration,
                    recommendation="All tests passing after self-healing.",
                )

            # Diagnose
            diagnosis = self.diagnose_fn(test_result)

            # Generate patch
            patch = self.patch_fn(diagnosis)

            # Apply patch
            patch_applied = self.apply_patch(patch)

            iteration = HealingIteration(
                iteration=i,
                test_result=test_result,
                diagnosis=diagnosis,
                patch=patch,
                patch_applied=patch_applied,
            )
            self.iterations.append(iteration)

            # If we can't generate a valid patch, stop
            if not patch_applied and patch.confidence < 0.3:
                break

        # Max iterations reached or no valid patches
        final_result = self.run_tests()
        duration = (datetime.now() - start_time).total_seconds() * 1000

        status = HealingStatus.MAX_ITERATIONS
        requires_human = True

        if final_result.failed_count < initial_failures:
            status = HealingStatus.PARTIAL

        return HealingReport(
            status=status,
            iterations=self.iterations,
            total_iterations=len(self.iterations),
            initial_failures=initial_failures,
            final_failures=final_result.failed_count,
            patches_applied=self.patches_applied,
            duration_ms=duration,
            requires_human=requires_human,
            recommendation="Human review required. See iterations for diagnosis.",
        )


# Export
__all__ = [
    "SelfHealingLoop",
    "HealingStatus",
    "HealingReport",
    "HealingIteration",
    "TestResult",
    "Diagnosis",
    "Patch",
]
