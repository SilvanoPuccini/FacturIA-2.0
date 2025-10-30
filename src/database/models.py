"""Modelos de base de datos para FacturIA 2.0"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class TipoTransaccion(enum.Enum):
    INGRESO = "ingreso"
    EGRESO = "egreso"

class OrigenArchivo(enum.Enum):
    PDF = "pdf"
    IMAGEN = "imagen"
    CSV = "csv"

class Transaccion(Base):
    __tablename__ = "transacciones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    persona = Column(String(100), nullable=True, index=True, default="General")
    tipo = Column(Enum(TipoTransaccion), nullable=False, index=True)
    categoria = Column(String(50), nullable=False, index=True)
    monto = Column(Float, nullable=False)
    fecha_transaccion = Column(DateTime, nullable=True, index=True)
    emisor_receptor = Column(String(200), nullable=True)
    descripcion = Column(Text, nullable=True)
    numero_comprobante = Column(String(100), nullable=True)
    origen = Column(Enum(OrigenArchivo), nullable=False)
    archivo_origen = Column(String(300), nullable=True)
    ruta_archivo = Column(String(500), nullable=True)
    email_id = Column(String(100), nullable=True)
    email_subject = Column(String(300), nullable=True)
    email_from = Column(String(200), nullable=True)
    procesado_por_ia = Column(Boolean, default=False)
    confianza_clasificacion = Column(Float, nullable=True)
    requiere_revision = Column(Boolean, default=False)
    razon_revision = Column(Text, nullable=True)
    editado_manualmente = Column(Boolean, default=False)
    fecha_ultima_edicion = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, default=func.now(), nullable=False)
    fecha_modificacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Transaccion {self.id}: {self.tipo.value} - {self.categoria} - ${self.monto}>"
