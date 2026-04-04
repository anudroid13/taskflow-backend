from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User


def get_task_summary(db: Session) -> dict:
    total = db.query(func.count(Task.id)).scalar()
    todo = db.query(func.count(Task.id)).filter(Task.status == TaskStatus.todo).scalar()
    in_progress = db.query(func.count(Task.id)).filter(Task.status == TaskStatus.in_progress).scalar()
    done = db.query(func.count(Task.id)).filter(Task.status == TaskStatus.done).scalar()
    overdue = db.query(func.count(Task.id)).filter(Task.status == TaskStatus.overdue).scalar()
    return {
        "total": total,
        "todo": todo,
        "in_progress": in_progress,
        "done": done,
        "overdue": overdue,
    }


def get_completion_rate(db: Session) -> dict:
    total = db.query(func.count(Task.id)).scalar()
    done = db.query(func.count(Task.id)).filter(Task.status == TaskStatus.done).scalar()
    rate = round((done / total) * 100, 2) if total > 0 else 0.0
    return {"total": total, "done": done, "completion_rate": rate}


def get_tasks_by_priority(db: Session) -> dict:
    low = db.query(func.count(Task.id)).filter(Task.priority == TaskPriority.low).scalar()
    medium = db.query(func.count(Task.id)).filter(Task.priority == TaskPriority.medium).scalar()
    high = db.query(func.count(Task.id)).filter(Task.priority == TaskPriority.high).scalar()
    return {"low": low, "medium": medium, "high": high}


def get_tasks_by_user(db: Session) -> list:
    results = (
        db.query(User.id, User.full_name, User.email, func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.owner_id == User.id)
        .group_by(User.id, User.full_name, User.email)
        .all()
    )
    return [
        {"user_id": r.id, "full_name": r.full_name, "email": r.email, "task_count": r.task_count}
        for r in results
    ]


def get_date_range_metrics(
    db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> dict:
    query = db.query(Task)
    if start_date:
        query = query.filter(Task.created_at >= start_date)
    if end_date:
        query = query.filter(Task.created_at <= end_date)

    total = query.count()
    done = query.filter(Task.status == TaskStatus.done).count()
    overdue = query.filter(Task.status == TaskStatus.overdue).count()
    return {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "total": total,
        "done": done,
        "overdue": overdue,
    }
