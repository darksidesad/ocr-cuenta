#!/bin/bash
# Script de inicio rápido — OCR DIAN
set -e

echo "=== OCR DIAN — Inicio rápido ==="

# Verificar que .env existe
if [ ! -f .env ]; then
    echo "❌ Archivo .env no encontrado"
    echo "   Ejecuta: cp .env.example .env"
    echo "   Luego edita .env con tus valores"
    exit 1
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    exit 1
fi

echo "✅ Dependencias verificadas"

# Levantar servicios
echo " levantando servicios..."
docker-compose up -d --build

echo ""
echo "✅ Servicios levantados"
echo ""
echo "   API:     http://localhost:8000"
echo "   UI:      http://localhost:8501"
echo "   Health:  http://localhost:8000/health"
echo ""
echo "   Logs:    docker-compose logs -f"
echo "   Parar:   docker-compose down"
