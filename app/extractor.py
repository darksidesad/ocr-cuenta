"""Lógica principal de extracción de datos de facturas colombianas."""

import logging
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pydantic import ValidationError

from app.models import FacturaDIAN
from app.services.llm_client import LLMError, LLMResponseError, extract_with_llm, ocr_with_llm
from app.services.ollama_client import OllamaError
from app.services.pdf_reader import PDFExtractionError, extract_text

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Error durante el proceso de extracción de datos."""


async def extract_factura(pdf_path: Path, nombre_archivo: str) -> FacturaDIAN:
    """Extrae datos de una factura colombiana desde un PDF.

    Flujo:
    1. Extraer texto (texto nativo → pdfplumber → pytesseract → Ollama glm-ocr)
    2. Enviar a LLM para extracción estructurada (OpenRouter o Ollama)
    3. Validar con Pydantic
    4. Retornar FacturaDIAN validado
    """
    # Paso 1: Extraer texto con métodos progresivos
    try:
        texto, metodo = await _extract_text_progressive(pdf_path)
    except PDFExtractionError as e:
        raise ExtractionError(str(e)) from e
    logger.info(f"Texto extraído: método={metodo}, {len(texto)} caracteres")

    # Paso 2: Enviar a LLM para extracción estructurada
    raw_data = await _extract_structured_data(texto)

    # Paso 3: Validar con Pydantic
    try:
        raw_data["metodo_extraccion"] = metodo
        factura = _parse_and_validate(raw_data, metodo)
        logger.info(f"Extracción exitosa: factura {factura.numero_factura}")
        return factura
    except (ValidationError, ValueError) as e:
        logger.warning(f"Validación falló, reintentando: {e}")
        try:
            retry_text = (
                texto
                + "\n\nNOTA IMPORTANTE: Asegúrate de que todos los campos numéricos "
                "sean valores puros (sin puntos ni comas). "
                "La fecha debe estar en formato YYYY-MM-DD."
            )
            raw_data_retry = await _extract_structured_data(retry_text)
            raw_data_retry["metodo_extraccion"] = metodo
            return _parse_and_validate(raw_data_retry, metodo)
        except (LLMError, LLMResponseError, OllamaError, ValidationError, ValueError) as e2:
            raise ExtractionError(
                f"No se pudieron extraer datos válidos después de reintentar: {e2}"
            ) from e2


async def _extract_text_progressive(pdf_path: Path) -> tuple[str, str]:
    """Extrae texto con método progresivo: nativo → OCR → Ollama glm-ocr."""
    # Intento 1: Texto nativo + pytesseract (métodos existentes)
    try:
        texto, metodo = extract_text(pdf_path)
        if texto.strip():
            return texto, metodo
    except PDFExtractionError:
        pass

    # Intento 2: Ollama glm-ocr (fallback local)
    try:
        from pdf2image import convert_from_path

        logger.info("Intentando OCR con Ollama glm-ocr...")
        images = convert_from_path(pdf_path, dpi=300)
        text_parts: list[str] = []

        for _i, image in enumerate(images):
            # Guardar imagen temporalmente
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                image.save(tmp.name, "PNG")
                tmp_path = Path(tmp.name)

            try:
                page_text = await ocr_with_llm(tmp_path)
                text_parts.append(page_text)
            finally:
                tmp_path.unlink(missing_ok=True)

        texto = "\n".join(text_parts)
        if texto.strip():
            return texto, "ollama_glm_ocr"

    except Exception as e:
        logger.warning(f"Ollama OCR falló: {e}")

    raise PDFExtractionError(
        "No se pudo extraer texto del PDF con ningún método disponible"
    )


async def _extract_structured_data(texto: str) -> dict:
    """Envía texto al LLM y retorna datos parseados (OpenRouter u Ollama)."""
    try:
        return await extract_with_llm(texto)
    except (LLMError, LLMResponseError, OllamaError) as e:
        raise ExtractionError(f"Error en extracción LLM: {e}") from e


def _parse_and_validate(raw_data: dict, metodo: str) -> FacturaDIAN:
    """Parsea y valida los datos crudos del LLM contra el schema FacturaDIAN."""
    # Normalizar valores numéricos
    for field in ["subtotal", "iva_total", "total"]:
        if field in raw_data:
            raw_data[field] = _to_decimal(raw_data[field])

    if "items" in raw_data:
        for item in raw_data["items"]:
            for field in ["precio_unitario", "iva"]:
                if field in item:
                    item[field] = _to_decimal(item[field])

    # Calcular confianza basada en completitud
    required_fields = [
        "nit_emisor", "nombre_emisor", "nit_receptor", "nombre_receptor",
        "numero_factura", "fecha_emision", "subtotal", "iva_total", "total",
    ]
    filled = sum(1 for f in required_fields if raw_data.get(f))
    confianza = filled / len(required_fields)

    raw_data["confianza"] = round(confianza, 2)

    return FacturaDIAN(**raw_data)


def _to_decimal(value) -> Decimal:
    """Convierte un valor a Decimal de forma segura.

    Maneja formatos: 100000, 100.000 (europeo), 100,000 (US), 100.50
    """
    if value is None:
        return Decimal("0")
    try:
        if isinstance(value, str):
            if "," in value and "." in value:
                if value.rindex(",") > value.rindex("."):
                    value = value.replace(".", "").replace(",", ".")
                else:
                    value = value.replace(",", "")
            elif "," in value:
                parts = value.split(",")
                if len(parts) == 2 and len(parts[1]) == 2:
                    value = value.replace(",", ".")
                else:
                    value = value.replace(",", "")
            elif "." in value:
                parts = value.split(".")
                if len(parts) == 2 and len(parts[1]) == 3 and parts[1].isdigit():
                    value = value.replace(".", "")
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")
