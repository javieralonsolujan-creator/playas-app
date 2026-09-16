# Fuentes de datos

Documento vivo. Cada vez que investiguemos una fuente nueva (o profundicemos en una existente), añadir/actualizar su sección siguiendo la plantilla.

## Plantilla

```
### Nombre de la fuente
- **Qué ofrece**:
- **Cobertura geográfica**:
- **Frecuencia de actualización**:
- **Acceso**: (API REST / descarga de ficheros / scraping / manual)
- **Requiere API key**: sí/no
- **Coste**: gratis / de pago / límites de uso
- **Formato de respuesta**:
- **Campos relevantes para nosotros**:
- **URL / documentación**:
- **Estado de la investigación**: pendiente / en pruebas / integrado
- **Notas**:
```

---

### AEMET OpenData — Predicción específica de playas ✅ INTEGRADO
- **Qué ofrece**: predicción específica **por playa individual** (no solo por zona/municipio): estado del cielo, categoría de viento, categoría de oleaje, temperatura máxima del aire, sensación térmica, temperatura del agua e índice UV máximo. Todo separado en mañana/tarde, para 3 días (hoy, D+1, D+2).
- **Cobertura geográfica**: ~1300 playas de toda España (existe un listado oficial con código único por playa).
- **Frecuencia de actualización**: 2 veces al día.
- **Acceso**: API REST — endpoint `GET /api/prediccion/especifica/playa/{codigo_playa}`.
- **Requiere API key**: sí (gratuita e indefinida, se solicita con tu email en https://opendata.aemet.es/centrodedescargas/altaUsuario).
- **Coste**: gratis.
- **Formato de respuesta**: JSON, pero con **doble petición**:
  1. Se llama al endpoint con la api_key → devuelve `{"datos": "URL_temporal", "metadatos": "URL_temporal"}`.
  2. Se llama a esa URL de "datos" (sin api_key) para obtener el JSON real.
  - ⚠️ La respuesta de la 2ª petición viene en **codificación ISO-8859-15**, no UTF-8 (si no se decodifica así, los acentos salen mal).
- **Campos relevantes para nosotros**: estado del cielo, viento (categoría: flojo/moderado/fuerte — **no da km/h exactos**), oleaje (categoría: débil/moderado/fuerte — **no da metros exactos**), temperatura máxima, sensación térmica, temperatura del agua, UV máximo.
- **URL / documentación**:
  - Endpoint: https://opendata.aemet.es/opendata/api/prediccion/especifica/playa/{codigo}
  - Listado oficial de códigos de playa (CSV): https://www.aemet.es/documentos/es/eltiempo/prediccion/playas/Playas_codigos.csv
- **Estado de la investigación**: ✅ integrado — ver `backend/app/integrations/aemet.py`.
- **Notas**:
  - Esta es una fuente excelente para el MVP porque ya viene **por playa concreta**, sin tener que mapear a zonas.
  - Las categorías de viento/oleaje son cualitativas; los valores numéricos exactos (metros, periodo) los aportará Puertos del Estado más adelante — por eso en el modelo de datos guardamos ambos tipos de campo por separado (`viento_categoria`/`oleaje_categoria` de AEMET vs. `altura_ola`/`periodo_ola` numéricos de Puertos del Estado).
  - No da el estado de bandera — sigue siendo el reto pendiente.

### AEMET OpenData — otros productos (sin integrar todavía)
- Predicción por municipios, avisos meteorológicos, predicción marítima costera por zonas (para alta mar/tramos amplios de costa, complementaria a la de playas). Mismo mecanismo de doble petición y misma codificación ISO-8859-15.
- URL: https://opendata.aemet.es/

### Puertos del Estado
- **Qué ofrece**: datos oceanográficos de boyas (altura de ola, periodo, dirección, temperatura del agua) y modelos de predicción de oleaje.
- **Cobertura geográfica**: costa española, mediante red de boyas + modelos por puntos de rejilla.
- **Frecuencia de actualización**: horaria (boyas) / varias veces al día (modelos).
- **Acceso**: portal de datos abiertos / API.
- **Requiere API key**: por confirmar.
- **Coste**: gratis.
- **Formato de respuesta**: por confirmar (probablemente JSON/CSV).
- **Campos relevantes para nosotros**: altura de ola significante, periodo, dirección de oleaje, temperatura del agua.
- **URL / documentación**: https://www.puertos.es/es-es/oceanografia
- **Estado de la investigación**: pendiente.
- **Notas**: es la fuente más importante para "estado del mar". Prioridad alta para investigar en detalle.

### Copernicus Marine Service (CMEMS)
- **Qué ofrece**: datos oceanográficos europeos (oleaje, corrientes, temperatura del agua) basados en modelos.
- **Cobertura geográfica**: Europa, incluida toda la costa española.
- **Frecuencia de actualización**: diaria/varias veces al día según producto.
- **Acceso**: API / descarga de ficheros NetCDF.
- **Requiere API key**: sí (registro gratuito).
- **Coste**: gratis.
- **Formato de respuesta**: NetCDF (requiere librerías como `xarray`/`netCDF4` para procesarlo).
- **Campos relevantes para nosotros**: altura de ola, corrientes, temperatura del agua — como respaldo o complemento a Puertos del Estado.
- **URL / documentación**: https://marine.copernicus.eu/
- **Estado de la investigación**: pendiente.
- **Notas**: más técnico de integrar que Puertos del Estado; valorar si aporta algo que la fuente anterior no dé.

### Banderas de playas (estado verde/amarilla/roja)
- **Qué ofrece**: estado de baño de la playa.
- **Cobertura geográfica**: gestionado de forma descentralizada — cada ayuntamiento, Cruz Roja o servicio de socorrismo local decide y publica (o no) este dato.
- **Frecuencia de actualización**: diaria, normalmente por la mañana.
- **Acceso**: variable — algunas webs municipales lo publican, muchas no tienen ningún canal digital.
- **Requiere API key**: no aplica (no hay API unificada).
- **Coste**: -
- **Formato de respuesta**: no estandarizado.
- **Campos relevantes para nosotros**: estado de bandera (verde/amarilla/roja), a veces con motivo (medusas, oleaje, corrientes).
- **URL / documentación**: sin fuente única. Ejemplos a explorar por comunidad autónoma.
- **Estado de la investigación**: pendiente — es el mayor reto del proyecto.
- **Notas**: estrategia propuesta:
  1. Empezar con una zona piloto donde el ayuntamiento sí publique el dato digitalmente.
  2. Explorar si Cruz Roja Española tiene algún canal centralizado por provincia.
  3. Como fallback, panel de administración interno para actualizar manualmente, o sistema de reportes de usuarios (crowdsourcing) con validación.

### Catálogo de playas (nombre, coordenadas, municipio)
- **Qué ofrece**: listado base de playas con su localización.
- **Cobertura geográfica**: toda España.
- **Frecuencia de actualización**: estático (cambia poco).
- **Acceso**: extracción de datos abiertos.
- **Requiere API key**: no.
- **Coste**: gratis.
- **Formato de respuesta**: JSON/GeoJSON/CSV según fuente.
- **Campos relevantes para nosotros**: nombre, lat/lon, municipio, provincia, comunidad autónoma.
- **URL / documentación**: 
  - OpenStreetMap (Overpass API, tag `natural=beach`) — https://overpass-turbo.eu/
  - Instituto Geográfico Nacional (IGN) — https://www.ign.es/
- **Estado de la investigación**: pendiente.
- **Notas**: probablemente la vía más rápida es una consulta Overpass sobre OSM filtrando por España, y luego limpiar/curar manualmente la zona piloto elegida.
