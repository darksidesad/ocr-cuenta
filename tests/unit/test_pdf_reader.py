"""Tests unitarios para lector de PDF."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.pdf_reader import (
    PDFExtractionError,
    detect_pdf_type,
    extract_native_text,
    extract_ocr_text,
    extract_text,
)


class TestDetectPdfType:
    """Tests para detect_pdf_type."""

    @patch("app.services.pdf_reader.pdfplumber.open")
    def test_pdf_texto_nativo(self, mock_open):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Factura electrónica DIAN\nNIT: 900123456\nTotal: $119.000"
        )
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        result = detect_pdf_type(Path("test.pdf"))
        assert result == "texto_nativo"

    @patch("app.services.pdf_reader.pdfplumber.open")
    def test_pdf_escaneado(self, mock_open):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        result = detect_pdf_type(Path("test.pdf"))
        assert result == "escaneado"

    @patch("app.services.pdf_reader.pdfplumber.open")
    def test_pdf_poco_texto(self, mock_open):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "abc"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        result = detect_pdf_type(Path("test.pdf"))
        assert result == "escaneado"

    @patch("app.services.pdf_reader.pdfplumber.open")
    def test_pdf_sin_paginas(self, mock_open):
        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        result = detect_pdf_type(Path("test.pdf"))
        assert result == "escaneado"

    @patch("app.services.pdf_reader.pdfplumber.open")
    def test_pdf_error_abriendo(self, mock_open):
        mock_open.side_effect = Exception("PDF corrupto")
        with pytest.raises(PDFExtractionError):
            detect_pdf_type(Path("test.pdf"))


class TestExtractNativeText:
    """Tests para extract_native_text."""

    @patch("app.services.pdf_reader.pdfplumber.open")
    def test_extraccion_exitosa(self, mock_open):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Factura DIAN\nNIT: 900123456"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        result = extract_native_text(Path("test.pdf"))
        assert "Factura DIAN" in result
        assert "NIT: 900123456" in result

    @patch("app.services.pdf_reader.pdfplumber.open")
    def test_texto_vacio_falla(self, mock_open):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(PDFExtractionError):
            extract_native_text(Path("test.pdf"))

    @patch("app.services.pdf_reader.pdfplumber.open")
    def test_multiples_paginas(self, mock_open):
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Página 1"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Página 2"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_pdf)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        result = extract_native_text(Path("test.pdf"))
        assert "Página 1" in result
        assert "Página 2" in result


class TestExtractOcrText:
    """Tests para extract_ocr_text."""

    @patch("app.services.pdf_reader.pytesseract.image_to_string")
    @patch("app.services.pdf_reader.convert_from_path")
    def test_ocr_exitoso(self, mock_convert, mock_ocr):
        mock_image = MagicMock()
        mock_convert.return_value = [mock_image]
        mock_ocr.return_value = "Texto extraído por OCR"

        result = extract_ocr_text(Path("test.pdf"))
        assert result == "Texto extraído por OCR"

    @patch("app.services.pdf_reader.convert_from_path")
    def test_ocr_vacio_falla(self, mock_convert):
        mock_image = MagicMock()
        mock_convert.return_value = [mock_image]

        with (
            patch("app.services.pdf_reader.pytesseract.image_to_string", return_value=""),
            pytest.raises(PDFExtractionError),
        ):
            extract_ocr_text(Path("test.pdf"))

    @patch("app.services.pdf_reader.convert_from_path")
    def test_ocr_error_conversion(self, mock_convert):
        mock_convert.side_effect = Exception("Error convirtiendo")
        with pytest.raises(PDFExtractionError):
            extract_ocr_text(Path("test.pdf"))


class TestExtractText:
    """Tests para extract_text (función principal)."""

    @patch("app.services.pdf_reader.extract_native_text")
    @patch("app.services.pdf_reader.detect_pdf_type")
    def test_primero_intenta_nativo(self, mock_detect, mock_native):
        mock_detect.return_value = "texto_nativo"
        mock_native.return_value = "Texto de factura"

        text, method = extract_text(Path("test.pdf"))
        assert text == "Texto de factura"
        assert method == "texto_nativo"

    @patch("app.services.pdf_reader.extract_ocr_text")
    @patch("app.services.pdf_reader.detect_pdf_type")
    def test_fallback_a_ocr(self, mock_detect, mock_ocr):
        mock_detect.return_value = "escaneado"
        mock_ocr.return_value = "Texto OCR"

        text, method = extract_text(Path("test.pdf"))
        assert text == "Texto OCR"
        assert method == "ocr_fallback"

    @patch("app.services.pdf_reader.extract_ocr_text")
    @patch("app.services.pdf_reader.extract_native_text")
    @patch("app.services.pdf_reader.detect_pdf_type")
    def test_fallback_cuando_nativo_falla(self, mock_detect, mock_native, mock_ocr):
        mock_detect.return_value = "texto_nativo"
        mock_native.side_effect = PDFExtractionError("No hay texto")
        mock_ocr.return_value = "Texto rescatado por OCR"

        text, method = extract_text(Path("test.pdf"))
        assert text == "Texto rescatado por OCR"
        assert method == "ocr_fallback"
