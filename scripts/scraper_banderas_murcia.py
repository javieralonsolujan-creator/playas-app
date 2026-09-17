"""
Intento de scraping AUTOMÁTICO de las banderas de la Región de Murcia
(Plan Copla, 112 Región de Murcia).

⚠️ EXPERIMENTAL: la página oficial (noticias.112rmurcia.es/playas/) bloqueó
las peticiones de la herramienta de desarrollo usada para investigar esta
integración (probablemente una regla anti-rastreadores-de-IA de Cloudflare,
no necesariamente un bloqueo a scripts normales). No se ha podido verificar
en directo si este scraper funciona desde un runner de GitHub Actions.

Por eso este módulo está diseñado para FALLAR EN SILENCIO ante cualquier
problema (bloqueo, cambio de estructura de la página, timeout...) y
devolver None — en ese caso, generar_datos.py cae automáticamente al
fichero manual (data/banderas_manual.json). Nunca se arriesga a inventar
o malinterpretar una bandera de seguridad.

Formato esperado (visto en fuentes que replican el mismo texto oficial):
    "...abren hoy [día] con bandera verde, excepto en estos municipios que
    ondean bandera amarilla: Municipio: playa1, playa2. Municipio2: ..."
    (y opcionalmente un bloque equivalente para "bandera roja").
Todo lo no mencionado se asume verde.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

import requests

URL_PLAYAS_MURCIA = "https://noticias.112rmurcia.es/playas/"

HEADERS_NAVEGADOR = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}


def _normalizar(texto: str) -> str:
    """minúsculas, sin acentos, sin puntuación sobrante — para comparar nombres."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


ARTICULOS_INICIALES = ("de ", "del ", "el ", "la ", "los ", "las ")


def _nombre_clave(nombre: str) -> str:
    """
    Quita artículos iniciales para poder casar 'De Calblanque' (nombre
    oficial de AEMET) con 'Calblanque' (como suele aparecer en prensa).
    """
    norm = _normalizar(nombre)
    for articulo in ARTICULOS_INICIALES:
        if norm.startswith(articulo):
            return norm[len(articulo):]
    return norm


def _extraer_segmento(texto_plano: str, color: str) -> str:
    """
    Devuelve el trozo de texto entre la mención de 'bandera {color}' y la
    siguiente mención de otro color (o el final del texto).
    """
    colores = ["verde", "amarilla", "roja"]
    patron_inicio = re.search(rf"bandera\s+{color}", texto_plano, re.IGNORECASE)
    if not patron_inicio:
        return ""

    inicio = patron_inicio.end()
    fin = len(texto_plano)
    for otro in colores:
        if otro == color:
            continue
        m = re.search(rf"bandera\s+{otro}", texto_plano[inicio:], re.IGNORECASE)
        if m:
            fin = min(fin, inicio + m.start())

    return texto_plano[inicio:fin]


def obtener_banderas_murcia_automatico(playas_murcia: list[dict]) -> Optional[dict]:
    """
    playas_murcia: lista de dicts con al menos 'nombre' y 'codigo_aemet',
    tal como están en data/playas_seed.json.

    Devuelve {codigo_aemet: 'verde'|'amarilla'|'roja'} si consigue leer e
    interpretar la página con confianza razonable, o None si algo falla o
    resulta ambiguo (en cuyo caso NO se debe usar este resultado).
    """
    try:
        resp = requests.get(URL_PLAYAS_MURCIA, headers=HEADERS_NAVEGADOR, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"  (scraping automático de Murcia falló: {exc})")
        return None

    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(resp.text, "html.parser")
        texto_plano = soup.get_text(separator=" ")
    except Exception as exc:
        print(f"  (no se pudo parsear el HTML de Murcia: {exc})")
        return None

    # Comprobación de confianza mínima: si ni siquiera aparece "bandera
    # verde", probablemente la página cambió de estructura o nos devolvió
    # un error/CAPTCHA disfrazado de 200 OK. Mejor no arriesgarse.
    if not re.search(r"bandera\s+verde", texto_plano, re.IGNORECASE):
        print("  (scraping automático de Murcia: no se reconoció el formato esperado)")
        return None

    segmento_amarilla = _normalizar(_extraer_segmento(texto_plano, "amarilla"))
    segmento_roja = _normalizar(_extraer_segmento(texto_plano, "roja"))

    resultado = {}
    for playa in playas_murcia:
        codigo = playa.get("codigo_aemet")
        if not codigo:
            continue
        nombre_norm = _nombre_clave(playa["nombre"])
        # Nombres cortos (<4 letras tras normalizar, ej. "isla") dan falsos
        # positivos con facilidad; exigimos un mínimo de longitud.
        if len(nombre_norm) < 4:
            continue

        if nombre_norm in segmento_roja:
            resultado[codigo] = "roja"
        elif nombre_norm in segmento_amarilla:
            resultado[codigo] = "amarilla"
        else:
            resultado[codigo] = "verde"

    if not resultado:
        return None

    print(f"  Scraping automático de Murcia OK ({len(resultado)} playas interpretadas).")
    return resultado
