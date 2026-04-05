# Low-Level Design (LLD) — TaskFlow Backend

## 1. Module Dependency Graph

```
main.py
 ├── core/config.py          (settings)
 ├── db/base.py              (Base ORM registry)
 ├── db/session.py           (engine, get_db)
 └── api/v1/routers/
      ├── auth.py            → crud/user.py, core/security.py, schemas/user.py
      ├── user.py            → crud/user.py, core/security.py, schemas/user.py
      ├── tasks.py           → crud/task.py, crud/user.py, core/security.py, schemas/task.py
      ├── attachment.py      → crud/attachment.py, crud/task.py, core/security.py, schemas/attachment.py
      └── dashboard.py       → services/analytics_service.py, core/security.py

core/security.py             → core/config.py, models/user.py, crud/user.py, db/session.py
crud/user.py                 → models/user.py, schemas/user.py, passlib
crud/task.py                 → models/task.py, schemas/task.py
crud/attachment.py           → models/attachment.py, schemas/attachment.py
services/analytics_service.py → models/task.py, models/user.py
db/base.py                   → models/user.py, models/task.py, models/attachment.py
schemas/user.py              → models/user.py (UserRole enum)
schemas/task.py              → models/task.py (TaskStatus, TaskPriority enums)
```

---

## 2. Database Schema (DDL-Level)

### 2.1 `users` Table
```sql
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR NOT NULL UNIQUE,
    hashed_password VARCHAR NOT NULL,
    full_name   VARCHAR,
    is_active   BOOLEAN DEFAULT TRUE,
    role        VARCHAR NOT NULL DEFAULT 'employee',  -- ENUM: admin | manager | employee
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_email ON users (email);
```

### 2.2 `tasks` Table
```sql
CREATE TABLE tasks (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR NOT NULL,
    description VARCHAR,
    status      VARCHAR NOT NULL DEFAULT 'todo',      -- ENUM: todo | in_progress | done | overdue
    priority    VARCHAR NOT NULL DEFAULT 'medium',     -- ENUM: low | medium | high
    owner_id    INTEGER NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_tasks_id ON tasks (id);
```

### 2.3 `attachments` Table
```sql
CREATE TABLE attachments (
    id          SERIAL PRIMARY KEY,
    filename    VARCHAR NOT NULL,
    url         VARCHAR NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    uploader_id INTEGER NOT NULL REFERENCES users(id),
    task_id     INTEGER NOT NULL REFERENCES tasks(id)
);

CREATE INDEX ix_attachments_id ON attachments (id);
```

### 2.4 Cascade Rules
```
ON DELETE users.id  → DELETE all tasks WHERE owner_id = users.id
                    → DELETE all attachments WHERE uploader_id = users.id
ON DELETE tasks.id  → DELETE all attachments WHERE task_id = tasks.id
```

---

## 3. Enum Definitions

### 3.1 UserRole (models/user.py)
```python
class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"
```

### 3.2 TaskStatus (models/task.py)
```python
class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    overdue = "overdue"
```

### 3.3 TaskPriority (models/task.py)
```python
class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
```

Enums defined in `models/` and re-imported in `schemas/` (single source of truth).

---

## 4. API Endpoint Specifications

### 4.1 Auth Router (`/auth`)

#### `POST /auth/signup`
```
Request:  { email: EmailStr, password: str (>=8), full_name?: str }
Response: 201 → { id, email, full_name, role, is_active }
Errors:   400 → "Email already registered"
          422 → validation error (short password, invalid email)
Logic:
  1. Check duplicate email via crud.get_user_by_email()
  2. Hash password with bcrypt
  3. Create user with role=employee (hardcoded for signup)
  4. Return UserRead
```

#### `POST /auth/login`
```
Request:  { email: EmailStr, password: str }
Response: 200 → { access_token: str, token_type: "bearer" }
Errors:   401 → "Incorrect email or password"
          429 → "Too many login attempts. Try again later."
Logic:
  1. Rate limit check: _login_attempts[client_ip] <= 5 in 300s window
  2. Query user by email
  3. bcrypt.verify(password, hashed_password)
  4. jwt.encode({ sub: str(user.id), exp: now+60min }, SECRET_KEY, HS256)
```

