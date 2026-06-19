"""Tests de integración para endpoints de autenticación."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_exitoso(client: AsyncClient):
    """POST /auth/login con credenciales válidas retorna token."""
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "secret"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_credenciales_invalidas(client: AsyncClient):
    """POST /auth/login con credenciales inválidas retorna 401."""
    response = await client.post(
        "/auth/login",
        json={"username": "wrong", "password": "wrong"},
    )
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_password_incorrecto(client: AsyncClient):
    """POST /auth/login con password incorrecto retorna 401."""
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "incorrecto"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """GET /health retorna status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ocr-dian"
