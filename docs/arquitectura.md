# Arquitectura

## Decisión clave (actualizada): sin servidor dedicado

AEMET solo actualiza sus datos 2 veces al día, así que no hace falta ningún
servidor "vivo" respondiendo peticiones. En su lugar:

```
[GitHub Actions]                    [GitHub Pages]              [Usuario]
(cron 2x/día)                       (hosting estático             
  │                                  gratuito)                    
  ├─ scripts/generar_datos.py  ──►  site/playas.json  ◄────  fetch('playas.json')
  │  (consulta AEMET)                site/index.html  ◄────  (mapa + ficha)
  └─ actions/deploy-pages
```

- **`scripts/generar_datos.py`**: consulta AEMET para cada playa y escribe `site/playas.json`. No usa base de datos ni servidor: es un script que se ejecuta, escribe un fichero, y termina.
- **GitHub Actions** (`.github/workflows/actualizar-datos.yml`) ejecuta ese script automáticamente 2 veces al día (cron) y publica el resultado en GitHub Pages. También se puede lanzar a mano desde la pestaña "Actions" del repositorio.
- **`site/index.html`**: la web/mapa, que simplemente hace `fetch('playas.json')`. Si ese fetch falla (por ejemplo, al abrir el archivo con doble clic en vez de por un servidor), usa datos de ejemplo como respaldo, para poder seguir probando el diseño sin conexión.
- **Coste**: 0€. GitHub Actions y GitHub Pages son gratuitos para repositorios públicos (y para privados hasta un límite de minutos generoso).
- **Nada que mantener**: no hay un Ubuntu Server, ni un proceso `uvicorn` que deba seguir corriendo, ni una base de datos que respaldar.

## Qué pasa con `backend/` (FastAPI + SQLAlchemy)

Se mantiene en el repositorio pero pasa a ser **exploratorio / Fase 2**, no la vía de producción. Sería necesario recuperarlo el día que necesitemos:
- Guardar histórico más allá de "el último dato".
- Reportes de usuarios sobre el estado de la bandera (crowdsourcing) — esto sí requiere algo que reciba escrituras, no solo un JSON estático.

En ese momento, la opción recomendada sería un backend **serverless** (Cloudflare Workers + D1, o similar) en vez de un servidor tradicional, para seguir sin tener nada que administrar 24/7.

## Despliegue (pasos únicos, una sola vez)

1. Sube este proyecto a un repositorio de GitHub.
2. En el repositorio: **Settings → Secrets and variables → Actions → New repository secret** → nombre `AEMET_API_KEY`, valor tu API key de AEMET. (Nunca se sube al código, solo GitHub Actions la usa en tiempo de ejecución.)
3. En **Settings → Pages → Source**, selecciona "GitHub Actions".
4. Haz `git push`. El workflow se ejecutará automáticamente y en unos minutos la web estará publicada en `https://tu-usuario.github.io/tu-repo/`.
5. A partir de ahí, se actualiza sola 2 veces al día. También puedes forzar una actualización manual desde la pestaña "Actions" → "Actualizar datos y publicar" → "Run workflow".

## Otras decisiones

- **Mapa**: Leaflet + tiles de CARTO (requieren API key gratuita desde agosto 2026, ver `site/index.html`).
- **Zona piloto**: por definir (ver `README.md` roadmap).

## Pendiente de decidir

- [ ] Framework definitivo para la app móvil (Kivy vs. Flet vs. BeeWare) — el prototipo actual es web (HTML/Leaflet); para publicar en las stores habrá que portarlo o envolverlo.
- [ ] Estrategia definitiva para el dato de banderas.
- [ ] Cuándo dar el salto a un backend con escritura (serverless) para reportes de usuarios.
