#!/usr/bin/env python3
"""
Script para limpiar completamente la base de datos de FacturIA 2.0
CUIDADO: Esto eliminará TODAS las transacciones y archivos procesados
"""

import os
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import Database
from src.database.models import Transaccion

def limpiar_base_datos():
    """Limpia todas las tablas de la base de datos"""

    print("\n" + "="*60)
    print("⚠️  LIMPIAR BASE DE DATOS - FacturIA 2.0")
    print("="*60)
    print("\n⚠️  ADVERTENCIA: Esta acción eliminará TODAS las transacciones")
    print("de la base de datos.")
    print("\nEsta acción NO se puede deshacer.\n")

    confirmacion = input("¿Estás seguro de continuar? Escribe 'SI' para confirmar: ")

    if confirmacion.upper() != "SI":
        print("\n❌ Operación cancelada.")
        return

    # Conectar a la base de datos
    db = Database('sqlite:///facturia2.db')

    try:
        with db.get_session() as session:
            # Contar antes de eliminar
            total_transacciones = session.query(Transaccion).count()

            print(f"\n📊 Registros a eliminar:")
            print(f"  - Transacciones: {total_transacciones}")

            if total_transacciones == 0:
                print("\n✅ La base de datos ya está vacía.")
                return

            print("\n🗑️  Eliminando registros...")

            # Eliminar todas las transacciones
            session.query(Transaccion).delete()
            print(f"  ✓ {total_transacciones} transacciones eliminadas")

            session.commit()

            print("\n✅ Base de datos limpiada exitosamente!")
            print("\n📝 Nota: Los archivos físicos en data/ NO fueron eliminados.")
            print("Si también quieres limpiar archivos físicos, usa la Opción 2")

    except Exception as e:
        print(f"\n❌ Error al limpiar base de datos: {e}")
        return


def limpiar_todo():
    """Limpia base de datos Y archivos físicos"""

    print("\n" + "="*60)
    print("🧹 LIMPIEZA COMPLETA - FacturIA 2.0")
    print("="*60)
    print("\n⚠️  ADVERTENCIA: Esto eliminará:")
    print("  1. TODAS las transacciones de la base de datos")
    print("  2. TODOS los registros de archivos procesados")
    print("  3. TODOS los archivos físicos en data/procesado/")
    print("  4. TODOS los archivos temporales en data/temp_*/")
    print("\nEsta acción NO se puede deshacer.\n")

    confirmacion = input("¿Estás TOTALMENTE seguro? Escribe 'ELIMINAR TODO' para confirmar: ")

    if confirmacion != "ELIMINAR TODO":
        print("\n❌ Operación cancelada.")
        return

    # Limpiar base de datos
    db = Database('sqlite:///facturia2.db')

    try:
        with db.get_session() as session:
            total_transacciones = session.query(Transaccion).count()

            print(f"\n📊 Eliminando de base de datos:")
            print(f"  - Transacciones: {total_transacciones}")

            session.query(Transaccion).delete()
            session.commit()

            print("  ✓ Base de datos limpiada")

        # Limpiar archivos físicos
        import shutil

        print(f"\n🗑️  Eliminando archivos físicos:")

        carpetas_limpiar = [
            "data/procesado/ingresos",
            "data/procesado/egresos",
            "data/temp_pdf",
            "data/temp_img",
            "data/temp_csv"
        ]

        archivos_eliminados = 0
        for carpeta in carpetas_limpiar:
            if os.path.exists(carpeta):
                archivos = list(Path(carpeta).glob("*"))
                for archivo in archivos:
                    if archivo.is_file():
                        archivo.unlink()
                        archivos_eliminados += 1
                print(f"  ✓ {carpeta}: {len(archivos)} archivos eliminados")

        print(f"\n✅ Limpieza completa exitosa!")
        print(f"  - Total archivos eliminados: {archivos_eliminados}")
        print(f"  - Base de datos: limpia")
        print(f"\n🎯 Sistema listo para empezar de cero!")

    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {e}")


if __name__ == "__main__":
    print("\n🧹 Script de Limpieza - FacturIA 2.0\n")
    print("Opciones:")
    print("  1. Limpiar solo BASE DE DATOS (mantiene archivos)")
    print("  2. Limpiar TODO (base de datos + archivos físicos)")
    print("  3. Cancelar")

    opcion = input("\nElige una opción (1/2/3): ")

    if opcion == "1":
        limpiar_base_datos()
    elif opcion == "2":
        limpiar_todo()
    else:
        print("\n❌ Operación cancelada.")
