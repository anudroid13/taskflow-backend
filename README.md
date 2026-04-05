# taskflow-backend

# Smart Task Management Platform

## Overview
A scalable backend solution built in FastAPI for enterprise task management with role-based access control, performance tracking, and mobile integration.

## Project Goals
- Efficient task tracking through API endpoints
- Role-based access control (Admin, Manager, Employee)
- Productivity metrics and dashboard data
- Production-grade security (JWT authentication, input validation)
- Cloud readiness (Docker + PostgreSQL)

## Features
- Authentication (signup/login, JWT)
- Users CRUD with role management
- Task CRUD with status/priority/assignment
- Dashboard endpoints (task stats, overdue, metrics)
- File attachments to tasks
- Filters: status, date range, assigned user

## Non-functional requirements
- API response time < 300ms for standard queries
- Secure validation and error handling
- Scalable microservices-ready architecture
- Logging, monitoring, and observability

## Folder structure (recommended)
```
taskflow-backend/
  app/
    main.py
    api/
      v1/
        routers/
          auth.py
          users.py
          tasks.py
          dashboard.py
        dependencies.py
    core/
      config.py
      security.py
      logger.py
    models/
      user.py
      task.py
      attachment.py
    schemas/
      token.py
      user.py
      task.py
      dashboard.py
    crud/
      user.py
      task.py
      attachment.py
    db/
      base.py
      session.py
      init.py
    services/
      auth_service.py
      task_service.py
      analytics_service.py
    tests/
      test_auth.py
      test_users.py
      test_tasks.py
      test_dashboard.py
  Dockerfile
  docker-compose.yml
  requirements.txt
  README.md
```

## Quick setup
1. Create virtual env: `python -m venv .venv`
2. Activate: `source .venv/bin/activate`
3. Install: `pip install -r requirements.txt`
4. Run migrations (Alembic or custom scripts)
5. Start app: `uvicorn app.main:app --reload`

## API reference (high-level)
- POST `/auth/signup`
- POST `/auth/login`
- GET `/users/`
- POST `/tasks/`
- GET `/tasks/`
- PUT `/tasks/{id}`
- DELETE `/tasks/{id}`
- GET `/dashboard/summary`
- POST `/attachments/`

## Testing
- `pytest -q`

## Deployment
- Build Docker image
- Start `docker-compose up`
- Provision PostgreSQL
- Set env vars: `DATABASE_URL`, `SECRET_KEY`, `JWT_EXPIRE_MINUTES`

## Future enhancements
- Realtime updates (WebSocket)
- AI suggestions for task assignment and priorities
- Mobile push notifications
