# Mobile Flow (Client App)

## Stack Decision
- **Flutter** (Dart) — single codebase for iOS + Android, fast native performance
- **MVVM architecture** — View (widgets) → ViewModel (Cubit/Bloc) → Model (data classes + services)
- **flutter_bloc** for dependency injection and state management (BlocProvider + BlocBuilder/BlocListener)
- **Dio** for HTTP with interceptors (JWT auto-attach, 401 redirect)
- **flutter_secure_storage** for token persistence
- **fl_chart** for dashboard charts
- **go_router** for declarative routing with auth redirect

---

## Backend API Contract (Confirmed)

### Base URL
```
http://<server>:8000
```

### Auth (no token required)
| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/auth/signup` | `{ email, password, full_name }` | `{ id, email, full_name, role, is_active }` (201) |
| POST | `/auth/login` | `{ email, password }` | `{ access_token, token_type }` (200) |

- Password must be >= 8 characters
- Login rate-limited to 5 attempts per 5 minutes per IP (429 on exceed)

### Users (token required)
| Method | Endpoint | Role | Query Params | Body |
|--------|----------|------|--------------|------|
| POST | `/users/` | admin | — | `{ email, password, full_name, role, is_active }` |
| GET | `/users/` | admin, manager | `skip, limit, role, email` | — |
| GET | `/users/{id}` | any authenticated | — | — |
| PUT | `/users/{id}` | admin | — | `{ full_name?, password?, role?, is_active? }` |
| DELETE | `/users/{id}` | admin | — | — (204) |

### Tasks (token required)
| Method | Endpoint | Role | Query Params | Body |
|--------|----------|------|--------------|------|
| POST | `/tasks/` | any (employee: self only) | — | `{ title, description?, status?, priority?, owner_id }` |
| GET | `/tasks/` | any authenticated | `skip, limit, status_filter, priority, owner_id, created_after, created_before` | — |
| GET | `/tasks/{id}` | any authenticated | — | — |
| PUT | `/tasks/{id}` | admin, manager | — | `{ title?, description?, status?, priority?, owner_id? }` |
| PATCH | `/tasks/{id}/assign` | admin, manager | — | `{ owner_id }` |
| DELETE | `/tasks/{id}` | admin | — | — (204) |

**Status values**: `todo`, `in_progress`, `done`, `overdue`
**Priority values**: `low`, `medium`, `high`
**Status transitions**: todo→in_progress, in_progress→done/todo, overdue→in_progress, done→(terminal)

### Attachments (token required)
| Method | Endpoint | Role | Body |
|--------|----------|------|------|
| POST | `/attachments/upload` | any authenticated | `multipart: file + task_id` (max 10MB) |
| POST | `/attachments/` | any authenticated | `{ filename, url, task_id }` |
| GET | `/attachments/` | any authenticated | `skip, limit` |
| GET | `/attachments/{id}` | any authenticated | — |
| PUT | `/attachments/{id}` | admin, manager | `{ filename? }` |
| DELETE | `/attachments/{id}` | admin | — (204) |

### Dashboard (token required)
| Method | Endpoint | Role | Query Params |
|--------|----------|------|--------------|
| GET | `/dashboard/summary` | any authenticated | — |
| GET | `/dashboard/completion-rate` | any authenticated | — |
| GET | `/dashboard/by-priority` | any authenticated | — |
| GET | `/dashboard/by-user` | admin, manager | — |
| GET | `/dashboard/date-range` | any authenticated | `start_date?, end_date?` |

### Auth Header Format
```
Authorization: Bearer <access_token>
```

### Common Error Codes
- `400` — validation error / duplicate email
- `401` — missing or invalid token
- `403` — insufficient role permissions
- `404` — resource not found
- `413` — file too large (>10MB)
- `422` — request body validation failed
- `429` — rate limited

---

## Phase 1: Project Setup
1. `flutter create taskflow_mobile`
2. Add dependencies to `pubspec.yaml`:
   ```yaml
   dependencies:
     dio: ^5.4.0
     flutter_bloc: ^8.1.4
     go_router: ^13.0.0
     flutter_secure_storage: ^9.0.0
     fl_chart: ^0.66.0
     file_picker: ^6.1.1
     intl: ^0.19.0
     equatable: ^2.0.5
   dev_dependencies:
     bloc_test: ^9.1.5
     mockito: ^5.4.4
     build_runner: ^2.4.8
   ```
3. Create folder structure (see below).
4. Create `ApiClient` (Dio instance) with base URL, JWT interceptor, and 401 auto-logout.
5. Create model classes matching backend schemas (`fromJson` / `toJson`).

## Phase 2: Authentication Flow
1. **LoginView** — email + password `TextFormField`, calls `AuthCubit.login()` → `POST /auth/login`, stores `access_token` via `flutter_secure_storage`.
2. **SignupView** — email + password + full_name form, calls `AuthCubit.signup()` → `POST /auth/signup`, auto-login on success.
3. **AuthCubit** (Cubit<AuthState>) — emits states: `AuthInitial`, `AuthLoading`, `Authenticated(user, token, role)`, `AuthError(message)`, `Unauthenticated`. Exposes `login()`, `signup()`, `logout()`, `restoreSession()`.
4. **AuthService** — raw API calls: `postLogin(email, password)`, `postSignup(email, password, fullName)`.
5. **Auth redirect** — `go_router` redirect checks `AuthCubit.state is Authenticated`; sends to `/login` if not.
6. **Auto-restore** — on app launch, read token from secure storage, call `GET /users/{id}` to validate, restore or clear.
7. Handle rate limiting (429) — `BlocListener` on `AuthError` shows SnackBar "Too many attempts, try again in 5 minutes".

## Phase 3: Task Flow (Core Screens)
1. **TaskListView**
   - `TaskListCubit` calls `TaskService.getTasks()` → `GET /tasks/` with `RefreshIndicator`.
   - Emits: `TaskListLoading`, `TaskListLoaded(tasks)`, `TaskListError(message)`.
   - Filter bar: status `ChoiceChip`s, priority `DropdownButton`, date range picker.
   - Each card shows: title, status badge, priority tag, assignee name.
   - Tap → navigate to TaskDetailView.
2. **TaskDetailView**
   - `TaskDetailCubit` loads task + attachments.
   - Admin/Manager: edit button → TaskEditView, assign button → user picker dialog.
   - Employee: status update button (only valid transitions shown as chips).
   - Attachment section: `ListView` of files, upload button (`file_picker` → `POST /attachments/upload` via `Dio` multipart).
3. **TaskCreateView**
   - Form: title (required), description, priority picker, assignee picker (employee: locked to self).
   - `TaskFormCubit.submit()` → `POST /tasks/`.
4. **TaskEditView** (admin/manager only)
   - Pre-filled form, status dropdown shows only valid transitions.
   - `TaskFormCubit.submit()` → `PUT /tasks/{id}`.

## Phase 4: Role-Specific Screens
1. **Admin**
   - Bottom nav: Tasks | Users | Dashboard
   - Users tab: `UserListView` + `UserListCubit` → `GET /users/`, create user, edit role/active, delete.
   - Full task CRUD + assign + delete.
2. **Manager**
   - Bottom nav: Tasks | Team | Dashboard
   - Team tab: `UserListView` (read-only), view tasks by user.
   - Task CRUD (no delete) + assign.
3. **Employee**
   - Bottom nav: My Tasks | Dashboard
   - My Tasks: `GET /tasks/?owner_id={self.id}` — only own tasks.
   - Can create tasks (self only), update status on own tasks.
   - No user management access.
4. **Role-based routing** — `go_router` builds different `ShellRoute` with `BottomNavigationBar` based on `AuthCubit.state`.

## Phase 5: Dashboard
1. **Summary cards** — `DashboardCubit` calls `GET /dashboard/summary` → display total, todo, in_progress, done, overdue in `Card` widgets.
2. **Completion rate** — `GET /dashboard/completion-rate` → `CircularProgressIndicator` or `PieChart` from `fl_chart`.
3. **Priority chart** — `GET /dashboard/by-priority` → `BarChart` (low/medium/high).
4. **Team overview** (admin/manager) — `GET /dashboard/by-user` → `ListView` with task counts per user.
5. **Date range filter** — `showDateRangePicker()` → `GET /dashboard/date-range?start_date=...&end_date=...`.
6. `RefreshIndicator` on entire dashboard.

## Phase 6: Polish and Edge Cases
1. **Offline handling** — show cached data when offline, queue mutations and retry on reconnect.
2. **Loading states** — `CircularProgressIndicator` while fetching, disabled buttons during submission.
3. **Error SnackBars** — map API error codes to user-friendly messages in `ErrorHandler`.
4. **Token expiry** — Dio interceptor catches 401, clears secure storage, calls `AuthCubit.logout()`.
5. **File upload progress** — Dio `onSendProgress` callback → `LinearProgressIndicator`.
6. **Empty states** — "No tasks yet" widget with illustration on empty lists.
7. **Search** — user email search field on Users screen (uses `?email=` query param).

## Phase 7: Testing and Release
1. **Unit tests** — test Cubits with `bloc_test` (`blocTest()`), verify state emissions with mocked Services.
2. **Widget tests** — pump widgets with `BlocProvider.value()`, verify UI renders correctly.
3. **Integration tests** — `integration_test` package for critical flows (login → create task → update status → logout).
4. **QA checklist**: test all 3 roles, test 401/403/429 handling, test large file rejection (>10MB), test bad network.
5. **Build** — `flutter build apk` + `flutter build ipa` (or use Fastlane/Codemagic).
6. **Distribute** — TestFlight (iOS) + Internal Testing (Android) → App Store + Play Store.

---

## Getting Started (First Steps)

```bash
# 1. Create project
flutter create taskflow_mobile
cd taskflow_mobile

