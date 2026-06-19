# Arquitectura — OCR DIAN

## Stack

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Backend | Python + FastAPI | 3.11 |
| LLM | OpenRouter (Gemini Flash) | google/gemini-2.0-flash-001 |
| OCR (texto nativo) | pdfplumber | ≥0.10.0 |
| OCR (escaneados) | pdf2image + pytesseract | ≥1.16.0 / ≥0.3.10 |
| Validación | Pydantic v2 | ≥2.0.0 |
| Auth | PyJWT | ≥2.8.0 |
| DB Driver | asyncpg | ≥0.29.0 |
| DB ORM | SQLAlchemy (async) | ≥2.0.0 |
| Frontend | Streamlit | ≥1.30.0 |
| DB | PostgreSQL | 15 |
| Deploy | Docker Compose | latest |

## Diagrama de componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                          │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │  Streamlit   │───▶│    FastAPI App    │───▶│  PostgreSQL  │  │
│  │  :8501       │    │    :8000          │    │  :5432       │  │
│  │              │    │                   │    │              │  │
│  │  ui/         │    │  app/             │    │  facturas_db │  │
│  │  streamlit_  │    │  ├── main.py      │    │              │  │
│  │  app.py      │    │  ├── config.py    │    └──────────────┘  │
│  └──────────────┘    │  ├── auth.py      │                      │
│                      │  ├── models.py    │    ┌──────────────┐  │
│                      │  ├── database.py  │    │  OpenRouter   │  │
│                      │  ├── extractor.py │───▶│  API          │  │
│                      │  ├── routers/     │    │  (Gemini)     │  │
│                      │  └── services/    │    └──────────────┘  │
│                      └──────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

## Flujo de datos principal

### Extracción de factura

```
1. POST /facturas/extraer (multipart/form-data)
   │
   ▼
2. Validar JWT token (auth middleware)
   │
   ▼
3. Validar archivo (tipo PDF, tamaño ≤ MAX_FILE_SIZE_MB)
   │
   ▼
4. Guardar archivo temporalmente en /tmp
   │
   ▼
5. Detectar tipo de PDF
   │
   ├── Texto nativo → pdfplumber.extract_text()
   │     └── Si texto vacío → fallback a OCR
   │
   └── Escaneado → pdf2image.convert_from_path()
         └── pytesseract.image_to_string()
   │
   ▼
6. Construir prompt para LLM
   │  "Extrae datos de esta factura colombiana DIAN.
   │   Responde SOLO con JSON válido con este schema: ..."
   │
   ▼
7. Enviar a OpenRouter (Gemini Flash)
   │  POST https://openrouter.ai/api/v1/chat/completions
   │  Body: { model, messages, response_format: { type: "json_object" } }
   │
   ▼
8. Parsear respuesta JSON
   │
   ▼
9. Validar con Pydantic (FacturaDIAN schema)
   │
   ├── Válido → Continuar
   └── Inválido → Reintentar 1 vez con prompt corregido
         └── Sigue inválido → Raises ExtractionError
   │
   ▼
10. Guardar en PostgreSQL (extracciones table)
   │
   ▼
11. Retornar JSON validado al cliente
```

### Autenticación

```
1. POST /auth/login { username, password }
   │
   ▼
2. Validar contra APP_USERNAME / APP_PASSWORD (env vars)
   │
   ├── Válido → Generar JWT (payload: sub, exp)
   └── Inválido → 401 Unauthorized
   │
   ▼
3. Token en Header: Authorization: Bearer <token>
   │
   ▼
4. Middleware valida token en cada request protegido
   │
   ├── Válido → Continuar
   ├── Expirado → 401 "Token expirado"
   └── Inválido → 401 "Token inválido"
```

## Decisiones técnicas

