import pytest
import io


@pytest.fixture
def sample_task(client, admin_headers, admin_user):
    response = client.post("/tasks/", json={
        "title": "Attach Task",
        "owner_id": admin_user["id"],
    }, headers=admin_headers)
    return response.json()


@pytest.fixture
def sample_attachment(client, admin_headers, admin_user, sample_task):
    response = client.post("/attachments/", json={
        "filename": "test.txt",
        "url": "/uploads/test.txt",
        "uploader_id": admin_user["id"],
        "task_id": sample_task["id"],
    }, headers=admin_headers)
    return response.json()


# --- CREATE ---

def test_create_attachment(client, admin_headers, admin_user, sample_task):
    response = client.post("/attachments/", json={
        "filename": "doc.pdf",
        "url": "/uploads/doc.pdf",
        "uploader_id": admin_user["id"],
        "task_id": sample_task["id"],
    }, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "doc.pdf"
    assert data["task_id"] == sample_task["id"]


def test_create_attachment_unauthenticated(client):
    response = client.post("/attachments/", json={
        "filename": "fail.txt",
        "url": "/uploads/fail.txt",
        "uploader_id": 1,
        "task_id": 1,
    })
    assert response.status_code == 401


# --- FILE UPLOAD ---

def test_upload_attachment(client, admin_headers, sample_task):
    file_content = b"hello world"
    response = client.post(
        "/attachments/upload",
        data={"task_id": str(sample_task["id"])},
        files={"file": ("hello.txt", io.BytesIO(file_content), "text/plain")},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "hello.txt"
    assert data["task_id"] == sample_task["id"]


# --- READ ---

def test_list_attachments(client, admin_headers, sample_attachment):
    response = client.get("/attachments/", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_attachment(client, admin_headers, sample_attachment):
    att_id = sample_attachment["id"]
    response = client.get(f"/attachments/{att_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == att_id


def test_get_attachment_not_found(client, admin_headers):
    response = client.get("/attachments/99999", headers=admin_headers)
    assert response.status_code == 404


# --- DELETE ---

def test_delete_attachment_as_admin(client, admin_headers, sample_attachment):
    att_id = sample_attachment["id"]
    response = client.delete(f"/attachments/{att_id}", headers=admin_headers)
    assert response.status_code == 204
    response = client.get(f"/attachments/{att_id}", headers=admin_headers)
    assert response.status_code == 404


def test_delete_attachment_as_employee_forbidden(client, employee_headers, sample_attachment):
    att_id = sample_attachment["id"]
    response = client.delete(f"/attachments/{att_id}", headers=employee_headers)
    assert response.status_code == 403
