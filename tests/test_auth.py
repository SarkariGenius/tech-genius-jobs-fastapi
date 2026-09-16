from tests.conftest import register_student, register_hr, login, auth_headers


def test_register_student(client):
    resp = register_student(client)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "STUDENT"


def test_register_hr(client):
    resp = register_hr(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == "HR"


def test_login(client):
    register_student(client, email="login@example.com")
    resp = login(client, "login@example.com")
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_invalid(client):
    resp = login(client, "nonexistent@example.com")
    assert resp.status_code == 401


def test_duplicate_email(client):
    register_student(client, email="dup@example.com")
    resp = register_student(client, email="dup@example.com")
    assert resp.status_code == 409


def test_get_me(client):
    resp = register_student(client, email="me@example.com")
    headers = auth_headers(resp)
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "me@example.com"


def test_password_mismatch(client):
    resp = client.post("/api/v1/auth/register/student", json={
        "full_name": "Test",
        "email": "mismatch@example.com",
        "phone": "9999999999",
        "password": "Password@123",
        "confirm_password": "Different@123",
        "current_city": "Indore",
        "experience_level": "FRESHER",
    })
    assert resp.status_code == 422


def test_logout(client):
    resp = register_student(client, email="logout@example.com")
    headers = auth_headers(resp)
    out = client.post("/api/v1/auth/logout", headers=headers)
    assert out.status_code == 200
