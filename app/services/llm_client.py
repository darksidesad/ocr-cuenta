"""Cliente para OpenRouter (LLM) — extracción de datos de facturas."""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

EXTRACTION_PROMPT = (
    "Eres un experto en facturas colombianas DIAN. "
    "Extrae los siguientes campos del texto de la factura "
    "y responde SOLO con JSON válido:\n\n"
    "{\n"
    '  "nit_emisor": "string - NIT del emisor sin puntos ni guiones",\n'
    '  "nombre_emisor": "string - Razón social del emisor",\n'
    '  "nit_receptor": "string - NIT del receptor",\n'
    '  "nombre_receptor": "string - Razón social del receptor",\n'
    '  "numero_factura": "string - Número consecutivo de la factura",\n'
    '  "fecha_emision": "YYYY-MM-DD",\n'
    '  "cufe": "string o null - Código Único de Facturación Electrónica",\n'
    '  "items": [{"descripcion": "string", "cantidad": 0.0, '
    '"precio_unitario": 0.0, "iva": 0.0}],\n'
    '  "subtotal": 0.0, "iva_total": 0.0, "total": 0.0, "moneda": "COP"\n'
    "}\n\n"
    "Si un campo no se encuentra en el texto, usa null para campos opcionales "
    "o cadena vacía para campos requeridos. Los valores numéricos deben ser "
    "sin formato (sin puntos ni comas de miles). "
    "Responde ÚNICAMENTE con el JSON, sin texto adicional."
)


class LLMError(Exception):
    """Error al comunicarse con el LLM."""


class LLMResponseError(Exception):
    """Error en la respuesta del LLM (JSON inválido)."""


async def extract_with_llm(text: str) -> dict:
    """Envía el texto extraído a OpenRouter y retorna los datos parseados.

    Usa Gemini Flash con structured outputs (response_format: json_object).
    """
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ocr-dian.local",
        "X-Title": "OCR DIAN",
    }

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "user",
                "content": f"{EXTRACTION_PROMPT}\n\n--- TEXTO DE LA FACTURA ---\n{text}",
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=payload)

            if response.status_code != 200:
                error_detail = response.text[:500]
                raise LLMError(
                    f"OpenRouter retornó status {response.status_code}: {error_detail}"
                )

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return _parse_json_response(content)

    except httpx.TimeoutException as err:
        raise LLMError("Timeout al conectar con OpenRouter (30s)") from err
    except httpx.ConnectError as err:
        raise LLMError("No se pudo conectar con OpenRouter") from err
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"Error inesperado con OpenRouter: {e}") from e


def _parse_json_response(content: str) -> dict:
    """Parsea la respuesta JSON del LLM."""
    try:
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMResponseError(
            f"Respuesta del LLM no es JSON válido: {e}"
        ) from e
