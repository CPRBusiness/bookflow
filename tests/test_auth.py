import uuid
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from bookflow.app.models import User
from bookflow.app.core.security import create_access_token
from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    email = f"test-{uuid.uuid4().hex}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data

    assert "password" not in data
    assert "password_hash" not in data

def test_register_duplicate_email(client: TestClient):
    email = f"test-{uuid.uuid4().hex}@example.com"

    payload = {
        "email": email,
        "password": "password123",
    }

    first_response = client.post(
        "/auth/register",
        json=payload,
    )

    second_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "A user with this email already exists"
    }

def test_register_invalid_data(client: TestClient):
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_login_user(client: TestClient):
    email = f"test-{uuid.uuid4().hex}@example.com"
    password = "password123"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_password(client: TestClient):
    email = f"test-{uuid.uuid4().hex}@example.com"

    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password"
    }


def test_get_current_user(client: TestClient):
    email = f"test-{uuid.uuid4().hex}@example.com"
    password = "password123"

    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == email
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data


def test_get_current_user_with_invalid_token(
    client: TestClient,
):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }


def test_get_current_user_with_expired_token(
    client: TestClient,
):
    register_response = client.post(
        "/auth/register",
        json={
            "email": f"test-{uuid.uuid4().hex}@example.com",
            "password": "password123",
        },
    )

    user_id = register_response.json()["id"]

    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }


def test_inactive_user_cannot_login(
    client: TestClient,
    db_session: Session,
):
    email = f"test-{uuid.uuid4().hex}@example.com"
    password = "password123"

    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    user = db_session.scalar(
        select(User).where(User.email == email)
    )

    assert user is not None

    user.is_active = False
    db_session.flush()

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Inactive user"
    }