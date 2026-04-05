# High-Level Design (HLD) — TaskFlow Backend

## 1. System Overview

TaskFlow is a REST API backend for enterprise task management. It provides authentication, role-based access control, task lifecycle management, file attachments, and analytics dashboards.

**Tech Stack**: Python 3.13 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · JWT (HS256) · bcrypt · Docker

---

## 2. System Architecture

```
┌─────────────┐       HTTPS        ┌──────────────────────────────────────┐
│   Clients   │ ─────────────────→ │         FastAPI Application          │
│  (Mobile /  │ ←───────────────── │         (Uvicorn ASGI)               │
│   Web /     │     JSON / JWT     │                                      │
│   Postman)  │                    │  ┌────────────┐  ┌───────────────┐   │
└─────────────┘                    │  │ Middleware  │  │   Routers     │   │
                                   │  │ (CORS)     │→ │ (5 modules)   │   │
                                   │  └────────────┘  └───────┬───────┘   │
                                   │                          │           │
                                   │  ┌───────────────────────▼────────┐  │
                                   │  │  Security Layer (JWT + RBAC)   │  │
                                   │  └───────────────────────┬────────┘  │
                                   │                          │           │
                                   │  ┌──────────┐  ┌────────▼────────┐  │
                                   │  │ Services  │  │   CRUD Layer    │  │
                                   │  │(Analytics)│  │ (Business Logic)│  │
                                   │  └─────┬─────┘  └────────┬───────┘  │
                                   │        │                  │          │
                                   │  ┌─────▼──────────────────▼───────┐  │
                                   │  │     SQLAlchemy ORM (Models)    │  │
                                   │  └──────────────┬─────────────────┘  │
                                   └─────────────────┼────────────────────┘
                                                     │
                                              ┌──────▼──────┐
                                              │ PostgreSQL   │
                                              │ (port 5432)  │
                                              └──────────────┘
                                                     │
                                              ┌──────▼──────┐
                                              │  File System │
                                              │  (uploads/)  │
                                              └─────────────┘
```

---

## 3. Component Breakdown

| Component | Purpose | Technology |
|-----------|---------|------------|
| **API Gateway** | Request routing, CORS, health checks | FastAPI + CORSMiddleware |
| **Auth Module** | Signup, login, JWT issuance, rate limiting | python-jose, bcrypt, in-memory limiter |
| **RBAC Layer** | Role-based endpoint protection | FastAPI Depends() chain |
| **User Module** | User CRUD, role management | SQLAlchemy ORM |
| **Task Module** | Task CRUD, status machine, assignment | SQLAlchemy ORM + transition rules |
| **Attachment Module** | File upload/metadata, disk storage | Dio multipart, UUID filenames |
| **Dashboard Module** | Analytics aggregation (5 metrics) | SQLAlchemy func.count + GROUP BY |
| **Database** | Persistent storage | PostgreSQL 16 (Docker) |
| **Config** | Centralized env management | python-dotenv → Settings class |

---

## 4. Data Flow Diagrams

### 4.1 Authentication Flow
```
Client                    API                     DB
  │                        │                       │
  │  POST /auth/login      │                       │
  │  {email, password}     │                       │
  │───────────────────────→│                       │
  │                        │  SELECT user by email │
  │                        │──────────────────────→│
  │                        │     User row          │
  │                        │←──────────────────────│
  │                        │                       │
  │                        │  bcrypt.verify()      │
  │                        │  jwt.encode(sub=id)   │
  │                        │                       │
  │  {access_token, bearer}│                       │
  │←───────────────────────│                       │
```

### 4.2 Authenticated Request Flow
```
Client                    API                         DB
  │                        │                           │
  │  GET /tasks/           │                           │
  │  Authorization: Bearer │                           │
  │───────────────────────→│                           │
  │                        │  jwt.decode(token)        │
  │                        │  SELECT user by id        │
  │                        │──────────────────────────→│
  │                        │  Check role permissions   │
  │                        │  SELECT tasks with filters│
  │                        │──────────────────────────→│
  │                        │     Task rows             │
  │                        │←──────────────────────────│
  │  [TaskRead, ...]       │                           │
  │←───────────────────────│                           │

```

### 4.3 File Upload Flow
```
Client                    API                   Disk        DB
  │                        │                     │           │
  │ POST /attachments/upload                     │           │
  │ multipart: file + task_id                    │           │
  │───────────────────────→│                     │           │
  │                        │ Read 1MB chunks     │           │
  │                        │ Check <= 10MB       │           │
  │                        │ Generate UUID name  │           │
  │                        │────────────────────→│           │
  │                        │ Write to uploads/   │           │
  │                        │                     │           │
  │                        │ INSERT attachment row│          │
  │                        │────────────────────────────────→│
  │  AttachmentRead (JSON) │                     │           │
  │←───────────────────────│                     │           │
```

