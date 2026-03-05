"""Tests for the web app."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_api_status():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


def test_dashboard():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Dashboard" in response.text


def test_login():
    response = client.get("/login")
    assert response.status_code == 200
    assert "Sign In" in response.text
