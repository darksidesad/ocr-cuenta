# Crítica v1

## Problemas críticos (bloquean tests/runtime)
| # | Archivo | Línea | Error | Corrección |
|---|---------|-------|-------|-----------|
| 1 | app/routers/facturas.py | 86 | `fecha_emision` es `date` pero `ExtraccionResponse.fecha` es `datetime` | Convertir a datetime en el response |
| 2 | app/database.py | 28 | `Extraccion.total` es Float, `HistorialItem.total` es Decimal | Cambiar a Numeric en DB |
| 3 | tests/e2e/test_flujo_completo.py | 24 | Fixture `page` no definido | Agregar fixture con Playwright |
| 4 | app/services/pdf_reader.py | 81 | `pass` silenciado sin logging | Agregar logger.warning |
| 5 | ui/streamlit_app.py | 8 | `API_BASE_URL` hardcodeado, no lee env var | Usar os.environ.get con fallback |

## Problemas mayores (degradan calidad)
| # | Archivo | Descripción | Corrección |
|---|---------|-------------|-----------|
| 6 | app/routers/facturas.py | `tmp_path` puede no existir en finally | Inicializar `tmp_path = None` antes del try |
| 7 | app/extractor.py | Reintento no setea metodo_extraccion | Agregar antes de _parse_and_validate |
| 8 | app/services/pdf_reader.py | `import tempfile` no usado | Eliminar |
| 9 | app/routers/facturas.py | `import tempfile` y `Path` no usados | Eliminar |
| 10 | app/services/pdf_reader.py | `from PIL import Image` no usado | Eliminar |
| 11 | ui/streamlit_app.py | `session_state.username` nunca se setea | Guardar en login |
| 12 | docs/architecture.md | Documenta retry con backoff pero código no lo tiene | Actualizar doc |
| 13 | requirements.txt | pydantic-settings duplicado | Eliminar duplicado |
| 15 | requirements.txt | python-dotenv innecesario | Eliminar |
| 16 | Dockerfile.ui | Usuario root | Agregar usuario no-root |
| 18 | tests/e2e, tests/unit | Naming camelCase inconsistente | Cambiar a snake_case |
| 19 | app/database.py | Type hint engañoso get_session | Cambiar a AsyncGenerator |
| 21 | app/main.py | CORS hardcodeado | Hacer configurable via env var |
| 22 | Dockerfile | COPY ui/ innecesario en API | Eliminar |

## Problemas menores (mejoras opcionales)
| # | Descripción | Impacto |
|---|-------------|---------|
| 17 | Test de función privada _to_decimal | Bajo — acopla test a implementación |
| 20 | Missing type hint en _to_decimal | Bajo — legibilidad |
| 24 | f-string en logger con potencial None | Bajo — logging |
| 25 | Exception genérica expuesta en UI | Medio — seguridad |
| 26 | `source .env` no portable en Windows | Bajo — portabilidad |
| 27 | Conversión implícita Decimal→float | Bajo — precisión |
| 28 | Sin constante MAX_RETRIES | Bajo — mantenibilidad |
| 29 | Validación de content_type débil | Medio — seguridad |
| 30 | Streamlit en requirements de API | Bajo — image size |

## Comparación con iteración anterior
| Problema | Estado anterior | Estado actual |
|----------|----------------|--------------|
| #1 date vs datetime | ❌ Pendiente | ✅ Resuelto |
| #2 Float vs Decimal | ❌ Pendiente | ✅ Resuelto |
| #3 fixture page | ❌ Pendiente | ✅ Resuelto |
| #4 pass silenciado | ❌ Pendiente | ✅ Resuelto |
| #5 API_BASE_URL hardcodeado | ❌ Pendiente | ✅ Resuelto |
| #6 tmp_path unbound | ❌ Pendiente | ✅ Resuelto |
| #7 metodo_extraccion faltante | ❌ Pendiente | ✅ Resuelto |
| #8-10 imports no usados | ❌ Pendiente | ✅ Resuelto |
| #11 username no guardado | ❌ Pendiente | ✅ Resuelto |
| #13 dependencia duplicada | ❌ Pendiente | ✅ Resuelto |
| #15 python-dotenv innecesario | ❌ Pendiente | ✅ Resuelto |
| #16 Dockerfile root user | ❌ Pendiente | ✅ Resuelto |
| #18,23 naming inconsistente | ❌ Pendiente | ✅ Resuelto |
| #19 type hint engañoso | ❌ Pendiente | ✅ Resuelto |
| #21 CORS hardcodeado | ❌ Pendiente | ✅ Resuelto |
| #22 COPY innecesario | ❌ Pendiente | ✅ Resuelto |
