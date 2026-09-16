"""
Carga data/playas_seed.json en la base de datos. Idempotente: si una playa
con el mismo nombre+municipio ya existe, la actualiza en vez de duplicarla.

Uso:
    cd backend
    python -m app.seed
"""
import json
import os

from .database import Base, SessionLocal, engine
from . import models

SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "playas_seed.json")


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        with open(SEED_PATH, encoding="utf-8") as f:
            playas = json.load(f)

        for datos in playas:
            existente = (
                db.query(models.Playa)
                .filter(
                    models.Playa.nombre == datos["nombre"],
                    models.Playa.municipio == datos["municipio"],
                )
                .first()
            )
            if existente:
                for campo, valor in datos.items():
                    setattr(existente, campo, valor)
                print(f"Actualizada: {datos['nombre']} ({datos['municipio']})")
            else:
                db.add(models.Playa(**datos))
                print(f"Creada: {datos['nombre']} ({datos['municipio']})")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()
