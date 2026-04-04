import pytest


@pytest.fixture
def sample_task(client, admin_headers, admin_user):
    response = client.post("/tasks/", json={
        "title": "Sample Task",
        "description": "A test task",
        "owner_id": admin_user["id"],
    }, headers=admin_headers)
    return response.json()


# --- CREATE ---

def test_create_task(client, admin_headers, admin_user):
    response = client.post("/tasks/", json={
        "title": "New Task",
        "description": "Task description",
        "owner_id": admin_user["id"],
    }, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Task"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"


def test_create_task_unauthenticated(client):
    response = client.post("/tasks/", json={
        "title": "Fail Task",
        "owner_id": 1,
    })
    assert response.status_code == 401


# --- READ ---

def test_list_tasks(client, admin_headers, sample_task):
    response = client.get("/tasks/", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_task(client, admin_headers, sample_task):
    task_id = sample_task["id"]
    response = client.get(f"/tasks/{task_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_get_task_not_found(client, admin_headers):
    response = client.get("/tasks/99999", headers=admin_headers)
    assert response.status_code == 404


# --- FILTERS ---

def test_filter_tasks_by_status(client, admin_headers, sample_task):
    response = client.get("/tasks/?status_filter=todo", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(t["status"] == "todo" for t in data)


def test_filter_tasks_by_priority(client, admin_headers, sample_task):
    response = client.get("/tasks/?priority=medium", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(t["priority"] == "medium" for t in data)


def test_filter_tasks_by_owner(client, admin_headers, admin_user, sample_task):
    owner_id = admin_user["id"]
    response = client.get(f"/tasks/?owner_id={owner_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(t["owner_id"] == owner_id for t in data)


# --- UPDATE ---

def test_update_task_as_admin(client, admin_headers, sample_task):
    task_id = sample_task["id"]
    response = client.put(f"/tasks/{task_id}", json={
        "title": "Updated Title",
    }, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_update_task_as_employee_forbidden(client, employee_headers, sample_task):
    task_id = sample_task["id"]
    response = client.put(f"/tasks/{task_id}", json={
        "title": "Hacked",
    }, headers=employee_headers)
    assert response.status_code == 403


# --- STATUS TRANSITIONS ---

def test_valid_status_transition(client, admin_headers, sample_task):
    task_id = sample_task["id"]
    # todo -> in_progress (valid)
    response = client.put(f"/tasks/{task_id}", json={
        "status": "in_progress",
    }, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_invalid_status_transition(client, admin_headers, sample_task):
    task_id = sample_task["id"]
    # todo -> done (invalid, must go through in_progress)
    response = client.put(f"/tasks/{task_id}", json={
        "status": "done",
    }, headers=admin_headers)
    assert response.status_code == 400
    assert "invalid status transition" in response.json()["detail"].lower()


# --- ASSIGNMENT ---

def test_assign_task(client, admin_headers, sample_task, employee_user):
    task_id = sample_task["id"]
    response = client.patch(f"/tasks/{task_id}/assign", json={
        "owner_id": employee_user["id"],
    }, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["owner_id"] == employee_user["id"]


def test_assign_task_as_employee_forbidden(client, employee_headers, sample_task):
    task_id = sample_task["id"]
    response = client.patch(f"/tasks/{task_id}/assign", json={
        "owner_id": 1,
    }, headers=employee_headers)
    assert response.status_code == 403


# --- DELETE ---

def test_delete_task_as_admin(client, admin_headers, sample_task):
    task_id = sample_task["id"]
    response = client.delete(f"/tasks/{task_id}", headers=admin_headers)
    assert response.status_code == 204
    response = client.get(f"/tasks/{task_id}", headers=admin_headers)
    assert response.status_code == 404


def test_delete_task_as_employee_forbidden(client, employee_headers, sample_task):
    task_id = sample_task["id"]
    response = client.delete(f"/tasks/{task_id}", headers=employee_headers)
    assert response.status_code == 403
