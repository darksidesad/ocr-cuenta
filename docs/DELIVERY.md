# Entrega Final — OCR DIAN

## Resumen
Servicio de extracción automática de datos de facturas colombianas (DIAN) usando OCR + LLMs con structured outputs. Permite a contadores y administradores subir facturas PDF y obtener datos extraídos (NIT, CUFE, ítems, totales) en JSON validado con Pydantic.

## Estado
- **Tests:** 71/71 pasando (100%)
- **Coverage:** 89.06%
- **Loops de crítica necesarios:** 1
- **DOD completado:** ✅

## Archivos generados

| Archivo | Descripción |
|---------|-------------|
| `app/__init__.py` | Package init |
| `app/main.py` | FastAPI app, lifespan, CORS, healthcheck |
| `app/config.py` | Settings desde .env (pydantic-settings) |
| `app/auth.py` | JWT create/verify, authenticate_user |
| `app/models.py` | Pydantic schemas (FacturaDIAN, responses) |
| `app/database.py` | SQLAlchemy async, Extraccion model |
| `app/extractor.py` | Lógica principal de extracción con retry |
| `app/routers/__init__.py` | Package init |
| `app/routers/auth.py` | POST /auth/login |
| `app/routers/facturas.py` | POST /extraer, GET /historial |
| `app/services/__init__.py` | Package init |
| `app/services/pdf_reader.py` | pdfplumber + pytesseract |
| `app/services/llm_client.py` | OpenRouter client |
| `ui/streamlit_app.py` | Frontend Streamlit (login + extractor + historial) |
| `tests/conftest.py` | Fixtures compartidos (DB, client) |
| `tests/unit/test_models.py` | 14 tests de modelos Pydantic |
| `tests/unit/test_auth.py` | 11 tests de autenticación JWT |
| `tests/unit/test_pdf_reader.py` | 12 tests de extracción PDF |
| `tests/unit/test_llm_client.py` | 7 tests del cliente LLM |
| `tests/unit/test_extractor.py` | 8 tests del extractor |
| `tests/integration/test_auth_api.py` | 4 tests de endpoints auth |
| `tests/integration/test_facturas_api.py` | 6 tests de endpoints facturas |
| `tests/e2e/test_flujo_completo.py` | 4 tests E2E con Playwright |
| `Dockerfile` | API multi-stage, usuario no-root |
| `Dockerfile.ui` | Streamlit, usuario no-root |
| `docker-compose.yml` | 3 servicios con healthchecks |
| `.gitignore` | Python, env, IDE, OS, uploads |
| `requirements.txt` | Dependencias con versiones exactas |
| `pyproject.toml` | Config proyecto, ruff, pytest, coverage |
| `.env.example` | 7 variables de entorno documentadas |
| `README.md` | Setup instructions ejecutables |
| `scripts/start.sh` | Inicio rápido |
| `scripts/migrate.sh` | Migración de DB |
| `scripts/test.sh` | Linting + tests |
| `docs/BRIEF.md` | Brief del proyecto |
| `docs/STACK.md` | Stack técnico |
| `docs/PRD.md` | Product Requirements Document |
| `docs/DOD.md` | Definition of Done |
| `docs/USER_FLOWS.md` | Flujos de usuario |
| `docs/architecture.md` | Arquitectura técnica |
| `docs/ADR-001.md` | Decisión: OpenRouter + Gemini Flash |
| `docs/critique_v1.md` | Crítica iteración 1 |
| `docs/loop_history.md` | Historial de loops |
| `.opencode/agents/orchestrator.md` | Agente coordinador |
| `.opencode/agents/developer.md` | Agente de código |
| `.opencode/agents/qa.md` | Agente de testing |
| `.opencode/agents/devops.md` | Agente de infraestructura |
| `.opencode/skills/ocr-extraction/SKILL.md` | Skill de extracción OCR |

## Instrucciones de ejecución

### Setup inicial
```bash
cd ocr-dian
cp .env.example .env

# Editar .env con tus valores:
# OPENROUTER_API_KEY=tu-api-key
# JWT_SECRET_KEY=tu-clave-secreta (generar con: python -c "import secrets; print(secrets.token_urlsafe(32))")
# APP_PASSWORD=tu-contraseña
```

### Con Docker Compose (recomendado)
```bash
docker-compose up -d --build
```

### Sin Docker (desarrollo)
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Solo PostgreSQL (con Docker):
docker run -d --name facturas-pg -p 5432:5432 \
  -e POSTGRES_USER=facturas_user \
  -e POSTGRES_PASSWORD=change_me \
  -e POSTGRES_DB=facturas_db \
  postgres:15-alpine

# Backend:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (otra terminal):
streamlit run ui/streamlit_app.py --server.port 8501
```

### Verificar que funciona
```bash
# Healthcheck
curl http://localhost:8000/health

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"tu-contraseña"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Extraer factura
curl -X POST http://localhost:8000/facturas/extraer \
  -H "Authorization: Bearer $TOKEN" \
  -F "archivo=@factura.pdf"

# Ver historial
curl http://localhost:8000/facturas/historial \
  -H "Authorization: Bearer $TOKEN"

# Ejecutar tests
pytest --tb=short -q
```

### Endpoints principales

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/health` | Healthcheck | No |
| POST | `/auth/login` | Login → JWT token | No |
| POST | `/facturas/extraer` | Extraer datos de factura PDF | Sí |
| GET | `/facturas/historial` | Historial paginado | Sí |

## Limitaciones conocidas
- **Procesamiento síncrono:** No usa Celery/Redis. Extracciones largas bloquean el thread.
- **Sin multi-tenant:** Un solo usuario (credenciales en .env).
- **Sin refresh token:** JWT expira sin renovación automática.
- **PDFs escaneados:** Dependen de la calidad del OCR (pytesseract). PDFs de baja calidad pueden fallar.
- **Sin validación de magic bytes:** Solo valida content-type, no la estructura real del PDF.
- **Playwright E2E:** Tests E2E requieren servidor corriendo (no ejecutan en CI sin setup).

## Deuda técnica identificada
- `alembic` está en pyproject.toml pero no se usa (pendiente para migraciones futuras)
- No hay rate limiting en endpoints públicos (v1 single user)
- No hay logging estructurado (JSON logs)
- No hay métricas ni monitoring
- No hay refresh token para JWT
- CORS no validate origins contra whitelist

## Próximos pasos recomendados
1. **Deploy real:** Levantar en VPS con dominio + HTTPS (nginx reverse proxy)
2. **Rate limiting:** Agregar slowapi o nginx rate limiting para producción
3. **Migraciones:** Configurar Alembic para schema evolution de PostgreSQL
