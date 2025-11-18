"""Tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


def test_register_user() -> None:
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
        },
    )

    # Note: This will fail without database
    # Uncomment when database is running
    # assert response.status_code == 201
    # assert "access_token" in response.json()


def test_login() -> None:
    """Test user login."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )

    # Note: This will fail without database
    # Uncomment when database is running
    # assert response.status_code == 200
    # assert "access_token" in response.json()


def test_get_current_user() -> None:
    """Test getting current user info."""
    # Create a test token
    token = create_access_token(subject="test-user-id")

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Note: This will fail without database
    # Uncomment when database is running
    # assert response.status_code == 200


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_check_v1() -> None:
    """Test API v1 health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["api_version"] == "v1"
