# Modelo de datos

Modelo inicial, pensado para evolucionar según se integren fuentes reales.

## Entidad: `Playa`
Información estática/semi-estática de cada playa.

| Campo | Tipo | Descripción |
|---|---|---|
| id | int (PK) | Identificador interno |
| nombre | string | Nombre de la playa |
| municipio | string | Municipio al que pertenece |
| provincia | string | Provincia |
| comunidad_autonoma | string | Comunidad autónoma |
| latitud | float | Coordenada |
| longitud | float | Coordenada |
| zona_costera_aemet | string (nullable) | Código de zona marítima de AEMET asociado, para poder cruzar predicciones |
| longitud_m | float (nullable) | Longitud de la playa en metros (dato informativo) |
| activa | bool | Si la playa ya está siendo monitorizada en la app |

## Entidad: `EstadoPlaya` (snapshot en el tiempo)
Cada vez que se actualizan los datos de una playa, se guarda un registro (permite ver histórico y también sirve para el "estado actual" = último registro).

| Campo | Tipo | Descripción |
|---|---|---|
| id | int (PK) | Identificador interno |
| playa_id | int (FK → Playa) | Playa a la que pertenece |
| timestamp | datetime | Momento de la medición/consulta |
| temperatura_aire | float (nullable) | °C |
| estado_cielo | string (nullable) | Descripción (despejado, nuboso, lluvia...) |
| viento_direccion | string (nullable) | N, NE, E... |
| viento_velocidad | float (nullable) | km/h |
| altura_ola | float (nullable) | metros |
| periodo_ola | float (nullable) | segundos |
| direccion_ola | string (nullable) | N, NE, E... |
| temperatura_agua | float (nullable) | °C |
| bandera | string (nullable) | verde / amarilla / roja |
| bandera_motivo | string (nullable) | ej. medusas, oleaje, corrientes |
| bandera_fuente | string (nullable) | de dónde viene el dato (ayuntamiento X, manual, usuario...) |
| fuente_meteo | string (nullable) | ej. "AEMET" |
| fuente_oleaje | string (nullable) | ej. "Puertos del Estado" |

## Notas de diseño

- Separar `Playa` (datos fijos) de `EstadoPlaya` (datos variables en el tiempo) permite:
  - Consultar el estado actual (última fila por `playa_id`).
  - Guardar histórico para futuras funcionalidades (gráficas de evolución, alertas, etc.).
- Los campos nullable reflejan que, según la playa y la fuente disponible, no siempre tendremos todos los datos (especialmente banderas al principio).
- Más adelante se puede añadir una entidad `Reporte` para permitir que usuarios reporten el estado de la bandera manualmente (crowdsourcing), con su propio timestamp y usuario, separada de `EstadoPlaya` para poder distinguir fuente oficial vs. fuente comunidad.