| Decisión | Alternativas consideradas | Justificación |
|----------|--------------------------|---------------|
| OpenRouter sobre OpenAI directo | OpenAI, Anthropic, local LLM (Ollama) | Costo bajo (Gemini Flash ~$0.0001/1K tokens), sin lock-in, structured outputs nativos |
| pdfplumber sobre PyMuPDF | PyMuPDF, pdfminer, tabula-py | Mejor extracción de tablas, API simple, texto nativo confiable |
| pytesseract sobre EasyOCR | EasyOCR, PaddleOCR | Más ligero, mejor para español, fallback suficiente |
| Streamlit sobre React/Vue | React, Vue, HTMX, Gradio | Velocidad de desarrollo, Python fullstack, widgets nativos |
| JWT simple sobre OAuth2/OIDC | OAuth2, sesiones server-side, API keys | Sin BD de usuarios v1, stateless, implementación mínima |
| PostgreSQL sobre SQLite | SQLite, MongoDB, JSON files | Escalabilidad futura, JSON type nativo, historial real con queries |
| SQLAlchemy async sobre tortoise | tortoise-orm, raw asyncpg | Ecosistema maduro, async nativo, migraciones con alembic |
| Síncrono sobre Celery | Celery+Redis, RQ, dramatiq | V1 no requiere colas, simplifica deploy, reduce dependencias |
| Pydantic v2 sobre marshmallow | marshmallow, cerberus, jsonschema | Validación nativa de FastAPI, structured outputs, rendimiento |

## Puntos de fallo identificados

| Componente | Fallo posible | Mitigación |
|------------|--------------|-----------|
| OpenRouter API | Caída, rate limit, timeout | Retry con backoff exponencial (3 intentos), timeout 30s, error message claro |
| PDF escaneado | pytesseract no extrae texto | Validar confianza OCR, retornar error si < 0.3, sugerir archivo de mejor calidad |
| PDF corrupto | pdfplumber/pytesseract fallan | Try/except específico por tipo de error, mensaje descriptivo |
| PostgreSQL | Conexión perdida, timeout | Healthcheck en docker-compose, pool con max_overflow, reconnect on fail |
| Archivo muy grande | Memoria agotada | MAX_FILE_SIZE_MB validation antes de procesar |
| JWT expirado | Request rechazado | Redirect a login en UI, mensaje "Sesión expirada" |
| LLM JSON inválido | Pydantic validation falla | Reintentar 1 vez con prompt corregido, luego ExtractionError |

## Seguridad

### Variables de entorno
- Ningún secret hardcodeado en código fuente
- `.env.example` tiene todas las variables (sin valores reales)
- `.gitignore` excluye `.env`, `*.key`, secrets

### Autenticación
- JWT con expiración (JWT_EXPIRE_MINUTES, default 8h)
- Password en env var, nunca en responses
- Todos los endpoints protegidos excepto `/auth/login` y `/health`

### Upload de archivos
- Validación de tipo MIME (application/pdf)
- Validación de tamaño (MAX_FILE_SIZE_MB)
- Archivos temporales eliminados después de procesar
- No se guardan PDFs en disco permanente

### CORS
- Permitir solo origen de Streamlit UI (localhost:8501 en dev)
- Configurable via env var para producción

### Rate limiting
- No implementado en v1 (single user)
- Prever para v2: slowapi o nginx rate limiting

## Performance targets

| Métrica | Target |
|---------|--------|
| API login | < 500ms p95 |
| API extracción (texto nativo) | < 15s p95 |
| API extracción (OCR fallback) | < 30s p95 |
| API historial | < 200ms p95 |
| UI load | < 3s |
| DB query historial | < 100ms p95 |

## Design tokens (UI Streamlit)

| Token | Valor | Uso |
|-------|-------|-----|
| primary_color | #1f77b4 | Botones, links |
| secondary_color | #ff7f0e | Alertas, warnings |
| success_color | #2ca02c | Éxito, extracción válida |
| error_color | #d62728 | Errores, validación fallida |
| background | #ffffff | Fondo principal |
| text_color | #333333 | Texto principal |
| font_family | system-ui | Fuente principal |
| border_radius | 8px | Bordes de componentes |
| spacing_sm | 8px | Espaciado pequeño |
| spacing_md | 16px | Espaciado medio |
| spacing_lg | 24px | Espaciado grande |
