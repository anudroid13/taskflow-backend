def test_create_user_as_admin(client, admin_headers):
    response = client.post("/users/", json={
        "email": "created@test.com",
        "password": "password123",
        "full_name": "Created User",
        "role": "employee",
    }, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["email"] == "created@test.com"


def test_create_user_as_employee_forbidden(client, employee_headers):
    response = client.post("/users/", json={
        "email": "forbidden@test.com",
        "password": "password123",
        "full_name": "Forbidden",
    }, headers=employee_headers)
    assert response.status_code == 403


def test_list_users_as_admin(client, admin_headers):
    response = client.get("/users/", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_users_as_manager(client, manager_headers):
    response = client.get("/users/", headers=manager_headers)
    assert response.status_code == 200


def test_list_users_as_employee_forbidden(client, employee_headers):
    response = client.get("/users/", headers=employee_headers)
    assert response.status_code == 403


def test_list_users_filter_by_role(client, admin_headers, admin_user, employee_user):
    response = client.get("/users/?role=admin", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert all(u["role"] == "admin" for u in data)


def test_list_users_filter_by_email(client, admin_headers, admin_user):
    response = client.get("/users/?email=admin", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "admin" in data[0]["email"]


def test_get_user_by_id(client, admin_headers, admin_user):
    user_id = admin_user["id"]
    response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_get_user_not_found(client, admin_headers):
    response = client.get("/users/99999", headers=admin_headers)
    assert response.status_code == 404


def test_update_user_as_admin(client, admin_headers, employee_user):
    user_id = employee_user["id"]
    response = client.put(f"/users/{user_id}", json={
        "full_name": "Updated Name",
    }, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_update_user_as_employee_forbidden(client, employee_headers, admin_user):
    user_id = admin_user["id"]
    response = client.put(f"/users/{user_id}", json={
        "full_name": "Hacked",
    }, headers=employee_headers)
    assert response.status_code == 403


def test_delete_user_as_admin(client, admin_headers, employee_user):
    user_id = employee_user["id"]
    response = client.delete(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 204
    response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == 404


def test_delete_user_as_employee_forbidden(client, employee_headers, admin_user):
    user_id = admin_user["id"]
    response = client.delete(f"/users/{user_id}", headers=employee_headers)
    assert response.status_code == 403


def test_unauthenticated_access(client):
    response = client.get("/users/")
    assert response.status_code == 401