---

## 5. API Design

### Endpoints Summary (22 total)

| Prefix | Endpoints | Auth | Description |
|--------|-----------|------|-------------|
| `/auth` | 2 | Public | Signup, Login |
| `/users` | 5 | Role-gated | User CRUD |
| `/tasks` | 6 | Role-gated | Task CRUD + Assign |
| `/attachments` | 6 | Authenticated | File CRUD + Upload |
| `/dashboard` | 5 | Authenticated | Analytics |
| `/` | 2 | Public | Root + Health check |

### Role Permissions Matrix

| Action | Admin | Manager | Employee |
|--------|-------|---------|----------|
| Create user | ✅ | ❌ | ❌ |
| List users | ✅ | ✅ | ❌ |
| View user by ID | ✅ | ✅ | ✅ |
| Update/Delete user | ✅ | ❌ | ❌ |
| Create task | ✅ (any) | ✅ (any) | ✅ (self only) |
| List/View tasks | ✅ | ✅ | ✅ |
| Update task | ✅ | ✅ | ❌ |
| Assign task | ✅ | ✅ | ❌ |
| Delete task | ✅ | ❌ | ❌ |
| Upload/View attachment | ✅ | ✅ | ✅ |
| Update attachment | ✅ | ✅ | ❌ |
| Delete attachment | ✅ | ❌ | ❌ |
| Dashboard summary | ✅ | ✅ | ✅ |
| Dashboard by-user | ✅ | ✅ | ❌ |

---

## 6. Data Model (ER Diagram)

```
┌──────────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
│        users         │       │        tasks         │       │     attachments      │
├──────────────────────┤       ├──────────────────────┤       ├──────────────────────┤
│ id         PK  INT   │←──┐   │ id         PK  INT   │←──┐   │ id         PK  INT   │
│ email      UQ  STR   │   │   │ title          STR   │   │   │ filename       STR   │
│ hashed_password  STR │   │   │ description    STR?  │   │   │ url            STR   │
│ full_name      STR?  │   │   │ status     ENUM      │   │   │ uploaded_at    DT    │
│ is_active      BOOL  │   │   │ priority   ENUM      │   │   │ uploader_id FK INT   │──→ users.id
│ role       ENUM      │   └───│ owner_id   FK  INT   │   └───│ task_id     FK INT   │──→ tasks.id
│ created_at     DT    │       │ created_at     DT    │       └──────────────────────┘
│ updated_at     DT    │       │ updated_at     DT    │
└──────────────────────┘       └──────────────────────┘

Relationships:
  User  1 ──→ N  Task        (cascade: all, delete-orphan)
  User  1 ──→ N  Attachment  (cascade: all, delete-orphan)
  Task  1 ──→ N  Attachment  (cascade: all, delete-orphan)
```

---

## 7. Security Architecture

| Layer | Mechanism | Details |
|-------|-----------|---------|
| **Transport** | HTTPS (reverse proxy) | TLS termination at load balancer |
| **Authentication** | JWT (HS256) | 60-min expiry, `sub` = user ID |
| **Password storage** | bcrypt | via passlib CryptContext |
| **Authorization** | RBAC | 3 roles, enforced via FastAPI Depends() |
| **Rate limiting** | In-memory | 5 login attempts per IP per 5 min |
| **Input validation** | Pydantic v2 | Email validation, password min 8 chars |
| **File security** | UUID filenames | Prevents directory traversal, 10MB cap |
| **CORS** | Configurable origins | Via CORS_ORIGINS env var |
| **Config** | Environment variables | SECRET_KEY warning if default |

---

## 8. Deployment Architecture

```
┌─────────────────────────────────────────────┐
│              docker-compose                  │
│                                              │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │   app            │  │   db             │  │
│  │   Python 3.13    │  │   PostgreSQL 16  │  │
│  │   Uvicorn :8000  │  │   Alpine :5432   │  │
│  │                  │  │                  │  │
│  │   Health: /health│  │   Health:        │  │
│  │   Restart: always│  │   pg_isready     │  │
│  │                  │  │                  │  │
│  │   Vol: uploads/  │  │   Vol: pgdata    │  │
│  └─────────────────┘  └──────────────────┘  │
│                                              │
│  Dependency: app → db (service_healthy)      │
└─────────────────────────────────────────────┘
```

---

## 9. Non-Functional Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| Response time | < 300ms | SQLAlchemy ORM, indexed queries |
| Availability | Health check monitored | `/health` endpoint + Docker restart |
| Scalability | Horizontal via containers | Stateless app (except file uploads) |
| Observability | Structured logging | Python logging, timestamped format |
| Test coverage | 72 tests passing | pytest + httpx, includes stress tests |
| Security | OWASP Top 10 addressed | JWT, bcrypt, RBAC, input validation |
