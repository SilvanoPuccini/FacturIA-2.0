"""
Operaciones CRUD para la base de datos
Create, Read, Update, Delete
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

from .models import (
    Transaccion, TipoTransaccion, OrigenArchivo
)


# ========== TRANSACCIONES ==========

def crear_transaccion(session: Session, datos: Dict) -> Transaccion:
    """
    Crea una nueva transacción en la base de datos

    Args:
        session: Sesión de SQLAlchemy
        datos: Diccionario con datos de la transacción

    Returns:
        Transacción creada
    """
    try:
        # Convertir strings a Enums
        if isinstance(datos.get("tipo"), str):
            datos["tipo"] = TipoTransaccion(datos["tipo"])

        if isinstance(datos.get("origen"), str):
            datos["origen"] = OrigenArchivo(datos["origen"])

        # Parsear fecha si es string
        if isinstance(datos.get("fecha_transaccion"), str):
            datos["fecha_transaccion"] = datetime.fromisoformat(datos["fecha_transaccion"])
        elif datos.get("fecha") and isinstance(datos["fecha"], str):
            # Manejar campo "fecha" además de "fecha_transaccion"
            datos["fecha_transaccion"] = datetime.fromisoformat(datos["fecha"])
            datos.pop("fecha", None)

        # Crear transacción
        transaccion = Transaccion(**datos)
        session.add(transaccion)
        session.flush()  # Para obtener el ID

        logger.info(f"✓ Transacción creada: ID {transaccion.id}")
        return transaccion

    except Exception as e:
        logger.error(f"❌ Error al crear transacción: {e}")
        raise


def crear_transacciones_batch(session: Session, lista_datos: List[Dict]) -> int:
    """
    Crea múltiples transacciones en batch

    Args:
        session: Sesión de SQLAlchemy
        lista_datos: Lista de diccionarios con datos

    Returns:
        Cantidad de transacciones creadas
    """
    try:
        transacciones = []

        for datos in lista_datos:
            try:
                # Convertir strings a Enums
                if isinstance(datos.get("tipo"), str):
                    datos["tipo"] = TipoTransaccion(datos["tipo"])

                if isinstance(datos.get("origen"), str):
                    datos["origen"] = OrigenArchivo(datos["origen"])

                # Parsear fecha
                if isinstance(datos.get("fecha_transaccion"), str):
                    datos["fecha_transaccion"] = datetime.fromisoformat(datos["fecha_transaccion"])
                elif datos.get("fecha") and isinstance(datos["fecha"], str):
                    datos["fecha_transaccion"] = datetime.fromisoformat(datos["fecha"])
                    datos.pop("fecha", None)

                transaccion = Transaccion(**datos)
                transacciones.append(transaccion)

            except Exception as e:
                logger.warning(f"Error al procesar transacción individual: {e}")
                continue

        # Insertar en batch
        session.bulk_save_objects(transacciones)
        session.flush()

        logger.info(f"✅ {len(transacciones)} transacciones creadas en batch")
        return len(transacciones)

    except Exception as e:
        logger.error(f"❌ Error al crear batch de transacciones: {e}")
        raise


def obtener_transaccion(session: Session, transaccion_id: int) -> Optional[Transaccion]:
    """Obtiene una transacción por ID"""
    return session.query(Transaccion).filter(Transaccion.id == transaccion_id).first()


def obtener_transacciones(
    session: Session,
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    limite: int = 100
) -> List[Transaccion]:
    """
    Obtiene transacciones con filtros opcionales

    Args:
        session: Sesión de SQLAlchemy
        tipo: Filtrar por tipo (ingreso/egreso)
        categoria: Filtrar por categoría
        fecha_desde: Fecha inicio
        fecha_hasta: Fecha fin
        limite: Cantidad máxima de resultados

    Returns:
        Lista de transacciones
    """
    query = session.query(Transaccion)

    # Aplicar filtros
    if tipo:
        query = query.filter(Transaccion.tipo == TipoTransaccion(tipo))

    if categoria:
        query = query.filter(Transaccion.categoria == categoria)

    if fecha_desde:
        query = query.filter(Transaccion.fecha_transaccion >= fecha_desde)

    if fecha_hasta:
        query = query.filter(Transaccion.fecha_transaccion <= fecha_hasta)

    # Ordenar por fecha descendente
    query = query.order_by(desc(Transaccion.fecha_transaccion))

    # Limitar resultados
    if limite:
        query = query.limit(limite)

    return query.all()


def actualizar_transaccion(session: Session, transaccion_id: int, datos: Dict) -> bool:
    """
    Actualiza una transacción existente

    Args:
        session: Sesión de SQLAlchemy
        transaccion_id: ID de la transacción
        datos: Diccionario con campos a actualizar

    Returns:
        True si se actualizó correctamente
    """
    try:
        transaccion = obtener_transaccion(session, transaccion_id)

        if not transaccion:
            logger.warning(f"Transacción {transaccion_id} no encontrada")
            return False

        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(transaccion, campo):
                setattr(transaccion, campo, valor)

        session.flush()
        logger.info(f"✓ Transacción {transaccion_id} actualizada")
        return True

    except Exception as e:
        logger.error(f"❌ Error al actualizar transacción: {e}")
        return False


def eliminar_transaccion(session: Session, transaccion_id: int) -> bool:
    """Elimina una transacción"""
    try:
        transaccion = obtener_transaccion(session, transaccion_id)

        if not transaccion:
            return False

        session.delete(transaccion)
        session.flush()
        logger.info(f"✓ Transacción {transaccion_id} eliminada")
        return True

    except Exception as e:
        logger.error(f"❌ Error al eliminar transacción: {e}")
        return False


# ========== ARCHIVOS PROCESADOS ==========
# TODO: Implementar modelo ArchivoProcesado en el futuro

_archivos_procesados_cache = set()

def registrar_archivo_procesado(
    session: Session,
    nombre: str,
    hash: str,
    tipo: str,
    transacciones_extraidas: int = 0,
    email_id: Optional[str] = None
) -> bool:
    """
    Registra un archivo como procesado (versión simplificada sin modelo)

    Returns:
        True si se registró exitosamente
    """
    try:
        # Por ahora solo guardamos el hash en un set en memoria
        _archivos_procesados_cache.add(hash)
        logger.info(f"✓ Archivo registrado: {nombre} (hash: {hash[:8]}...)")
        return True

    except Exception as e:
        logger.error(f"❌ Error al registrar archivo: {e}")
        return False


def archivo_ya_procesado(session: Session, hash_archivo: str) -> bool:
    """
    Verifica si un archivo ya fue procesado (por hash)

    Returns:
        True si el archivo ya fue procesado
    """
    # Por ahora verificamos en el cache en memoria
    return hash_archivo in _archivos_procesados_cache


# ========== ESTADÍSTICAS ==========

def calcular_estadisticas_periodo(
    session: Session,
    fecha_inicio: datetime,
    fecha_fin: datetime
) -> Dict:
    """
    Calcula estadísticas de un período

    Args:
        session: Sesión de SQLAlchemy
        fecha_inicio: Fecha de inicio
        fecha_fin: Fecha de fin

    Returns:
        Diccionario con estadísticas
    """
    try:
        # Obtener transacciones del período
        transacciones = session.query(Transaccion).filter(
            and_(
                Transaccion.fecha_transaccion >= fecha_inicio,
                Transaccion.fecha_transaccion <= fecha_fin
            )
        ).all()

        # Calcular totales
        ingresos = [t for t in transacciones if t.tipo == TipoTransaccion.INGRESO]
        egresos = [t for t in transacciones if t.tipo == TipoTransaccion.EGRESO]

        total_ingresos = sum(t.monto for t in ingresos)
        total_egresos = sum(t.monto for t in egresos)

        # Agrupar por categoría
        categorias_ingresos = {}
        for t in ingresos:
            cat = t.categoria
            categorias_ingresos[cat] = categorias_ingresos.get(cat, 0) + t.monto

        categorias_egresos = {}
        for t in egresos:
            cat = t.categoria
            categorias_egresos[cat] = categorias_egresos.get(cat, 0) + t.monto

        return {
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat(),
            "total_transacciones": len(transacciones),
            "total_ingresos": round(total_ingresos, 2),
            "total_egresos": round(total_egresos, 2),
            "balance": round(total_ingresos - total_egresos, 2),
            "cantidad_ingresos": len(ingresos),
            "cantidad_egresos": len(egresos),
            "categorias_ingresos": {k: round(v, 2) for k, v in categorias_ingresos.items()},
            "categorias_egresos": {k: round(v, 2) for k, v in categorias_egresos.items()}
        }

    except Exception as e:
        logger.error(f"❌ Error al calcular estadísticas: {e}")
        return {}


def obtener_totales_mes_actual(session: Session) -> Dict:
    """Obtiene totales del mes actual"""
    hoy = datetime.now()
    primer_dia_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ultimo_dia_mes = (primer_dia_mes + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    return calcular_estadisticas_periodo(session, primer_dia_mes, ultimo_dia_mes)


def obtener_top_categorias(session: Session, tipo: str, limite: int = 5) -> List[Dict]:
    """
    Obtiene las categorías con mayor monto

    Args:
        session: Sesión de SQLAlchemy
        tipo: "ingreso" o "egreso"
        limite: Cantidad de categorías a retornar

    Returns:
        Lista de diccionarios con categoría y monto
    """
    try:
        query = session.query(
            Transaccion.categoria,
            func.sum(Transaccion.monto).label('total'),
            func.count(Transaccion.id).label('cantidad')
        ).filter(
            Transaccion.tipo == TipoTransaccion(tipo)
        ).group_by(
            Transaccion.categoria
        ).order_by(
            desc('total')
        ).limit(limite)

        resultados = query.all()

        return [
            {
                "categoria": r.categoria,
                "total": round(r.total, 2),
                "cantidad": r.cantidad
            }
            for r in resultados
        ]

    except Exception as e:
        logger.error(f"❌ Error al obtener top categorías: {e}")
        return []


# ========== LOGS ==========

def registrar_log(
    session: Session,
    nivel: str,
    modulo: str,
    evento: str,
    mensaje: Optional[str] = None
):
    """Registra un evento en el log"""
    try:
        log = LogProcesamiento(
            nivel=nivel,
            modulo=modulo,
            evento=evento,
            mensaje=mensaje
        )
        session.add(log)
        session.flush()

    except Exception as e:
        logger.error(f"Error al registrar log: {e}")


if __name__ == "__main__":
    # Prueba del módulo
    from .connection import inicializar_base_datos

    print("\n🗄️  Probando operaciones CRUD...\n")

    db = inicializar_base_datos("sqlite:///:memory:")

    with db.get_session() as session:
        # Crear transacciones de prueba
        datos1 = {
            "tipo": "ingreso",
            "categoria": "sueldo",
            "monto": 500000,
            "fecha_transaccion": datetime.now(),
            "descripcion": "Sueldo octubre",
            "origen": "csv"
        }

        datos2 = {
            "tipo": "egreso",
            "categoria": "factura_servicios",
            "monto": 15000,
            "fecha_transaccion": datetime.now(),
            "descripcion": "Factura Edenor",
            "origen": "pdf"
        }

        t1 = crear_transaccion(session, datos1)
        t2 = crear_transaccion(session, datos2)

        print(f"✅ Transacciones creadas: {t1.id}, {t2.id}\n")

        # Obtener estadísticas
        stats = obtener_totales_mes_actual(session)
        print("📊 Estadísticas del mes:")
        for key, value in stats.items():
            if not isinstance(value, dict):
                print(f"   {key}: {value}")

        # Top categorías
        print("\n🏆 Top categorías de egresos:")
        top = obtener_top_categorias(session, "egreso", 3)
        for cat in top:
            print(f"   {cat['categoria']}: ${cat['total']} ({cat['cantidad']} transacciones)")

    db.cerrar()
    print("\n✅ Prueba completada")
