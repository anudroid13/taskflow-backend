from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.schemas.task import TaskRead, TaskCreate, TaskUpdate, TaskAssign
from app.crud import task as crud_task
from app.crud import user as crud_user
from app.db.session import get_db

from app.core.security import get_current_active_user, require_role
router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Employees can only create tasks owned by themselves
    if current_user.role.value == "employee" and task_in.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Employees can only create tasks for themselves")
    # Verify the target owner exists
    if not crud_user.get_user(db, task_in.owner_id):
        raise HTTPException(status_code=404, detail="Target owner not found")
    return crud_task.create_task(db, task_in)

@router.get("/", response_model=List[TaskRead])
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    owner_id: Optional[int] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return crud_task.get_tasks(
        db, skip=skip, limit=limit,
        status=status_filter, priority=priority,
        owner_id=owner_id,
        created_after=created_after, created_before=created_before,
    )

@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    db_task = crud_task.get_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    db_task = crud_task.get_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        return crud_task.update_task(db, db_task, task_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{task_id}/assign", response_model=TaskRead)
def assign_task(
    task_id: int,
    assignment: TaskAssign,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    db_task = crud_task.get_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud_user.get_user(db, assignment.owner_id):
        raise HTTPException(status_code=404, detail="Target owner not found")
    return crud_task.assign_task(db, db_task, assignment.owner_id)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    db_task = crud_task.get_task(db, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    crud_task.delete_task(db, db_task)
    return None
