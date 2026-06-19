"""Modelos Pydantic para validación de datos."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class LoginRequest(BaseModel):
    """Solicitud de login."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Respuesta con token JWT."""

    access_token: str
    token_type: str = "bearer"


class ItemFactura(BaseModel):
    """Ítem de una factura colombiana."""

    model_config = ConfigDict(from_attributes=True)

    descripcion: str
    cantidad: float
    precio_unitario: Decimal
    iva: Decimal


class FacturaDIAN(BaseModel):
    """Schema de extracción de factura colombiana DIAN."""

    model_config = ConfigDict(from_attributes=True)

    # Emisor
    nit_emisor: str
    nombre_emisor: str
    # Receptor
    nit_receptor: str
    nombre_receptor: str
    # Factura
    numero_factura: str
    fecha_emision: date
    cufe: str | None = None
    # Items
    items: list[ItemFactura]
    # Totales
    subtotal: Decimal
    iva_total: Decimal
    total: Decimal
    moneda: str = "COP"
    # Metadata
    metodo_extraccion: Literal["texto_nativo", "ocr_fallback"]
    confianza: float

    @field_validator("confianza")
    @classmethod
    def validate_confianza(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confianza debe estar entre 0.0 y 1.0")
        return v

    @field_validator("nit_emisor", "nit_receptor")
    @classmethod
    def validate_nit(cls, v: str) -> str:
        return v.strip() if v else v


class ExtraccionResponse(BaseModel):
    """Respuesta de una extracción exitosa."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    nombre_archivo: str
    datos: FacturaDIAN
    estado: str


class HistorialItem(BaseModel):
    """Item del historial de extracciones."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime
    nombre_archivo: str
    nit_emisor: str
    nombre_emisor: str
    total: Decimal
    estado: str


class HistorialResponse(BaseModel):
    """Respuesta paginada del historial."""

    items: list[HistorialItem]
    total: int
    offset: int
    limit: int


class ErrorResponse(BaseModel):
    """Respuesta de error estándar."""

    detail: str
