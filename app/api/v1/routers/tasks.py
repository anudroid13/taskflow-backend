from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.schemas.task import TaskRead, TaskCreate, TaskUpdate
from app.crud import task as crud_task
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.core.security import get_current_active_user, require_role
router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Optionally, you can restrict creation to certain roles
    return crud_task.create_task(db, task_in)

@router.get("/", response_model=List[TaskRead])
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return crud_task.get_tasks(db, skip=skip, limit=limit)

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
    return crud_task.update_task(db, db_task, task_update)

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
