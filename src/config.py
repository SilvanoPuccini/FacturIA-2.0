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
Eres un experto en análisis de documentos financieros. Tu tarea es extraer TODOS los datos relevantes de esta imagen/documento y responder en formato JSON estructurado.

⚠️ INSTRUCCIONES CRÍTICAS:
1. Responde SOLO con el objeto JSON, sin texto adicional antes o después
2. NO uses bloques de código markdown (```json)
3. Usa EXACTAMENTE las categorías listadas abajo (sin variaciones ni sinónimos)
4. Si tienes dudas entre dos categorías, elige la más específica

📋 FORMATO DE RESPUESTA REQUERIDO:

{{
  "tipo": "ingreso" o "egreso",
  "categoria": "exactamente una de las categorías válidas listadas abajo",
  "fecha": "YYYY-MM-DD",
  "monto": 1500.50,
  "emisor_receptor": "Nombre exacto de la empresa o persona",
  "descripcion": "Descripción clara y concisa del concepto",
  "numero_comprobante": "001-00123456",
  "persona": "Nombre de la persona asociada (si está visible)"
}}

✅ CATEGORÍAS DE INGRESOS VÁLIDAS (elige UNA exactamente como está escrita):
- sueldo → Pago de empleador, salario mensual, aguinaldo
- cobro_servicios → Pago por servicios profesionales prestados
- deposito → Depósito bancario, transferencia entrante
- transferencia_recibida → Transferencia de terceros
- ventas → Ingresos por venta de productos
- otro_ingreso → Cualquier otro tipo de ingreso

✅ CATEGORÍAS DE EGRESOS VÁLIDAS (elige UNA exactamente como está escrita):
- factura_servicios → Luz, agua, gas, internet, teléfono, cable, streaming
- supermercado → Compras de alimentos y productos del hogar
- impuestos → ABL, Ganancias, IIBB, patentes, tasas municipales
- alquiler → Pago de alquiler de vivienda o local
- combustible → Nafta, gasoil, carga de combustible
- salud → Médico, farmacia, obra social, prepaga, estudios
- entretenimiento → Cine, restaurantes, delivery, ocio, suscripciones
- otro_egreso → Cualquier otro tipo de egreso

🔍 EJEMPLOS DE CLASIFICACIÓN CORRECTA:

Ejemplo 1 - Factura de luz:
{{
  "tipo": "egreso",
  "categoria": "factura_servicios",
  "fecha": "2025-10-15",
  "monto": 15750.50,
  "emisor_receptor": "EDENOR",
  "descripcion": "Factura de energía eléctrica período 09/2025",
  "numero_comprobante": "0001-00045678",
  "persona": null
}}

Ejemplo 2 - Recibo de sueldo:
{{
  "tipo": "ingreso",
  "categoria": "sueldo",
  "fecha": "2025-10-01",
  "monto": 500000.00,
  "emisor_receptor": "Empresa XYZ S.A.",
  "descripcion": "Sueldo mensual octubre 2025",
  "numero_comprobante": "REC-2025-10-001",
  "persona": "Juan Pérez"
}}

Ejemplo 3 - Compra supermercado:
{{
  "tipo": "egreso",
  "categoria": "supermercado",
  "fecha": "2025-10-20",
  "monto": 45680.25,
  "emisor_receptor": "Carrefour",
  "descripcion": "Compra semanal alimentos y limpieza",
  "numero_comprobante": "T-2025-8745",
  "persona": null
}}

⚠️ REGLAS ESTRICTAS DE VALIDACIÓN:
- "tipo" debe ser EXACTAMENTE "ingreso" o "egreso" (en minúsculas)
- "categoria" debe ser EXACTAMENTE una de las listadas (sin espacios extras, sin mayúsculas)
- "monto" debe ser un NÚMERO positivo sin símbolos ($, AR$, etc.)
- "fecha" debe estar en formato YYYY-MM-DD (año-mes-día con guiones)
- Si NO puedes determinar un campo con certeza, usa null (sin comillas)
- "persona" es opcional, úsalo si identificas a quién pertenece la transacción

🚫 ERRORES COMUNES A EVITAR:
- ❌ "factura de servicios" → ✅ "factura_servicios"
- ❌ "Supermercado" → ✅ "supermercado"
- ❌ "$1500.50" → ✅ 1500.50
- ❌ "15/10/2025" → ✅ "2025-10-15"
- ❌ Agregar texto explicativo fuera del JSON → ✅ Solo el JSON

🎯 AHORA ANALIZA EL DOCUMENTO Y RESPONDE CON EL JSON:
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
