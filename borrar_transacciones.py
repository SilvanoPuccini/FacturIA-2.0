#!/usr/bin/env python3
"""
Script para borrar transacciones de FacturIA 2.0
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_database, obtener_transacciones
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def main():
    """Borra transacciones"""
    print("\n🗑️  Eliminador de Transacciones - FacturIA 2.0\n")
    
    db = get_database()
    
    # Obtener todas las transacciones
    with db.get_session() as session:
        transacciones = obtener_transacciones(session)
        
        if not transacciones:
            print("✅ No hay transacciones para borrar\n")
            return
        
        print(f"📊 Total de transacciones: {len(transacciones)}\n")
        
        print("Opciones:")
        print("  1. Borrar TODAS las transacciones")
        print("  2. Borrar por ID específico")
        print("  3. Cancelar")
        
        opcion = input("\nElige una opción (1/2/3): ")
        
        if opcion == "1":
            confirmar = input(f"\n⚠️  ¿Borrar TODAS las {len(transacciones)} transacciones? (si/no): ")
            if confirmar.lower() in ['si', 's', 'yes', 'y']:
                from sqlalchemy import delete
                from src.database.models import Transaccion
                
                session.execute(delete(Transaccion))
                session.commit()
                print(f"\n✅ {len(transacciones)} transacciones eliminadas\n")
            else:
                print("\n❌ Operación cancelada\n")
        
        elif opcion == "2":
            # Mostrar transacciones
            print("\nTransacciones disponibles:")
            for t in transacciones[:10]:  # Mostrar primeras 10
                print(f"  ID {t.id}: {t.tipo.value} - {t.categoria} - ${t.monto:,.2f}")
            
            if len(transacciones) > 10:
                print(f"  ... y {len(transacciones) - 10} más")
            
            ids = input("\nIDs a borrar (separados por coma): ")
            ids_list = [int(x.strip()) for x in ids.split(',') if x.strip()]
            
            from src.database.crud import eliminar_transaccion
            eliminadas = 0
            for tid in ids_list:
                if eliminar_transaccion(session, tid):
                    eliminadas += 1
            
            session.commit()
            print(f"\n✅ {eliminadas} transacciones eliminadas\n")
        
        else:
            print("\n❌ Operación cancelada\n")


if __name__ == "__main__":
    main()
