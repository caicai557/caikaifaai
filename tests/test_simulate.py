#!/usr/bin/env python3
"""
TDD Tests for Pre-Flight Simulator (Predictive Healing / Digital Twin).

Acceptance Criteria:
- AC3: scripts/simulate.py 能够预检测依赖冲突
- AC5: just verify 全部通过
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSimulatePlanBasic:
    """Basic tests for simulate_plan function."""

    def test_simulate_plan_import(self):
        """Test simulate_plan can be imported."""
        from scripts.simulate import simulate_plan

        assert callable(simulate_plan)

    def test_simulate_empty_plan_returns_no_warnings(self):
        """Test empty plan produces no warnings."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        warnings = simulate_plan([], kg)

        assert warnings == []

    def test_simulate_safe_plan_returns_no_warnings(self):
        """Test plan without risky operations returns no warnings."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph()
        plan = [
            "Create new file src/utils.py",
            "Add function parse_config",
            "Update README.md",
        ]
        warnings = simulate_plan(plan, kg)

        assert warnings == []


class TestSimulatePlanDeleteDetection:
    """Tests for detecting delete operation conflicts."""

    def test_detect_delete_with_dependency(self):
        """Test warning when deleting a file that others depend on."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import (
            EntityType,
            KnowledgeGraph,
            RelationType,
        )

        kg = KnowledgeGraph()

        # Setup: file_b depends on file_a
        kg.add_entity("file_a", EntityType.FILE, "src/utils.py")
        kg.add_entity("file_b", EntityType.FILE, "src/main.py")
        kg.add_relation("file_b", "file_a", RelationType.DEPENDS_ON)

        plan = ["Delete file src/utils.py"]
        warnings = simulate_plan(plan, kg)

        assert len(warnings) >= 1
        assert any("utils.py" in w or "file_a" in w for w in warnings)

    def test_no_warning_when_delete_has_no_dependents(self):
        """Test no warning when deleted file has no dependents."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import KnowledgeGraph, EntityType

        kg = KnowledgeGraph()

        # Setup: orphan file with no dependents
        kg.add_entity("orphan", EntityType.FILE, "src/unused.py")

        plan = ["Delete file src/unused.py"]
        warnings = simulate_plan(plan, kg)

        assert len(warnings) == 0

    def test_detect_rm_command(self):
        """Test detection of 'rm' command as delete operation."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import (
            EntityType,
            KnowledgeGraph,
            RelationType,
        )

        kg = KnowledgeGraph()

        kg.add_entity("config", EntityType.FILE, "config.yaml")
        kg.add_entity("app", EntityType.FILE, "app.py")
        kg.add_relation("app", "config", RelationType.DEPENDS_ON)

        plan = ["rm config.yaml"]
        warnings = simulate_plan(plan, kg)

        assert len(warnings) >= 1

    def test_detect_remove_keyword(self):
        """Test detection of 'remove' keyword as delete operation."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import (
            EntityType,
            KnowledgeGraph,
            RelationType,
        )

        kg = KnowledgeGraph()

        kg.add_entity("module", EntityType.FILE, "module.py")
        kg.add_entity("test", EntityType.FILE, "test_module.py")
        kg.add_relation("test", "module", RelationType.DEPENDS_ON)

        plan = ["Remove module.py from codebase"]
        warnings = simulate_plan(plan, kg)

        assert len(warnings) >= 1


class TestSimulatePlanMultipleSteps:
    """Tests for multi-step plan simulation."""

    def test_multiple_risky_operations(self):
        """Test plan with multiple risky operations returns multiple warnings."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import (
            EntityType,
            KnowledgeGraph,
            RelationType,
        )

        kg = KnowledgeGraph()

        # Setup dependency chain
        kg.add_entity("base", EntityType.FILE, "base.py")
        kg.add_entity("utils", EntityType.FILE, "utils.py")
        kg.add_entity("app", EntityType.FILE, "app.py")
        kg.add_relation("utils", "base", RelationType.DEPENDS_ON)
        kg.add_relation("app", "utils", RelationType.DEPENDS_ON)

        plan = [
            "Delete base.py",
            "Delete utils.py",
        ]
        warnings = simulate_plan(plan, kg)

        assert len(warnings) >= 2

    def test_mixed_safe_and_risky_operations(self):
        """Test plan with mixed operations only warns for risky ones."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import (
            EntityType,
            KnowledgeGraph,
            RelationType,
        )

        kg = KnowledgeGraph()

        kg.add_entity("core", EntityType.FILE, "core.py")
        kg.add_entity("feature", EntityType.FILE, "feature.py")
        kg.add_relation("feature", "core", RelationType.DEPENDS_ON)

        plan = [
            "Add new function to feature.py",
            "Delete core.py",  # This is risky
            "Update documentation",
        ]
        warnings = simulate_plan(plan, kg)

        assert len(warnings) == 1
        assert any("core" in w for w in warnings)


class TestSimulatePlanExtraction:
    """Tests for target extraction from plan steps."""

    def test_extract_target_from_delete_statement(self):
        """Test extracting file path from delete statement."""
        from scripts.simulate import extract_target

        target = extract_target("Delete file src/config.py")
        assert "config" in target or "src/config.py" in target

    def test_extract_target_from_rm_command(self):
        """Test extracting file path from rm command."""
        from scripts.simulate import extract_target

        target = extract_target("rm -rf build/")
        assert "build" in target

    def test_extract_target_handles_quotes(self):
        """Test extracting target from quoted paths."""
        from scripts.simulate import extract_target

        target = extract_target('Delete "src/my file.py"')
        assert "my file" in target or "src/my file.py" in target


class TestSimulatePlanWarningFormat:
    """Tests for warning message format."""

    def test_warning_contains_target_info(self):
        """Test warning message includes the target being deleted."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import (
            EntityType,
            KnowledgeGraph,
            RelationType,
        )

        kg = KnowledgeGraph()

        kg.add_entity("important", EntityType.FILE, "important.py")
        kg.add_entity("dependent", EntityType.FILE, "dependent.py")
        kg.add_relation("dependent", "important", RelationType.DEPENDS_ON)

        plan = ["Delete important.py"]
        warnings = simulate_plan(plan, kg)

        assert len(warnings) == 1
        # Warning should mention what's being deleted
        assert "important" in warnings[0].lower()

    def test_warning_contains_dependent_info(self):
        """Test warning message includes what depends on the target."""
        from scripts.simulate import simulate_plan
        from council.memory.knowledge_graph import (
            EntityType,
            KnowledgeGraph,
            RelationType,
        )

        kg = KnowledgeGraph()

        kg.add_entity("lib", EntityType.FILE, "lib.py")
        kg.add_entity("consumer", EntityType.FILE, "consumer.py")
        kg.add_relation("consumer", "lib", RelationType.DEPENDS_ON)

        plan = ["Delete lib.py"]
        warnings = simulate_plan(plan, kg)

        assert len(warnings) == 1
        # Warning should mention what will break
        assert "consumer" in warnings[0].lower() or "dependent" in warnings[0].lower()
