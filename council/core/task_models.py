from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class Task(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[int] = Field(default_factory=list)
    priority: str = "medium"
    result: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TaskList(BaseModel):
    tasks: List[Task] = Field(default_factory=list)
    next_id: int = 1