### 4.2 User Router (`/users`)

#### `POST /users/` — Admin only
```
Request:  { email, password (>=8), full_name?, role?, is_active? }
Response: 201 → UserRead
Auth:     require_role(["admin"])
```

#### `GET /users/` — Admin, Manager
```
Query:    ?skip=0&limit=100&role=admin&email=search
Response: 200 → [UserRead, ...]
Auth:     require_role(["admin", "manager"])
Logic:    role → exact match, email → ILIKE %search%
```

#### `GET /users/{user_id}` — Any authenticated
```
Response: 200 → UserRead | 404
Auth:     get_current_active_user
```

#### `PUT /users/{user_id}` — Admin only
```
Request:  { full_name?, password?, role?, is_active? }  (all optional)
Response: 200 → UserRead | 404
Auth:     require_role(["admin"])
Logic:    If password provided, re-hash with bcrypt
```

#### `DELETE /users/{user_id}` — Admin only
```
Response: 204 (no content) | 404
Auth:     require_role(["admin"])
Logic:    Cascade deletes user's tasks and attachments
```

### 4.3 Task Router (`/tasks`)

#### `POST /tasks/`
```
Request:  { title, description?, status?=todo, priority?=medium, owner_id }
Response: 201 → TaskRead
Auth:     get_current_active_user
Errors:   403 → employee creating for another user
          404 → target owner not found
          422 → status="overdue" blocked on create
Logic:
  1. If employee: assert owner_id == current_user.id
  2. Verify owner exists: crud.get_user(owner_id)
  3. Create task via crud.create_task()
```

#### `GET /tasks/`
```
Query:    ?skip=0&limit=100&status_filter=todo&priority=high&owner_id=1
          &created_after=2025-01-01T00:00:00&created_before=2025-12-31T23:59:59
Response: 200 → [TaskRead, ...]
Auth:     get_current_active_user
Logic:    Chain .filter() for each non-null param, .offset(skip).limit(limit)
```

#### `GET /tasks/{task_id}`
```
Response: 200 → TaskRead | 404
Auth:     get_current_active_user
```

#### `PUT /tasks/{task_id}` — Admin, Manager
```
Request:  { title?, description?, status?, priority?, owner_id? }
Response: 200 → TaskRead | 400 (invalid transition) | 404
Auth:     require_role(["admin", "manager"])
```

#### `PATCH /tasks/{task_id}/assign` — Admin, Manager
```
Request:  { owner_id: int }
Response: 200 → TaskRead | 404 (task or owner not found)
Auth:     require_role(["admin", "manager"])
```

#### `DELETE /tasks/{task_id}` — Admin only
```
Response: 204 | 404
Auth:     require_role(["admin"])
Logic:    Cascade deletes task's attachments
```

### 4.4 Attachment Router (`/attachments`)

#### `POST /attachments/upload`
```
Request:  multipart/form-data { file: UploadFile, task_id: int }
Response: 201 → AttachmentRead
Auth:     get_current_active_user
Errors:   404 → task not found, 413 → file > 10MB
Logic:
  1. Validate task exists
  2. Read file in 1MB chunks, accumulate, check <= 10MB
  3. Save as uploads/{uuid4_hex}{ext}
  4. Insert attachment row (uploader_id = current_user.id)
```

#### `POST /attachments/` (metadata only)
```
Request:  { filename, url, task_id }
Response: 201 → AttachmentRead
Auth:     get_current_active_user
Logic:    uploader_id forced from current_user.id (prevents mass assignment)
```

#### `GET /attachments/`
```
Query:    ?skip=0&limit=100
Response: 200 → [AttachmentRead, ...]
```

#### `GET /attachments/{id}`
```
Response: 200 → AttachmentRead | 404
```

#### `PUT /attachments/{id}` — Admin, Manager
```
Request:  { filename?: str }
Response: 200 → AttachmentRead | 404
```

#### `DELETE /attachments/{id}` — Admin only
```
Response: 204 | 404
Logic:    Delete file from disk (if exists) + delete DB row
```

