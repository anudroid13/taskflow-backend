import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import create_access_token
from app.models.user import User, UserRole

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_user(client, db_session):
    response = client.post("/auth/signup", json={
        "email": "admin@test.com",
        "password": "admin123",
        "full_name": "Admin User",
    })
    data = response.json()
    user = db_session.query(User).filter(User.id == data["id"]).first()
    user.role = UserRole.admin
    db_session.commit()
    data["role"] = "admin"
    return data


@pytest.fixture
def manager_user(client, db_session):
    response = client.post("/auth/signup", json={
        "email": "manager@test.com",
        "password": "manager123",
        "full_name": "Manager User",
    })
    data = response.json()
    user = db_session.query(User).filter(User.id == data["id"]).first()
    user.role = UserRole.manager
    db_session.commit()
    data["role"] = "manager"
    return data


@pytest.fixture
def employee_user(client):
    response = client.post("/auth/signup", json={
        "email": "employee@test.com",
        "password": "employee123",
        "full_name": "Employee User",
    })
    return response.json()


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(data={"sub": str(admin_user["id"])})


@pytest.fixture
def manager_token(manager_user):
    return create_access_token(data={"sub": str(manager_user["id"])})


@pytest.fixture
def employee_token(employee_user):
    return create_access_token(data={"sub": str(employee_user["id"])})


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def manager_headers(manager_token):
    return {"Authorization": f"Bearer {manager_token}"}


@pytest.fixture
def employee_headers(employee_token):
    return {"Authorization": f"Bearer {employee_token}"}
