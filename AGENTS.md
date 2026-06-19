# Índice del Proyecto — OCR DIAN

## Stack
- **Backend:** Python 3.11 + FastAPI
- **LLM:** OpenRouter (google/gemini-2.0-flash-001)
- **OCR:** pdfplumber (texto nativo) + pdf2image + pytesseract (escaneados)
- **Validación:** Pydantic v2
- **Auth:** JWT (PyJWT)
- **Frontend:** Streamlit
- **DB:** PostgreSQL 15
- **Deploy:** Docker Compose

## Estructura de carpetas (objetivo)
```
ocr-dian/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py             # Settings from env
│   ├── auth.py               # JWT auth
│   ├── models.py             # Pydantic schemas
│   ├── database.py           # PostgreSQL connection
│   ├── extractor.py          # OCR + LLM extraction logic
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py           # POST /auth/login
│   │   └── facturas.py       # POST /extraer, GET /historial
│   └── services/
│       ├── __init__.py
│       ├── pdf_reader.py     # pdfplumber + pytesseract
│       └── llm_client.py     # OpenRouter client
├── ui/
│   └── streamlit_app.py      # Streamlit frontend
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── scripts/
│   ├── start.sh
│   ├── migrate.sh
│   └── test.sh
├── docs/
│   ├── BRIEF.md
│   ├── STACK.md
│   ├── PRD.md
│   ├── DOD.md
│   ├── USER_FLOWS.md
│   └── architecture.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── AGENTS.md
```

## Agentes y responsabilidades

| Agente | Responsabilidad | Archivos generados |
|--------|----------------|-------------------|
| Product Owner | Definir QUÉ se construye | PRD.md, DOD.md, USER_FLOWS.md |
| Architect | Definir CÓMO se construye | architecture.md, ADR-001.md, .opencode/agents/*, .opencode/skills/* |
| Developer | Implementar código funcional | app/*, ui/*, requirements.txt, .env.example, README.md |
| DevOps | Infraestructura y entornos | Dockerfile, docker-compose.yml, .gitignore, scripts/* |
| QA | Validar que todo funciona | tests/*, docs/critique_v*.md |

## Estado actual

| Paso | Estado | Archivos generados | Última actualización |
|------|--------|-------------------|---------------------|
| FASE 0 | ✅ | BRIEF.md, STACK.md, .env.example | 2026-06-19 |
| PASO 1 (Product Owner) | ✅ | PRD.md, DOD.md, USER_FLOWS.md, AGENTS.md | 2026-06-19 |
| PASO 2 (Architect) | ✅ | architecture.md, ADR-001.md, .opencode/agents/*, .opencode/skills/*, pyproject.toml | 2026-06-19 |
| PASO 3 (Developer) | ✅ | app/*, ui/*, requirements.txt, .env.example, README.md | 2026-06-19 |
| PASO 4 (DevOps) | ✅ | Dockerfile, Dockerfile.ui, docker-compose.yml, .gitignore, scripts/*, tests/conftest.py | 2026-06-19 |
| PASO 5 (QA) | ✅ | tests/unit/*, tests/integration/*, tests/e2e/*, tests/conftest.py | 2026-06-19 |
| LOOPS | 1 iteración (✅ resuelta) | loop_history.md, critique_v1.md | 2026-06-19 |
