import sys
from unittest.mock import MagicMock
import os

# Mock litellm before importing council
sys.modules["litellm"] = MagicMock()

# Set dummy API key to avoid BaseAgent init warning/error
os.environ["OPENAI_API_KEY"] = "dummy"

import pytest
from council.core.task_manager import TaskManager
from council.skills.task_management_skill import TaskManagementSkill
from council.agents.orchestrator import Orchestrator


@pytest.fixture
def temp_task_file(tmp_path):
    d = tmp_path / "council_skill_test"
    d.mkdir()
    return str(d)


def test_skill_add_task(temp_task_file):
    manager = TaskManager(temp_task_file)
    skill = TaskManagementSkill(manager)

    result = skill.add_task("Skill Task", "Desc")
    assert result["title"] == "Skill Task"
    assert result["id"] == 1

    tasks = skill.list_tasks()
    assert len(tasks) == 1


def test_skill_update_status(temp_task_file):
    manager = TaskManager(temp_task_file)
    skill = TaskManagementSkill(manager)
    task = skill.add_task("Task", "Desc")

    updated = skill.update_task_status(task["id"], "in-progress")
    assert updated["status"] == "in-progress"


def test_orchestrator_integration(temp_task_file):
    orchestrator = Orchestrator(model="test-model")
    # Swap manager to use temp file
    orchestrator.task_manager = TaskManager(temp_task_file)
    orchestrator.task_skill = TaskManagementSkill(orchestrator.task_manager)

    # Test decompose logic
    # "Refactor the login page" should trigger Architect and Coder
    result = orchestrator.decompose("Refactor the login page")

    # Check if tasks were created in the manager
    tasks = orchestrator.task_manager.list_tasks()
    assert len(tasks) > 0

    # Verify at least one task description matches the goal
    found = False
    for t in tasks:
        if "Refactor" in t.title or "Refactor" in t.description:
            found = True
            break
    assert found
