"""Router de facturas — POST /extraer, GET /historial."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_token
from app.config import settings
from app.database import get_historial, get_session, save_extraccion
from app.extractor import ExtractionError, extract_factura
from app.models import (
    ErrorResponse,
    ExtraccionResponse,
    HistorialItem,
    HistorialResponse,
)
from app.services.pdf_reader import PDFExtractionError

router = APIRouter(prefix="/facturas", tags=["facturas"])


@router.post(
    "/extraer",
    response_model=ExtraccionResponse,
    responses={
        401: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def extraer_factura(
    archivo: UploadFile,
    _username: str = Depends(verify_token),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ExtraccionResponse:
    """Extrae datos de una factura colombiana (PDF).

    Acepta un archivo PDF (multipart/form-data). Detecta si es texto nativo
    o escaneado, extrae el texto, envía al LLM y retorna datos validados.
    """
    # Validar tipo de archivo
    if archivo.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se permiten archivos PDF",
        )

    # Validar tamaño
    contents = await archivo.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo excede el tamaño máximo de {settings.max_file_size_mb}MB",
        )

    # Guardar temporalmente
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = Path(tmp.name)

        # Extraer datos
        nombre_archivo = archivo.filename or "factura.pdf"
        factura = await extract_factura(tmp_path, nombre_archivo)

        # Guardar en BD
        datos_json = factura.model_dump_json()
        extraccion_id = await save_extraccion(
            session=session,
            nombre_archivo=nombre_archivo,
            datos_json=datos_json,
            nit_emisor=factura.nit_emisor,
            nombre_emisor=factura.nombre_emisor,
            total=factura.total,
            estado="exito",
        )

        return ExtraccionResponse(
            id=extraccion_id,
            fecha=datetime.combine(factura.fecha_emision, datetime.min.time(), tzinfo=UTC),
            nombre_archivo=nombre_archivo,
            datos=factura,
            estado="exito",
        )

    except ExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    except PDFExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando PDF: {e}",
        ) from e
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


@router.get(
    "/historial",
    response_model=HistorialResponse,
    responses={401: {"model": ErrorResponse}},
)
async def historial(
    offset: int = 0,
    limit: int = 20,
    _username: str = Depends(verify_token),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> HistorialResponse:
    """Obtiene el historial de extracciones paginado."""
    if limit > 100:
        limit = 100
    if offset < 0:
        offset = 0

    items_db, total = await get_historial(session, offset, limit)

    items = []
    for item in items_db:
        items.append(
            HistorialItem(
                id=item.id,
                fecha=item.fecha,
                nombre_archivo=item.nombre_archivo,
                nit_emisor=item.nit_emisor,
                nombre_emisor=item.nombre_emisor,
                total=item.total,
                estado=item.estado,
            )
        )

    return HistorialResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )
