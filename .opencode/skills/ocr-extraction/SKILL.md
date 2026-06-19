# Skill: OCR Extraction — Facturas Colombianas

## Overview
Skill especializado en extracción de datos de facturas colombianas (DIAN) usando pdfplumber para texto nativo y pytesseract para PDFs escaneados.

## When to Use
- Cuando se implementa la lógica de extracción de PDF
- Cuando se configuran los servicios de OCR
- Cuando se diseña el prompt para el LLM

## Workflow

### 1. Detección de tipo de PDF
```python
def detect_pdf_type(pdf_path: Path) -> str:
    """Detecta si un PDF es texto nativo o escaneado."""
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        if text and len(text.strip()) > 50:
            return "texto_nativo"
        return "escaneado"
```

### 2. Extracción de texto nativo
```python
def extract_native_text(pdf_path: Path) -> str:
    """Extrae texto de PDFs generados electrónicamente."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )
    return text.strip()
```

### 3. Extracción OCR (fallback)
```python
def extract_ocr_text(pdf_path: Path) -> str:
    """Extrae texto de PDFs escaneados usando OCR."""
    images = pdf2image.convert_from_path(pdf_path)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image, lang="spa") + "\n"
    return text.strip()
```

### 4. Prompt para LLM
```
Eres un experto en facturas colombianas DIAN. Extrae los siguientes campos 
del texto de la factura y responde SOLO con JSON válido:

{
  "nit_emisor": "string - NIT del emisor sin puntos ni guiones",
  "nombre_emisor": "string - Razón social del emisor",
  "nit_receptor": "string - NIT del receptor",
  "nombre_receptor": "string - Razón social del receptor",
  "numero_factura": "string - Número consecutivo",
  "fecha_emision": "YYYY-MM-DD",
  "cufe": "string o null - Código Único de Facturación Electrónica",
  "items": [
    {
      "descripcion": "string",
      "cantidad": number,
      "precio_unitario": number,
      "iva": number
    }
  ],
  "subtotal": number,
  "iva_total": number,
  "total": number,
  "moneda": "COP"
}

Si un campo no se encuentra en el texto, usa null para campos opcionales 
o cadena vacía para campos requeridos.
```

### 5. Validación Pydantic
```python
from pydantic import BaseModel, field_validator
from decimal import Decimal
from datetime import date
from typing import Literal

class ItemFactura(BaseModel):
    descripcion: str
    cantidad: float
    precio_unitario: Decimal
    iva: Decimal

class FacturaDIAN(BaseModel):
    nit_emisor: str
    nombre_emisor: str
    nit_receptor: str
    nombre_receptor: str
    numero_factura: str
    fecha_emision: date
    cufe: str | None = None
    items: list[ItemFactura]
    subtotal: Decimal
    iva_total: Decimal
    total: Decimal
    moneda: str = "COP"
    metodo_extraccion: Literal["texto_nativo", "ocr_fallback"]
    confianza: float

    @field_validator("confianza")
    @classmethod
    def validate_confianza(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confianza debe estar entre 0.0 y 1.0")
        return v
```

## Error Handling
| Error | Causa | Acción |
|-------|-------|--------|
| PDFExtractionError | pdfplumber falla | Intentar OCR fallback |
| OCRError | pytesseract falla | Retornar error "Calidad insuficiente" |
| LLMError | OpenRouter caído | Retry 3 veces, luego error |
| ValidationError | JSON inválido | Reintentar 1 vez, luego error |
| ExtractionError | Todos los métodos fallan | Error message claro al usuario |
