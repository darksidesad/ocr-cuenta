# User Flows — OCR DIAN

## Flow 1: Login

```
Usuario abre Streamlit UI (:8501)
  │
  ▼
Pantalla de Login
  │
  ├── Ingresa usuario + contraseña
  │     │
  │     ▼
  │   POST /auth/login { username, password }
  │     │
  │     ├── Credenciales válidas → JWT token → Redirigir a Extractor
  │     │
  │     └── Credenciales inválidas → Mensaje de error → Permanecer en Login
  │
  └── Cierre de sesión → Limpiar token → Volver a Login
```

## Flow 2: Extracción de Factura

```
Extractor (pantalla principal)
  │
  ▼
Usuario selecciona archivo PDF
  │
  ├── Validación cliente: tipo = application/pdf
  │     │
  │     ├── No es PDF → Error "Solo se permiten archivos PDF"
  │     │
  │     └── Es PDF → Continuar
  │
  ├── Validación cliente: tamaño ≤ MAX_FILE_SIZE_MB
  │     │
  │     ├── Muy grande → Error "Archivo excede el tamaño máximo"
  │     │
  │     └── Tamaño válido → Continuar
  │
  ▼
POST /facturas/extraer (multipart/form-data, campo "archivo")
  │
  ├── Sin token / token expirado → 401 → Volver a Login
  │
  ├── Archivo inválido → 422 → Mostrar error
  │
  ▼
Backend procesa:
  │
  ├── 1. Detectar tipo de PDF
  │     ├── Texto nativo → pdfplumber extrae texto
  │     └── Escaneado → pdf2image + pytesseract
  │
  ├── 2. Enviar texto a OpenRouter (Gemini Flash)
  │     ├── API caída → Error "Servicio temporalmente no disponible"
  │     └── Respuesta válida → Continuar
  │
  ├── 3. Parsear y validar con Pydantic
  │     ├── JSON inválido → Reintentar 1 vez
  │     │     └── Sigue inválido → Error "No se pudo extraer datos"
  │     └── Validación OK → Continuar
  │
  ├── 4. Guardar en PostgreSQL
  │     │
  │     ▼
  │   Retornar JSON validado
  │
  ▼
UI muestra resultado:
  │
  ├── Campos renderizados (NIT, nombre, fecha, total, etc.)
  ├── JSON completo con opción de copiar
  ├── Indicador de confianza (0.0 - 1.0)
  └── Método de extracción utilizado
```

## Flow 3: Historial de Extracciones

```
Extractor → Pestaña/Sección "Historial"
  │
  ▼
GET /facturas/historial?offset=0&limit=20
  │
  ├── Sin token → 401 → Volver a Login
  │
  ▼
Respuesta: lista de extracciones
  │
  ├── Cada registro muestra:
  │     ├── Fecha de extracción
  │     ├── Nombre del archivo
  │     ├── NIT emisor
  │     ├── Total
  │     └── Estado (éxito/error)
  │
  ├── Paginación:
  │     ├── Anterior / Siguiente
  │     └── Indicador de página actual
  │
  └── Click en registro → Ver detalle de extracción
```

## Flow 4: Manejo de Errores

```
Error durante extracción
  │
  ├── Error de red / API caída
  │     → Mensaje: "Servicio temporalmente no disponible. Intente de nuevo."
  │
  ├── PDF corrupto / no legible
  │     → Mensaje: "No se pudo leer el archivo. Verifique que sea un PDF válido."
  │
  ├── OCR falló (confianza < 0.3)
  │     → Mensaje: "La calidad del documento es insuficiente para extracción."
  │
  ├── LLM no pudo extraer datos
  │     → Mensaje: "No se pudieron extraer los datos de la factura."
  │
  ├── Token expirado
  │     → Redirigir a Login con mensaje "Sesión expirada"
  │
  └── Error desconocido
        → Mensaje: "Error inesperado. Contacte al administrador."
```
