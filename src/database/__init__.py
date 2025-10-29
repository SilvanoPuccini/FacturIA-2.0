"""
Database - Gestion de base de datos con SQLAlchemy
"""
from .models import Transaccion, TipoTransaccion, OrigenArchivo
from .connection import Database, get_database, inicializar_base_datos
from .crud import (
    crear_transaccion,
    crear_transacciones_batch,
    obtener_transaccion,
    obtener_transacciones,
    actualizar_transaccion,
    eliminar_transaccion,
    registrar_archivo_procesado,
    archivo_ya_procesado,
    calcular_estadisticas_periodo,
    obtener_totales_mes_actual,
    obtener_top_categorias
)

__all__ = [
    # Modelos
    "Transaccion",
    "TipoTransaccion",
    "OrigenArchivo",
    # Conexion
    "Database",
    "get_database",
    "inicializar_base_datos",
    # CRUD
    "crear_transaccion",
    "crear_transacciones_batch",
    "obtener_transaccion",
    "obtener_transacciones",
    "actualizar_transaccion",
    "eliminar_transaccion",
    "registrar_archivo_procesado",
    "archivo_ya_procesado",
    "calcular_estadisticas_periodo",
    "obtener_totales_mes_actual",
    "obtener_top_categorias"
]