### 4.5 Dashboard Router (`/dashboard`)

#### `GET /dashboard/summary`
```
Response: { total, todo, in_progress, done, overdue }
Query:    5 separate COUNT queries on tasks table
```

#### `GET /dashboard/completion-rate`
```
Response: { total, done, completion_rate }
Logic:    rate = round((done / total) * 100, 2) or 0.0 if empty
```

#### `GET /dashboard/by-priority`
```
Response: { low, medium, high }
```

#### `GET /dashboard/by-user` — Admin, Manager
```
Response: [{ user_id, full_name, email, task_count }, ...]
Query:    LEFT OUTER JOIN tasks on users, GROUP BY user, COUNT(task.id)
```

#### `GET /dashboard/date-range`
```
Query:    ?start_date=2025-01-01T00:00:00&end_date=2025-06-30T00:00:00
Response: { total, todo, in_progress, done, overdue }
Logic:    Filter Task.created_at by date range, then count by status
```

---

## 5. Task Status State Machine

```
            ┌──────────┐
            │   todo   │
            └────┬─────┘
                 │
                 ▼
            ┌──────────┐
     ┌──────│in_progress│──────┐
     │      └──────────┘      │
     │                        │
     ▼                        ▼
┌──────────┐           ┌──────────┐
│   todo   │           │   done   │
│ (revert) │           │(terminal)│
└──────────┘           └──────────┘

┌──────────┐
│ overdue  │───────→ in_progress
│(sys-set) │
└──────────┘
```

### Transition Table
| From | Allowed To | Blocked |
|------|-----------|---------|
| `todo` | `in_progress` | done, overdue |
| `in_progress` | `done`, `todo` | overdue |
| `done` | — (terminal) | all |
| `overdue` | `in_progress` | todo, done |

Enforced in: `crud/task.py → VALID_TRANSITIONS dict + validate_status_transition()`

---

## 6. Authentication & Security Details

### 6.1 JWT Token Structure
```json
Header:  { "alg": "HS256", "typ": "JWT" }
Payload: { "sub": "42", "exp": 1712345678 }
         sub = str(user.id), exp = now_utc + 60 minutes
Signed:  HMACSHA256(header.payload, SECRET_KEY)
```

### 6.2 Token Validation Chain
```
OAuth2PasswordBearer(tokenUrl="/auth/login")
    │
    ▼
get_current_user(token, db)
    ├── jwt.decode(token, SECRET_KEY, [ALGORITHM])
    ├── Extract sub → int(sub) → user_id
    ├── Query: User.filter(id == user_id).first()
    └── Return User or raise 401
    │
    ▼
get_current_active_user(user)
    ├── Check user.is_active == True
    └── Return User or raise 400
    │
    ▼
require_role(["admin", "manager"])(user)
    ├── Check user.role in required_roles
    └── Return User or raise 403
```

### 6.3 Password Security
```
Hash:   passlib.CryptContext(schemes=["bcrypt"]).hash(password)
Verify: passlib.CryptContext(schemes=["bcrypt"]).verify(plain, hashed)
Rules:  Minimum 8 characters (enforced in Pydantic field_validator)
```

### 6.4 Rate Limiter (Login)
```python
_login_attempts: dict[str, list[float]]  # IP → [timestamps]

On each login attempt:
  1. Periodic sweep: remove IPs with all timestamps > 300s old (every 60s)
  2. Filter current IP's list: keep only timestamps within 300s window
  3. If count >= 5: raise HTTP 429
  4. Append current timestamp
```

---

## 7. CRUD Layer Function Signatures

### 7.1 user.py
```python
get_password_hash(password: str) → str                        # bcrypt hash
verify_password(plain: str, hashed: str) → bool               # bcrypt verify
get_user(db, user_id: int) → Optional[User]                   # by PK
get_user_by_email(db, email: str) → Optional[User]            # by unique email
get_users(db, skip, limit, role?, email?) → List[User]        # filtered list
create_user(db, user: UserCreate) → User                      # hash + insert
update_user(db, db_user: User, update: UserUpdate) → User     # partial update
delete_user(db, db_user: User) → None                         # cascade delete
```

