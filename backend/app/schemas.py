from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlayaBase(BaseModel):
    nombre: str
    municipio: str
    provincia: str
    comunidad_autonoma: str
    latitud: float
    longitud: float
    zona_costera_aemet: Optional[str] = None
    codigo_aemet: Optional[str] = None
    longitud_m: Optional[float] = None
    activa: bool = True


class PlayaCreate(PlayaBase):
    pass


class Playa(PlayaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class EstadoPlayaBase(BaseModel):
    temperatura_aire: Optional[float] = None
    estado_cielo: Optional[str] = None
    viento_direccion: Optional[str] = None
    viento_velocidad: Optional[float] = None
    viento_categoria: Optional[str] = None
    sensacion_termica: Optional[str] = None
    uv_max: Optional[int] = None
    altura_ola: Optional[float] = None
    periodo_ola: Optional[float] = None
    direccion_ola: Optional[str] = None
    oleaje_categoria: Optional[str] = None
    temperatura_agua: Optional[float] = None
    bandera: Optional[str] = None
    bandera_motivo: Optional[str] = None
    bandera_fuente: Optional[str] = None
    fuente_meteo: Optional[str] = None
    fuente_oleaje: Optional[str] = None


class EstadoPlayaCreate(EstadoPlayaBase):
    playa_id: int


class EstadoPlaya(EstadoPlayaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    playa_id: int
    timestamp: datetime


class PlayaConEstado(Playa):
    """Playa junto con su último estado conocido (para el mapa)."""
    ultimo_estado: Optional[EstadoPlaya] = None
