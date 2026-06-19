"""Tests unitarios para modelos Pydantic."""

from datetime import date
from decimal import Decimal

import pytest

from app.models import FacturaDIAN, ItemFactura, LoginRequest, TokenResponse


class TestItemFactura:
    """Tests para ItemFactura."""

    def test_crear_item_valido(self):
        item = ItemFactura(
            descripcion="Servicio de consultoría",
            cantidad=2.0,
            precio_unitario=Decimal("100000"),
            iva=Decimal("19000"),
        )
        assert item.descripcion == "Servicio de consultoría"
        assert item.cantidad == 2.0
        assert item.precio_unitario == Decimal("100000")
        assert item.iva == Decimal("19000")

    def test_item_con_valores_decimales(self):
        item = ItemFactura(
            descripcion="Producto",
            cantidad=1.5,
            precio_unitario=Decimal("50000.50"),
            iva=Decimal("9500.095"),
        )
        assert item.cantidad == 1.5
        assert item.precio_unitario == Decimal("50000.50")


class TestFacturaDIAN:
    """Tests para FacturaDIAN."""

    def _make_factura(self, **overrides) -> FacturaDIAN:
        data = {
            "nit_emisor": "900123456",
            "nombre_emisor": "Empresa S.A.S",
            "nit_receptor": "900654321",
            "nombre_receptor": "Cliente Ltda",
            "numero_factura": "FE0000001",
            "fecha_emision": date(2024, 1, 15),
            "cufe": "abc123def456",
            "items": [
                ItemFactura(
                    descripcion="Servicio",
                    cantidad=1.0,
                    precio_unitario=Decimal("100000"),
                    iva=Decimal("19000"),
                )
            ],
            "subtotal": Decimal("100000"),
            "iva_total": Decimal("19000"),
            "total": Decimal("119000"),
            "moneda": "COP",
            "metodo_extraccion": "texto_nativo",
            "confianza": 0.95,
        }
        data.update(overrides)
        return FacturaDIAN(**data)

    def test_factura_valida(self):
        f = self._make_factura()
        assert f.nit_emisor == "900123456"
        assert f.total == Decimal("119000")
        assert f.confianza == 0.95

    def test_factura_sin_cufe(self):
        f = self._make_factura(cufe=None)
        assert f.cufe is None

    def test_factura_confianza_minima(self):
        f = self._make_factura(confianza=0.0)
        assert f.confianza == 0.0

    def test_factura_confianza_maxima(self):
        f = self._make_factura(confianza=1.0)
        assert f.confianza == 1.0

    def test_factura_confianza_invalida(self):
        with pytest.raises(ValueError):
            self._make_factura(confianza=1.5)

    def test_factura_confianza_negativa(self):
        with pytest.raises(ValueError):
            self._make_factura(confianza=-0.1)

    def test_nit_emisor_vacio(self):
        f = self._make_factura(nit_emisor="")
        assert f.nit_emisor == ""

    def test_nit_receptor_espacios(self):
        f = self._make_factura(nit_receptor="   ")
        assert f.nit_receptor == ""

    def test_factura_items_vacios(self):
        f = self._make_factura(items=[])
        assert f.items == []

    def test_default_moneda(self):
        f = self._make_factura()
        assert f.moneda == "COP"


class TestLoginRequest:
    """Tests para LoginRequest."""

    def test_login_valido(self):
        req = LoginRequest(username="admin", password="secret")
        assert req.username == "admin"
        assert req.password == "secret"


class TestTokenResponse:
    """Tests para TokenResponse."""

    def test_token_response(self):
        resp = TokenResponse(access_token="abc123")
        assert resp.access_token == "abc123"
        assert resp.token_type == "bearer"
