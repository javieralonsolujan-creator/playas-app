"""
Cliente para la API de AEMET OpenData.

Documentación: https://opendata.aemet.es/
Necesitas una API key gratuita (registro con email en
https://opendata.aemet.es/centrodedescargas/altaUsuario) y pasarla
mediante la variable de entorno AEMET_API_KEY.

Detalles importantes de esta API (comprobados contra su documentación real):

1. Todas las llamadas son de "doble petición":
   - 1ª petición: a /api/... con tu api_key. Devuelve un JSON pequeño con
     dos URLs: "datos" (donde está la información real) y "metadatos"
     (descripción de los campos).
   - 2ª petición: a la URL de "datos" (esta ya NO necesita api_key) para
     obtener el JSON real.

2. La respuesta de la 2ª petición viene codificada en ISO-8859-15, no en
   UTF-8. Si no se decodifica explícitamente así, los acentos y la "ñ"
   salen corruptos.

3. El endpoint específico de playas (
   GET /api/prediccion/especifica/playa/{codigo}) da, para cada uno de los
   3 días de validez (hoy, mañana, pasado mañana) y separado en mañana/tarde:
   - estado del cielo (categoría + descripción)
   - viento (categoría: flojo/moderado/fuerte + descripción)
   - oleaje (categoría: débil/moderado/fuerte + descripción)
   - temperatura máxima del aire
   - sensación térmica (categoría + descripción)
   - temperatura del agua
   - índice UV máximo

   OJO: viento y oleaje aquí son CATEGORÍAS cualitativas, no metros ni
   km/h exactos. Los valores numéricos de oleaje real los aportará más
   adelante Puertos del Estado (ver docs/fuentes-datos.md).

El listado oficial de códigos de playa (necesario para saber qué código
pasarle a este endpoint) está en:
https://www.aemet.es/documentos/es/eltiempo/prediccion/playas/Playas_codigos.csv
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import requests

AEMET_BASE_URL = "https://opendata.aemet.es/opendata/api"


class AemetError(Exception):
    """Error al consultar la API de AEMET."""


@dataclass
class PrediccionPlaya:
    """Resultado ya interpretado para un día concreto de la predicción de playa."""

    fecha: Optional[str]
    estado_cielo: Optional[str]
    viento_categoria: Optional[str]
    oleaje_categoria: Optional[str]
    temperatura_aire: Optional[float]
    sensacion_termica: Optional[str]
    temperatura_agua: Optional[float]
    uv_max: Optional[int]
    fuente: str = "AEMET"


class AemetClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 15):
        self.api_key = api_key or os.environ.get("AEMET_API_KEY")
        if not self.api_key:
            raise AemetError(
                "Falta la API key de AEMET. Defínela en la variable de entorno "
                "AEMET_API_KEY (consíguela gratis en "
                "https://opendata.aemet.es/centrodedescargas/altaUsuario)."
            )
        self.timeout = timeout

    def _get_json(self, url: str, with_api_key: bool) -> Any:
        params = {"api_key": self.api_key} if with_api_key else None
        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        # AEMET a veces devuelve JSON con content-type raro; forzamos la
        # codificación real (ISO-8859-15) en vez de dejar que requests adivine.
        resp.encoding = "ISO-8859-15"
        return resp.json()

    def _call_endpoint(self, path: str) -> Any:
        """Realiza la doble llamada estándar de AEMET OpenData y devuelve el JSON de datos."""
        first = self._get_json(f"{AEMET_BASE_URL}{path}", with_api_key=True)

        if not isinstance(first, dict) or "datos" not in first:
            raise AemetError(f"Respuesta inesperada de AEMET para {path}: {first}")

        if first.get("estado") != 200:
            raise AemetError(
                f"AEMET devolvió estado {first.get('estado')} para {path}: "
                f"{first.get('descripcion')}"
            )

        return self._get_json(first["datos"], with_api_key=False)

    def get_prediccion_playa_raw(self, codigo_playa: str) -> Any:
        """Devuelve el JSON crudo (ya parseado) de la predicción de una playa."""
        return self._call_endpoint(f"/prediccion/especifica/playa/{codigo_playa}")

    def get_prediccion_playa_hoy(self, codigo_playa: str) -> PrediccionPlaya:
        """
        Devuelve la predicción de HOY para una playa, ya simplificada a los
        campos que usamos en nuestro modelo de datos (ver docs/modelo-datos.md).
        """
        raw = self.get_prediccion_playa_raw(codigo_playa)
        dias = _extraer_dias(raw)
        if not dias:
            raise AemetError(f"No se encontraron días de predicción para playa {codigo_playa}")

        return _parsear_dia(dias[0])


def _unwrap(valor: Any) -> Any:
    """
    AEMET a veces envuelve un único objeto en una lista de 1 elemento
    (según su propia documentación de metadatos). Esta función normaliza
    eso: si es una lista no vacía, devuelve el primer elemento; si no,
    devuelve el valor tal cual.
    """
    if isinstance(valor, list):
        return valor[0] if valor else None
    return valor


def _extraer_dias(raw: Any) -> list:
    """Navega la respuesta cruda hasta llegar a la lista de días (hoy, D+1, D+2)."""
    playa = _unwrap(raw)
    if not isinstance(playa, dict):
        raise AemetError(f"Formato de respuesta de playa inesperado: {raw!r}")

    prediccion = _unwrap(playa.get("prediccion"))
    if not isinstance(prediccion, dict):
        raise AemetError(f"Campo 'prediccion' con formato inesperado: {playa!r}")

    dias = prediccion.get("dia")
    if not isinstance(dias, list):
        raise AemetError(f"Campo 'prediccion.dia' con formato inesperado: {prediccion!r}")

    return dias


def _texto_manana_tarde(categoria: Optional[dict]) -> Optional[str]:
    """
    Combina las descripciones de mañana y tarde de un campo tipo
    estadoCielo/viento/oleaje en un único texto legible.
    """
    if not isinstance(categoria, dict):
        return None
    manana = categoria.get("descripcion1")
    tarde = categoria.get("descripcion2")
    if manana and tarde:
        if manana == tarde:
            return manana
        return f"Mañana: {manana}. Tarde: {tarde}."
    return manana or tarde


def _valor_numerico(campo: Optional[dict], clave: str = "valor1") -> Optional[float]:
    if not isinstance(campo, dict):
        return None
    valor = campo.get(clave)
    try:
        return float(valor) if valor is not None else None
    except (TypeError, ValueError):
        return None


def _parsear_dia(dia: dict) -> PrediccionPlaya:
    t_aire = _valor_numerico(dia.get("tMaxima"))
    uv = _valor_numerico(dia.get("uvMax"))
    return PrediccionPlaya(
        fecha=dia.get("fecha"),
        estado_cielo=_texto_manana_tarde(dia.get("estadoCielo")),
        viento_categoria=_texto_manana_tarde(dia.get("viento")),
        oleaje_categoria=_texto_manana_tarde(dia.get("oleaje")),
        temperatura_aire=t_aire,
        sensacion_termica=(dia.get("sTermica") or {}).get("descripcion1")
        if isinstance(dia.get("sTermica"), dict)
        else None,
        temperatura_agua=_valor_numerico(dia.get("tAgua")),
        uv_max=int(uv) if uv is not None else None,
    )
