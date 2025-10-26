"""
Gestión de conexión a la base de datos
Configuración de SQLAlchemy y gestión de sesiones
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from loguru import logger
from pathlib import Path
import os

from .models import Base


class Database:
    """Gestor de base de datos SQLAlchemy"""

    def __init__(self, database_url: str = None):
        """
        Inicializa la conexión a la base de datos

        Args:
            database_url: URL de conexión (ej: sqlite:///facturia2.db o postgresql://...)
        """
        if database_url is None:
            database_url = os.getenv("DATABASE_URL", "sqlite:///facturia2.db")

        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

        self._crear_engine()

    def _crear_engine(self):
        """Crea el engine de SQLAlchemy con configuración optimizada"""
        try:
            # Configuración según tipo de base de datos
            if self.database_url.startswith("sqlite"):
                # SQLite: configuración especial
                self.engine = create_engine(
                    self.database_url,
                    echo=False,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool
                )

                # Habilitar foreign keys en SQLite
                @event.listens_for(self.engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging para mejor rendimiento
                    cursor.close()

            else:
                # PostgreSQL u otras bases
                self.engine = create_engine(
                    self.database_url,
                    echo=False,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True  # Verificar conexiones antes de usar
                )

            # Crear SessionLocal
            self.SessionLocal = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
            )

            logger.info(f"✅ Engine de base de datos creado: {self.database_url}")

        except Exception as e:
            logger.error(f"❌ Error al crear engine de BD: {e}")
            raise

    def crear_tablas(self):
        """Crea todas las tablas en la base de datos"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Tablas de base de datos creadas/verificadas")
        except Exception as e:
            logger.error(f"❌ Error al crear tablas: {e}")
            raise

    def drop_tablas(self):
        """Elimina todas las tablas (¡CUIDADO!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("⚠️  Todas las tablas fueron eliminadas")
        except Exception as e:
            logger.error(f"❌ Error al eliminar tablas: {e}")
            raise

    @contextmanager
    def get_session(self):
        """
        Context manager para obtener una sesión de base de datos

        Uso:
            with db.get_session() as session:
                session.add(objeto)
                session.commit()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en transacción de BD: {e}")
            raise
        finally:
            session.close()

    def get_session_sync(self):
        """
        Obtiene una sesión sin context manager (debe cerrarse manualmente)

        Returns:
            Session de SQLAlchemy
        """
        return self.SessionLocal()

    def cerrar(self):
        """Cierra todas las conexiones"""
        try:
            self.SessionLocal.remove()
            self.engine.dispose()
            logger.info("✅ Conexiones de base de datos cerradas")
        except Exception as e:
            logger.error(f"Error al cerrar BD: {e}")

    def verificar_conexion(self) -> bool:
        """
        Verifica que la conexión a la base de datos funcione

        Returns:
            True si la conexión es exitosa
        """
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("✅ Conexión a base de datos verificada")
            return True
        except Exception as e:
            logger.error(f"❌ Error al verificar conexión a BD: {e}")
            return False

    def obtener_estadisticas(self) -> dict:
        """
        Obtiene estadísticas de la base de datos

        Returns:
            Diccionario con estadísticas
        """
        from .models import Transaccion, ArchivoProcesado

        with self.get_session() as session:
            total_transacciones = session.query(Transaccion).count()
            total_archivos = session.query(ArchivoProcesado).count()

            # Contar por tipo
            total_ingresos = session.query(Transaccion).filter(
                Transaccion.tipo == "ingreso"
            ).count()
            total_egresos = session.query(Transaccion).filter(
                Transaccion.tipo == "egreso"
            ).count()

            return {
                "total_transacciones": total_transacciones,
                "total_ingresos": total_ingresos,
                "total_egresos": total_egresos,
                "total_archivos_procesados": total_archivos
            }

    def backup(self, ruta_backup: str):
        """
        Crea un backup de la base de datos (solo SQLite)

        Args:
            ruta_backup: Ruta donde guardar el backup
        """
        if not self.database_url.startswith("sqlite"):
            logger.warning("Backup solo disponible para SQLite")
            return

        try:
            import shutil

            # Extraer ruta de la base de datos del URL
            db_path = self.database_url.replace("sqlite:///", "")

            if Path(db_path).exists():
                shutil.copy2(db_path, ruta_backup)
                logger.info(f"✅ Backup creado: {ruta_backup}")
            else:
                logger.warning(f"Base de datos no encontrada: {db_path}")

        except Exception as e:
            logger.error(f"❌ Error al crear backup: {e}")


# Instancia global de base de datos
_db_instance = None


def get_database(database_url: str = None) -> Database:
    """
    Obtiene la instancia global de la base de datos (Singleton)

    Args:
        database_url: URL de conexión (solo se usa la primera vez)

    Returns:
        Instancia de Database
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = Database(database_url)

    return _db_instance


def inicializar_base_datos(database_url: str = None, recrear: bool = False):
    """
    Inicializa la base de datos

    Args:
        database_url: URL de conexión
        recrear: Si True, elimina y recrea todas las tablas (¡CUIDADO!)
    """
    db = get_database(database_url)

    if recrear:
        logger.warning("⚠️  RECREANDO BASE DE DATOS - TODOS LOS DATOS SE PERDERÁN")
        db.drop_tablas()

    db.crear_tablas()

    if db.verificar_conexion():
        logger.info("✅ Base de datos inicializada correctamente")
        return db
    else:
        logger.error("❌ Error al inicializar base de datos")
        raise Exception("No se pudo inicializar la base de datos")


if __name__ == "__main__":
    # Prueba del módulo
    import sys

    print("\n🗄️  Inicializando base de datos de prueba...\n")

    # Base de datos en memoria para prueba
    db = inicializar_base_datos("sqlite:///:memory:")

    print("\n📊 Estadísticas:")
    stats = db.obtener_estadisticas()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Crear una transacción de prueba
    from .models import Transaccion, TipoTransaccion, OrigenArchivo
    from datetime import datetime

    with db.get_session() as session:
        transaccion = Transaccion(
            tipo=TipoTransaccion.EGRESO,
            categoria="factura_servicios",
            monto=15000.50,
            fecha_transaccion=datetime.now(),
            emisor_receptor="Edenor SA",
            descripcion="Factura de luz",
            origen=OrigenArchivo.PDF,
            procesado_por_ia=True
        )
        session.add(transaccion)

    print("\n✅ Transacción creada")

    # Ver estadísticas actualizadas
    print("\n📊 Estadísticas actualizadas:")
    stats = db.obtener_estadisticas()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    db.cerrar()
    print("\n✅ Prueba completada")
