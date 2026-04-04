from datetime import datetime
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate
from typing import Optional, List

# Valid status transitions
VALID_TRANSITIONS = {
    TaskStatus.todo: [TaskStatus.in_progress],
    TaskStatus.in_progress: [TaskStatus.done, TaskStatus.todo],
    TaskStatus.done: [],
    TaskStatus.overdue: [TaskStatus.in_progress],
}

def get_task(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id).first()

def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    owner_id: Optional[int] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> List[Task]:
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if owner_id:
        query = query.filter(Task.owner_id == owner_id)
    if created_after:
        query = query.filter(Task.created_at >= created_after)
    if created_before:
        query = query.filter(Task.created_at <= created_before)
    return query.offset(skip).limit(limit).all()

def create_task(db: Session, task: TaskCreate) -> Task:
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        owner_id=task.owner_id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def validate_status_transition(current_status: TaskStatus, new_status: TaskStatus) -> bool:
    return new_status in VALID_TRANSITIONS.get(current_status, [])

def update_task(db: Session, db_task: Task, task_update: TaskUpdate) -> Task:
    if task_update.title is not None:
        db_task.title = task_update.title
    if task_update.description is not None:
        db_task.description = task_update.description
    if task_update.status is not None:
        if not validate_status_transition(db_task.status, task_update.status):
            raise ValueError(
                f"Invalid status transition from '{db_task.status.value}' to '{task_update.status.value}'"
            )
        db_task.status = task_update.status
    if task_update.priority is not None:
        db_task.priority = task_update.priority
    if task_update.owner_id is not None:
        db_task.owner_id = task_update.owner_id
    db.commit()
    db.refresh(db_task)
    return db_task

def assign_task(db: Session, db_task: Task, new_owner_id: int) -> Task:
    db_task.owner_id = new_owner_id
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, db_task: Task) -> None:
    db.delete(db_task)
    db.commit()
