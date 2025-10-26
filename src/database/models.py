"""
Modelos de base de datos para FacturIA 2.0
Define la estructura de todas las tablas
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class TipoTransaccion(enum.Enum):
    """Enum para tipos de transacción"""
    INGRESO = "ingreso"
    EGRESO = "egreso"


class OrigenArchivo(enum.Enum):
    """Enum para origen de los datos"""
    PDF = "pdf"
    IMAGEN = "imagen"
    CSV = "csv"


class Transaccion(Base):
    """
    Tabla principal de transacciones financieras
    Almacena ingresos y egresos procesados
    """
    __tablename__ = "transacciones"

    # Identificador único
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Clasificación
    tipo = Column(Enum(TipoTransaccion), nullable=False, index=True)
    categoria = Column(String(50), nullable=False, index=True)

    # Datos financieros
    monto = Column(Float, nullable=False)
    fecha_transaccion = Column(DateTime, nullable=True, index=True)

    # Información adicional
    emisor_receptor = Column(String(200), nullable=True)
    descripcion = Column(Text, nullable=True)
    numero_comprobante = Column(String(100), nullable=True)

    # Metadata del archivo
    origen = Column(Enum(OrigenArchivo), nullable=False)
    archivo_origen = Column(String(300), nullable=True)
    ruta_archivo = Column(String(500), nullable=True)

    # Información del email (si aplica)
    email_id = Column(String(100), nullable=True)
    email_subject = Column(String(300), nullable=True)
    email_from = Column(String(200), nullable=True)

    # Control
    procesado_por_ia = Column(Boolean, default=False)
    confianza_clasificacion = Column(Float, nullable=True)  # 0-1 (si viene de IA)
    requiere_revision = Column(Boolean, default=False)

    # Timestamps
    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)
    fecha_modificacion = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Transaccion {self.id}: {self.tipo.value} - {self.categoria} - ${self.monto}>"

    def to_dict(self):
        """Convierte el modelo a diccionario"""
        return {
            "id": self.id,
            "tipo": self.tipo.value if self.tipo else None,
            "categoria": self.categoria,
            "monto": self.monto,
            "fecha_transaccion": self.fecha_transaccion.isoformat() if self.fecha_transaccion else None,
            "emisor_receptor": self.emisor_receptor,
            "descripcion": self.descripcion,
            "numero_comprobante": self.numero_comprobante,
            "origen": self.origen.value if self.origen else None,
            "archivo_origen": self.archivo_origen,
            "procesado_por_ia": self.procesado_por_ia,
            "requiere_revision": self.requiere_revision,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }


class ArchivoProcesado(Base):
    """
    Registro de archivos procesados
    Para detectar duplicados y trackear procesamiento
    """
    __tablename__ = "archivos_procesados"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identificación del archivo
    nombre_archivo = Column(String(300), nullable=False)
    hash_archivo = Column(String(64), nullable=False, unique=True, index=True)
    tipo_archivo = Column(Enum(OrigenArchivo), nullable=False)

    # Información del procesamiento
    fecha_procesamiento = Column(DateTime, default=func.now(), nullable=False)
    transacciones_extraidas = Column(Integer, default=0)
    exito = Column(Boolean, default=True)
    error_mensaje = Column(Text, nullable=True)

    # Información del email (si aplica)
    email_id = Column(String(100), nullable=True)
    email_subject = Column(String(300), nullable=True)

    def __repr__(self):
        return f"<ArchivoProcesado {self.id}: {self.nombre_archivo}>"


class LogProcesamiento(Base):
    """
    Log de eventos del sistema
    Para auditoría y debugging
    """
    __tablename__ = "logs_procesamiento"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Tipo de evento
    nivel = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR
    modulo = Column(String(50), nullable=False)  # email_monitor, ai_processor, etc.
    evento = Column(String(100), nullable=False)

    # Detalles
    mensaje = Column(Text, nullable=True)
    datos_adicionales = Column(Text, nullable=True)  # JSON string

    # Timestamp
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<Log {self.id}: {self.nivel} - {self.modulo} - {self.evento}>"


class Configuracion(Base):
    """
    Configuraciones del sistema
    Almacena settings que pueden cambiar en runtime
    """
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Clave-valor
    clave = Column(String(100), nullable=False, unique=True, index=True)
    valor = Column(Text, nullable=False)
    tipo_dato = Column(String(20), nullable=False)  # string, int, float, bool, json

    # Metadata
    descripcion = Column(Text, nullable=True)
    fecha_modificacion = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Configuracion {self.clave}: {self.valor}>"


class EstadisticasDiarias(Base):
    """
    Estadísticas agregadas por día
    Para optimizar consultas del dashboard
    """
    __tablename__ = "estadisticas_diarias"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Fecha
    fecha = Column(DateTime, nullable=False, unique=True, index=True)

    # Totales
    total_ingresos = Column(Float, default=0)
    total_egresos = Column(Float, default=0)
    balance = Column(Float, default=0)

    # Cantidades
    cantidad_ingresos = Column(Integer, default=0)
    cantidad_egresos = Column(Integer, default=0)

    # Categoría más frecuente
    categoria_top_ingreso = Column(String(50), nullable=True)
    categoria_top_egreso = Column(String(50), nullable=True)

    # Metadata
    fecha_calculo = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<EstadisticasDiarias {self.fecha.date()}: Balance ${self.balance}>"


if __name__ == "__main__":
    # Prueba de los modelos
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Crear base de datos en memoria para prueba
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Crear una transacción de prueba
    transaccion = Transaccion(
        tipo=TipoTransaccion.EGRESO,
        categoria="factura_servicios",
        monto=15000.50,
        fecha_transaccion=datetime.now(),
        emisor_receptor="Edenor SA",
        descripcion="Factura de luz octubre 2024",
        numero_comprobante="001-00012345",
        origen=OrigenArchivo.PDF,
        archivo_origen="factura_edenor_oct.pdf",
        procesado_por_ia=True
    )

    session.add(transaccion)
    session.commit()

    print("\n✅ Transacción creada:")
    print(transaccion)
    print(transaccion.to_dict())

    session.close()
