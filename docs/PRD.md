# Product Requirements Document — OCR DIAN

## Objetivo
Automatizar la extracción de datos de facturas colombianas (DIAN) a partir de PDFs, usando OCR + LLMs con structured outputs, reemplazando el proceso manual de digitación por contadores y administradores.

## Usuarios objetivo
- **Primario:** Contadores y administradores de empresas colombianas que reciben facturas PDF (electrónicas DIAN o escaneadas) y necesitan extraer datos para sistemas contables.
- **Secundario:** Cualquier usuario con facturas colombianas que necesite digitalizar datos de facturas.

## Flujo principal del usuario
1. Abrir la aplicación Streamlit
2. Ingresar credenciales (usuario/contraseña) → login JWT
3. Navegar a la pantalla del extractor
4. Subir un archivo PDF de factura colombiana
5. Verificar que el sistema procesa el archivo (detecta tipo, extrae texto, envía a LLM)
6. Visualizar los datos extraídos en formato estructurado (JSON + campos renderizados)
7. Copiar el JSON o descargar el resultado
8. Ver historial de extracciones anteriores

## Funcionalidades MVP

### F1 — Autenticación JWT
- Login con credenciales de variables de entorno
- Token JWT con expiración configurable (default 8h)
- Todos los endpoints protegidos excepto `/auth/login` y `/health`

### F2 — Extracción de factura
- Endpoint `POST /facturas/extraer` (multipart/form-data)
- Validación de tamaño máximo de archivo (MAX_FILE_SIZE_MB)
- Detección automática de tipo de PDF:
  - **Texto nativo:** PDFs generados electrónicamente → pdfplumber
  - **Escaneado:** PDFs imagen → pdf2image + pytesseract (fallback)
- Envío de texto extraído a OpenRouter (Gemini Flash) con prompt estructurado
- Parseo y validación de respuesta con Pydantic (schema FacturaDIAN)
- Guardado de extracción en PostgreSQL
- Retorno de JSON validado al frontend

### F3 — Campos extraídos
| Campo | Tipo | Descripción |
|-------|------|-------------|
| nit_emisor | str | NIT del emisor de la factura |
| nombre_emisor | str | Razón social del emisor |
| nit_receptor | str | NIT del receptor |
| nombre_receptor | str | Razón social del receptor |
| numero_factura | str | Número consecutivo de la factura |
| fecha_emision | date | Fecha de emisión |
| cufe | str \| None | Código Único de Facturación Electrónica |
| items | list | Lista de ítems (descripción, cantidad, precio unitario, IVA) |
| subtotal | Decimal | Subtotal antes de IVA |
| iva_total | Decimal | Total de IVA |
| total | Decimal | Total de la factura |
| moneda | str | Moneda (default: COP) |
| metodo_extraccion | str | "texto_nativo" o "ocr_fallback" |
| confianza | float | Nivel de confianza (0.0 a 1.0) |

### F4 — Historial de extracciones
- Endpoint `GET /facturas/historial` con paginación
- Muestra: fecha, nombre archivo, NIT emisor, total, estado
- Paginación simple (offset/limit)

### F5 — UI Streamlit
- Pantalla 1: Login
- Pantalla 2: Extractor (subir archivo + ver resultado + historial)
- Feedback visual durante procesamiento (spinner/progress)
- Renderizado del JSON extraído con opción de copiar

## Funcionalidades fuera de scope v1
- Multi-tenant / múltiples empresas por usuario
- Integración con sistemas contables (Siigo, World Office)
- Facturas en formatos distintos a PDF
- Procesamiento por lotes masivo
- Celery, Redis o cualquier sistema de colas
- Edición manual de datos extraídos
- Exportación a Excel/CSV
- Soporte para facturas de otros países

## Restricciones técnicas
- Procesamiento síncrono (sin colas)
- PDFs de hasta MAX_FILE_SIZE_MB (default 10MB)
- JWT sin refresh token en v1
- Contraseña de usuario en variables de entorno (no BD de usuarios)
- Deploy con Docker Compose en VPS local
- Puertos: 8000 (API), 8501 (UI), 5432 (DB)

## Riesgos identificados
| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| OpenRouter caído o rate limited | Alto — extracciones fallan | Retry con backoff, mensaje de error claro |
| PDF escaneado de baja calidad | Medio — OCR falla | Validar confianza, retornar error si < 0.3 |
| PDF corrupto o no facturable | Medio — procesamiento falla | Validación de archivo antes de procesar |
| LLM retorna JSON inválido | Medio — parseo falla | Validación Pydantic estricta, reintentar 1 vez |
| PostgreSQL no disponible | Alto — no guarda historial | Healthcheck en docker-compose |

## Cronograma estimado
| Fase | Tiempo estimado |
|------|----------------|
| FASE 0: Brief y Stack | Completada |
| FASE 1: Creación (5 pasos) | 2-3 sesiones |
| FASE 2: Loop de Crítica | 1-2 sesiones |
| FASE 3: Pre-entrega | 1 sesión |
| FASE 4: Entrega | 1 sesión |
| **Total estimado** | **5-7 sesiones** |
