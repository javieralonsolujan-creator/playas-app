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
from scraper_banderas_murcia import obtener_banderas_murcia_automatico  # noqa: E402
from open_meteo import obtener_oleaje  # noqa: E402

RAIZ = os.path.join(os.path.dirname(__file__), "..")
SEED_PATH = os.path.join(RAIZ, "data", "playas_seed.json")
BANDERAS_PATH = os.path.join(RAIZ, "data", "banderas_manual.json")
SALIDA_PATH = os.path.join(RAIZ, "site", "playas.json")


def cargar_banderas_del_dia() -> dict:
    """
    Lee data/banderas_manual.json y devuelve {codigo_aemet: color} SOLO si
    el fichero fue actualizado hoy (fecha de Madrid). Si está desactualizado
    (nadie lo tocó hoy), se ignora por completo para no mostrar una bandera
    de un día anterior como si fuera la de hoy.
    """
    if not os.path.exists(BANDERAS_PATH):
        return {}

    with open(BANDERAS_PATH, encoding="utf-8") as f:
        datos = json.load(f)

    hoy = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    # Aproximación simple a "hoy en España" (evita depender de zoneinfo/tz data)
    hoy_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if datos.get("actualizado") not in (hoy, hoy_utc):
        print(
            f"  (banderas_manual.json desactualizado: pone '{datos.get('actualizado')}', "
            f"hoy es {hoy_utc}. Se ignoran las banderas hasta que se actualice.)"
        )
        return {}

    print(f"  Usando banderas manuales actualizadas a fecha {datos.get('actualizado')}.")
    return datos.get("banderas", {})


def obtener_banderas(playas_config: list) -> tuple[dict, str]:
    """
    Intenta primero el scraping automático de Murcia; si falla o no
    devuelve nada de confianza, cae al fichero manual (solo si está
    actualizado a hoy). Devuelve ({codigo_aemet: color}, etiqueta_fuente).
    """
    playas_murcia = [
        p for p in playas_config if p.get("comunidad_autonoma") == "Región de Murcia"
    ]

    if playas_murcia:
        print("Probando scraping automático de banderas (Murcia)...")
        try:
            automatico = obtener_banderas_murcia_automatico(playas_murcia)
        except Exception as exc:  # nunca debe tumbar el job
            print(f"  (scraping automático falló con excepción inesperada: {exc})")
            automatico = None

        if automatico:
            return automatico, "Automático (scraping Plan Copla)"
        print("  Scraping automático no disponible, se usará el fichero manual si está al día.")

    return cargar_banderas_del_dia(), "Manual (Plan Copla)"


def estimar_bandera(prediccion) -> tuple:
    """
    Estimación NO OFICIAL del riesgo de baño a partir de las categorías de
    AEMET (oleaje, viento, estado del cielo). No sustituye a la bandera
    real: no puede saber si hay medusas, corrientes locales, mala calidad
    del agua, etc. — cosas que solo un socorrista in situ puede valorar.

    Devuelve (color_estimado, motivo) o (None, None) si no hay datos
    suficientes para estimar nada.
    """
    texto_oleaje = (prediccion.oleaje_categoria or "").lower()
    texto_viento = (prediccion.viento_categoria or "").lower()
    texto_cielo = (prediccion.estado_cielo or "").lower()

    if not texto_oleaje and not texto_viento:
        return None, None

    if "tormenta" in texto_cielo:
        return "roja", "Tormenta prevista"
    if "fuerte" in texto_oleaje:
        return "roja", "Oleaje fuerte previsto"
    if "moderado" in texto_oleaje or "fuerte" in texto_viento:
        return "amarilla", "Oleaje o viento moderado/fuerte previsto"
    return "verde", "Oleaje y viento en calma previstos"


def main() -> None:
    with open(SEED_PATH, encoding="utf-8") as f:
        playas_config = json.load(f)

    banderas_hoy, fuente_bandera_label = obtener_banderas(playas_config)

    client = AemetClient()  # lee AEMET_API_KEY del entorno
    resultado = []
    errores_aemet = 0

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
        bandera_hoy = banderas_hoy.get(codigo) if codigo else None
        estado: dict = {}

        # --- Fuente 1: AEMET (tiempo + categorías de viento/oleaje) ---
        if codigo:
            print(f"Consultando AEMET para: {playa['nombre']} ({codigo})...")
            try:
                prediccion = client.get_prediccion_playa_hoy(codigo)
                bandera_estimada, motivo_estimada = estimar_bandera(prediccion)
                estado.update({
                    "estado_cielo": prediccion.estado_cielo,
                    "viento_categoria": prediccion.viento_categoria,
                    "oleaje_categoria": prediccion.oleaje_categoria,
                    "temperatura_aire": prediccion.temperatura_aire,
                    "temperatura_agua": prediccion.temperatura_agua,
                    "uv_max": prediccion.uv_max,
                    "bandera_estimada": bandera_estimada,
                    "bandera_estimada_motivo": motivo_estimada,
                    "fuente_meteo": "AEMET",
                })
                print("  OK (AEMET)")
            except AemetError as exc:
                print(f"  ERROR AEMET: {exc}")
                errores_aemet += 1
            except Exception as exc:  # red de seguridad: nunca tumbar el job entero
                print(f"  ERROR inesperado AEMET: {exc}")
                errores_aemet += 1
        else:
            print(f"  (sin codigo_aemet, se omite AEMET) {playa['nombre']}")

        # --- Fuente 2: Open-Meteo Marine (oleaje numérico real) ---
        oleaje = obtener_oleaje(playa["latitud"], playa["longitud"])
        if oleaje:
            estado.update({
                "altura_ola": oleaje["altura_ola"],
                "periodo_ola": oleaje["periodo_ola"],
                "direccion_ola": oleaje["direccion_ola"],
                "fuente_oleaje": "Open-Meteo Marine",
            })

        # --- Fuente 3: bandera oficial (scraping Murcia o manual) ---
        if bandera_hoy:
            estado["bandera"] = bandera_hoy
            estado["fuente_bandera"] = fuente_bandera_label
        else:
            estado.setdefault("bandera", None)

        if estado:
            estado.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            entrada["ultimo_estado"] = estado

        resultado.append(entrada)
        time.sleep(2)  # cortesía entre llamadas (AEMET aplica límite de peticiones)

    os.makedirs(os.path.dirname(SALIDA_PATH), exist_ok=True)
    with open(SALIDA_PATH, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\nEscrito {SALIDA_PATH} ({len(resultado)} playas, {errores_aemet} errores de AEMET).")
    if errores_aemet == len(playas_config) and errores_aemet > 0:
        sys.exit(1)  # falla el job si NINGUNA playa se pudo consultar en AEMET


if __name__ == "__main__":
    try:
        main()
    except AemetError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        sys.exit(1)
