# 💰 FacturIA 2.0 - Sistema Inteligente de Gestión Financiera

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29-red?logo=streamlit)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI-orange?logo=google)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

Sistema automatizado y completo de procesamiento, clasificación y análisis de transacciones financieras mediante **Inteligencia Artificial**. FacturIA 2.0 revoluciona la gestión contable al automatizar todo el ciclo: desde la recepción de comprobantes por email hasta la generación de reportes ejecutivos con visualizaciones interactivas.

---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso del Sistema](#-uso-del-sistema)
- [Dashboard Interactivo](#-dashboard-interactivo)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Funcionalidades Avanzadas](#-funcionalidades-avanzadas)
- [Solución de Problemas](#-solución-de-problemas)
- [Mejoras Futuras](#-mejoras-futuras)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)
- [Autor](#-autor)

---

## 🚀 Características Principales

### 🤖 Inteligencia Artificial con Google Gemini Vision

- **Clasificación Automática**: Gemini 2.0 Flash analiza PDFs e imágenes de comprobantes
- **Extracción de Datos**: Identifica montos, fechas, emisores y números de comprobante
- **Categorización Inteligente**: Distingue automáticamente entre ingresos y egresos
- **Confianza Ajustable**: Sistema de scoring para detectar transacciones que requieren revisión manual
- **Optimizado para Free Tier**: Implementa rate limiting inteligente (15 RPM) y circuit breaker para evitar costos

### 📧 Monitor Automático de Email

- **Lectura Continua**: Revisa tu casilla de email cada 5 minutos (configurable)
- **Detección de Adjuntos**: Identifica automáticamente PDFs, PNGs y JPGs en emails
- **Descarga Inteligente**: Evita procesar archivos duplicados mediante tracking por Message-ID
- **Detección Automática de Personas**: Extrae el nombre del remitente del email para asociar transacciones
- **Filtros Personalizables**: Define remitentes confiables y palabras clave para búsqueda
- **Soporte IMAP y Gmail API**: Compatible con cualquier proveedor de email

### 💾 Base de Datos Completa

- **ORM con SQLAlchemy**: Abstracción completa sobre SQL para flexibilidad
- **Soporte Multi-DB**: SQLite (desarrollo) y PostgreSQL (producción)
- **Modelo de Datos Robusto**:
  - Transacciones con 20+ campos detallados
  - Tracking de origen (PDF/imagen/CSV)
  - Auditoría completa (fechas de creación, modificación, edición manual)
  - Flags de revisión y validación
- **Migraciones Automáticas**: Schema evolution sin pérdida de datos
- **Herramienta de Limpieza**: Script `limpiar_db.py` para resetear la base de datos

### 📊 Dashboard Interactivo en Tiempo Real

- **4 Páginas Especializadas**:
  1. **Principal**: KPIs, gráficos y estadísticas generales
  2. **Revisar Transacciones**: Edición manual con interfaz intuitiva
  3. **Cargar CSV**: Importación masiva de transacciones
  4. **Configuración**: Ajustes del sistema y preferencias
- **Visualizaciones con Plotly**: Gráficos interactivos y responsivos
- **Filtros Avanzados**: Por fecha, categoría, persona, tipo y origen
- **Edición en Línea**: Modifica cualquier transacción directamente desde el dashboard
- **Exportaciones**: Descarga datos en Excel (.xlsx) y PDF con formato profesional

### 📈 Reportes y Análisis

- **KPIs en Tiempo Real**:
  - Total de transacciones del mes actual
  - Balance general (ingresos - egresos)
  - Promedio de transacciones por día
  - Top 5 categorías por monto
- **Gráficos Avanzados**:
  - Evolución temporal de ingresos vs egresos
  - Distribución por categorías (pie charts)
  - Análisis comparativo por personas
  - Heat maps de actividad
- **Exportación de Reportes**:
  - Excel con formato y fórmulas
  - PDF con gráficos y tablas profesionales
  - CSV para análisis en otras herramientas

### 🔔 Notificaciones por Email

- **Alertas Automáticas**: Recibe un email cada vez que se procesan nuevas transacciones
- **Resumen Detallado**: Incluye estadísticas y lista de transacciones procesadas
- **HTML Estilizado**: Emails con formato profesional y legible
- **Multi-destinatario**: Envía alertas a múltiples emails simultáneamente

### 🔒 Seguridad y Privacidad

- **Credenciales Seguras**: Todas las API keys en archivo `.env` (excluido de Git)
- **Solo Lectura**: El sistema no modifica ni elimina emails
- **Datos Locales**: Toda la información se almacena en tu máquina
- **Sin Telemetría**: No se envían datos a terceros (excepto APIs configuradas)
- **Validación de Encoding**: Manejo robusto de UTF-8 para caracteres especiales en español

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    FACTURIA 2.0 - ARQUITECTURA                  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  📧 Email    │  ← Monitor IMAP/Gmail API (cada 5 min)
│  Corporativo │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│  📥 Email Monitor    │  ← src/email_monitor/gmail_reader.py
│  - Detecta adjuntos  │
│  - Descarga archivos │
│  - Extrae metadata   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  🤖 AI Processor     │  ← src/ai_processor/gemini_classifier.py
│  - Google Gemini 2.0 │
│  - Clasifica docs    │
│  - Extrae datos      │
│  - Rate limiting     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  💾 Database Layer   │  ← src/database/
│  - SQLAlchemy ORM    │     - models.py (Transaccion)
│  - CRUD operations   │     - crud.py (operaciones)
│  - SQLite/PostgreSQL │     - connection.py (sesiones)
└──────┬───────────────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
┌──────────────────┐              ┌──────────────────┐
│  📊 Dashboard    │              │  🔔 Notificador  │
│  - Streamlit     │              │  - Email HTML    │
│  - 4 páginas     │              │  - Resúmenes     │
│  - Visualización │              │  - Alertas       │
│  - Edición       │              └──────────────────┘
│  - Exportación   │
└──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE PROCESAMIENTO                       │
└─────────────────────────────────────────────────────────────────┘

Email nuevo → Descarga adjunto → Clasifica con IA → Guarda en DB →
  ↓                                                                ↓
Procesa próximo ← Espera 15s ← Rate limit OK? ← Envía notificación
```

### Componentes Principales

1. **main.py**: Orquestador principal que coordina todos los módulos
2. **email_monitor/**: Gestión de conexión IMAP/Gmail y descarga de adjuntos
3. **ai_processor/**: Integración con Gemini Vision API y clasificación
4. **database/**: Modelos SQLAlchemy, CRUD operations y conexiones
5. **dashboard/**: Interfaz Streamlit con páginas y utilidades de exportación

---

## 🛠️ Tecnologías Utilizadas

### Backend

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Python** | 3.10+ | Lenguaje principal |
| **SQLAlchemy** | 2.0.23 | ORM para base de datos |
| **Google Gemini** | 2.0 Flash | Clasificación con IA |
| **google-generativeai** | 0.3.1 | SDK de Gemini |
| **Pydantic** | 2.5.0 | Validación de datos |
| **python-dotenv** | 1.0.0 | Variables de entorno |
| **schedule** | 1.2.0 | Tareas programadas |
| **loguru** | 0.7.2 | Logging avanzado |

### Email Processing

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **google-api-python-client** | 2.108.0 | Gmail API |
| **google-auth-oauthlib** | 1.2.0 | OAuth para Gmail |
| **imaplib** | Built-in | Protocolo IMAP |

### Document Processing

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **PyPDF2** | 3.0.1 | Lectura de PDFs |
| **pdf2image** | 1.16.3 | Conversión PDF → Imagen |
| **Pillow** | 10.1.0 | Procesamiento de imágenes |
| **chardet** | 5.2.0 | Detección de encoding CSV |

### Frontend & Visualization

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **Streamlit** | 1.29.0 | Framework de dashboard |
| **Plotly** | 5.18.0 | Gráficos interactivos |
| **Pandas** | 2.1.3 | Análisis de datos |
| **NumPy** | 1.26.2 | Operaciones numéricas |

### Export & Reports

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **openpyxl** | 3.1.2 | Exportación a Excel |
| **xlsxwriter** | 3.1.9 | Excel con formato avanzado |
| **reportlab** | 4.0.7 | Generación de PDFs |

### Development

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| **pytest** | 7.4.3 | Testing |
| **black** | 23.11.0 | Code formatting |
| **flake8** | 6.1.0 | Linting |

---

## 📋 Requisitos Previos

### 1. Python 3.10 o superior

Verifica tu versión:
```bash
python3 --version
```

### 2. Google Gemini API Key (Gratis)

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Crea una nueva API key
4. **Límites del Free Tier**:
   - 15 requests por minuto (RPM)
   - 1 millón de tokens por día
   - 1,500 requests por día

### 3. Gmail App Password

Si usas autenticación de 2 factores (recomendado):

1. Ve a [Google Account Security](https://myaccount.google.com/security)
2. Activa **Verificación en 2 pasos**
3. Ve a **Contraseñas de aplicaciones**: https://myaccount.google.com/apppasswords
4. Genera una contraseña para "Mail" en "Otro dispositivo personalizado"
5. Guarda la contraseña de 16 caracteres

### 4. Dependencias del Sistema (para PDF processing)

**En Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**En macOS:**
```bash
brew install poppler
```

**En Windows:**
- Descarga Poppler desde [aquí](https://github.com/oschwartz10612/poppler-windows/releases/)
- Agrega la carpeta `bin` al PATH

---

## 🚀 Instalación

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/SilvanoPuccini/FacturIA-2.0.git
cd FacturIA-2.0
```

### Paso 2: Crear Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Linux/macOS:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### Paso 3: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Verificar instalación:**
```bash
pip list | grep -E "streamlit|google-generativeai|sqlalchemy"
```

### Paso 4: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tu editor favorito
nano .env  # o vim, code, etc.
```

**Completar las variables esenciales:**
```bash
# === GOOGLE GEMINI API ===
GOOGLE_API_KEY=AIzaSy...tu_api_key_real

# === GMAIL IMAP ===
GMAIL_EMAIL=tu_email@gmail.com
GMAIL_PASSWORD=tu_app_password_de_16_caracteres

# === BASE DE DATOS ===
DATABASE_URL=sqlite:///facturia2.db

# === CONFIGURACIÓN ===
EMAIL_CHECK_INTERVAL=5
ENVIRONMENT=development
```

### Paso 5: Crear Estructura de Carpetas

```bash
# El sistema creará automáticamente estas carpetas, pero puedes hacerlo manualmente:
mkdir -p data/procesado/ingresos data/procesado/egresos
mkdir -p data/temp_pdf data/temp_img data/temp_csv
mkdir -p logs
```

### Paso 6: Inicializar Base de Datos

```bash
python -c "from src.database import inicializar_base_datos; inicializar_base_datos()"
```

**Salida esperada:**
```
✅ Base de datos inicializada correctamente
📊 Tablas creadas: transacciones
```

### Paso 7: Probar Gemini API (Opcional)

Verifica que tu API key funcione:

```bash
python test_gemini_api.py
```

---

## ⚙️ Configuración

### Variables de Entorno (`.env`)

#### Google Gemini API
```bash
GOOGLE_API_KEY=AIzaSy...
```
- **Obligatorio**: Sí
- **Descripción**: API key de Google AI Studio
- **Obtener**: https://makersuite.google.com/app/apikey

#### Gmail IMAP
```bash
GMAIL_EMAIL=tu_email@gmail.com
GMAIL_PASSWORD=app_password_16_chars
```
- **Obligatorio**: Sí (para monitor de email)
- **Descripción**: Credenciales para leer emails vía IMAP
- **App Password**: https://myaccount.google.com/apppasswords

#### Base de Datos
```bash
DATABASE_URL=sqlite:///facturia2.db
```
- **Obligatorio**: Sí
- **Opciones**:
  - SQLite (desarrollo): `sqlite:///facturia2.db`
  - PostgreSQL (producción): `postgresql://user:pass@localhost:5432/facturia2`

#### Configuración del Sistema
```bash
EMAIL_CHECK_INTERVAL=5
ENVIRONMENT=development
```
- `EMAIL_CHECK_INTERVAL`: Minutos entre cada revisión de email (default: 5)
- `ENVIRONMENT`: `development` o `production`

#### Streamlit (Opcional)
```bash
STREAMLIT_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

#### Notificaciones (Opcional)
```bash
NOTIFICATION_EMAIL_FROM=tu_email@gmail.com
NOTIFICATION_EMAIL_PASSWORD=app_password_16_chars
NOTIFICATION_EMAIL_TO=destinatario1@email.com,destinatario2@email.com
```
- **Descripción**: Recibe alertas cuando se procesan transacciones
- **Múltiples destinatarios**: Separar con comas

---

## 🎯 Uso del Sistema

### Modo 1: Sistema Completo (Recomendado)

Ejecuta el monitor de email + procesamiento automático:

```bash
python main.py
```

**¿Qué hace?**
1. Conecta a tu email vía IMAP
2. Busca emails con adjuntos (PDF, PNG, JPG)
3. Descarga archivos nuevos
4. Clasifica con Gemini AI
5. Guarda transacciones en la base de datos
6. Envía notificaciones por email
7. **Repite cada 5 minutos** (configurable)

**Salida de ejemplo:**
```
[2025-10-30 10:30:00] INFO | ===== INICIANDO FACTURIA 2.0 =====
[2025-10-30 10:30:01] INFO | ✅ Conectado a Gmail: tu_email@gmail.com
[2025-10-30 10:30:02] INFO | 📧 Buscando nuevos emails...
[2025-10-30 10:30:05] INFO | ✅ Encontrados 3 emails con adjuntos
[2025-10-30 10:30:06] INFO | 📥 Descargando: factura_luz_octubre.pdf
[2025-10-30 10:30:08] INFO | 🤖 Procesando con Gemini AI...
[2025-10-30 10:30:25] INFO | ✅ Clasificado como: EGRESO - Factura de servicios - $145.50
[2025-10-30 10:30:26] INFO | 💾 Guardado en base de datos (ID: 1247)
[2025-10-30 10:30:27] INFO | ⏰ Esperando 15 segundos (rate limit)...
```

**Para detener**: Presiona `Ctrl+C`

### Modo 2: Solo Dashboard

Si ya tienes transacciones en la base de datos y solo quieres visualizarlas:

```bash
streamlit run src/dashboard/app.py
```

**Accede desde tu navegador:**
- URL: http://localhost:8501
- El dashboard se abrirá automáticamente

### Modo 3: Procesamiento Manual de Archivos

Puedes procesar archivos específicos sin el monitor de email:

```python
from src.ai_processor import GeminiClassifier
from pathlib import Path

# Inicializar clasificador
classifier = GeminiClassifier()

# Procesar un archivo
resultado = classifier.clasificar_documento(Path("facturas/mi_factura.pdf"))

print(f"Tipo: {resultado.tipo}")
print(f"Categoría: {resultado.categoria}")
print(f"Monto: ${resultado.monto}")
```

### Modo 4: Importación de CSV

1. Abre el dashboard: `streamlit run src/dashboard/app.py`
2. Ve a la página **"3 - Cargar CSV"**
3. Carga tu archivo CSV con columnas:
   - `fecha` (opcional)
   - `descripcion`
   - `monto`
   - `categoria` (opcional)
   - `tipo` (ingreso/egreso, opcional)
4. Mapea las columnas y haz clic en "Importar"

---

## 📊 Dashboard Interactivo

### Página 1: Dashboard Principal

**KPIs Destacados:**
- 📊 Total de transacciones del mes
- 💰 Balance general (ingresos - egresos)
- 📈 Promedio diario de transacciones
- 🏆 Top 5 categorías por monto

**Visualizaciones:**
- Gráfico de líneas: Evolución temporal de ingresos vs egresos
- Gráfico circular: Distribución de egresos por categoría
- Gráfico de barras: Comparación de transacciones por persona
- Tabla detallada: Últimas 100 transacciones

**Filtros Disponibles:**
- Rango de fechas (date picker)
- Tipo de transacción (ingreso/egreso/ambos)
- Categoría específica
- Persona asociada
- Origen del archivo (PDF/imagen/CSV)

**Acciones:**
- 📥 Exportar a Excel (.xlsx)
- 📥 Exportar a PDF con gráficos
- 🔄 Actualizar datos en tiempo real

### Página 2: Revisar Transacciones

**Funcionalidades:**
- Ver lista completa de transacciones con paginación
- Buscar por ID, monto, descripción o categoría
- Filtrar por:
  - Estado de revisión (requiere atención)
  - Editadas manualmente
  - Procesadas por IA
  - Rango de fechas
- **Editar transacción**:
  - Modificar tipo (ingreso/egreso)
  - Cambiar categoría
  - Ajustar monto
  - Actualizar fecha
  - Editar persona asociada
  - Modificar emisor/receptor
  - Agregar/editar descripción
  - Cambiar número de comprobante
  - Marcar/desmarcar "requiere revisión"
- **Eliminar permanentemente** con confirmación
- Ver historial de modificaciones

**Indicadores Visuales:**
- 🔴 Rojo: Requiere revisión manual
- ✏️ Icono: Editado manualmente
- 🤖 Badge: Procesado por IA
- ⭐ Estrella: Confianza de clasificación > 80%

### Página 3: Cargar CSV

**Proceso de Importación:**
1. **Subir archivo**: Arrastra o selecciona tu CSV
2. **Vista previa**: Revisa las primeras 5 filas
3. **Mapeo de columnas**:
   - Fecha de transacción
   - Descripción
   - Monto
   - Categoría (opcional)
   - Tipo (opcional)
   - Persona (opcional)
4. **Configuración**:
   - Tipo por defecto (si no viene en CSV)
   - Categoría por defecto
   - Persona por defecto
   - Origen: CSV
5. **Validación**: El sistema verifica:
   - Montos válidos (números positivos)
   - Fechas en formato correcto
   - Categorías existentes
6. **Importación**: Batch insert optimizado
7. **Confirmación**: Muestra transacciones importadas

**Formatos de CSV Soportados:**
- Separador: coma (`,`) o punto y coma (`;`)
- Encoding: UTF-8, Latin-1, Windows-1252 (auto-detectado)
- Fechas: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`

### Página 4: Configuración

**Ajustes Disponibles:**
- Ver estadísticas del sistema:
  - Total de transacciones
  - Transacciones este mes
  - Procesadas por IA
  - Requieren revisión
  - Editadas manualmente
- Configuración de categorías:
  - Agregar nuevas categorías
  - Renombrar categorías existentes
  - Ver uso de cada categoría
- Mantenimiento:
  - Limpiar archivos temporales
  - Vaciar caché de procesamiento
  - Ver logs del sistema
- Información del sistema:
  - Versión de FacturIA
  - Base de datos utilizada
  - Espacio en disco
  - Última sincronización de email

---

## 📁 Estructura del Proyecto

```
FacturIA-2.0/
│
├── 📄 main.py                          # Script principal (orquestador)
├── 📄 limpiar_db.py                    # Script de limpieza de base de datos
├── 📄 test_gemini_api.py               # Script de prueba de Gemini API
│
├── 📄 requirements.txt                 # Dependencias Python
├── 📄 .env.example                     # Plantilla de variables de entorno
├── 📄 .env                             # Variables de entorno (NO en Git)
├── 📄 .gitignore                       # Archivos ignorados por Git
├── 📄 README.md                        # Este archivo
├── 📄 LICENSE                          # Licencia MIT
│
├── 📂 src/                             # Código fuente principal
│   │
│   ├── 📂 email_monitor/               # Monitor de emails
│   │   ├── __init__.py
│   │   └── gmail_reader.py             # Lectura IMAP y descarga de adjuntos
│   │
│   ├── 📂 ai_processor/                # Procesamiento con IA
│   │   ├── __init__.py
│   │   └── gemini_classifier.py        # Clasificación con Gemini Vision
│   │
│   ├── 📂 database/                    # Gestión de base de datos
│   │   ├── __init__.py
│   │   ├── models.py                   # Modelos SQLAlchemy (Transaccion)
│   │   ├── connection.py               # Conexión y sesiones
│   │   ├── crud.py                     # Operaciones CRUD
│   │   └── init_db.py                  # Inicialización de esquema
│   │
│   ├── 📂 dashboard/                   # Dashboard Streamlit
│   │   ├── __init__.py
│   │   ├── app.py                      # Página principal del dashboard
│   │   ├── export_utils.py             # Utilidades de exportación (Excel/PDF)
│   │   │
│   │   └── 📂 pages/                   # Páginas adicionales
│   │       ├── 1_Revisar_Transacciones.py
│   │       ├── 2_Cargar_CSV.py
│   │       └── 3_Configuracion.py
│   │
│   └── 📂 notifications/               # Sistema de notificaciones
│       ├── __init__.py
│       └── email_sender.py             # Envío de emails HTML
│
├── 📂 data/                            # Datos y archivos procesados
│   ├── 📂 procesado/                   # Archivos clasificados
│   │   ├── 📂 ingresos/                # Comprobantes de ingresos
│   │   └── 📂 egresos/                 # Comprobantes de egresos
│   │
│   ├── 📂 temp_pdf/                    # PDFs temporales descargados
│   ├── 📂 temp_img/                    # Imágenes temporales descargadas
│   └── 📂 temp_csv/                    # CSVs temporales importados
│
├── 📂 logs/                            # Logs del sistema
│   ├── facturia_2025-10-30.log
│   └── facturia_2025-10-29.log
│
├── 📂 venv/                            # Entorno virtual (NO en Git)
│
└── 📄 facturia2.db                     # Base de datos SQLite (NO en Git)
```

---

## 🔧 Funcionalidades Avanzadas

### 1. Rate Limiting Inteligente

El sistema implementa un **rate limiter** optimizado para el free tier de Gemini:

```python
# Límite: 15 RPM (requests por minuto)
# Estrategia: 1 request cada 4 segundos + exponential backoff

Intento 1 → Fallo → Espera 10s
Intento 2 → Fallo → Espera 20s
Intento 3 → Fallo → Espera 30s
Intento 4 → Activar circuit breaker (detener procesamiento temporalmente)
```

**Circuit Breaker**: Si fallan 10 archivos consecutivos, el sistema:
1. Pausa el procesamiento por 5 minutos
2. Registra el error en los logs
3. Reinicia automáticamente después del cooldown

### 2. Detección Automática de Personas

Extrae el nombre de la persona desde el email del remitente:

**Ejemplos:**
```
silva.puccini@gmail.com         → Silva Puccini
maria_rodriguez_123@hotmail.com → Maria Rodriguez
juan-perez@empresa.com          → Juan Perez
info@empresa.com                → Empresa (usa el dominio)
```

**Beneficios:**
- Asocia automáticamente transacciones a personas
- Evita duplicados por variaciones de email
- Genera reportes por persona

### 3. Manejo Robusto de UTF-8

El sistema maneja correctamente caracteres especiales del español:

```python
# Función safe_str() en export_utils.py
safe_str("Descripción")    # ✅ Funciona
safe_str("Señor José")     # ✅ Funciona
safe_str(None)             # ✅ Devuelve ""
```

**Casos manejados:**
- Acentos: á, é, í, ó, ú
- Ñ mayúscula y minúscula
- Caracteres especiales: ¿, ¡, €, $
- Emojis en descripciones

### 4. JSON Parsing con Error Recovery

Gemini 2.0 a veces devuelve JSON con formato incorrecto. El sistema lo corrige automáticamente:

**Problema detectado:**
```json
{{ "tipo": "egreso", "monto": 150 }}  ❌ Inválido
```

**Corrección automática:**
```json
{ "tipo": "egreso", "monto": 150 }   ✅ Válido
```

### 5. Exportación con Formato Profesional

#### Excel (.xlsx)
- Encabezados en negrita con fondo azul
- Columnas auto-ajustadas al contenido
- Formato de moneda con símbolo $
- Formato de fecha legible
- Congelación de encabezados
- Filtros automáticos en todas las columnas

#### PDF
- Header con logo y título
- Tabla con bordes y colores alternados
- Pie de página con número de página y fecha
- Resumen estadístico al final
- Formato A4 profesional

### 6. Validación de Datos

Antes de guardar en la base de datos, el sistema valida:

**Transacciones:**
- ✅ Monto > 0
- ✅ Tipo es "ingreso" o "egreso"
- ✅ Categoría existe en el catálogo
- ✅ Fecha no es futura (con margen de 1 día)
- ✅ Descripción no vacía

**Archivos:**
- ✅ Extensión permitida (pdf, png, jpg, csv)
- ✅ Tamaño < 10 MB
- ✅ No está duplicado (por hash MD5)

---

## 🔍 Solución de Problemas

### Problema 1: Error de Gemini API "404 Model Not Found"

**Error completo:**
```
404 models/gemini-1.5-flash-8b is not found for API version v1beta
```

**Causas:**
- Modelo no disponible en tu región
- Modelo deprecado o renombrado
- API key sin acceso al modelo

**Solución:**
1. Verifica los modelos disponibles:
   ```bash
   python test_gemini_api.py
   ```
2. Actualiza el modelo en `src/ai_processor/gemini_classifier.py:53`:
   ```python
   self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
   ```
3. Modelos recomendados (Oct 2025):
   - `gemini-2.0-flash-exp` (más rápido)
   - `gemini-1.5-flash` (estable)
   - `gemini-1.5-pro` (más preciso, más lento)

### Problema 2: Rate Limit Exceeded (429)

**Error completo:**
```
⏱️ Rate limit alcanzado. Esperando 10 segundos...
```

**Causas:**
- Superaste 15 requests por minuto (free tier)
- Procesaste muchos archivos seguidos

**Solución:**
1. El sistema espera automáticamente con exponential backoff
2. Si persiste, aumenta los delays en `gemini_classifier.py:133-136`:
   ```python
   delays = [15, 30, 60]  # Aumentar a 15s, 30s, 60s
   ```
3. Reduce la frecuencia de revisión de emails en `.env`:
   ```bash
   EMAIL_CHECK_INTERVAL=10  # Cambiar de 5 a 10 minutos
   ```

### Problema 3: JSON Parsing Error

**Error completo:**
```
Error al decodificar JSON: Expecting property name enclosed in double quotes
```

**Causas:**
- Gemini devuelve JSON con doble llaves `{{ }}`
- Respuesta incluye markdown (```json)
- Caracteres especiales sin escapar

**Solución:**
Ya está implementada en `gemini_classifier.py:291-294`. Si sigue fallando:
1. Revisa los logs en `logs/facturia_YYYY-MM-DD.log`
2. Busca "TEXTO ORIGINAL" y "TEXTO LIMPIO"
3. Reporta el patrón nuevo en los issues del proyecto

### Problema 4: UTF-8 Encoding Error en Exportaciones

**Error completo:**
```
❌ Error de Excel: El códec 'utf-8' no puede decodificar el byte 0xf3
```

**Causas:**
- Archivo con encoding incorrecto (Latin-1, Windows-1252)
- Caracteres especiales sin manejar

**Solución:**
1. Verifica que `src/dashboard/__init__.py` tenga:
   ```python
   # -*- coding: utf-8 -*-
   ```
2. Asegúrate de usar `safe_str()` en todas las exportaciones
3. Si el error persiste, regenera el archivo:
   ```bash
   rm src/dashboard/__init__.py
   # Volver a crear con encoding correcto
   ```

### Problema 5: Botones de Dashboard no Funcionan

**Síntomas:**
- Click en "Guardar Cambios" pero no guarda
- Click en "Eliminar" pero no borra

**Causas:**
- `st.rerun()` termina el script antes del commit
- `session.flush()` no es suficiente

**Solución:**
Ya está implementada en `pages/1_Revisar_Transacciones.py:429-450`. Verifica que incluya:
```python
actualizar_transaccion(session, id, datos)
session.commit()  # ← Importante
time.sleep(1)     # ← Para ver el mensaje de éxito
st.rerun()
```

### Problema 6: Gmail IMAP "Authentication Failed"

**Error completo:**
```
❌ Error de autenticación: [AUTHENTICATIONFAILED] Invalid credentials
```

**Causas:**
- App Password incorrecta
- Autenticación de 2 factores no activada
- IMAP deshabilitado en Gmail

**Solución:**
1. Verifica que 2FA esté activo: https://myaccount.google.com/security
2. Genera nueva App Password: https://myaccount.google.com/apppasswords
3. Copia la contraseña de 16 caracteres sin espacios a `.env`:
   ```bash
   GMAIL_PASSWORD=abcdabcdabcdabcd
   ```
4. Habilita IMAP en Gmail:
   - Ve a Configuración → Ver toda la configuración
   - Pestaña "Reenvío y correo POP/IMAP"
   - Activar "Habilitar IMAP"

### Problema 7: Base de Datos Bloqueada (SQLite)

**Error completo:**
```
sqlalchemy.exc.OperationalError: database is locked
```

**Causas:**
- Múltiples procesos accediendo a SQLite simultáneamente
- Dashboard abierto mientras corre `main.py`

**Solución:**
1. Cierra el dashboard antes de ejecutar `main.py`
2. O cambia a PostgreSQL para producción:
   ```bash
   # Instalar PostgreSQL
   sudo apt install postgresql postgresql-contrib

   # Crear base de datos
   sudo -u postgres createdb facturia2

   # Actualizar .env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/facturia2
   ```

### Problema 8: Importación CSV Falla

**Síntomas:**
- CSV sube pero no se importa
- Error: "No se pudo leer el archivo"

**Causas:**
- Encoding incorrecto
- Separador incorrecto (coma vs punto y coma)
- Formato de fecha no reconocido

**Solución:**
1. Verifica el encoding del CSV:
   ```bash
   file -i tu_archivo.csv
   # Debe ser: utf-8 o iso-8859-1
   ```
2. Convierte a UTF-8 si es necesario:
   ```bash
   iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
   ```
3. Formatos de fecha soportados:
   - `2025-10-30` (YYYY-MM-DD)
   - `30/10/2025` (DD/MM/YYYY)
   - `30-10-2025` (DD-MM-YYYY)

---

## 🚀 Mejoras Futuras

### Features Planeados

- [ ] **Multi-usuario con Roles**
  - Sistema de autenticación
  - Roles: Admin, Contador, Visualizador
  - Permisos granulares por rol

- [ ] **Integración con Bancos**
  - API de bancos argentinos (MercadoPago, BruBank)
  - Sincronización automática de movimientos
  - Reconciliación con comprobantes

- [ ] **Machine Learning Avanzado**
  - Entrenamiento de modelo propio con PyTorch
  - Predicción de categorías sin usar API externa
  - Detección de anomalías en transacciones

- [ ] **Reportes Automáticos Programados**
  - Resumen semanal/mensual por email
  - Alertas de gastos excesivos
  - Comparativa mes anterior

- [ ] **App Móvil**
  - React Native o Flutter
  - Escaneo de comprobantes con cámara
  - Notificaciones push

- [ ] **Export a Sistemas Contables**
  - Tango
  - ContaSuite
  - Formato AFIP (Argentina)

- [ ] **OCR Mejorado**
  - Tesseract para PDFs escaneados
  - Detección de campos específicos (CUIT, CAE)

- [ ] **Dashboard con Predicciones**
  - Proyección de gastos próximo mes
  - Tendencias con regresión lineal
  - Recomendaciones de ahorro

### Optimizaciones Técnicas

- [ ] Migrar a FastAPI para el backend (API REST)
- [ ] Dockerizar aplicación completa
- [ ] CI/CD con GitHub Actions
- [ ] Tests unitarios (pytest) para cobertura > 80%
- [ ] Cache de clasificaciones con Redis
- [ ] Queue de procesamiento con Celery
- [ ] Websockets para updates en tiempo real

---

## 📊 Categorías Soportadas

### Ingresos

| Categoría | Descripción | Ejemplos |
|-----------|-------------|----------|
| 🏢 **Sueldo** | Salario mensual | Recibo de haberes, liquidación |
| 💼 **Cobro de servicios** | Facturación profesional | Honorarios, consultorías |
| 💰 **Depósito** | Depósitos bancarios | Transferencias entrantes |
| 📩 **Transferencia recibida** | Recepción de dinero | Mercado Pago, Ualá |
| 🛍️ **Ventas** | Ventas de productos | Factura A, B, C |
| ➕ **Otro ingreso** | Otros ingresos no categorizados | Devoluciones, reembolsos |

### Egresos

| Categoría | Descripción | Ejemplos |
|-----------|-------------|----------|
| 💡 **Factura de servicios** | Servicios básicos | Luz, agua, gas, internet, cable |
| 🛒 **Supermercado** | Compras de alimentos | Carrefour, Día, Walmart |
| 🏛️ **Impuestos** | Obligaciones fiscales | AFIP, Ingresos Brutos, ABL |
| 🏠 **Alquiler** | Pago de alquiler | Renta mensual, expensas |
| ⛽ **Combustible** | Carga de nafta/diesel | YPF, Shell, Axion |
| 🏥 **Salud** | Gastos médicos | OSDE, Swiss Medical, farmacias |
| 🎬 **Entretenimiento** | Ocio y recreación | Cine, Netflix, Spotify |
| ➖ **Otro egreso** | Otros gastos no categorizados | Varios |

**Agregar Categorías Personalizadas:**
1. Edita `src/ai_processor/gemini_classifier.py`
2. Busca `CATEGORIAS_INGRESOS` y `CATEGORIAS_EGRESOS`
3. Agrega tu categoría a la lista
4. Reinicia `main.py`

---

## 🤝 Contribuir

Las contribuciones son bienvenidas y apreciadas. Sigue estos pasos:

### 1. Fork del Proyecto

```bash
# Desde GitHub, haz click en "Fork"
# Luego clona tu fork:
git clone https://github.com/TU_USUARIO/FacturIA-2.0.git
cd FacturIA-2.0
```

### 2. Crear Rama de Feature

```bash
git checkout -b feature/nueva-funcionalidad
```

**Convención de nombres:**
- `feature/nombre` - Nueva funcionalidad
- `fix/nombre` - Corrección de bug
- `docs/nombre` - Documentación
- `refactor/nombre` - Refactorización

### 3. Hacer Cambios

```bash
# Edita archivos
# Asegúrate de seguir PEP 8
black src/  # Formatear código
flake8 src/  # Linting
```

### 4. Commit

```bash
git add .
git commit -m "feat: Agregar integración con MercadoPago API"
```

**Convención de commits:**
- `feat:` - Nueva característica
- `fix:` - Corrección de bug
- `docs:` - Documentación
- `style:` - Formato (no afecta código)
- `refactor:` - Refactorización
- `test:` - Tests
- `chore:` - Mantenimiento

### 5. Push y Pull Request

```bash
git push origin feature/nueva-funcionalidad
```

Luego desde GitHub, abre un Pull Request con:
- Título descriptivo
- Descripción detallada de cambios
- Screenshots (si aplica)
- Referencias a issues relacionados

### Código de Conducta

- Sé respetuoso con todos los colaboradores
- Acepta críticas constructivas
- Enfócate en lo mejor para el proyecto
- Reporta comportamiento inapropiado a: silvano.jm.puccini@gmail.com

---

## 📝 Licencia

Este proyecto está bajo la **Licencia MIT**.

```
MIT License

Copyright (c) 2025 Silvano Puccini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Ver archivo completo: [LICENSE](LICENSE)

---

## 👤 Autor

<div align="center">

### **Silvano Puccini**

*Full Stack Developer | AI Engineer | Data Scientist*

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/Silvano-Puccini)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/silvanopuccini)
[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:silvano.jm.puccini@gmail.com)

</div>

**Sobre mí:**

Desarrollador con pasión por la automatización y la inteligencia artificial. FacturIA 2.0 nace de la necesidad de simplificar la gestión contable para pequeñas empresas y freelancers, aprovechando las últimas tecnologías de IA.

**Otros proyectos:**
- 🔗 [Portfolio Personal](https://silvanopuccini.com) (próximamente)
- 🤖 Chatbot de Atención al Cliente con LangChain
- 📊 Dashboard de Analytics en Tiempo Real con FastAPI + React

**¿Quieres colaborar?**
Siempre estoy abierto a nuevas ideas y colaboraciones. ¡Contáctame!

---

## 🙏 Agradecimientos

- **Google Gemini Team** - Por la increíble API de Vision AI
- **Streamlit Community** - Por la mejor herramienta de dashboards en Python
- **SQLAlchemy Contributors** - Por el ORM más robusto de Python
- **Open Source Community** - Por todas las librerías que hacen posible este proyecto

**Librerías Utilizadas:**
- [google-generativeai](https://github.com/google/generative-ai-python) - SDK de Gemini
- [streamlit](https://streamlit.io/) - Framework de dashboards
- [sqlalchemy](https://www.sqlalchemy.org/) - ORM
- [plotly](https://plotly.com/python/) - Gráficos interactivos
- [reportlab](https://www.reportlab.com/) - Generación de PDFs
- [openpyxl](https://openpyxl.readthedocs.io/) - Exportación a Excel

**Inspiración:**
- [Notion](https://www.notion.so/) - Por el diseño de interfaces intuitivas
- [Expensify](https://www.expensify.com/) - Por la automatización de gastos
- [QuickBooks](https://quickbooks.intuit.com/) - Por la gestión contable profesional

---

## 📞 Soporte y Contacto

¿Necesitas ayuda o encontraste un bug?

### 1. Issues de GitHub
Reporta problemas en: https://github.com/SilvanoPuccini/FacturIA-2.0/issues

### 2. Documentación
Consulta este README y los comentarios en el código.

### 3. Contacto Directo
- Email: silvano.jm.puccini@gmail.com
- LinkedIn: [Silvano Puccini](https://www.linkedin.com/in/Silvano-Puccini)

### 4. Comunidad
- ⭐ Dale una estrella al proyecto si te resultó útil
- 🐛 Reporta bugs con detalles (logs, screenshots)
- 💡 Sugiere nuevas features en Discussions
- 🔀 Contribuye con Pull Requests

---

## 📊 Estadísticas del Proyecto

![GitHub stars](https://img.shields.io/github/stars/SilvanoPuccini/FacturIA-2.0?style=social)
![GitHub forks](https://img.shields.io/github/forks/SilvanoPuccini/FacturIA-2.0?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/SilvanoPuccini/FacturIA-2.0?style=social)

**Líneas de código:** ~5,000
**Archivos Python:** 15
**Dependencias:** 20+
**Tiempo de desarrollo:** 4 semanas
**Versión actual:** 2.0

---

<div align="center">

**Última actualización:** Octubre 2025

Hecho con ❤️ por [Silvano Puccini](https://github.com/silvanopuccini)

⭐ **¡Si este proyecto te ayudó, dale una estrella!** ⭐

</div>
