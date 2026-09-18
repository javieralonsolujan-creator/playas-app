"""
Cliente para Open-Meteo Marine API — oleaje numérico real (altura, periodo,
dirección), como alternativa a Puertos del Estado.

Por qué esta fuente y no Puertos del Estado: ver docs/fuentes-datos.md.
En resumen: Puertos del Estado no tiene una API pública pensada para esto
(su servicio de descarga prohíbe expresamente redistribuir datos a
terceros) y su API interna no está documentada. Open-Meteo Marine es
gratuita, sin api_key, con licencia CC BY 4.0 que permite explícitamente
este uso, y cubre cualquier coordenada de España sin depender de la
cercanía a una boya.

Documentación: https://open-meteo.com/en/docs/marine-weather-api
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

import requests

BASE_URL = "https://marine-api.open-meteo.com/v1/marine"

COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def grados_a_rumbo(grados: Optional[float]) -> Optional[str]:
    """Convierte 0-360° a un punto de la rosa de los vientos (N, NE, E...)."""
    if grados is None:
        return None
    indice = round(grados / 22.5) % 16
    return COMPASS[indice]


def obtener_oleaje(latitud: float, longitud: float, intentos: int = 2, timeout: int = 15) -> Optional[dict]:
    """
    Devuelve {'altura_ola': metros, 'periodo_ola': segundos,
    'direccion_ola': grados} para la hora actual en esa coordenada, o None
    si la petición falla (nunca lanza excepción — es una fuente adicional,
    no debe tumbar el resto de la generación de datos).
    """
    params = {
        "latitude": latitud,
        "longitude": longitud,
        "hourly": "wave_height,wave_period,wave_direction",
        "timezone": "UTC",
        "forecast_days": 1,
    }

    for intento in range(1, intentos + 1):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            break
        except requests.exceptions.RequestException as exc:
            if intento < intentos:
                time.sleep(2 * intento)
                continue
            print(f"  (Open-Meteo Marine falló: {exc})")
            return None
        except ValueError as exc:
            print(f"  (Open-Meteo Marine: respuesta no es JSON válido: {exc})")
            return None

    horas = (data.get("hourly") or {}).get("time", [])
    if not horas:
        return None

    alturas = data["hourly"].get("wave_height", [])
    periodos = data["hourly"].get("wave_period", [])
    direcciones = data["hourly"].get("wave_direction", [])

    # Busca la hora actual exacta; si no está (p.ej. desfases de segundos),
    # usa el primer dato disponible como aproximación razonable.
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
    idx = horas.index(ahora) if ahora in horas else 0

    def _valor(lista):
        try:
            v = lista[idx]
            return round(float(v), 2) if v is not None else None
        except (IndexError, TypeError, ValueError):
            return None

    altura = _valor(alturas)
    periodo = _valor(periodos)
    direccion_grados = _valor(direcciones)

    if altura is None and periodo is None and direccion_grados is None:
        return None

    return {
        "altura_ola": altura,
        "periodo_ola": periodo,
        "direccion_ola": grados_a_rumbo(direccion_grados),
        "direccion_ola_grados": direccion_grados,
    }
