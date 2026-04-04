from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.db.session import get_db
from app.core.security import get_current_active_user, require_role
from app.services import analytics_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def task_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return analytics_service.get_task_summary(db)


@router.get("/completion-rate")
def completion_rate(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return analytics_service.get_completion_rate(db)


@router.get("/by-priority")
def tasks_by_priority(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return analytics_service.get_tasks_by_priority(db)


@router.get("/by-user")
def tasks_by_user(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "manager"])),
):
    return analytics_service.get_tasks_by_user(db)


@router.get("/date-range")
def date_range_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return analytics_service.get_date_range_metrics(db, start_date, end_date)
