def test_signup_success(client):
    response = client.post("/auth/signup", json={
        "email": "new@test.com",
        "password": "password123",
        "full_name": "New User",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@test.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "employee"
    assert "id" in data


def test_signup_duplicate_email(client):
    client.post("/auth/signup", json={
        "email": "dup@test.com",
        "password": "password123",
        "full_name": "User One",
    })
    response = client.post("/auth/signup", json={
        "email": "dup@test.com",
        "password": "password456",
        "full_name": "User Two",
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client):
    client.post("/auth/signup", json={
        "email": "login@test.com",
        "password": "password123",
        "full_name": "Login User",
    })
    response = client.post("/auth/login", data={
        "username": "login@test.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/auth/signup", json={
        "email": "wrong@test.com",
        "password": "password123",
        "full_name": "Wrong User",
    })
    response = client.post("/auth/login", data={
        "username": "wrong@test.com",
        "password": "badpassword",
    })
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/auth/login", data={
        "username": "nonexistent@test.com",
        "password": "password123",
    })
    assert response.status_code == 401
