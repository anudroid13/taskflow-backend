from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from app.models.task import TaskStatus, TaskPriority

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
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    owner_id: Optional[int] = None

class TaskAssign(BaseModel):
    owner_id: int
