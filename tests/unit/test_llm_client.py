"""Tests unitarios para el cliente LLM (OpenRouter)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm_client import (
    LLMError,
    LLMResponseError,
    _parse_json_response,
    extract_with_llm,
)


class TestParseJsonResponse:
    """Tests para _parse_json_response."""

    def test_json_valido(self):
        data = '{"nit_emisor": "900123456", "total": 100000}'
        result = _parse_json_response(data)
        assert result["nit_emisor"] == "900123456"
        assert result["total"] == 100000

    def test_json_con_markdown(self):
        data = '```json\n{"nit_emisor": "900123456"}\n```'
        result = _parse_json_response(data)
        assert result["nit_emisor"] == "900123456"

    def test_json_con_espacios(self):
        data = '  {"nit_emisor": "900123456"}  '
        result = _parse_json_response(data)
        assert result["nit_emisor"] == "900123456"

    def test_json_invalido(self):
        with pytest.raises(LLMResponseError):
            _parse_json_response("esto no es json")

    def test_json_vacio(self):
        with pytest.raises(LLMResponseError):
            _parse_json_response("")

    def test_json_con_texto_extra(self):
        with pytest.raises(LLMResponseError):
            _parse_json_response("Aquí está el JSON: {\"a\": 1}")


class TestExtractWithLlm:
    """Tests para extract_with_llm."""

    @pytest.mark.asyncio
    @patch("app.services.llm_client.httpx.AsyncClient")
    async def test_extraccion_exitosa(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "nit_emisor": "900123456",
                                "nombre_emisor": "Empresa S.A.S",
                                "nit_receptor": "900654321",
                                "nombre_receptor": "Cliente Ltda",
                                "numero_factura": "FE0000001",
                                "fecha_emision": "2024-01-15",
                                "cufe": None,
                                "items": [],
                                "subtotal": 100000,
                                "iva_total": 19000,
                                "total": 119000,
                                "moneda": "COP",
                            }
                        )
                    }
                }
            ]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await extract_with_llm("Factura de prueba")
        assert result["nit_emisor"] == "900123456"
        assert result["total"] == 119000

    @pytest.mark.asyncio
    @patch("app.services.llm_client.httpx.AsyncClient")
    async def test_api_retorna_error(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(LLMError):
            await extract_with_llm("Factura")

    @pytest.mark.asyncio
    @patch("app.services.llm_client.httpx.AsyncClient")
    async def test_timeout(self, mock_client_cls):
        import httpx

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(LLMError):
            await extract_with_llm("Factura")

    @pytest.mark.asyncio
    @patch("app.services.llm_client.httpx.AsyncClient")
    async def test_conexion_fallida(self, mock_client_cls):
        import httpx

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(LLMError):
            await extract_with_llm("Factura")
