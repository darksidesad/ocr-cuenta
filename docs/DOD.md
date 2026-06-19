# Definition of Done — OCR DIAN

## Checklist de calidad

### Code Quality
- [ ] Cero errores de linting (ruff para Python)
- [ ] Type hints en todas las funciones
- [ ] Docstrings en funciones y clases públicas
- [ ] Sin TODOs ni FIXMEs pendientes
- [ ] Sin comentarios de código comentado
- [ ] Sin placeholders ni pseudocódigo

### Testing
- [ ] Tests pasan al 100%
- [ ] Coverage ≥ 80%
- [ ] Tests unitarios para funciones de extracción
- [ ] Tests de integración para endpoints API
- [ ] Test de autenticación JWT
- [ ] Test de validación Pydantic (schema FacturaDIAN)

### Security
- [ ] No hay secrets hardcodeados en código fuente
- [ ] `.env.example` tiene todas las variables documentadas
- [ ] `.gitignore` excluye `.env` y archivos de secrets
- [ ] JWT con expiración configurada
- [ ] Password no exuesto en responses de API
- [ ] CORS configurado correctamente
- [ ] MAX_FILE_SIZE_MB enforced en endpoint
- [ ] Input validation en todos los endpoints públicos

### Documentation
- [ ] `README.md` con instrucciones de setup ejecutables paso a paso
- [ ] `docs/STACK.md` actualizado con versiones finales
- [ ] `docs/architecture.md` refleja el código real
- [ ] `docs/USER_FLOWS.md` actualizado
- [ ] `.env.example` con todas las variables

### Infrastructure
- [ ] `Dockerfile` funciona con `docker build .` sin errores
- [ ] `docker-compose up` levanta todos los servicios (app, ui, db)
- [ ] Healthchecks en cada servicio de docker-compose
- [ ] Scripts ejecutan sin errores en ambiente limpio
- [ ] Variables de entorno documentadas por ambiente

### Entrega
- [ ] URL pública funcionando (API + UI)
- [ ] Login funcional con credenciales de .env
- [ ] Extracción de factura colombiana real exitosa
- [ ] JSON retornado tiene todos los campos del schema
- [ ] Historial de extracciones visible en UI
- [ ] No hay imports rotos
- [ ] No hay errores en consola al levantar servicios

## Criterios de aceptación por feature

### F1 — Autenticación JWT
- `POST /auth/login` con credenciales válidas retorna token JWT
- `POST /auth/login` con credenciales inválidas retorna 401
- Endpoints protegidos retornan 401 sin token o con token expirado
- Token expira después de JWT_EXPIRE_MINUTES

### F2 — Extracción de factura
- `POST /facturas/extraer` con PDF válido retorna JSON con schema FacturaDIAN
- `POST /facturas/extraer` sin token retorna 401
- `POST /facturas/extraer` con archivo > MAX_FILE_SIZE_MB retorna 413
- `POST /facturas/extraer` con archivo no-PDF retorna 422
- PDF de texto nativo usa método "texto_nativo"
- PDF escaneado usa método "ocr_fallback"
- Extracción se guarda en PostgreSQL

### F3 — Campos extraídos
- NIT emisor y receptor son strings no vacíos
- Número de factura es string no vacío
- Fecha de emisión es fecha válida
- Items tienen: descripción, cantidad, precio unitario, IVA
- Subtotal, IVA total y total son Decimales positivos
- Confianza está entre 0.0 y 1.0

### F4 — Historial
- `GET /facturas/historial` retorna lista paginada
- Cada registro muestra: fecha, nombre archivo, NIT emisor, total, estado
- Paginación funciona con offset y limit

### F5 — UI Streamlit
- Login funcional con credenciales de .env
- Pantalla de extractor permite subir PDF
- Spinner/progress visible durante procesamiento
- JSON extraído se muestra con opción de copiar
- Historial se muestra con paginación

## Métricas de éxito
| Métrica | Target v1 |
|---------|-----------|
| Extracción exitosa (factura DIAN real) | ≥ 90% |
| Campos correctos (NIT, total, fecha) | ≥ 95% |
| Tiempo de extracción | < 30s p95 |
| Uptime del servicio | ≥ 99% |
| Coverage de tests | ≥ 80% |
