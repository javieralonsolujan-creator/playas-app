"""
Modelos SQLAlchemy. Ver docs/modelo-datos.md para la descripción completa
de cada campo.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .database import Base


class Playa(Base):
    __tablename__ = "playas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    municipio = Column(String, nullable=False)
    provincia = Column(String, nullable=False)
    comunidad_autonoma = Column(String, nullable=False)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    zona_costera_aemet = Column(String, nullable=True)
    codigo_aemet = Column(String, nullable=True, index=True)  # código de playa AEMET (Playas_codigos.csv)
    longitud_m = Column(Float, nullable=True)
    activa = Column(Boolean, default=True)

    estados = relationship(
        "EstadoPlaya", back_populates="playa", order_by="EstadoPlaya.timestamp.desc()"
    )


class EstadoPlaya(Base):
    __tablename__ = "estados_playa"

    id = Column(Integer, primary_key=True, index=True)
    playa_id = Column(Integer, ForeignKey("playas.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Meteo
    temperatura_aire = Column(Float, nullable=True)
    estado_cielo = Column(String, nullable=True)
    viento_direccion = Column(String, nullable=True)
    viento_velocidad = Column(Float, nullable=True)
    viento_categoria = Column(String, nullable=True)  # flojo/moderado/fuerte (AEMET, mañana y tarde)
    sensacion_termica = Column(String, nullable=True)
    uv_max = Column(Integer, nullable=True)

    # Oleaje / mar
    altura_ola = Column(Float, nullable=True)  # metros exactos (Puertos del Estado)
    periodo_ola = Column(Float, nullable=True)
    direccion_ola = Column(String, nullable=True)
    oleaje_categoria = Column(String, nullable=True)  # débil/moderado/fuerte (AEMET, mañana y tarde)
    temperatura_agua = Column(Float, nullable=True)

    # Bandera
    bandera = Column(String, nullable=True)  # verde / amarilla / roja
    bandera_motivo = Column(String, nullable=True)
    bandera_fuente = Column(String, nullable=True)

    # Trazabilidad de fuentes
    fuente_meteo = Column(String, nullable=True)
    fuente_oleaje = Column(String, nullable=True)

    playa = relationship("Playa", back_populates="estados")
