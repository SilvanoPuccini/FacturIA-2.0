"""
Configuración global de FacturIA 2.0
Carga variables de entorno y configuraciones del sistema
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# === PATHS DEL PROYECTO ===
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

INGRESOS_DIR = DATA_DIR / "ingresos"
EGRESOS_DIR = DATA_DIR / "egresos"
PROCESADOS_DIR = DATA_DIR / "procesados"

# === CREDENCIALES ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

# === BASE DE DATOS ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///facturia2.db")

# === CONFIGURACIÓN DEL SISTEMA ===
EMAIL_CHECK_INTERVAL = int(os.getenv("EMAIL_CHECK_INTERVAL", "5"))  # minutos
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# === CATEGORÍAS PREDEFINIDAS ===
CATEGORIAS_INGRESOS = [
    "sueldo",
    "cobro_servicios",
    "deposito",
    "transferencia_recibida",
    "ventas",
    "otro_ingreso"
]

CATEGORIAS_EGRESOS = [
    "factura_servicios",
    "supermercado",
    "impuestos",
    "alquiler",
    "combustible",
    "salud",
    "entretenimiento",
    "otro_egreso"
]

# === PROMPT PARA GEMINI ===
GEMINI_PROMPT_TEMPLATE = """
Analiza esta imagen/documento financiero y extrae TODOS los datos en formato JSON.

Responde EXACTAMENTE en este formato JSON (sin texto adicional):

{{
  "tipo": "ingreso" o "egreso",
  "categoria": "una de las categorías listadas abajo",
  "fecha": "YYYY-MM-DD",
  "monto": 1500.50,
  "emisor_receptor": "Nombre de la empresa o persona",
  "descripcion": "Breve descripción del concepto",
  "numero_comprobante": "001-00123456 (si existe)"
}}

CATEGORÍAS DE INGRESOS VÁLIDAS:
- sueldo
- cobro_servicios
- deposito
- transferencia_recibida
- ventas
- otro_ingreso

CATEGORÍAS DE EGRESOS VÁLIDAS:
- factura_servicios (luz, agua, gas, internet, teléfono)
- supermercado
- impuestos
- alquiler
- combustible
- salud
- entretenimiento
- otro_egreso

IMPORTANTE:
- Si no puedes determinar algún campo, usa null
- El monto debe ser solo número (sin símbolos de moneda)
- La fecha debe estar en formato YYYY-MM-DD
- Responde SOLO el JSON, sin explicaciones adicionales
"""

# === VALIDACIÓN ===
def validar_configuracion():
    """Valida que las configuraciones necesarias estén presentes"""
    errores = []

    if not GOOGLE_API_KEY:
        errores.append("❌ GOOGLE_API_KEY no configurada en .env")

    if not GMAIL_EMAIL:
        errores.append("❌ GMAIL_EMAIL no configurado en .env")

    if not GMAIL_PASSWORD:
        errores.append("❌ GMAIL_PASSWORD no configurado en .env")

    if errores:
        print("\n🚨 ERRORES DE CONFIGURACIÓN:")
        for error in errores:
            print(f"   {error}")
        print("\n💡 Solución:")
        print("   1. Copiá .env.example como .env")
        print("   2. Completá las variables necesarias")
        return False

    print("✅ Configuración validada correctamente")
    return True

if __name__ == "__main__":
    validar_configuracion()
