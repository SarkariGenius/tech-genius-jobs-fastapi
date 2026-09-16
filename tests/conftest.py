import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db, Base
from app.core.config import settings
from app.main import app


@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_student(client, email="test.student@example.com", password="Password@123"):
    return client.post("/api/v1/auth/register/student", json={
        "full_name": "Test Student",
        "email": email,
        "phone": "9999999999",
        "password": password,
        "confirm_password": password,
        "current_city": "Indore",
        "experience_level": "FRESHER",
    })


def register_hr(client, email="test.hr@example.com", company_name="Test Company"):
    return client.post("/api/v1/auth/register/hr", json={
        "full_name": "Test HR",
        "email": email,
        "phone": "8888888888",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "company_name": company_name,
        "designation": "HR Manager",
    })


def login(client, email, password="Password@123"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(token_response):
    return {"Authorization": f"Bearer {token_response.json()['access_token']}"}
