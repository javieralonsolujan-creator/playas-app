"""
Test del PARSER de AEMET (no de la llamada de red).

Simula el JSON que AEMET devuelve en la 2ª petición (la de "datos"), con
la forma real documentada en su esquema de metadatos oficial, para
verificar que _extraer_dias/_parsear_dia lo interpretan correctamente
sin necesidad de una API key real ni de acceso a internet.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.integrations.aemet import _extraer_dias, _parsear_dia  # noqa: E402

RESPUESTA_SIMULADA = [
    {
        "origen": {
            "productor": "Agencia Estatal de Meteorología - AEMET",
            "web": "https://www.aemet.es",
        },
        "id": "4625001",
        "elaborado": "2026-06-15T10:00:00",
        "nombre": "Playa de Levante / Malvarrosa",
        "localidad": 46250,
        "prediccion": {
            "dia": [
                {
                    "fecha": "20260615",
                    "estadoCielo": {
                        "f1": "100",
                        "descripcion1": "Despejado",
                        "f2": "110",
                        "descripcion2": "Nuboso",
                    },
                    "viento": {
                        "f1": "210",
                        "descripcion1": "Flojo",
                        "f2": "220",
                        "descripcion2": "Moderado",
                    },
                    "oleaje": {
                        "f1": "310",
                        "descripcion1": "Débil",
                        "f2": "310",
                        "descripcion2": "Débil",
                    },
                    "tMaxima": {"valor1": "27"},
                    "sTermica": {"valor1": "460", "descripcion1": "Calor agradable"},
                    "tAgua": {"valor1": "22"},
                    "uvMax": {"valor1": "8"},
                },
                {
                    "fecha": "20260616",
                    "estadoCielo": {"descripcion1": "Nuboso", "descripcion2": "Nuboso"},
                    "viento": {"descripcion1": "Moderado", "descripcion2": "Moderado"},
                    "oleaje": {"descripcion1": "Moderado", "descripcion2": "Moderado"},
                    "tMaxima": {"valor1": "25"},
                    "sTermica": {"valor1": "450", "descripcion1": "Suave"},
                    "tAgua": {"valor1": "22"},
                    "uvMax": {"valor1": "7"},
                },
            ]
        },
    }
]


def test_extraer_dias():
    dias = _extraer_dias(RESPUESTA_SIMULADA)
    assert len(dias) == 2
    assert dias[0]["fecha"] == "20260615"


def test_parsear_dia_hoy():
    dias = _extraer_dias(RESPUESTA_SIMULADA)
    resultado = _parsear_dia(dias[0])

    assert resultado.fecha == "20260615"
    assert resultado.estado_cielo == "Mañana: Despejado. Tarde: Nuboso."
    assert resultado.viento_categoria == "Mañana: Flojo. Tarde: Moderado."
    assert resultado.oleaje_categoria == "Débil"  # mañana == tarde -> sin repetir
    assert resultado.temperatura_aire == 27.0
    assert resultado.sensacion_termica == "Calor agradable"
    assert resultado.temperatura_agua == 22.0
    assert resultado.uv_max == 8


if __name__ == "__main__":
    test_extraer_dias()
    test_parsear_dia_hoy()
    print("Todos los tests del parser de AEMET pasan correctamente.")
