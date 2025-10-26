# 💰 FacturIA 2.0 - Sistema Inteligente de Gestión Financiera

Sistema automatizado de procesamiento y análisis de ingresos y egresos mediante Inteligencia Artificial.

## 🚀 Características

- ✅ **Monitoreo Automático de Email:** Lee emails corporativos 24/7
- ✅ **Descarga Inteligente:** Detecta y descarga adjuntos (PDF, PNG, JPG)
- ✅ **Clasificación con IA:** Google Gemini Vision clasifica automáticamente
- ✅ **Categorización Automática:** Distingue ingresos/egresos y categorías
- ✅ **Dashboard en Tiempo Real:** Visualización con Streamlit
- ✅ **Reportes Automáticos:** KPIs, gráficos y tendencias
- ✅ **Base de Datos Completa:** Histórico de todas las transacciones

## 📊 Flujo del Sistema

```
Email → Descarga → Procesamiento IA → Base de Datos → Dashboard
```

## 🛠️ Tecnologías

- **Python 3.10+**
- **Google Gemini Vision API** - Clasificación inteligente
- **Gmail API / IMAP** - Lectura de emails
- **SQLite / PostgreSQL** - Almacenamiento
- **Streamlit** - Dashboard interactivo
- **Plotly** - Gráficos avanzados

## 📁 Estructura del Proyecto

```
FacturIA-2.0/
├── src/
│   ├── email_monitor/      # Monitor de emails
│   ├── ai_processor/       # Procesamiento con IA
│   ├── database/           # Gestión de BD
│   └── dashboard/          # Dashboard Streamlit
├── data/                   # Datos procesados
├── logs/                   # Logs del sistema
└── main.py                 # Script principal
```

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/SilvanoPuccini/FacturIA-2.0.git
cd FacturIA-2.0
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

Completar:
- `GOOGLE_API_KEY`: Tu API key de Google Gemini
- `GMAIL_EMAIL`: Tu email corporativo
- `GMAIL_PASSWORD`: Tu App Password de Gmail

### 5. Inicializar base de datos

```bash
python src/database/init_db.py
```

## 🎯 Uso

### Ejecutar el sistema completo

```bash
python main.py
```

Esto iniciará:
1. Monitor de email (revisa cada 5 minutos)
2. Procesador automático de documentos
3. Actualización de base de datos

### Ejecutar solo el dashboard

```bash
streamlit run src/dashboard/app.py
```

El dashboard estará disponible en: `http://localhost:8501`

## 📊 Categorías Soportadas

### Ingresos
- Sueldo
- Cobro de servicios
- Depósito
- Transferencia recibida
- Ventas
- Otro ingreso

### Egresos
- Factura de servicios (luz, agua, gas, internet)
- Supermercado
- Impuestos
- Alquiler
- Combustible
- Salud
- Entretenimiento
- Otro egreso

## 🔐 Seguridad

- ✅ Credenciales en archivo `.env` (nunca en Git)
- ✅ API keys cifradas
- ✅ Acceso de solo lectura a emails
- ✅ Datos almacenados localmente

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👤 Autor

**Silvano Puccini**
- LinkedIn: [linkedin.com/in/Silvano-Puccini](https://www.linkedin.com/in/Silvano-Puccini)
- GitHub: [github.com/silvanopuccini](https://github.com/silvanopuccini)
- Email: silvano.jm.puccini@gmail.com

## 🙏 Agradecimientos

- Google Gemini Vision API
- Comunidad de Streamlit
- Open Source Contributors

---

**Última actualización:** Octubre 2024
