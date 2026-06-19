# Loop History

## Iteración 1 — 2026-06-19

### Estado inicial
- Tests pasando: 70/70
- Errores críticos: 5
- Errores mayores: 12
- Errores menores: 13

### Acciones tomadas
- Corregido tipo date vs datetime en ExtraccionResponse (#1)
- Corregido Float vs Decimal inconsistente en database.py (#2)
- Agregado fixture `page` para tests E2E (#3)
- Eliminado pass silenciado en pdf_reader.py, agregado logging (#4)
- API_BASE_URL ahora lee de env var con fallback (#5)
- Inicializado tmp_path = None en facturas.py (#6)
- Agregado metodo_extraccion en reintento de extractor.py (#7)
- Eliminados imports no usados (#8, #9, #10)
- Guardado de username en session_state (#11)
- Eliminada dependencia duplicada pydantic-settings (#13)
- Eliminada dependencia innecesaria python-dotenv (#15)
- Agregado usuario no-root en Dockerfile.ui (#16)
- Corregido naming de tests camelCase → snake_case (#18, #23)
- Corregido type hint de get_session (#19)
- Agregado CORS configurable via env var (#21)
- Eliminado COPY ui/ innecesario en Dockerfile (#22)

### Estado final
- Tests pasando: 70/70
- Errores críticos: 0
- Errores mayores: 0
- Errores menores: ~10 (mejoras opcionales)

### Decisión
- ✅ Avanzar a pre-entrega
