"""Lógica principal de extracción de datos de facturas colombianas."""

import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pydantic import ValidationError

from app.models import FacturaDIAN
from app.services.llm_client import LLMError, LLMResponseError, extract_with_llm
from app.services.pdf_reader import PDFExtractionError, extract_text

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Error durante el proceso de extracción de datos."""


async def extract_factura(pdf_path: Path, nombre_archivo: str) -> FacturaDIAN:
    """Extrae datos de una factura colombiana desde un PDF.

    Flujo:
    1. Extraer texto (texto nativo o OCR)
    2. Enviar a LLM para extracción estructurada
    3. Validar con Pydantic
    4. Retornar FacturaDIAN validado
    """
    # Paso 1: Extraer texto
    try:
        texto, metodo = extract_text(pdf_path)
        logger.info(f"Texto extraído con método: {metodo} ({len(texto)} caracteres)")
    except PDFExtractionError as e:
        raise ExtractionError(f"Error extrayendo texto del PDF: {e}") from e

    # Paso 2: Enviar a LLM
    try:
        raw_data = await extract_with_llm(texto)
        logger.info("LLM retornó respuesta válida")
    except (LLMError, LLMResponseError) as e:
        raise ExtractionError(f"Error en extracción LLM: {e}") from e

    # Paso 3: Validar con Pydantic
    try:
        raw_data["metodo_extraccion"] = metodo
        factura = _parse_and_validate(raw_data, metodo)
        logger.info(f"Extracción exitosa: factura {factura.numero_factura}")
        return factura
    except (ValidationError, ValueError) as e:
        # Reintentar una vez con prompt corregido
        logger.warning(f"Validación falló, reintentando: {e}")
        try:
            retry_text = (
                texto
                + "\n\nNOTA IMPORTANTE: Asegúrate de que todos los campos numéricos "
                "sean valores puros (sin puntos ni comas). "
                "La fecha debe estar en formato YYYY-MM-DD."
            )
            raw_data_retry = await extract_with_llm(retry_text)
            raw_data_retry["metodo_extraccion"] = metodo
            return _parse_and_validate(raw_data_retry, metodo)
        except (LLMError, LLMResponseError, ValidationError, ValueError) as e2:
            raise ExtractionError(
                f"No se pudieron extraer datos válidos después de reintentar: {e2}"
            ) from e2


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
            # Si tiene coma Y punto, determinar cuál es el separador decimal
            if "," in value and "." in value:
                # 1.000,50 → europeo, 1,000.50 → US
                if value.rindex(",") > value.rindex("."):
                    value = value.replace(".", "").replace(",", ".")
                else:
                    value = value.replace(",", "")
            elif "," in value:
                # Podría ser 100,000 (US) o 100,5 (europeo decimal)
                parts = value.split(",")
                if len(parts) == 2 and len(parts[1]) == 2:
                    value = value.replace(",", ".")
                else:
                    value = value.replace(",", "")
            # Si solo tiene puntos, verificar si es miles o decimal
            elif "." in value:
                parts = value.split(".")
                if len(parts) == 2 and len(parts[1]) == 3 and parts[1].isdigit():
                    value = value.replace(".", "")
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")
