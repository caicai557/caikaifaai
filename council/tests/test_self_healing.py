"""
Unit tests for Self-Healing Loop

Tests cover:
- Test result parsing
- Healing loop execution
- Patch application and rollback
- Diagnosis generation
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from council.self_healing.loop import (
    SelfHealingLoop,
    HealingStatus,
    HealingReport,
    HealingIteration,
    TestResult,
    Diagnosis,
    Patch,
)
from council.self_healing.patch_generator import PatchGenerator


class TestTestResult:
    """Tests for TestResult dataclass"""

    def test_create_passing_result(self):
        """Should create a passing test result"""
        result = TestResult(
            passed=True,
            total_tests=10,
            passed_count=10,
            failed_count=0,
            error_output="",
            duration_ms=100,
        )
        assert result.passed is True
        assert result.failed_count == 0

    def test_create_failing_result(self):
        """Should create a failing test result"""
        result = TestResult(
            passed=False,
            total_tests=10,
            passed_count=8,
            failed_count=2,
            error_output="FAILED test_foo",
            duration_ms=150,
            failed_tests=["test_foo", "test_bar"],
        )
        assert result.passed is False
        assert result.failed_count == 2
        assert len(result.failed_tests) == 2


class TestDiagnosis:
    """Tests for Diagnosis dataclass"""

    def test_create_diagnosis(self):
        """Should create diagnosis with all fields"""
        diagnosis = Diagnosis(
            failed_test="test_example",
            error_type="assertion",
            error_message="Expected 1, got 2",
            suspected_file="src/main.py",
            suspected_line=42,
            root_cause="Value mismatch",
            suggested_fix="Update expected value",
        )
        assert diagnosis.error_type == "assertion"
        assert diagnosis.suspected_line == 42


class TestPatch:
    """Tests for Patch dataclass"""

    def test_create_patch(self):
        """Should create patch with confidence"""
        diagnosis = Diagnosis(
            failed_test="test_foo",
            error_type="type",
            error_message="type error",
        )
        patch = Patch(
            file_path="src/main.py",
            original_content="x = 1",
            patched_content="x = '1'",
            diagnosis=diagnosis,
            confidence=0.8,
        )
        assert patch.confidence == 0.8
        assert patch.file_path == "src/main.py"


class TestSelfHealingLoop:
    """Tests for SelfHealingLoop class"""

    def test_init_with_defaults(self):
        """Should initialize with default values"""
        loop = SelfHealingLoop()
        assert loop.max_iterations == 5
        assert "pytest" in loop.test_command

    def test_init_with_custom_values(self):
        """Should initialize with custom values"""
        loop = SelfHealingLoop(
            test_command="npm test",
            max_iterations=3,
            working_dir="/tmp",
        )
        assert loop.test_command == "npm test"
        assert loop.max_iterations == 3

    def test_default_diagnose(self):
        """Should diagnose from test result"""
        loop = SelfHealingLoop()
        result = TestResult(
            passed=False,
            total_tests=1,
            passed_count=0,
            failed_count=1,
            error_output="AssertionError: assert 1 == 2",
            duration_ms=100,
            failed_tests=["test_example"],
        )
        diagnosis = loop._default_diagnose(result)
        assert diagnosis.error_type == "assertion"
        assert diagnosis.failed_test == "test_example"

    def test_default_diagnose_import_error(self):
        """Should detect import error"""
        loop = SelfHealingLoop()
        result = TestResult(
            passed=False,
            total_tests=0,
            passed_count=0,
            failed_count=0,
            error_output="ImportError: No module named 'foo'",
            duration_ms=50,
        )
        diagnosis = loop._default_diagnose(result)
        assert diagnosis.error_type == "import"

    def test_default_patch_low_confidence(self):
        """Default patch should have low confidence"""
        loop = SelfHealingLoop()
        diagnosis = Diagnosis(
            failed_test="test_foo",
            error_type="assertion",
            error_message="test failed",
        )
        patch = loop._default_patch(diagnosis)
        assert patch.confidence == 0.0


class TestHealingReport:
    """Tests for HealingReport dataclass"""

    def test_create_success_report(self):
        """Should create success report"""
        report = HealingReport(
            status=HealingStatus.SUCCESS,
            iterations=[],
            total_iterations=1,
            initial_failures=2,
            final_failures=0,
            patches_applied=[],
            duration_ms=500,
        )
        assert report.status == HealingStatus.SUCCESS
        assert report.requires_human is False

    def test_create_failed_report(self):
        """Should create failed report requiring human"""
        report = HealingReport(
            status=HealingStatus.MAX_ITERATIONS,
            iterations=[],
            total_iterations=5,
            initial_failures=3,
            final_failures=2,
            patches_applied=[],
            duration_ms=5000,
            requires_human=True,
            recommendation="Manual fix needed",
        )
        assert report.status == HealingStatus.MAX_ITERATIONS
        assert report.requires_human is True


class TestPatchGenerator:
    """Tests for PatchGenerator class"""

    def test_init(self):
        """Should initialize with model"""
        generator = PatchGenerator(model="gpt-4")
        assert generator.model == "gpt-4"

    def test_detect_error_type_assertion(self):
        """Should detect assertion error"""
        generator = PatchGenerator()
        error_type = generator._detect_error_type("AssertionError: x != y")
        assert error_type == "assertion"

    def test_detect_error_type_import(self):
        """Should detect import error"""
        generator = PatchGenerator()
        error_type = generator._detect_error_type("ImportError: No module")
        assert error_type == "import"

    def test_detect_error_type_type(self):
        """Should detect type error"""
        generator = PatchGenerator()
        error_type = generator._detect_error_type("TypeError: expected str")
        assert error_type == "type"

    def test_extract_failed_test(self):
        """Should extract failed test name"""
        generator = PatchGenerator()
        output = "FAILED tests/test_main.py::test_example"
        test_name = generator._extract_failed_test(output)
        assert "test" in test_name

    def test_extract_location(self):
        """Should extract file and line from error"""
        generator = PatchGenerator()
        output = 'File "/path/to/file.py", line 42'
        file_path, line_num = generator._extract_location(output)
        assert file_path == "/path/to/file.py"
        assert line_num == 42

    def test_diagnose_full(self):
        """Should create full diagnosis"""
        generator = PatchGenerator()
        output = '''
        FAILED test_example
        File "src/main.py", line 10
        AssertionError: Expected True, got False
        '''
        diagnosis = generator.diagnose(output)
        assert diagnosis.error_type == "assertion"
        assert diagnosis.suspected_line == 10

    def test_generate_patch_no_file(self):
        """Should return low confidence patch when no file"""
        generator = PatchGenerator()
        diagnosis = Diagnosis(
            failed_test="test_foo",
            error_type="assertion",
            error_message="failed",
        )
        patch = generator.generate_patch(diagnosis)
        assert patch.confidence == 0.0

    def test_analyze_root_cause(self):
        """Should provide root cause analysis"""
        generator = PatchGenerator()
        cause = generator._analyze_root_cause("import", "No module")
        assert "import" in cause.lower() or "module" in cause.lower()

    def test_suggest_fix(self):
        """Should suggest appropriate fix"""
        generator = PatchGenerator()
        fix = generator._suggest_fix("key", "key not found")
        assert "key" in fix.lower() or "get" in fix.lower()


class TestHealingStatus:
    """Tests for HealingStatus enum"""

    def test_status_values(self):
        """Should have all expected status values"""
        assert HealingStatus.SUCCESS.value == "success"
        assert HealingStatus.PARTIAL.value == "partial"
        assert HealingStatus.FAILED.value == "failed"
        assert HealingStatus.MAX_ITERATIONS.value == "max_iterations"
        assert HealingStatus.HUMAN_REQUIRED.value == "human_required"
