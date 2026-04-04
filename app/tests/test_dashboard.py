import pytest


@pytest.fixture
def seeded_tasks(client, admin_headers, admin_user, employee_user):
    tasks = [
        {"title": "Task 1", "owner_id": admin_user["id"], "status": "todo", "priority": "high"},
        {"title": "Task 2", "owner_id": admin_user["id"], "status": "todo", "priority": "medium"},
        {"title": "Task 3", "owner_id": employee_user["id"], "status": "todo", "priority": "low"},
    ]
    created = []
    for t in tasks:
        resp = client.post("/tasks/", json=t, headers=admin_headers)
        created.append(resp.json())

    # Move Task 1: todo -> in_progress -> done
    client.put(f"/tasks/{created[0]['id']}", json={"status": "in_progress"}, headers=admin_headers)
    client.put(f"/tasks/{created[0]['id']}", json={"status": "done"}, headers=admin_headers)

    # Move Task 2: todo -> in_progress
    client.put(f"/tasks/{created[1]['id']}", json={"status": "in_progress"}, headers=admin_headers)

    return created


# --- SUMMARY ---

def test_task_summary(client, admin_headers, seeded_tasks):
    response = client.get("/dashboard/summary", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["done"] == 1
    assert data["in_progress"] == 1
    assert data["todo"] == 1
    assert data["overdue"] == 0


# --- COMPLETION RATE ---

def test_completion_rate(client, admin_headers, seeded_tasks):
    response = client.get("/dashboard/completion-rate", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["done"] == 1
    assert data["completion_rate"] == pytest.approx(33.33, abs=0.01)


def test_completion_rate_empty(client, admin_headers):
    response = client.get("/dashboard/completion-rate", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["completion_rate"] == 0.0


# --- BY PRIORITY ---

def test_tasks_by_priority(client, admin_headers, seeded_tasks):
    response = client.get("/dashboard/by-priority", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["high"] == 1
    assert data["medium"] == 1
    assert data["low"] == 1


# --- BY USER ---

def test_tasks_by_user_as_admin(client, admin_headers, seeded_tasks):
    response = client.get("/dashboard/by-user", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    admin_entry = next(u for u in data if u["email"] == "admin@test.com")
    assert admin_entry["task_count"] == 2


def test_tasks_by_user_as_employee_forbidden(client, employee_headers):
    response = client.get("/dashboard/by-user", headers=employee_headers)
    assert response.status_code == 403


# --- DATE RANGE ---

def test_date_range_metrics(client, admin_headers, seeded_tasks):
    response = client.get("/dashboard/date-range", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


def test_date_range_with_dates(client, admin_headers, seeded_tasks):
    response = client.get(
        "/dashboard/date-range?start_date=2020-01-01T00:00:00&end_date=2030-01-01T00:00:00",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


# --- UNAUTHENTICATED ---

def test_dashboard_unauthenticated(client):
    response = client.get("/dashboard/summary")
    assert response.status_code == 401
