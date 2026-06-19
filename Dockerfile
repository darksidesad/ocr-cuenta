# === Stage 1: Builder ===
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar dependencias del sistema para compilar
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# === Stage 2: Runtime ===
FROM python:3.11-slim AS runtime

# Instalar dependencias del sistema (Tesseract + poppler)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas
COPY --from=builder /install /usr/local

# Crear usuario no-root
RUN groupadd -r ocruser && useradd -r -g ocruser -d /app ocruser

WORKDIR /app

# Copiar código fuente
COPY app/ ./app/
COPY pyproject.toml .
COPY requirements.txt .

# Crear directorio temporal
RUN mkdir -p /tmp/ocr && chown ocruser:ocruser /tmp/ocr

# Cambiar a usuario no-root
USER ocruser

# Puerto de la API
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Ejecutar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
