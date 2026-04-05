from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from enum import Enum

class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    overdue = "overdue"

class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium

class TaskCreate(TaskBase):
    owner_id: int

    @field_validator("status")
    @classmethod
    def block_overdue_on_create(cls, v):
        if v == TaskStatus.overdue:
            raise ValueError("Cannot create a task with 'overdue' status")
        return v

class TaskRead(TaskBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    owner_id: Optional[int] = None

class TaskAssign(BaseModel):
    owner_id: int
