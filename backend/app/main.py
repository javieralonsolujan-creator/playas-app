"""
API de Playas App.

Arrancar en local con:
    uvicorn app.main:app --reload

Documentación interactiva disponible en /docs una vez arrancado.
"""
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

# Crea las tablas si no existen (para desarrollo; en producción usar migraciones, ej. Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Playas App API",
    description="API para consultar el estado en tiempo real de las playas de España",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"status": "ok", "servicio": "playas-app-api"}


# ---------- Playas ----------

@app.get("/playas", response_model=List[schemas.Playa])
def listar_playas(
    comunidad_autonoma: Optional[str] = None,
    provincia: Optional[str] = None,
    activa: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Playa)
    if comunidad_autonoma:
        query = query.filter(models.Playa.comunidad_autonoma == comunidad_autonoma)
    if provincia:
        query = query.filter(models.Playa.provincia == provincia)
    if activa is not None:
        query = query.filter(models.Playa.activa == activa)
    return query.all()


@app.post("/playas", response_model=schemas.Playa)
def crear_playa(playa: schemas.PlayaCreate, db: Session = Depends(get_db)):
    db_playa = models.Playa(**playa.model_dump())
    db.add(db_playa)
    db.commit()
    db.refresh(db_playa)
    return db_playa


@app.get("/playas/{playa_id}", response_model=schemas.PlayaConEstado)
def obtener_playa(playa_id: int, db: Session = Depends(get_db)):
    playa = db.query(models.Playa).filter(models.Playa.id == playa_id).first()
    if not playa:
        raise HTTPException(status_code=404, detail="Playa no encontrada")

    ultimo_estado = (
        db.query(models.EstadoPlaya)
        .filter(models.EstadoPlaya.playa_id == playa_id)
        .order_by(models.EstadoPlaya.timestamp.desc())
        .first()
    )

    resultado = schemas.PlayaConEstado.model_validate(playa)
    if ultimo_estado:
        resultado.ultimo_estado = schemas.EstadoPlaya.model_validate(ultimo_estado)
    return resultado


# ---------- Estados de playa ----------

@app.post("/estados", response_model=schemas.EstadoPlaya)
def crear_estado(estado: schemas.EstadoPlayaCreate, db: Session = Depends(get_db)):
    playa = db.query(models.Playa).filter(models.Playa.id == estado.playa_id).first()
    if not playa:
        raise HTTPException(status_code=404, detail="Playa no encontrada")

    db_estado = models.EstadoPlaya(**estado.model_dump())
    db.add(db_estado)
    db.commit()
    db.refresh(db_estado)
    return db_estado


@app.get("/playas/{playa_id}/historico", response_model=List[schemas.EstadoPlaya])
def historico_playa(playa_id: int, limite: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(models.EstadoPlaya)
        .filter(models.EstadoPlaya.playa_id == playa_id)
        .order_by(models.EstadoPlaya.timestamp.desc())
        .limit(limite)
        .all()
    )
