#!/bin/bash
# Script de testing — OCR DIAN
set -e

echo "=== OCR DIAN — Tests ==="

# Verificar entorno virtual o Docker
if [ -d "venv" ]; then
    echo "Usando entorno virtual..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Usando entorno virtual (.venv)..."
    source .venv/bin/activate
fi

# Instalar dependencias de dev si es necesario
if ! python -c "import pytest" 2>/dev/null; then
    echo "Instalando dependencias de desarrollo..."
    pip install -r requirements.txt pytest pytest-asyncio pytest-cov ruff
fi

# Linting
echo ""
echo "🔍 Ejecutando ruff..."
ruff check app/ tests/ --output-format=concise
LINT_EXIT=$?

if [ $LINT_EXIT -ne 0 ]; then
    echo "⚠️  Errores de linting encontrados"
else
    echo "✅ Linting pasado"
fi

# Tests
echo ""
echo "🧪 Ejecutando tests..."
pytest --tb=short -q --cov=app --cov-report=term-missing
TEST_EXIT=$?

# Coverage check
echo ""
if [ $TEST_EXIT -eq 0 ]; then
    echo "✅ Todos los tests pasaron"
else
    echo "❌ Algunos tests fallaron"
    exit $TEST_EXIT
fi
