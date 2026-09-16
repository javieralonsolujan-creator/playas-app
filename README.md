# Playas App 🏖️

App para consultar en tiempo (casi) real el estado de las playas de España: tiempo atmosférico, estado del mar (altura de ola, periodo, dirección) y estado de bandera, todo mostrado sobre un mapa interactivo.

## Arquitectura: sin servidor dedicado

Este proyecto NO necesita un servidor corriendo permanentemente. Un job automático (GitHub Actions) consulta AEMET dos veces al día y genera un fichero estático que se publica solo en GitHub Pages. Ver `docs/arquitectura.md` para el detalle completo y los pasos de despliegue.

## Fase actual
MVP — Fase 1: fuente meteorológica (AEMET) integrada, mapa interactivo funcionando con datos reales, sin banderas todavía.

## Estructura del proyecto

```
playas-app/
├── README.md
├── docs/
│   ├── fuentes-datos.md      # Investigación de APIs y fuentes (AEMET, Puertos del Estado, etc.)
│   ├── modelo-datos.md       # Modelo de datos
│   └── arquitectura.md       # Arquitectura y pasos de despliegue
├── scripts/
│   ├── aemet.py               # Cliente de AEMET (autocontenido)
│   ├── generar_datos.py       # Genera site/playas.json
│   └── requirements.txt
├── site/                       # Esto es lo que se publica en GitHub Pages
│   ├── index.html              # Mapa interactivo (Leaflet + CARTO)
│   └── playas.json             # Generado automáticamente, no editar a mano
├── .github/workflows/
│   └── actualizar-datos.yml    # El job que hace toda la magia
├── data/
│   └── playas_seed.json        # Catálogo de playas piloto (con código AEMET)
└── backend/                     # Exploratorio / Fase 2 (ver docs/arquitectura.md)
    ├── requirements.txt
    └── app/
        ├── main.py, database.py, models.py, schemas.py
        ├── seed.py, ingest_aemet.py
        └── integrations/aemet.py
```

## Roadmap corto plazo

1. [x] Documentar y validar acceso a APIs: AEMET ✅ integrado. Puertos del Estado, Copernicus Marine pendientes.
2. [ ] Definir zona piloto (ej. Comunidad Valenciana o Baleares).
3. [x] Construir catálogo base de playas piloto (5 playas de ejemplo con código AEMET real, ver `data/playas_seed.json`).
4. [x] Mapa interactivo funcionando (`site/index.html`) con datos reales de AEMET.
5. [x] Arquitectura sin servidor: GitHub Actions + GitHub Pages.
6. [ ] Resolver el problema de banderas (sin API nacional): definir estrategia (manual/scraping/crowdsourcing).
7. [ ] Puertos del Estado: sumar altura de ola exacta.

## Cómo probarlo en local

```bash
export AEMET_API_KEY="tu_api_key"
pip install -r scripts/requirements.txt
python scripts/generar_datos.py     # genera site/playas.json
cd site && python -m http.server    # sirve la web en http://localhost:8000
```

## Cómo desplegarlo (una vez)

Ver la sección "Despliegue" en `docs/arquitectura.md`: subir a GitHub, añadir el secreto `AEMET_API_KEY`, activar GitHub Pages con origen "GitHub Actions", y hacer push.

## Cómo continuar

Cada vez que se investigue una nueva fuente de datos, añadir la info en `docs/fuentes-datos.md` siguiendo la plantilla ya definida ahí. Cada vez que se decida algo de arquitectura, dejarlo anotado en `docs/arquitectura.md`.
