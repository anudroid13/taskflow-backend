# Backend Development Flow

## Architecture Overview

### File Tree
```
app/
├── main.py                          # FastAPI entry, CORS, router registration, health check
├── core/
│   ├── config.py                    # Settings class (SECRET_KEY, JWT, CORS from env)
│   └── security.py                  # JWT create/decode, authenticate_user, RBAC guards
├── db/
│   ├── base.py                      # SQLAlchemy DeclarativeBase + model registration
│   └── session.py                   # Engine, SessionLocal, get_db() dependency
├── models/
│   ├── user.py                      # User model + UserRole enum (admin|manager|employee)
│   ├── task.py                      # Task model + TaskStatus/TaskPriority enums
│   └── attachment.py                # Attachment model (file metadata)
├── schemas/
│   ├── user.py                      # UserCreate, UserSignup, UserRead, UserUpdate, LoginRequest
│   ├── task.py                      # TaskCreate, TaskRead, TaskUpdate, TaskAssign
│   └── attachment.py                # AttachmentCreate, AttachmentRead, AttachmentUpdate
├── crud/
│   ├── user.py                      # User DB ops + bcrypt hash/verify
│   ├── task.py                      # Task DB ops + status transition validation
│   └── attachment.py                # Attachment DB ops
├── api/v1/routers/
│   ├── auth.py                      # POST /auth/signup, POST /auth/login + rate limiter
│   ├── user.py                      # /users CRUD (admin/manager gated)
│   ├── tasks.py                     # /tasks CRUD + /tasks/{id}/assign
│   ├── attachment.py                # /attachments CRUD + /attachments/upload (10MB limit)
│   └── dashboard.py                 # /dashboard analytics (5 endpoints)
├── services/
│   └── analytics_service.py         # Dashboard aggregation queries (summary, rates, charts)
└── tests/
    ├── conftest.py                  # SQLite test DB, user fixtures, token helpers
    ├── test_auth.py                 # 6 tests
    ├── test_users.py                # 15 tests
    ├── test_tasks.py                # 16 tests
    ├── test_attachments.py          # 11 tests
    ├── test_dashboard.py            # 11 tests
    ├── test_edge_cases.py           # 16 tests (JWT, pagination, upload, validation)
    └── test_stress.py               # 4 stress tests (1000+ records)
```

### Request Flow
```
HTTP Request
     │
     ▼
┌──────────────────────────────────────────┐
│  Router (api/v1/routers/)                │
│  Endpoint handler receives the request   │
│  FastAPI dependency injection kicks in:  │
│    • get_db() → DB session               │
│    • get_current_active_user() → auth    │
│    • require_role([...]) → RBAC check    │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│  Schema Validation (schemas/)            │
│  Pydantic validates request body         │
│  Field validators enforce rules          │
│  (e.g. password >= 8 chars, no overdue)  │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│  CRUD Layer (crud/)                      │
│  Business logic + DB operations          │
│  Status transitions, password hashing    │
│  Returns ORM model instances             │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│  Model Layer (models/)                   │
│  SQLAlchemy ORM ↔ PostgreSQL tables      │
│  Relationships: User→Tasks→Attachments   │
│  Cascade deletes on parent removal       │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│  Response Serialization                  │
│  ORM model → Pydantic Read schema → JSON │
└──────────────────────────────────────────┘
```

### Authentication & RBAC
```
Login:  POST /auth/login {email, password}
        → bcrypt verify → JWT encode {sub: user_id, exp: 60min}
        → {access_token, token_type: "bearer"}

Auth:   Authorization: Bearer <token>
        → jwt.decode → user_id → DB lookup → User object
        → check is_active → inject into endpoint

RBAC:   require_role(["admin", "manager"])
        → calls get_current_active_user() first
        → checks user.role against allowed list
        → 403 if denied

Roles:
  admin    → full CRUD on users, tasks, attachments + dashboard/by-user
  manager  → update/assign tasks, list users, dashboard/by-user
  employee → create own tasks, update own status, view dashboard
```

### Data Model Relationships
```
User (1) ──→ (N) Task (1) ──→ (N) Attachment
  │                                    ▲
  └────────────────────────────────────┘
           User (1) ──→ (N) Attachment

All relationships cascade: deleting a User removes their Tasks and Attachments.
Deleting a Task removes its Attachments.
```

---

## Phase 1: Architecture and Setup
1. Initialize project folder and virtual environment.
2. Create FastAPI app (app/main.py).
3. Setup PostgreSQL DB and SQLAlchemy session config (`app/db/session.py`).
4. Define base models in `app/db/base.py`.
5. Create user/task/attachment models (`app/models/`).
6. Add Pydantic schemas in `app/schemas/`.
7. Add core config and security (`app/core/`).

## Phase 2: Authentication + RBAC
1. Implement JWT utils in `app/core/security.py`.
2. Build `auth` router and services.
3. Implement `signup` and `login` endpoints.
4. Add role checks (Admin/Manager/Employee).
5. Add dependency for current user and role guard.

## Phase 3: Users API
1. Create `app/crud/user.py` with functions create/get/update/delete.
2. Add user router (`app/api/v1/routers/users.py`).
3. Support listing, filtering by role/email.
4. Add role-based access: Admin only for create/delete; Manager limited.

## Phase 4: Tasks API
1. Create `app/crud/task.py` for task operations.
2. Add task router (`app/api/v1/routers/tasks.py`).
3. Define status/priority constants and update flows.
4. Add assignment and status transition logic.
5. Implement task filters: status/date/user/priority.
6. Add attachments support, file upload endpoint.

## Phase 5: Dashboard + Metrics
1. Add analytics service `app/services/analytics_service.py`.
2. Add dashboard router (`app/api/v1/routers/dashboard.py`).
3. Implement endpoints: total tasks, overdue, completion rate.
4. Add paginated reports and date-range metrics.

## Phase 6: Testing and Validation
1. Add pytest tests in `app/tests`.
2. Test auth, users, tasks, dashboard.
3. Add error handling and response models.
4. Test RBAC and invalid inputs.

## Phase 7: Deployment
1. Add `Dockerfile`, `docker-compose.yml`.
2. Add env var docs and sample `.env.example`.
3. Configure health checks and logging.
4. stress test with 1000+ record simulation.

## Recommended folder structure
```
app/
  api/v1/routers/
  core/
  models/
  schemas/
  crud/
  db/
  services/
  tests/
Dockerfile
docker-compose.yml
requirements.txt
```