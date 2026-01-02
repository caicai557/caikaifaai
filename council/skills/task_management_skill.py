from typing import Dict, Any, List, Optional
from council.skills.base_skill import BaseSkill
from council.core.task_manager import TaskManager
from council.core.task_models import TaskStatus


class TaskManagementSkill(BaseSkill):
    def __init__(self, task_manager: TaskManager):
        super().__init__(
            name="task_management",
            description="Manage project tasks: add, list, update, and complete tasks.",
        )
        self.task_manager = task_manager

    async def execute(self, task: str, **kwargs) -> Any:
        # This skill is primarily a collection of tools
        return {
            "message": "TaskManagementSkill provides tools for managing tasks. Use specific methods."
        }

    def add_task(
        self,
        title: str,
        description: str,
        dependencies: List[int] = None,
        priority: str = "medium",
    ) -> Dict[str, Any]:
        """Add a new task to the project."""
        task = self.task_manager.add_task(title, description, dependencies, priority)
        return task.model_dump()

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tasks, optionally filtered by status."""
        task_status = TaskStatus(status) if status else None
        tasks = self.task_manager.list_tasks(task_status)
        return [t.model_dump() for t in tasks]

    def update_task_status(
        self, task_id: int, status: str, result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Update the status of a task."""
        try:
            task_status = TaskStatus(status)
            task = self.task_manager.update_task_status(task_id, task_status, result)
            if task:
                return task.model_dump()
            return {"error": f"Task {task_id} not found"}
        except ValueError:
            return {"error": f"Invalid status: {status}"}

    def get_task(self, task_id: int) -> Dict[str, Any]:
        """Get details of a specific task."""
        task = self.task_manager.get_task(task_id)
        if task:
            return task.model_dump()
        return {"error": f"Task {task_id} not found"}
