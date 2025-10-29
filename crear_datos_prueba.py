#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_database, crear_transaccion
from src.database.models import TipoTransaccion, OrigenArchivo

print("\n🎲 Creando transacciones de prueba...")
db = get_database()

transacciones = [
    {"tipo": TipoTransaccion.INGRESO, "categoria": "sueldo", "monto": 500000, "fecha_transaccion": datetime.now() - timedelta(days=25), "emisor_receptor": "EMPRESA SA", "descripcion": "Sueldo octubre", "origen": OrigenArchivo.PDF, "procesado_por_ia": True, "persona": "Juan Perez"},
    {"tipo": TipoTransaccion.EGRESO, "categoria": "supermercado", "monto": 12450, "fecha_transaccion": datetime.now() - timedelta(days=12), "emisor_receptor": "CARREFOUR", "descripcion": "Compra semanal", "origen": OrigenArchivo.IMAGEN, "procesado_por_ia": True, "persona": "Maria Rodriguez"},
]

with db.get_session() as session:
    for datos in transacciones:
        crear_transaccion(session, datos)
        print(f"  ✓ {datos['descripcion']}")

print(f"\n✅ {len(transacciones)} transacciones creadas!\n")
