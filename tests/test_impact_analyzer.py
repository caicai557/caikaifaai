"""
Tests for council/governance/impact_analyzer.py
"""

import pytest
import tempfile
import os
from pathlib import Path

from council.governance.impact_analyzer import (
    BlastRadiusAnalyzer,
    ImpactAnalysis,
    ImpactLevel,
)


class TestImpactLevel:
    """Tests for ImpactLevel enum"""

    def test_impact_levels_exist(self):
        """Test all impact levels are defined"""
        assert ImpactLevel.LOW.value == "LOW (Leaf Node)"
        assert ImpactLevel.MEDIUM.value == "MEDIUM (Local Util)"
        assert ImpactLevel.HIGH.value == "HIGH (Core Interface)"


class TestImpactAnalysis:
    """Tests for ImpactAnalysis dataclass"""

    def test_create_analysis(self):
        """Test creating an impact analysis"""
        analysis = ImpactAnalysis(
            level=ImpactLevel.LOW,
            incoming_deps=0,
            outgoing_deps=2,
            dependents=[],
            dependencies=["os", "sys"],
        )
        assert analysis.level == ImpactLevel.LOW
        assert analysis.incoming_deps == 0
        assert analysis.outgoing_deps == 2


class TestBlastRadiusAnalyzer:
    """Tests for BlastRadiusAnalyzer"""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple project structure:
            # project/
            #   core/
            #     __init__.py
            #     base.py (imported by many)
            #   utils/
            #     __init__.py
            #     helpers.py (imports core.base)
            #   features/
            #     __init__.py
            #     feature_a.py (imports utils.helpers)
            #     feature_b.py (imports utils.helpers)
            #   standalone/
            #     __init__.py
            #     isolated.py (no imports, no dependents)

            # Create directories
            os.makedirs(os.path.join(tmpdir, "core"))
            os.makedirs(os.path.join(tmpdir, "utils"))
            os.makedirs(os.path.join(tmpdir, "features"))
            os.makedirs(os.path.join(tmpdir, "standalone"))

            # Create __init__.py files
            for subdir in ["core", "utils", "features", "standalone"]:
                Path(tmpdir, subdir, "__init__.py").touch()

            # core/base.py - Core module
            with open(os.path.join(tmpdir, "core", "base.py"), "w") as f:
                f.write("""
class BaseClass:
    pass
""")

            # utils/helpers.py - Imports core
            with open(os.path.join(tmpdir, "utils", "helpers.py"), "w") as f:
                f.write("""
from core import base

def helper_function():
    return base.BaseClass()
""")

            # features/feature_a.py - Imports utils
            with open(os.path.join(tmpdir, "features", "feature_a.py"), "w") as f:
                f.write("""
from utils import helpers

def feature_a():
    return helpers.helper_function()
""")

            # features/feature_b.py - Imports utils
            with open(os.path.join(tmpdir, "features", "feature_b.py"), "w") as f:
                f.write("""
from utils import helpers

def feature_b():
    return helpers.helper_function()
""")

            # standalone/isolated.py - No imports
            with open(os.path.join(tmpdir, "standalone", "isolated.py"), "w") as f:
                f.write("""
def isolated_function():
    return "I am isolated"
""")

            yield tmpdir

    def test_leaf_node_low_impact(self, temp_project):
        """Test that a file with no dependents returns LOW impact"""
        analyzer = BlastRadiusAnalyzer(temp_project)

        analysis = analyzer.calculate_impact(["standalone/isolated.py"])

        assert analysis.level == ImpactLevel.LOW
        assert analysis.incoming_deps == 0
        assert len(analysis.dependents) == 0

    def test_local_util_medium_impact(self, temp_project):
        """Test that a file with few dependents returns MEDIUM impact"""
        analyzer = BlastRadiusAnalyzer(temp_project)

        # utils/helpers.py is imported by features/feature_a.py and feature_b.py
        analysis = analyzer.calculate_impact(["utils/helpers.py"])

        assert analysis.level == ImpactLevel.MEDIUM
        assert analysis.incoming_deps >= 1  # At least feature_a imports it
        assert analysis.incoming_deps < 5  # Less than 5 dependents

    def test_core_module_high_impact(self, temp_project):
        """Test that a heavily imported file returns HIGH impact"""
        # For this test, we need to create a more connected project
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "core"))

            # Core module
            with open(os.path.join(tmpdir, "core", "base.py"), "w") as f:
                f.write("class Base: pass")

            # Create 6 files that import core
            for i in range(6):
                with open(os.path.join(tmpdir, f"module_{i}.py"), "w") as f:
                    f.write("from core import base\n")

            analyzer = BlastRadiusAnalyzer(tmpdir)
            analysis = analyzer.calculate_impact(["core/base.py"])

            assert analysis.level == ImpactLevel.HIGH
            assert analysis.incoming_deps >= 5

    def test_get_impact_level(self, temp_project):
        """Test convenience method get_impact_level"""
        analyzer = BlastRadiusAnalyzer(temp_project)

        level = analyzer.get_impact_level(["standalone/isolated.py"])

        assert level == "LOW (Leaf Node)"

    def test_should_fast_track_low_impact(self, temp_project):
        """Test that LOW impact files can be fast-tracked"""
        analyzer = BlastRadiusAnalyzer(temp_project)

        assert analyzer.should_fast_track(["standalone/isolated.py"]) is True

    def test_should_not_fast_track_high_impact(self, temp_project):
        """Test that HIGH impact files cannot be fast-tracked"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "core"))

            with open(os.path.join(tmpdir, "core", "base.py"), "w") as f:
                f.write("class Base: pass")

            for i in range(6):
                with open(os.path.join(tmpdir, f"module_{i}.py"), "w") as f:
                    f.write("from core import base\n")

            analyzer = BlastRadiusAnalyzer(tmpdir)
            assert analyzer.should_fast_track(["core/base.py"]) is False

    def test_cache_clearing(self, temp_project):
        """Test that cache can be cleared"""
        analyzer = BlastRadiusAnalyzer(temp_project)

        # First call builds cache
        analyzer.calculate_impact(["standalone/isolated.py"])
        assert analyzer._cached is True

        # Clear cache
        analyzer.clear_cache()
        assert analyzer._cached is False

    def test_handles_syntax_errors(self, temp_project):
        """Test that analyzer handles files with syntax errors gracefully"""
        # Create a file with syntax error
        with open(os.path.join(temp_project, "bad_syntax.py"), "w") as f:
            f.write("def broken(:\n  pass")

        analyzer = BlastRadiusAnalyzer(temp_project)

        # Should not raise, just skip the bad file
        analysis = analyzer.calculate_impact(["standalone/isolated.py"])
        assert analysis is not None


class TestBlastRadiusAnalyzerEdgeCases:
    """Edge case tests for BlastRadiusAnalyzer"""

    def test_empty_project(self):
        """Test analyzer with an empty project"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = BlastRadiusAnalyzer(tmpdir)
            analysis = analyzer.calculate_impact([])

            assert analysis.level == ImpactLevel.LOW
            assert analysis.incoming_deps == 0

    def test_nonexistent_file(self):
        """Test analyzing a non-existent file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = BlastRadiusAnalyzer(tmpdir)
            analysis = analyzer.calculate_impact(["nonexistent.py"])

            assert analysis.level == ImpactLevel.LOW
            assert analysis.incoming_deps == 0