### 7.2 task.py
```python
VALID_TRANSITIONS: dict[TaskStatus, list[TaskStatus]]         # state machine
get_task(db, task_id: int) → Optional[Task]                   # by PK
get_tasks(db, skip, limit, status?, priority?,                # filtered list
          owner_id?, created_after?, created_before?) → List[Task]
create_task(db, task: TaskCreate) → Task                      # insert
validate_status_transition(current, new) → bool               # check allowed
update_task(db, db_task, update: TaskUpdate) → Task           # partial + transition check
assign_task(db, db_task, new_owner_id: int) → Task            # change owner_id
delete_task(db, db_task: Task) → None                         # cascade delete
```

### 7.3 attachment.py
```python
create_attachment(db, att: AttachmentCreate) → Attachment      # insert
get_attachment(db, attachment_id: int) → Attachment             # by PK
get_attachments(db, skip, limit) → List[Attachment]            # paginated list
update_attachment(db, db_att, update: AttachmentUpdate) → Attachment  # partial
delete_attachment(db, attachment: Attachment) → None            # delete row
```

---

## 8. Pydantic Schema Definitions

### 8.1 User Schemas
```
UserBase       { email: EmailStr, full_name?: str, role: UserRole, is_active: bool }
UserCreate     extends UserBase + password: str (>=8)
UserSignup     { email: EmailStr, password: str (>=8), full_name?: str }
LoginRequest   { email: EmailStr, password: str }
UserRead       extends UserBase + id: int          [ConfigDict(from_attributes=True)]
UserUpdate     { full_name?, password? (>=8), role?, is_active? }
```

### 8.2 Task Schemas
```
TaskBase       { title: str, description?: str, status: TaskStatus, priority: TaskPriority }
TaskCreate     extends TaskBase + owner_id: int    [validator: status != overdue]
TaskRead       extends TaskBase + id, owner_id     [ConfigDict(from_attributes=True)]
TaskUpdate     { title?, description?, status?, priority?, owner_id? }
TaskAssign     { owner_id: int }
```

### 8.3 Attachment Schemas
```
AttachmentBase          { filename: str, url: str }
AttachmentCreate        extends AttachmentBase + uploader_id: int, task_id: int  (internal)
AttachmentCreateRequest { filename: str, url: str, task_id: int }               (user-facing)
AttachmentUpdate        { filename?: str }
AttachmentRead          extends AttachmentBase + id, uploader_id, task_id       [ConfigDict(from_attributes=True)]
```

---

## 9. Service Layer (Analytics)

### analytics_service.py — 5 Functions

```python
get_task_summary(db) → dict
    # 5 COUNT queries: total, todo, in_progress, done, overdue

get_completion_rate(db) → dict
    # total COUNT, done COUNT, rate = (done/total)*100

get_tasks_by_priority(db) → dict
    # 3 COUNT queries: low, medium, high

get_tasks_by_user(db) → list[dict]
    # LEFT OUTER JOIN users ← tasks, GROUP BY user, COUNT(task.id)
    # Returns: [{ user_id, full_name, email, task_count }]

get_date_range_metrics(db, start_date?, end_date?) → dict
    # Filter tasks by created_at range, then count by status
```

---

## 10. Configuration Management

### 10.1 Settings Class (`core/config.py`)
```python
class Settings:
    SECRET_KEY: str       # from SECRET_KEY env (warns if "changeme" or empty)
    JWT_EXPIRE_MINUTES: int  # from JWT_EXPIRE_MINUTES env (default: 60)
    ALGORITHM: str        # from ALGORITHM env (default: "HS256")
    DATABASE_URL: str     # from DATABASE_URL env (required in session.py)
    CORS_ORIGINS: list[str]  # from CORS_ORIGINS env (comma-separated, default: "*")
```