# 2. Add dependencies
flutter pub add dio flutter_bloc equatable go_router flutter_secure_storage fl_chart file_picker intl
flutter pub add --dev bloc_test mockito build_runner

# 3. Create MVVM folder structure
mkdir -p lib/{models,services,cubits,views/{auth,tasks,users,dashboard},widgets,core,routes}

# 4. Make sure backend is running
# In taskflow-backend directory: uvicorn app.main:app --reload
# Backend runs at http://localhost:8000
# For Android emulator use http://10.0.2.2:8000

# 5. Run the app
flutter run
```

---

## MVVM Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  View (Widgets)                                 │
│  - Renders UI from Cubit state                  │
│  - Calls Cubit methods on user actions          │
│  - Listens via BlocBuilder / BlocListener       │
├─────────────────────────────────────────────────┤
│  ViewModel / Cubit (Cubit<State>)               │
│  - Holds screen state via Equatable state class │
│  - Calls Service methods                        │
│  - Emits new state on changes                   │
├─────────────────────────────────────────────────┤
│  Model + Service                                │
│  - Model: plain Dart classes (fromJson/toJson)  │
│  - Service: Dio HTTP calls to backend API       │
└─────────────────────────────────────────────────┘
```

---

## Folder Structure
```
taskflow_mobile/
  lib/
    main.dart                        # entry point, MultiBlocProvider + GoRouter
    core/
      api_client.dart                # Dio instance, base URL, JWT interceptor, 401 handler
      constants.dart                 # BASE_URL, timeouts
      error_handler.dart             # maps DioException to user-friendly messages
      secure_storage.dart            # getToken(), setToken(), clearToken()
    models/
      user.dart                      # User, UserRole enum, fromJson/toJson
      task.dart                      # Task, TaskStatus/TaskPriority enums, fromJson/toJson
      attachment.dart                # Attachment, fromJson/toJson
      login_response.dart            # LoginResponse (access_token, token_type)
      dashboard.dart                 # Summary, CompletionRate, PriorityBreakdown, etc.
    services/
      auth_service.dart              # login(), signup() → raw Dio calls
      user_service.dart              # getUsers(), createUser(), updateUser(), deleteUser()
      task_service.dart              # getTasks(), createTask(), updateTask(), assignTask(), deleteTask()
      attachment_service.dart        # uploadFile(), getAttachments(), deleteAttachment()
      dashboard_service.dart         # getSummary(), getCompletionRate(), getByPriority(), getByUser(), getDateRange()
    cubits/
      auth/
        auth_cubit.dart              # login(), signup(), logout(), restoreSession()
        auth_state.dart              # AuthInitial, AuthLoading, Authenticated, Unauthenticated, AuthError
      task_list/
        task_list_cubit.dart         # fetchTasks(), applyFilters()
        task_list_state.dart         # TaskListLoading, TaskListLoaded, TaskListError
      task_detail/
        task_detail_cubit.dart       # loadTask(), updateStatus(), uploadFile()
        task_detail_state.dart
      task_form/
        task_form_cubit.dart         # submit() for create or edit
        task_form_state.dart
      user_list/
        user_list_cubit.dart         # fetchUsers(), deleteUser()
        user_list_state.dart
      user_form/
        user_form_cubit.dart         # submit() for create or edit
        user_form_state.dart
      dashboard/
        dashboard_cubit.dart         # fetchAll()
        dashboard_state.dart         # DashboardLoading, DashboardLoaded, DashboardError
    views/
      auth/
        login_view.dart
        signup_view.dart
      tasks/
        task_list_view.dart
        task_detail_view.dart
        task_create_view.dart
        task_edit_view.dart
      users/
        user_list_view.dart
        user_create_view.dart
        user_edit_view.dart
      dashboard/
        dashboard_view.dart
      shell/
        admin_shell.dart             # BottomNav: Tasks | Users | Dashboard
        manager_shell.dart           # BottomNav: Tasks | Team | Dashboard
        employee_shell.dart          # BottomNav: My Tasks | Dashboard
    widgets/
      status_badge.dart
      priority_tag.dart
      filter_bar.dart
      empty_state.dart
      loading_overlay.dart
      file_upload_button.dart
      confirm_dialog.dart
    routes/
      app_router.dart                # GoRouter config, auth redirect, role-based shell routes
  test/
    cubits/                          # bloc_test unit tests for each Cubit
    services/                        # mocked Dio tests for each Service
    widgets/                         # widget tests
  integration_test/
    app_test.dart                    # E2E flow tests
  pubspec.yaml
```