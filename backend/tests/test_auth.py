import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_conn, get_pool
from app.repositories import auth_repo

client = TestClient(app)

def test_login_all_three_roles_success():
    """Verify that all 3 roles (QUAN_LY, LE_TAN, BUONG_PHONG) can log in successfully."""
    credentials = [
        ("quanly", "QuanLy123#", "QUAN_LY"),
        ("letan", "LeTan123#", "LE_TAN"),
        ("buongphong", "BuongPhong123#", "BUONG_PHONG"),
    ]
    for username, password, expected_role in credentials:
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200, f"Failed for {username}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert "token" in data
        assert data["user"]["role"] == expected_role
        assert "password" not in response.text
        assert "mat_khau" not in response.text

def test_login_invalid_credentials():
    """Wrong password returns 401 AUTH_INVALID_CREDENTIALS."""
    response = client.post("/api/v1/auth/login", json={"username": "quanly", "password": "WrongPassword!@#"})
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["code"] == "AUTH_INVALID_CREDENTIALS"

def test_login_non_existent_user():
    """Non-existent username returns 401 AUTH_INVALID_CREDENTIALS (no username enumeration)."""
    response = client.post("/api/v1/auth/login", json={"username": "user_does_not_exist_xyz", "password": "password"})
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["code"] == "AUTH_INVALID_CREDENTIALS"

def test_account_temporary_locking():
    """Entering wrong password repeatedly triggers temporary account lock (AUTH_ACCOUNT_LOCKED)."""
    # 1. Reset user first
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
        user = auth_repo.get_user_by_username(conn, "letan")
        assert user is not None
        auth_repo.reset_failed_attempts(conn, user.user_id)
        conn.commit()

    # 2. Make 5 failed attempts
    for i in range(4):
        res = client.post("/api/v1/auth/login", json={"username": "letan", "password": f"wrong_{i}"})
        assert res.status_code == 401
        assert res.json()["code"] == "AUTH_INVALID_CREDENTIALS"

    # 5th failed attempt should trigger lock
    res = client.post("/api/v1/auth/login", json={"username": "letan", "password": "wrong_5"})
    assert res.status_code == 403
    assert res.json()["code"] == "AUTH_ACCOUNT_LOCKED"

    # 6th attempt even with correct password should be rejected as locked
    res = client.post("/api/v1/auth/login", json={"username": "letan", "password": "LeTan123#"})
    assert res.status_code == 403
    assert res.json()["code"] == "AUTH_ACCOUNT_LOCKED"

    # 3. Clean up: unlock account
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
        auth_repo.reset_failed_attempts(conn, user.user_id)
        conn.commit()

    # Verify user can log in again after reset
    res = client.post("/api/v1/auth/login", json={"username": "letan", "password": "LeTan123#"})
    assert res.status_code == 200

def test_get_me_unauthorized():
    """Accessing /auth/me without token returns 401 UNAUTHORIZED."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["code"] == "UNAUTHORIZED"

def test_get_me_authorized():
    """Accessing /auth/me with valid token returns user details."""
    login_res = client.post("/api/v1/auth/login", json={"username": "quanly", "password": "QuanLy123#"})
    token = login_res.json()["token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["username"] == "quanly"
    assert data["user"]["role"] == "QUAN_LY"

def test_change_password_flow():
    """Verify change-password flow with validation, wrong current password, and success."""
    login_res = client.post("/api/v1/auth/login", json={"username": "buongphong", "password": "BuongPhong123#"})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Wrong current password
    res = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"currentPassword": "WrongCurrentPassword", "newPassword": "NewPassword123#"}
    )
    assert res.status_code == 401
    assert res.json()["code"] == "AUTH_INVALID_CREDENTIALS"

    # 2. New password too short (< 8 chars)
    res = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"currentPassword": "BuongPhong123#", "newPassword": "short"}
    )
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"

    # 3. Successful change
    res = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"currentPassword": "BuongPhong123#", "newPassword": "UpdatedBuongPhong123#"}
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 4. Verify login with new password works
    res = client.post("/api/v1/auth/login", json={"username": "buongphong", "password": "UpdatedBuongPhong123#"})
    assert res.status_code == 200

    # 5. Restore original password
    new_token = res.json()["token"]
    client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {new_token}"},
        json={"currentPassword": "UpdatedBuongPhong123#", "newPassword": "BuongPhong123#"}
    )
