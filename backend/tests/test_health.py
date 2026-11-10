import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.config import settings

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == settings.PROJECT_NAME
    assert data["api_v1"] == "/api/v1"

def test_health_check_success():
    """Test /api/v1/health returns 200 when Oracle is connected."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data

def test_not_found_standard_error():
    """Test non-existent API endpoint returns 404 in standard format."""
    response = client.get("/api/v1/non-existent-endpoint-12345")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["code"] == "NOT_FOUND"

def test_health_check_failure_when_db_down():
    """Test /api/v1/health returns 503 when Oracle connection fails."""
    with patch("app.routers.health.get_pool") as mock_get_pool:
        mock_get_pool.side_effect = Exception("Oracle connection error")
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
