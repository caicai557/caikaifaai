import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from council.core.task_models import Task, TaskList, TaskStatus


class TaskManager:
    def __init__(self, project_root: str, filename: str = "tasks.json"):
        self.project_root = project_root
        self.file_path = os.path.join(project_root, filename)
        self.tasks: List[Task] = []
        self.next_id: int = 1
        self.load_tasks()

    def load_tasks(self):
        if not os.path.exists(self.file_path):
            self.tasks = []
            self.next_id = 1
            return

        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                task_list = TaskList(**data)
                self.tasks = task_list.tasks
                self.next_id = task_list.next_id
        except (json.JSONDecodeError, IOError) as e:
            # In a real app we might want to log this
            print(f"Warning: Error loading tasks from {self.file_path}: {e}")
            self.tasks = []
            self.next_id = 1

    def save_tasks(self):
        task_list = TaskList(tasks=self.tasks, next_id=self.next_id)
        with open(self.file_path, "w") as f:
            f.write(task_list.model_dump_json(indent=2))

    def add_task(
        self,
        title: str,
        description: str,
        dependencies: List[int] = None,
        priority: str = "medium",
    ) -> Task:
        now = datetime.now().isoformat()
        task = Task(
            id=self.next_id,
            title=title,
            description=description,
            dependencies=dependencies or [],
            priority=priority,
            created_at=now,
            updated_at=now,
        )
        self.tasks.append(task)
        self.next_id += 1
        self.save_tasks()
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def update_task_status(
        self, task_id: int, status: TaskStatus, result: Dict[str, Any] = None
    ) -> Optional[Task]:
        task = self.get_task(task_id)
        if task:
            task.status = status
            if result:
                task.result = result
            task.updated_at = datetime.now().isoformat()
            self.save_tasks()
        return task

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        if status:
            return [t for t in self.tasks if t.status == status]
        return self.tasks
