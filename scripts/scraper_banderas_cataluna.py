"""
Scraping de banderas de playas de Barcelona (y, en el futuro, otros
municipios catalanes) vía Maritimum (https://www.maritimum.info), que
publica en abierto los datos de banderas de la **Àrea Metropolitana de
Barcelona (AMB)** — un organismo público, no una empresa. A diferencia
de Murcia, esta página SÍ se pudo leer directamente durante la
investigación (sin bloqueo anti-bots), con datos reales verificados.

Estructura de la página (confirmada en vivo): cada playa aparece como
    Platja <Nombre> <img alt="Bandera <color>" ...> <img alt="Afluència..."> ...
donde <color> es una palabra en catalán: verda / groga / vermella (a
veces puede no haber información, en cuyo caso no debe interpretarse
como ninguna de las anteriores).

URL por municipio: https://www.maritimum.info/<Municipio> (ej. Barcelona,
ElPratDeLlobregat) — solo tenemos integrado Barcelona por ahora, ya que
es la única playa catalana en nuestro catálogo piloto.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

import requests

URL_POR_MUNICIPIO = {
    "Barcelona": "https://www.maritimum.info/Barcelona",
}

HEADERS_NAVEGADOR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ca-ES,ca;q=0.9,es;q=0.8",
}

COLOR_CATALAN_A_ESTANDAR = {
    "verda": "verde",
    "groga": "amarilla",
    "vermella": "roja",
}

PATRON_PLAYA = re.compile(
    r"Platja\s+([^!\n]+?)\s*(?:!\[|<img[^>]*alt=[\"'])Bandera\s+(\w+)",
    re.IGNORECASE,
)


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def obtener_banderas_municipio(municipio: str, playas_municipio: list[dict]) -> Optional[dict]:
    """
    playas_municipio: lista de dicts con al menos 'nombre' y 'codigo_aemet'.
    Devuelve {codigo_aemet: color} o None si falla o no hay confianza.
    """
    url = URL_POR_MUNICIPIO.get(municipio)
    if not url:
        return None  # municipio catalán todavía no soportado

    try:
        resp = requests.get(url, headers=HEADERS_NAVEGADOR, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"  (scraping automático de {municipio} falló: {exc})")
        return None

    coincidencias = PATRON_PLAYA.findall(resp.text)
    if not coincidencias:
        print(f"  (scraping automático de {municipio}: no se reconoció el formato esperado)")
        return None

    banderas_por_nombre = {}
    for nombre_bruto, color_catalan in coincidencias:
        color = COLOR_CATALAN_A_ESTANDAR.get(color_catalan.lower())
        if color:
            banderas_por_nombre[_normalizar(nombre_bruto)] = color

    resultado = {}
    for playa in playas_municipio:
        codigo = playa.get("codigo_aemet")
        if not codigo:
            continue
        nombre_norm = _normalizar(playa["nombre"])
        # Búsqueda flexible: coincidencia exacta o por inclusión en cualquier sentido
        color = banderas_por_nombre.get(nombre_norm)
        if color is None:
            for nombre_scrapeado, c in banderas_por_nombre.items():
                if nombre_norm in nombre_scrapeado or nombre_scrapeado in nombre_norm:
                    color = c
                    break
        if color:
            resultado[codigo] = color

    if not resultado:
        return None

    print(f"  Scraping automático de {municipio} OK ({len(resultado)} playas interpretadas).")
    return resultado


def obtener_banderas_cataluna_automatico(playas_cataluna: list[dict]) -> Optional[dict]:
    """
    Agrupa las playas catalanas de nuestro catálogo por municipio y
    consulta Maritimum para cada uno de los municipios soportados.
    """
    por_municipio: dict[str, list[dict]] = {}
    for playa in playas_cataluna:
        por_municipio.setdefault(playa["municipio"], []).append(playa)

    resultado: dict = {}
    for municipio, playas_municipio in por_municipio.items():
        banderas = obtener_banderas_municipio(municipio, playas_municipio)
        if banderas:
            resultado.update(banderas)

    return resultado or None
