# Brief del Proyecto — OCR DIAN

## Problema que resuelve
Las empresas colombianas reciben facturas en PDF (electrónicas DIAN y escaneadas) y extraen los datos manualmente. Este servicio automatiza la extracción de campos clave con validación estructurada usando OCR + LLMs.

## Usuarios principales
Contadores y administradores de empresas colombianas.

## Flujo principal del usuario
1. Login con credenciales (usuario/contraseña)
2. Subir factura PDF (electrónica DIAN o escaneada)
3. Ver datos extraídos en JSON + UI
4. Descargar o copiar resultado

## Criterio mínimo de entrega (v1)
Subir una factura colombiana real → extraer correctamente:
- NIT emisor
- NIT receptor
- Número de factura
- Fecha
- CUFE
- Ítems con cantidad/precio/IVA
- Subtotal, IVA total y total
- Con una URL pública funcionando

## Fuera de scope v1
- Multi-tenant / múltiples empresas
- Integración con sistemas contables (Siigo, World Office)
- Facturas en formatos distintos a PDF
- Procesamiento por lotes masivo
- Celery, Redis, queues (procesamiento síncrono en v1)

## Campos objetivo (schema Pydantic)
| Campo | Tipo | Requerido |
|-------|------|-----------|
| nit_emisor | str | Sí |
| nombre_emisor | str | Sí |
| nit_receptor | str | Sí |
| nombre_receptor | str | Sí |
| numero_factura | str | Sí |
| fecha_emision | date | Sí |
| cufe | str \| None | No |
| items | list[ItemFactura] | Sí |
| subtotal | Decimal | Sí |
| iva_total | Decimal | Sí |
| total | Decimal | Sí |
| moneda | str | Sí (default: COP) |
| metodo_extraccion | Literal["texto_nativo", "ocr_fallback"] | Sí |
| confianza | float (0.0-1.0) | Sí |

## Variables de entorno definidas
| Variable | Propósito |
|----------|-----------|
| OPENROUTER_API_KEY | API key de OpenRouter para LLM |
| APP_USERNAME | Usuario para login JWT |
| APP_PASSWORD | Contraseña para login JWT |
| JWT_SECRET_KEY | Secret para firmar tokens |
| JWT_EXPIRE_MINUTES | Duración del token (default: 480) |
| DATABASE_URL | URL de conexión PostgreSQL |
| MAX_FILE_SIZE_MB | Tamaño máximo de archivo (default: 10) |
