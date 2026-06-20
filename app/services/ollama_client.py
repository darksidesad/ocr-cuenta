"""Cliente Ollama — fallback local cuando no hay OpenRouter."""

import base64
import json
import logging
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = (
    "Eres un experto en facturas colombianas DIAN. "
    "Extrae los siguientes campos del texto de la factura "
    "y responde SOLO con JSON válido:\n\n"
    "{\n"
    '  "nit_emisor": "string",\n'
    '  "nombre_emisor": "string",\n'
    '  "nit_receptor": "string",\n'
    '  "nombre_receptor": "string",\n'
    '  "numero_factura": "string",\n'
    '  "fecha_emision": "YYYY-MM-DD",\n'
    '  "cufe": "string o null",\n'
    '  "items": [{"descripcion": "string", "cantidad": 0.0, '
    '"precio_unitario": 0.0, "iva": 0.0}],\n'
    '  "subtotal": 0.0, "iva_total": 0.0, "total": 0.0, "moneda": "COP"\n'
    "}\n\n"
    "Responde ÚNICAMENTE con el JSON, sin texto adicional."
)

OCR_PROMPT = (
    "Extrae TODO el texto de esta imagen de factura colombiana DIAN. "
    "Incluye NIT, nombre, número de factura, fecha, CUFE, ítems, "
    "cantidades, precios, IVA, subtotal y total. "
    "Respeta el formato original del documento."
)


class OllamaError(Exception):
    """Error al comunicarse con Ollama."""


class OllamaResponseError(Exception):
    """Error en la respuesta de Ollama (JSON inválido)."""


async def ensure_model(model_name: str | None = None) -> bool:
    """Verifica si el modelo existe en Ollama. Lo descarga si no existe."""
    model = model_name or settings.ollama_model

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Verificar modelos instalados
            resp = await client.get(f"{settings.ollama_host}/api/tags")
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                if model in models or f"{model}:latest" in models:
                    logger.info(f"Modelo {model} ya instalado en Ollama")
                    return True

            # Descargar modelo
            logger.info(f"Descargando modelo {model} desde Ollama...")
            resp = await client.post(
                f"{settings.ollama_host}/api/pull",
                json={"name": model},
                timeout=300.0,
            )
            if resp.status_code == 200:
                logger.info(f"Modelo {model} descargado exitosamente")
                return True
            else:
                logger.error(f"Error descargando modelo: {resp.status_code}")
                return False

    except httpx.ConnectError:
        logger.error("No se pudo conectar a Ollama")
        return False
    except Exception as e:
        logger.error(f"Error verificando modelo Ollama: {e}")
        return False


async def ocr_with_ollama(image_path: Path) -> str:
    """Extrae texto de una imagen usando Ollama glm-ocr."""
    model = settings.ollama_model

    # Leer imagen y convertir a base64
    image_bytes = image_path.read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": model,
        "prompt": OCR_PROMPT,
        "images": [image_b64],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 4096},
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.ollama_host}/api/generate", json=payload
            )

            if resp.status_code != 200:
                raise OllamaError(f"Ollama OCR retornó status {resp.status_code}")

            data = resp.json()
            text = data.get("response", "")
            if not text.strip():
                raise OllamaError("Ollama OCR retornó texto vacío")
            return text.strip()

    except httpx.TimeoutException as err:
        raise OllamaError("Timeout en Ollama OCR (120s)") from err
    except httpx.ConnectError as err:
        raise OllamaError("No se pudo conectar a Ollama") from err
    except OllamaError:
        raise
    except Exception as e:
        raise OllamaError(f"Error inesperado en Ollama OCR: {e}") from e


async def extract_with_ollama(text: str) -> dict:
    """Envía texto a Ollama para extracción estructurada de factura."""
    model = settings.ollama_model

    payload = {
        "model": model,
        "prompt": f"{EXTRACTION_PROMPT}\n\n--- TEXTO DE LA FACTURA ---\n{text}",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_predict": 4096},
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.ollama_host}/api/generate", json=payload
            )

            if resp.status_code != 200:
                raise OllamaError(f"Ollama retornó status {resp.status_code}")

            data = resp.json()
            content = data.get("response", "")
            return _parse_json_response(content)

    except httpx.TimeoutException as err:
        raise OllamaError("Timeout en Ollama (120s)") from err
    except httpx.ConnectError as err:
        raise OllamaError("No se pudo conectar a Ollama") from err
    except OllamaError:
        raise
    except Exception as e:
        raise OllamaError(f"Error inesperado en Ollama: {e}") from e


def _parse_json_response(content: str) -> dict:
    """Parsea la respuesta JSON de Ollama."""
    try:
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise OllamaResponseError(
            f"Respuesta de Ollama no es JSON válido: {e}"
        ) from e
