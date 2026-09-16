"""
Script de ingesta: consulta AEMET para cada playa activa (con código AEMET
asignado) y guarda un nuevo snapshot en EstadoPlaya.

Uso manual:
    export AEMET_API_KEY="tu_api_key"
    cd backend
    python -m app.ingest_aemet

Pensado para lanzarse periódicamente (ej. con un cron cada 6-12 horas,
ya que AEMET solo actualiza esta predicción dos veces al día).
"""
import sys
import time

from .database import Base, SessionLocal, engine
from .integrations.aemet import AemetClient, AemetError
from . import models


def ingest_all(api_key: str | None = None) -> None:
    Base.metadata.create_all(bind=engine)
    client = AemetClient(api_key=api_key)
    db = SessionLocal()

    try:
        playas = (
            db.query(models.Playa)
            .filter(models.Playa.activa.is_(True))
            .filter(models.Playa.codigo_aemet.isnot(None))
            .all()
        )

        if not playas:
            print(
                "No hay playas activas con codigo_aemet asignado. "
                "Añade el código AEMET a alguna playa (ver data/playas_seed.json) "
                "antes de ejecutar la ingesta."
            )
            return

        for playa in playas:
            print(f"Consultando AEMET para: {playa.nombre} ({playa.codigo_aemet})...")
            try:
                prediccion = client.get_prediccion_playa_hoy(playa.codigo_aemet)
            except AemetError as exc:
                print(f"  ERROR al consultar {playa.nombre}: {exc}")
                continue

            estado = models.EstadoPlaya(
                playa_id=playa.id,
                temperatura_aire=prediccion.temperatura_aire,
                estado_cielo=prediccion.estado_cielo,
                viento_categoria=prediccion.viento_categoria,
                oleaje_categoria=prediccion.oleaje_categoria,
                sensacion_termica=prediccion.sensacion_termica,
                temperatura_agua=prediccion.temperatura_agua,
                uv_max=prediccion.uv_max,
                fuente_meteo="AEMET",
            )
            db.add(estado)
            db.commit()
            print(f"  OK: guardado nuevo estado (id={estado.id})")

            # Pequeña pausa de cortesía entre llamadas para no saturar la API.
            time.sleep(1)

    finally:
        db.close()


if __name__ == "__main__":
    try:
        ingest_all()
    except AemetError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        sys.exit(1)
