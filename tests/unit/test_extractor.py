"""Tests unitarios para el módulo extractor."""

from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.extractor import ExtractionError, _to_decimal, extract_factura
from app.models import FacturaDIAN
from app.services.llm_client import LLMError
from app.services.pdf_reader import PDFExtractionError


class TestToDecimal:
    """Tests para _to_decimal."""

    def test_entero(self):
        assert _to_decimal(100) == Decimal("100")

    def test_float(self):
        assert _to_decimal(100.50) == Decimal("100.50")

    def test_string_entero(self):
        assert _to_decimal("100000") == Decimal("100000")

    def test_string_con_puntos(self):
        assert _to_decimal("100.000") == Decimal("100000")

    def test_string_con_comas(self):
        assert _to_decimal("100,000") == Decimal("100000")

    def test_string_vacio(self):
        assert _to_decimal("") == Decimal("0")

    def test_none(self):
        assert _to_decimal(None) == Decimal("0")

    def test_string_invalido(self):
        assert _to_decimal("abc") == Decimal("0")


class TestExtractFactura:
    """Tests para extract_factura."""

    @pytest.mark.asyncio
    @patch("app.extractor.extract_text")
    @patch("app.extractor.extract_with_llm")
    async def test_extraccion_exitosa(self, mock_llm, mock_extract):
        mock_extract.return_value = ("Texto de factura", "texto_nativo")
        mock_llm.return_value = {
            "nit_emisor": "900123456",
            "nombre_emisor": "Empresa S.A.S",
            "nit_receptor": "900654321",
            "nombre_receptor": "Cliente Ltda",
            "numero_factura": "FE0000001",
            "fecha_emision": "2024-01-15",
            "cufe": "abc123",
            "items": [
                {
                    "descripcion": "Servicio",
                    "cantidad": 1.0,
                    "precio_unitario": 100000,
                    "iva": 19000,
                }
            ],
            "subtotal": 100000,
            "iva_total": 19000,
            "total": 119000,
            "moneda": "COP",
        }

        result = await extract_factura(Path("test.pdf"), "factura.pdf")
        assert isinstance(result, FacturaDIAN)
        assert result.nit_emisor == "900123456"
        assert result.metodo_extraccion == "texto_nativo"
        assert result.confianza > 0

    @pytest.mark.asyncio
    @patch("pdf2image.convert_from_path")
    @patch("app.extractor.ocr_with_llm")
    @patch("app.extractor.extract_text")
    async def test_error_extraccion_texto(self, mock_extract, mock_ocr, mock_convert):
        mock_extract.side_effect = PDFExtractionError("No se pudo leer")
        mock_convert.side_effect = Exception("poppler no disponible")

        with pytest.raises(ExtractionError):
            await extract_factura(Path("test.pdf"), "factura.pdf")

    @pytest.mark.asyncio
    @patch("app.extractor.extract_with_llm")
    @patch("app.extractor.extract_text")
    async def test_error_llm(self, mock_extract, mock_llm):
        mock_extract.return_value = ("Texto", "texto_nativo")
        mock_llm.side_effect = LLMError("API caída")

        with pytest.raises(ExtractionError):
            await extract_factura(Path("test.pdf"), "factura.pdf")

    @pytest.mark.asyncio
    @patch("app.extractor.extract_with_llm")
    @patch("app.extractor.extract_text")
    async def test_json_invalido_reintenta(self, mock_extract, mock_llm):
        """Si el primer intento retorna JSON inválido (fecha mala), reintenta una vez."""
        mock_extract.return_value = ("Texto", "texto_nativo")

        # Primer intento: fecha inválida → falla validación
        # Segundo intento: fecha válida → éxito
        mock_llm.side_effect = [
            {
                "nit_emisor": "900123456",
                "nombre_emisor": "Empresa",
                "nit_receptor": "900654321",
                "nombre_receptor": "Cliente",
                "numero_factura": "FE001",
                "fecha_emision": "fecha-invalida",
                "items": [],
                "subtotal": 0,
                "iva_total": 0,
                "total": 0,
            },
            {
                "nit_emisor": "900123456",
                "nombre_emisor": "Empresa S.A.S",
                "nit_receptor": "900654321",
                "nombre_receptor": "Cliente Ltda",
                "numero_factura": "FE0000001",
                "fecha_emision": "2024-01-15",
                "items": [],
                "subtotal": 100000,
                "iva_total": 19000,
                "total": 119000,
            },
        ]

        result = await extract_factura(Path("test.pdf"), "factura.pdf")
        assert isinstance(result, FacturaDIAN)
        assert result.nit_emisor == "900123456"

    @pytest.mark.asyncio
    @patch("app.extractor.extract_with_llm")
    @patch("app.extractor.extract_text")
    async def test_confianza_baja_campos_faltantes(self, mock_extract, mock_llm):
        """Campos faltantes resultan en confianza baja, no en error."""
        mock_extract.return_value = ("Texto", "texto_nativo")
        mock_llm.return_value = {
            "nit_emisor": "900123456",
            "nombre_emisor": "",
            "nit_receptor": "",
            "nombre_receptor": "",
            "numero_factura": "",
            "fecha_emision": "2024-01-15",
            "items": [],
            "subtotal": 0,
            "iva_total": 0,
            "total": 0,
        }

        result = await extract_factura(Path("test.pdf"), "factura.pdf")
        assert isinstance(result, FacturaDIAN)
        assert result.confianza < 0.5


class TestExtractFromImage:
    """Tests para extracción desde imágenes (JPG/PNG)."""

    @pytest.mark.asyncio
    @patch("app.extractor.ocr_with_llm")
    @patch("app.extractor.Image")
    async def test_extraccion_jpg_exitosa(self, mock_image, mock_ocr):
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img

        mock_ocr.return_value = "NIT: 900123456\nEmpresa S.A.S\nTotal: 119000"

        with patch("app.extractor.extract_with_llm") as mock_llm:
            mock_llm.return_value = {
                "nit_emisor": "900123456",
                "nombre_emisor": "Empresa S.A.S",
                "nit_receptor": "900654321",
                "nombre_receptor": "Cliente Ltda",
                "numero_factura": "FE0000001",
                "fecha_emision": "2024-01-15",
                "items": [],
                "subtotal": 100000,
                "iva_total": 19000,
                "total": 119000,
            }
            result = await extract_factura(Path("foto.jpg"), "factura.jpg")

        assert isinstance(result, FacturaDIAN)
        assert result.metodo_extraccion == "imagen_directa"
        assert result.nit_emisor == "900123456"

    @pytest.mark.asyncio
    @patch("app.extractor.ocr_with_llm")
    @patch("app.extractor.Image")
    async def test_extraccion_jpg_ocr_falla(self, mock_image, mock_ocr):
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img
        mock_ocr.side_effect = Exception("Ollama no disponible")

        with pytest.raises(ExtractionError, match="No se pudo procesar la imagen"):
            await extract_factura(Path("foto.jpg"), "factura.jpg")
