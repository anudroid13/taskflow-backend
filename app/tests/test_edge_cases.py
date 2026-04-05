import io
import pytest
from jose import jwt
from datetime import datetime, timezone, timedelta
from app.core.config import settings


# --- ROOT & HEALTH ---

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "TaskFlow API"}


def test_health_check_healthy(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


# --- JWT EDGE CASES ---

def test_expired_token(client):
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    response = client.get("/users/1", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_malformed_token(client):
    response = client.get("/users/1", headers={"Authorization": "Bearer not.a.real.token"})
    assert response.status_code == 401


def test_token_missing_sub(client):
    token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    response = client.get("/users/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_invalid_sub(client):
    token = jwt.encode(
        {"sub": "not_an_int", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    response = client.get("/users/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_nonexistent_user(client):
    token = jwt.encode(
        {"sub": "99999", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    response = client.get("/users/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


# --- PAGINATION ---

def test_list_tasks_pagination(client, admin_user, admin_headers):
    for i in range(5):
        client.post("/tasks/", json={
            "title": f"Task {i}",
            "owner_id": admin_user["id"],
        }, headers=admin_headers)
    # limit=2
    response = client.get("/tasks/?limit=2", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
    # skip=3, limit=10
    response = client.get("/tasks/?skip=3&limit=10", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_users_pagination(client, admin_headers):
    response = client.get("/users/?limit=1", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_attachments_pagination(client, admin_headers, admin_user):
    task = client.post("/tasks/", json={
        "title": "Pagination Task",
        "owner_id": admin_user["id"],
    }, headers=admin_headers).json()
    for i in range(3):
        client.post("/attachments/", json={
            "filename": f"file{i}.txt",
            "url": f"/uploads/file{i}.txt",
            "task_id": task["id"],
        }, headers=admin_headers)
    response = client.get("/attachments/?limit=2", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


# --- UPLOAD EDGE CASES ---

def test_upload_no_file(client, admin_headers, admin_user):
    task = client.post("/tasks/", json={
        "title": "No File Task",
        "owner_id": admin_user["id"],
    }, headers=admin_headers).json()
    response = client.post(
        "/attachments/upload",
        data={"task_id": str(task["id"])},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_upload_invalid_task_id(client, admin_headers):
    file_content = b"hello"
    response = client.post(
        "/attachments/upload",
        data={"task_id": "99999"},
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
        headers=admin_headers,
    )
    assert response.status_code == 404


# --- PASSWORD VALIDATION ---

def test_signup_short_password(client):
    response = client.post("/auth/signup", json={
        "email": "short@test.com",
        "password": "abc",
        "full_name": "Short Pass",
    })
    assert response.status_code == 422


def test_create_user_short_password(client, admin_headers):
    response = client.post("/users/", json={
        "email": "short2@test.com",
        "password": "abc",
        "full_name": "Short Pass",
        "role": "employee",
    }, headers=admin_headers)
    assert response.status_code == 422


# --- STATUS TRANSITION EDGE CASES ---

def test_cannot_create_overdue_task(client, admin_headers, admin_user):
    response = client.post("/tasks/", json={
        "title": "Overdue",
        "owner_id": admin_user["id"],
        "status": "overdue",
    }, headers=admin_headers)
    assert response.status_code == 422


def test_cannot_transition_done_to_todo(client, admin_headers, admin_user):
    task = client.post("/tasks/", json={
        "title": "Done Block",
        "owner_id": admin_user["id"],
    }, headers=admin_headers).json()
    # todo -> in_progress
    client.put(f"/tasks/{task['id']}", json={"status": "in_progress"}, headers=admin_headers)
    # in_progress -> done
    client.put(f"/tasks/{task['id']}", json={"status": "done"}, headers=admin_headers)
    # done -> todo (should fail)
    response = client.put(f"/tasks/{task['id']}", json={"status": "todo"}, headers=admin_headers)
    assert response.status_code == 400
