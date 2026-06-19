# OCR DIAN — Extracción de Facturas Colombianas

Servicio de extracción automática de datos de facturas colombianas (DIAN) usando OCR + LLMs con structured outputs.

## Stack

- **Backend:** Python 3.11 + FastAPI
- **LLM:** OpenRouter (Gemini Flash)
- **OCR:** pdfplumber + pytesseract
- **DB:** PostgreSQL 15
- **Frontend:** Streamlit
- **Deploy:** Docker Compose

## Requisitos previos

- Python 3.11+
- Docker y Docker Compose
- Tesseract OCR (para PDFs escaneados)
- Cuenta en OpenRouter con API key

### Instalar Tesseract (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-spa poppler-utils
```

### Instalar Tesseract (macOS)

```bash
brew install tesseract tesseract-lang poppler
```

## Setup rápido

### 1. Clonar y configurar

```bash
cd ocr-dian
cp .env.example .env
```

### 2. Editar `.env` con tus valores

```bash
OPENROUTER_API_KEY=tu-api-key-aqui
JWT_SECRET_KEY=tu-clave-secreta-aqui
APP_PASSWORD=tu-contraseña-aqui
DATABASE_URL=postgresql+asyncpg://facturas_user:change_me@localhost:5432/facturas_db
```

### 3. Levantar con Docker Compose

```bash
docker-compose up -d
```

### 4. Verificar

- API: http://localhost:8000/health
- UI: http://localhost:8501

## Setup sin Docker (desarrollo)

### 1. Instalar dependencias

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Configurar PostgreSQL

```bash
createdb facturas_db
# O con Docker solo la DB:
docker run -d --name facturas-pg -p 5432:5432 \
  -e POSTGRES_USER=facturas_user \
  -e POSTGRES_PASSWORD=change_me \
  -e POSTGRES_DB=facturas_db \
  postgres:15-alpine
```

### 3. Ejecutar

```bash
# Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (en otra terminal)
streamlit run ui/streamlit_app.py --server.port 8501
```

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/health` | Healthcheck | No |
| POST | `/auth/login` | Login → JWT token | No |
| POST | `/facturas/extraer` | Extraer datos de factura PDF | Sí (Bearer) |
| GET | `/facturas/historial` | Historial de extracciones | Sí (Bearer) |

### Ejemplo de uso

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"tu-contraseña"}' | jq -r '.access_token')

# Extraer factura
curl -X POST http://localhost:8000/facturas/extraer \
  -H "Authorization: Bearer $TOKEN" \
  -F "archivo=@factura.pdf"

# Ver historial
curl http://localhost:8000/facturas/historial \
  -H "Authorization: Bearer $TOKEN"
```

## Campos extraídos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| nit_emisor | str | NIT del emisor |
| nombre_emisor | str | Razón social del emisor |
| nit_receptor | str | NIT del receptor |
| nombre_receptor | str | Razón social del receptor |
| numero_factura | str | Número consecutivo |
| fecha_emision | date | Fecha de emisión |
| cufe | str \| null | CUFE (si existe) |
| items | list | Ítems con descripción, cantidad, precio, IVA |
| subtotal | Decimal | Subtotal |
| iva_total | Decimal | Total IVA |
| total | Decimal | Total factura |
| moneda | str | COP |
| metodo_extraccion | str | "texto_nativo" o "ocr_fallback" |
| confianza | float | 0.0 a 1.0 |

## Testing

```bash
# Ejecutar tests
pytest --tb=short -q

# Con coverage
pytest --cov=app --cov-report=term-missing

# Linting
ruff check app/ tests/
```

## Estructura del proyecto

```
ocr-dian/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py             # Settings desde .env
│   ├── auth.py               # JWT auth
│   ├── models.py             # Pydantic schemas
│   ├── database.py           # PostgreSQL (SQLAlchemy async)
│   ├── extractor.py          # Lógica de extracción
│   ├── routers/
│   │   ├── auth.py           # POST /auth/login
│   │   └── facturas.py       # POST /extraer, GET /historial
│   └── services/
│       ├── pdf_reader.py     # pdfplumber + pytesseract
│       └── llm_client.py     # OpenRouter client
├── ui/
│   └── streamlit_app.py      # Frontend Streamlit
├── tests/
│   ├── unit/
│   └── integration/
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
├── pyproject.toml
└── .env.example
```

## Variables de entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| OPENROUTER_API_KEY | API key de OpenRouter | (requerido) |
| OPENROUTER_MODEL | Modelo LLM | google/gemini-2.0-flash-001 |
| APP_USERNAME | Usuario para login | admin |
| APP_PASSWORD | Contraseña para login | (requerido) |
| JWT_SECRET_KEY | Secret para JWT | (requerido) |
| JWT_EXPIRE_MINUTES | Minutos de expiración | 480 |
| DATABASE_URL | URL PostgreSQL | (requerido) |
| MAX_FILE_SIZE_MB | Tamaño máximo archivo | 10 |
| ENVIRONMENT | environment | development |
