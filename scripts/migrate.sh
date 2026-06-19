#!/bin/bash
# Script de migración de base de datos — OCR DIAN
set -e

echo "=== OCR DIAN — Migración de DB ==="

# Verificar que .env existe
if [ ! -f .env ]; then
    echo "❌ Archivo .env no encontrado"
    exit 1
fi

# Cargar variables
source .env

# Verificar conexión a PostgreSQL
echo "Verificando conexión a PostgreSQL..."
if ! docker-compose exec db pg_isready -U facturas_user -d facturas_db &> /dev/null; then
    echo "❌ No se puede conectar a PostgreSQL"
    echo "   Verifica que el servicio db esté corriendo: docker-compose ps"
    exit 1
fi

echo "✅ Conexión a PostgreSQL verificada"

# Ejecutar init_db desde la app (crea tablas)
echo "Creando tablas..."
docker-compose exec app python -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
print('✅ Tablas creadas/verificadas')
"

echo ""
echo "✅ Migración completada"
