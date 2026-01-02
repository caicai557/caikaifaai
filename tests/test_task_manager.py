import sys
from unittest.mock import MagicMock

# Mock litellm before importing council
sys.modules["litellm"] = MagicMock()

import os
import json
import pytest
from council.core.task_manager import TaskManager
from council.core.task_models import TaskStatus


@pytest.fixture
def temp_task_file(tmp_path):
    # Create a temporary directory and file path for tasks.json
    d = tmp_path / "council_test"
    d.mkdir()
    return str(d)


def test_add_task(temp_task_file):
    manager = TaskManager(temp_task_file)
    task = manager.add_task("Test Task", "Description", priority="high")

    assert task.id == 1
    assert task.title == "Test Task"
    assert task.status == TaskStatus.PENDING
    assert task.priority == "high"

    # Verify persistence
    manager2 = TaskManager(temp_task_file)
    assert len(manager2.tasks) == 1
    assert manager2.tasks[0].title == "Test Task"


def test_update_task_status(temp_task_file):
    manager = TaskManager(temp_task_file)
    task = manager.add_task("Test Task", "Description")

    updated_task = manager.update_task_status(
        task.id, TaskStatus.IN_PROGRESS, {"foo": "bar"}
    )

    assert updated_task.status == TaskStatus.IN_PROGRESS
    assert updated_task.result == {"foo": "bar"}

    # Verify persistence
    manager2 = TaskManager(temp_task_file)
    loaded_task = manager2.get_task(task.id)
    assert loaded_task.status == TaskStatus.IN_PROGRESS
    assert loaded_task.result == {"foo": "bar"}


def test_list_tasks(temp_task_file):
    manager = TaskManager(temp_task_file)
    manager.add_task("Task 1", "Desc 1")
    t2 = manager.add_task("Task 2", "Desc 2")
    manager.update_task_status(t2.id, TaskStatus.COMPLETED)

    all_tasks = manager.list_tasks()
    assert len(all_tasks) == 2

    completed_tasks = manager.list_tasks(status=TaskStatus.COMPLETED)
    assert len(completed_tasks) == 1
    assert completed_tasks[0].title == "Task 2"


def test_load_existing_tasks(temp_task_file):
    # Manually create a tasks.json file
    tasks_data = {
        "tasks": [
            {
                "id": 1,
                "title": "Existing Task",
                "description": "Desc",
                "status": "pending",
                "dependencies": [],
                "priority": "low",
            }
        ],
        "next_id": 2,
    }

    with open(os.path.join(temp_task_file, "tasks.json"), "w") as f:
        json.dump(tasks_data, f)

    manager = TaskManager(temp_task_file)
    assert len(manager.tasks) == 1
    assert manager.tasks[0].title == "Existing Task"
    assert manager.next_id == 2
