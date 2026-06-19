# Stack Técnico — OCR DIAN

## Stack seleccionado

| Capa | Tecnología | Versión | Justificación |
|------|-----------|---------|---------------|
| Backend | Python + FastAPI | Python 3.11 | Async nativo, Pydantic v2 integrado, rendimiento alto |
| LLM | OpenRouter | google/gemini-2.0-flash-001 | Barato, buen manejo de documentos, structured outputs |
| OCR/PDF (texto nativo) | pdfplumber | latest | Extrae texto de PDFs generados electrónicamente |
| OCR/PDF (escaneados) | pdf2image + pytesseract | latest | Fallback para PDFs escaneados/bajo calidad |
| Validación | Pydantic v2 | latest | Structured outputs, validación estricta de schema |
| Auth | JWT (PyJWT) | latest | Stateless, sin BD de usuarios en v1 |
| Frontend | Streamlit | latest | Rápido de implementar, mismo patrón que proyectos anteriores |
| DB | PostgreSQL | 15 | Historial de extracciones, queries paginadas |
| Deploy | Docker Compose | latest | 3 servicios: app, ui, db |

## Diagrama de componentes

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Streamlit UI  │────▶│   FastAPI App    │────▶│  PostgreSQL │
│   :8501         │     │   :8000          │     │  :5432      │
└─────────────────┘     └──────────────────┘     └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │  OpenRouter   │
                        │  (Gemini)    │
                        └──────────────┘
```

## Flujo de datos principal

```
1. POST /auth/login → retorna JWT
2. POST /facturas/extraer (multipart/form-data)
   → detectar tipo (texto nativo vs escaneado)
   → extraer texto (pdfplumber o pytesseract)
   → enviar prompt + texto a OpenRouter
   → parsear respuesta JSON con Pydantic
   → validar schema FacturaDIAN
   → guardar en PostgreSQL
   → retornar JSON validado
3. GET /facturas/historial → paginación de extracciones
```

## Decisiones técnicas

| Decisión | Alternativas | Justificación |
|----------|-------------|---------------|
| OpenRouter sobre OpenAI directo | OpenAI, Anthropic, local LLM | Costo bajo (Gemini Flash), sin lock-in, structured outputs |
| pdfplumber sobre PyMuPDF | PyMuPDF, pdfminer | Mejor extracción de tablas, más simple para texto nativo |
| Streamlit sobre React | React, Vue, HTMX | Velocidad de desarrollo, mismo patrón conocido |
| JWT simple sobre OAuth2 | OAuth2, sesiones | Sin BD de usuarios v1, stateless, simplest |
| PostgreSQL sobre SQLite | SQLite, MongoDB | Escalabilidad futura, JSON support, historial real |
| Síncrono sobre Celery | Celery + Redis, RQ | V1 no requiere colas, simplifica deploy |

## Puntos de fallo identificados

| Componente | Fallo posible | Mitigación |
|------------|--------------|-----------|
| OpenRouter | API caírate o rate limited | Retry con backoff, mensaje de error claro al usuario |
| PDF escaneado | pytesseract no extrae texto | Validar confianza, retornar error si < 0.3 |
| PDF corrupto | pdfplumber falla | Try/except con mensaje específico |
| PostgreSQL | Conexión perdida | Healthcheck en docker-compose, reconnect on fail |
| Archivo muy grande | Memoria agotada | MAX_FILE_SIZE_MB validation en endpoint |

## Security checklist

- [ ] Variables de entorno no expuestas en código
- [ ] JWT con expiración (8h default)
- [ ] Password hasheado en variables de entorno (no hardcodeado)
- [ ] CORS configurado para Streamlit UI
- [ ] MAX_FILE_SIZE_MB enforced
- [ ] Input validation en todos los endpoints
- [ ] Dependencias sin CVEs conocidos

## Performance targets

- API response (extracción): < 30s p95 (depende del LLM)
- API response (historial): < 200ms p95
- Login: < 500ms p95
- UI load: < 3s
