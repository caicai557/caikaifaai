"""Test Project Memory - CLAUDE.md style project context"""

import sys
from unittest.mock import MagicMock
import os
import tempfile
import shutil

# Mock litellm before any council imports
sys.modules["litellm"] = MagicMock()
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.memory.project_memory import ProjectMemory, ProjectConfig


@pytest.fixture
def temp_project():
    """Create temporary project with config files"""
    d = tempfile.mkdtemp()

    # Create CLAUDE.md
    claude_md = """# TestProject

This is a test project for council.

## Style Guide
- Use type hints everywhere
- Follow PEP 8
- Use descriptive variable names

## Caveats
- Do not modify the database directly
- Always use transactions
- Check for null values

## Dependencies
- Python 3.12+
- FastAPI
- Pydantic
"""
    (Path(d) / "CLAUDE.md").write_text(claude_md)

    # Create README.md
    readme = "# My Test Project\n\nA sample project."
    (Path(d) / "README.md").write_text(readme)

    # Create workflow directory
    workflow_dir = Path(d) / ".agent" / "workflows"
    workflow_dir.mkdir(parents=True)

    # Create a workflow
    workflow = """---
description: Run tests
---
1. Run pytest
2. Check coverage
"""
    (workflow_dir / "test.md").write_text(workflow)

    yield d
    shutil.rmtree(d, ignore_errors=True)


from pathlib import Path


class TestProjectMemory:
    """Test ProjectMemory functionality"""

    def test_load_claude_md(self, temp_project):
        """Test loading CLAUDE.md"""
        memory = ProjectMemory(temp_project)

        assert memory.config.name == "TestProject"
        assert "CLAUDE.md" in memory.config.raw_configs

    def test_parse_style_guide(self, temp_project):
        """Test parsing style guide from CLAUDE.md"""
        memory = ProjectMemory(temp_project)

        style = memory.get_style_guide()
        assert "type hints" in style
        assert "PEP 8" in style

    def test_parse_caveats(self, temp_project):
        """Test parsing caveats from CLAUDE.md"""
        memory = ProjectMemory(temp_project)

        caveats = memory.get_caveats()
        assert len(caveats) >= 2
        assert any("database" in c.lower() for c in caveats)

    def test_load_workflows(self, temp_project):
        """Test loading workflow commands"""
        memory = ProjectMemory(temp_project)

        commands = memory.get_custom_commands()
        assert "test" in commands
        assert "pytest" in commands["test"]

    def test_get_command(self, temp_project):
        """Test getting specific command"""
        memory = ProjectMemory(temp_project)

        cmd = memory.get_command("test")
        assert cmd is not None
        assert "pytest" in cmd

        # Non-existent command
        assert memory.get_command("nonexistent") is None

    def test_get_context(self, temp_project):
        """Test getting formatted context"""
        memory = ProjectMemory(temp_project)

        context = memory.get_context()
        assert "TestProject" in context
        assert "代码风格" in context or "Style" in context

    def test_get_context_max_chars(self, temp_project):
        """Test context truncation"""
        memory = ProjectMemory(temp_project)

        context = memory.get_context(max_chars=100)
        assert len(context) <= 150  # Allow some margin for truncation message

    def test_has_config(self, temp_project):
        """Test config file existence check"""
        memory = ProjectMemory(temp_project)

        assert memory.has_config("CLAUDE.md")
        assert memory.has_config("README.md")
        assert not memory.has_config("NONEXISTENT.md")

    def test_get_raw_config(self, temp_project):
        """Test getting raw config content"""
        memory = ProjectMemory(temp_project)

        raw = memory.get_raw_config("CLAUDE.md")
        assert raw is not None
        assert "TestProject" in raw

    def test_get_stats(self, temp_project):
        """Test statistics"""
        memory = ProjectMemory(temp_project)

        stats = memory.get_stats()
        assert stats["project_name"] == "TestProject"
        assert stats["config_files_loaded"] >= 2
        assert stats["custom_commands"] >= 1
        assert stats["has_style_guide"] is True


class TestProjectMemoryEmpty:
    """Test ProjectMemory with empty/missing config"""

    def test_empty_project(self):
        """Test with no config files"""
        with tempfile.TemporaryDirectory() as d:
            memory = ProjectMemory(d)

            assert memory.config.name == ""
            assert memory.get_context() == ""
            assert memory.get_custom_commands() == {}

    def test_readme_only(self):
        """Test with only README.md"""
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "README.md").write_text("# Simple Project\n\nDescription.")

            memory = ProjectMemory(d)

            assert memory.config.name == "Simple Project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