### 10.2 Environment Variables
| Variable | Required | Default | Used In |
|----------|----------|---------|---------|
| `DATABASE_URL` | Yes | — (raises ValueError) | db/session.py |
| `SECRET_KEY` | Yes* | "changeme" (warns) | core/config.py → security.py |
| `JWT_EXPIRE_MINUTES` | No | 60 | core/config.py → security.py |
| `ALGORITHM` | No | "HS256" | core/config.py → security.py |
| `CORS_ORIGINS` | No | "*" | core/config.py → main.py |

---

## 11. File Upload Implementation

```
Constants:
  UPLOAD_DIR = "uploads/"          (created at import time via os.makedirs)
  MAX_FILE_SIZE = 10 * 1024 * 1024 (10 MB)
  CHUNK_SIZE = 1024 * 1024         (1 MB read chunks)

Upload flow:
  1. Validate task_id → crud.get_task() or 404
  2. Read file.file in 1MB chunks
  3. Accumulate bytes, check len <= 10MB after each chunk (413 if exceeded)
  4. Generate filename: uuid4().hex + original extension
  5. Write to uploads/{uuid_filename}
  6. Create DB row: { filename: original, url: /uploads/{uuid}, uploader_id, task_id }

Delete flow:
  1. Get attachment row from DB
  2. Extract file_path from url, strip leading "/"
  3. If os.path.isfile(path): os.remove(path)
  4. db.delete(attachment); db.commit()
```

---

## 12. Middleware & Error Handling

### 12.1 CORS Middleware
```python
CORSMiddleware(
    allow_origins=settings.CORS_ORIGINS,   # configurable via env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 12.2 Error Response Patterns
| Code | Trigger | Response |
|------|---------|----------|
| 400 | Duplicate email, invalid transition, inactive user | `{ detail: "..." }` |
| 401 | Missing/invalid/expired JWT | `{ detail: "Could not validate credentials" }` |
| 403 | Insufficient role | `{ detail: "Insufficient permissions" }` |
| 404 | Resource not found | `{ detail: "X not found" }` |
| 413 | File > 10MB | `{ detail: "File size exceeds 10 MB limit" }` |
| 422 | Pydantic validation | `{ detail: [{ loc, msg, type }] }` |
| 429 | Rate limited | `{ detail: "Too many login attempts..." }` |
| 503 | DB unreachable | `{ status: "unhealthy", error: "..." }` |

---

## 13. Test Architecture

### 13.1 Test Infrastructure
```python
# conftest.py
Engine:    SQLite in-memory (test.db) with check_same_thread=False
Override:  app.dependency_overrides[get_db] = override_get_db
Fixtures:  setup_db (autouse) → create_all / drop_all per test
           admin_user, manager_user, employee_user → signup + role override
           admin_token, manager_token, employee_token → JWT from user ID
           admin_headers → { Authorization: "Bearer {token}" }
```

### 13.2 Test Coverage Map
| Module | Tests | Coverage |
|--------|-------|----------|
| Auth | 6 | signup, login, duplicate, wrong password, nonexistent |
| Users | 15 | CRUD, RBAC, filters, 404, unauthenticated |
| Tasks | 16 | CRUD, RBAC, filters, transitions, assign |
| Attachments | 11 | CRUD, upload, RBAC, unauthenticated |
| Dashboard | 11 | All 5 endpoints, empty data, RBAC |
| Edge Cases | 16 | JWT (expired/malformed/missing-sub), pagination, uploads, passwords, status |
| Stress | 4 | 1000+ tasks, bulk filtering, 100 users, large dataset dashboard |
| **Total** | **79** | |

---

## 14. Docker Configuration

### 14.1 Dockerfile
```
Base:     python:3.13-slim
Build:    apt install libpq-dev gcc → pip install requirements.txt
Runtime:  COPY app, mkdir uploads, EXPOSE 8000
CMD:      uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 14.2 docker-compose.yml
```
db service:
  Image:       postgres:16-alpine
  Healthcheck: pg_isready -U postgres (5s interval, 5 retries)
  Volume:      pgdata (named, persistent)

app service:
  Build:       . (Dockerfile)
  Depends:     db (condition: service_healthy)
  Healthcheck: urllib.request to /health (10s interval, 3 retries)
  Volumes:     ./uploads → /app/uploads (file persistence)
  Env:         .env file
  Restart:     always
```
