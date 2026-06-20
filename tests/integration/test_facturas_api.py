"""Tests de integración para endpoints de facturas."""

import io
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models import FacturaDIAN


@pytest.mark.asyncio
async def test_extraer_sin_token(client: AsyncClient):
    """POST /facturas/extraer sin token retorna 401."""
    pdf_bytes = b"%PDF-1.4 fake content"
    response = await client.post(
        "/facturas/extraer",
        files={"archivo": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_extraer_no_pdf(client: AsyncClient):
    """POST /facturas/extraer con archivo no permitido retorna 422."""
    # Login para obtener token
    login_resp = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "secret"},
    )
    token = login_resp.json()["access_token"]

    response = await client.post(
        "/facturas/extraer",
        headers={"Authorization": f"Bearer {token}"},
        files={"archivo": ("test.txt", io.BytesIO(b"no es pdf"), "text/plain")},
    )
    assert response.status_code == 422
    assert "PDF, JPG" in response.json()["detail"]


@pytest.mark.asyncio
@patch("app.routers.facturas.extract_factura")
async def test_extraer_jpg_exito(mock_extract, client: AsyncClient):
    """POST /facturas/extraer con JPG acepta el archivo."""
    from datetime import date
    from decimal import Decimal

    mock_factura = FacturaDIAN(
        nit_emisor="900123456",
        nombre_emisor="Empresa S.A.S",
        nit_receptor="900654321",
        nombre_receptor="Cliente Ltda",
        numero_factura="FE0000001",
        fecha_emision=date(2024, 1, 15),
        cufe=None,
        items=[],
        subtotal=Decimal("100000"),
        iva_total=Decimal("19000"),
        total=Decimal("119000"),
        metodo_extraccion="imagen_directa",
        confianza=0.95,
    )
    mock_extract.return_value = mock_factura

    login_resp = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "secret"},
    )
    token = login_resp.json()["access_token"]

    jpg_bytes = b"\xff\xd8\xff\xe0 fake jpg"
    response = await client.post(
        "/facturas/extraer",
        headers={"Authorization": f"Bearer {token}"},
        files={"archivo": ("factura.jpg", io.BytesIO(jpg_bytes), "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["datos"]["metodo_extraccion"] == "imagen_directa"
    assert data["datos"]["nit_emisor"] == "900123456"


@pytest.mark.asyncio
async def test_historial_sin_token(client: AsyncClient):
    """GET /facturas/historial sin token retorna 401."""
    response = await client.get("/facturas/historial")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_historial_vacio(client: AsyncClient):
    """GET /facturas/historial con token retorna lista vacía."""
    login_resp = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "secret"},
    )
    token = login_resp.json()["access_token"]

    response = await client.get(
        "/facturas/historial",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_historial_paginacion(client: AsyncClient):
    """GET /facturas/historial respeta offset y limit."""
    login_resp = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "secret"},
    )
    token = login_resp.json()["access_token"]

    response = await client.get(
        "/facturas/historial",
        headers={"Authorization": f"Bearer {token}"},
        params={"offset": 0, "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["offset"] == 0
    assert data["limit"] == 5


@pytest.mark.asyncio
@patch("app.routers.facturas.extract_factura")
async def test_extraer_exito(mock_extract, client: AsyncClient):
    """POST /facturas/extraer con PDF mock retorna datos."""
    from datetime import date
    from decimal import Decimal

    mock_factura = FacturaDIAN(
        nit_emisor="900123456",
        nombre_emisor="Empresa S.A.S",
        nit_receptor="900654321",
        nombre_receptor="Cliente Ltda",
        numero_factura="FE0000001",
        fecha_emision=date(2024, 1, 15),
        cufe=None,
        items=[],
        subtotal=Decimal("100000"),
        iva_total=Decimal("19000"),
        total=Decimal("119000"),
        metodo_extraccion="texto_nativo",
        confianza=0.95,
    )
    mock_extract.return_value = mock_factura

    login_resp = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "secret"},
    )
    token = login_resp.json()["access_token"]

    pdf_bytes = b"%PDF-1.4 test"
    response = await client.post(
        "/facturas/extraer",
        headers={"Authorization": f"Bearer {token}"},
        files={"archivo": ("factura.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["datos"]["nit_emisor"] == "900123456"
    assert float(data["datos"]["total"]) == 119000
