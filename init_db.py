#!/usr/bin/env python3
"""
Script de inicialización de base de datos para FacturIA 2.0
Crea todas las tablas necesarias
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import inicializar_base_datos
from src.config import DATABASE_URL
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def main():
    """Inicializa la base de datos"""
    print("\n" + "="*60)
    print("🗄️  Inicializando Base de Datos - FacturIA 2.0")
    print("="*60 + "\n")

    # Verificar si se debe recrear
    recrear = False
    if len(sys.argv) > 1 and sys.argv[1] == "--recrear":
        confirmar = input("⚠️  ADVERTENCIA: Esto eliminará TODOS los datos. ¿Continuar? (si/no): ")
        if confirmar.lower() in ['si', 's', 'yes', 'y']:
            recrear = True
        else:
            print("❌ Operación cancelada")
            return

    try:
        # Inicializar base de datos
        db = inicializar_base_datos(DATABASE_URL, recrear=recrear)

        print("\n✅ Base de datos inicializada correctamente")
        print(f"📍 Ubicación: {DATABASE_URL}\n")

        # Mostrar estadísticas
        stats = db.obtener_estadisticas()
        print("📊 Estadísticas actuales:")
        for key, value in stats.items():
            print(f"   {key}: {value}")

        print("\n🎉 Listo para usar!\n")

    except Exception as e:
        logger.error(f"❌ Error al inicializar base de datos: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
