"""
Genera site/playas.json a partir de data/playas_seed.json + AEMET.

Este script NO necesita servidor ni base de datos: simplemente escribe un
fichero JSON estático que luego sirve GitHub Pages (o cualquier hosting
estático). Pensado para ejecutarse:
  - En local, para probar: python scripts/generar_datos.py
  - Automáticamente 2 veces al día vía GitHub Actions
    (ver .github/workflows/actualizar-datos.yml)

Requiere la variable de entorno AEMET_API_KEY.
Dependencias: solo 'requests' (ver requirements.txt de esta carpeta).
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from aemet import AemetClient, AemetError  # noqa: E402

RAIZ = os.path.join(os.path.dirname(__file__), "..")
SEED_PATH = os.path.join(RAIZ, "data", "playas_seed.json")
SALIDA_PATH = os.path.join(RAIZ, "site", "playas.json")


def main() -> None:
    with open(SEED_PATH, encoding="utf-8") as f:
        playas_config = json.load(f)

    client = AemetClient()  # lee AEMET_API_KEY del entorno
    resultado = []
    errores = 0

    for i, playa in enumerate(playas_config):
        entrada = {
            "id": i + 1,
            "nombre": playa["nombre"],
            "municipio": playa["municipio"],
            "comunidad_autonoma": playa["comunidad_autonoma"],
            "provincia": playa["provincia"],
            "latitud": playa["latitud"],
            "longitud": playa["longitud"],
            "ultimo_estado": None,
        }

        codigo = playa.get("codigo_aemet")
        if not codigo:
            print(f"  (sin codigo_aemet, se omite AEMET) {playa['nombre']}")
            resultado.append(entrada)
            continue

        print(f"Consultando AEMET para: {playa['nombre']} ({codigo})...")
        try:
            prediccion = client.get_prediccion_playa_hoy(codigo)
            entrada["ultimo_estado"] = {
                "estado_cielo": prediccion.estado_cielo,
                "viento_categoria": prediccion.viento_categoria,
                "oleaje_categoria": prediccion.oleaje_categoria,
                "temperatura_aire": prediccion.temperatura_aire,
                "temperatura_agua": prediccion.temperatura_agua,
                "uv_max": prediccion.uv_max,
                "bandera": None,  # pendiente: sin fuente automática todavía
                "fuente_meteo": "AEMET",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            print("  OK")
        except AemetError as exc:
            print(f"  ERROR: {exc}")
            errores += 1

        resultado.append(entrada)
        time.sleep(1)  # cortesía entre llamadas

    os.makedirs(os.path.dirname(SALIDA_PATH), exist_ok=True)
    with open(SALIDA_PATH, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\nEscrito {SALIDA_PATH} ({len(resultado)} playas, {errores} errores).")
    if errores == len(playas_config) and errores > 0:
        sys.exit(1)  # falla el job si NINGUNA playa se pudo consultar


if __name__ == "__main__":
    try:
        main()
    except AemetError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        sys.exit(1)
