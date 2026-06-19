"""Lectura y extracción de texto de archivos PDF."""

import logging
from pathlib import Path

import pdfplumber
import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Error durante la extracción de texto de un PDF."""


def detect_pdf_type(pdf_path: Path) -> str:
    """Detecta si un PDF es texto nativo o escaneado.

    Retorna 'texto_nativo' si el PDF contiene texto extraíble,
    'escaneado' si es una imagen escaneada.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return "escaneado"
            first_page = pdf.pages[0]
            text = first_page.extract_text() or ""
            if len(text.strip()) > 50:
                return "texto_nativo"
            return "escaneado"
    except Exception as e:
        raise PDFExtractionError(f"Error detectando tipo de PDF: {e}") from e


def extract_native_text(pdf_path: Path) -> str:
    """Extrae texto de PDFs generados electrónicamente (texto nativo)."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if not text.strip():
            raise PDFExtractionError("El PDF no contiene texto extraíble")
        return text.strip()
    except PDFExtractionError:
        raise
    except Exception as e:
        raise PDFExtractionError(f"Error extrayendo texto nativo: {e}") from e


def extract_ocr_text(pdf_path: Path) -> str:
    """Extrae texto de PDFs escaneados usando OCR (pytesseract)."""
    try:
        images = convert_from_path(pdf_path, dpi=300)
        text_parts: list[str] = []
        for image in images:
            page_text = pytesseract.image_to_string(image, lang="spa")
            text_parts.append(page_text)
        text = "\n".join(text_parts)
        if not text.strip():
            raise PDFExtractionError(
                "OCR no pudo extraer texto. El documento puede ser de baja calidad."
            )
        return text.strip()
    except PDFExtractionError:
        raise
    except Exception as e:
        raise PDFExtractionError(f"Error en extracción OCR: {e}") from e


def extract_text(pdf_path: Path) -> tuple[str, str]:
    """Extrae texto de un PDF usando el método apropiado.

    Retorna una tupla (texto, metodo_extraccion).
    Intenta texto nativo primero, fallback a OCR si falla.
    """
    pdf_type = detect_pdf_type(pdf_path)

    if pdf_type == "texto_nativo":
        try:
            text = extract_native_text(pdf_path)
            return text, "texto_nativo"
        except PDFExtractionError as e:
            logger.warning("Texto nativo falló, intentando OCR: %s", e)

    # Fallback a OCR
    try:
        text = extract_ocr_text(pdf_path)
        return text, "ocr_fallback"
    except PDFExtractionError as e:
        raise PDFExtractionError(
            f"No se pudo extraer texto del PDF: {e}"
        ) from e
