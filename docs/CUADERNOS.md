# Cuadernos del proyecto

Los cuadernos viven en `notebooks/`. Se abren con Jupyter o con el editor, usando el entorno del proyecto (Python 3.14, dependencias de `pyproject.toml`).

Las rutas de salida ya no dependen de la carpeta desde la que se lance el kernel. Si el directorio de trabajo es la raíz del proyecto o `notebooks/`, los CSV, JSON y HTML van a `salidas_gbif_multiespecie/` y el JSON bruto de la exploración a `datos/registros_gbif_brutos.json`.

Ejecución habitual:

1. Activar el entorno (`.venv\Scripts\Activate.ps1`).
2. Abrir el cuaderno.
3. Elegir el kernel **Python (biodiversidad)**. Es el intérprete `.venv\Scripts\python.exe`.
4. Ejecutar las celdas en orden. Si una celda se queda en `[*]` y no imprime el intérprete, el kernel no es ese: interrumpe y vuelve a lanzarla.

La interfaz de escritorio no es un cuaderno. El archivo está en la raíz: `python interfaz_gbif.py`. Antes de Poblar o de Consultas, la base tiene que estar iniciada: en SQLite, el archivo `datos/gbif_biodiversidad.sqlite` con el esquema creado; en MySQL, el servidor en marcha y la base `gbif_biodiversidad` creada.

## Cuál usar

| Si quieres… | Cuaderno |
|---|---|
| Estudiar *Canis lupus* en España, separar lobo y perro, y mirar mortalidad | `exploracion_biodiversidad_gbif_v7_mortalidad.ipynb` |
| Listar especies de España y Portugal y luego bajar una especie | `exploracion_biodiversidad_gbif-v6-es-pt.ipynb` (revisión de v4) |
| *Canis lupus* en ES y PT, solo entre 1.000 y 3.000 m, sin perro doméstico | `exploracion_biodiversidad_gbif-v5-es-pt.ipynb` |
| Ver especies de varias clases (no solo las aves más registradas) | `gbif_especies_por_clase_es_pt.ipynb` |
| Varias especies a CSV y mapas, sin base de datos | `gbif_multiespecie_es_pt.ipynb` |
| Lo mismo y, además, guardarlo en SQLite o MySQL | `gbif_multiespecie_es_pt_sqlite_mysql.ipynb` |
| Llenar MySQL 8 con el esquema de `src/` | `ingesta_gbif_mysql.ipynb` y después `analisis_offline_gbif.ipynb` |
| Llenar y consultar `datos/gbif_biodiversidad.sqlite` | no hace falta cuaderno: `src/ingesta_gbif_sqlite.py` o la interfaz |

## Exploración de una especie

### `exploracion_biodiversidad_gbif_v4_es_pt.ipynb`

Primera exploración ibérica. Descubre especies en España y Portugal con facetas de `/v1/occurrence/search`, resuelve nombres comunes y descarga la especie elegida (por defecto *Canis lupus*). El tope es de unos 600 registros **en total** para los dos países, no 600 por país. El mapa pinta España y Portugal con colores distintos. El CSV y el HTML quedan en `salidas_gbif_multiespecie/`.

Úsalo como referencia histórica de aquella muestra. Para repetir el catálogo, el cuaderno vigente es v6.

### `exploracion_biodiversidad_gbif-v5-es-pt.ipynb`

Consulta solo *Canis lupus* en España y Portugal, años 2020–2026, en la franja de 1.000 a 3.000 m, y aparta *Canis lupus familiaris*. Exporta un CSV Darwin Core y `mapa_canis_lupus_es_pt.html`. No recorre un catálogo de especies.

La copia ya generada de ese CSV está archivada en `datos/canis_lupus_es_pt_2020_2026_darwin_core.csv`. Una ejecución nueva escribe otra copia en `salidas_gbif_multiespecie/` y no pisa el archivo de `datos/`.

### `exploracion_biodiversidad_gbif-v6-es-pt.ipynb`

Revisión de la exploración ibérica de v4, con el mismo título. Tiene dos fases: catálogo alfabético de especies en ES y PT (faceta `speciesKey`, nombre científico y nombre común) y, después, descarga paginada de `ESPECIE_OBJETIVO`. Incluye diagnóstico de filtros, normalización, CSV y mapa por país.

### `exploracion_biodiversidad_gbif_v7_mortalidad.ipynb`

Cuaderno principal de una sola especie en **España**. Resuelve *Canis lupus* con `/v1/species/match`, descarga 2020–2026 con coordenadas, guarda el JSON bruto en `datos/registros_gbif_brutos.json` y separa lobo (`specificEpithet == lupus`) de perro (`familiaris`) antes de interpretar nada. Revisa vitalidad, protocolo de muestreo, evidencia de presencia y territorio GADM. El mapa distingue el epíteto, no el país.

Para repetir el análisis sin red, carga `datos/registros_gbif_brutos.json` y sigue desde la normalización.

La muestra de referencia del manual (600 registros, 315 lobos y 285 perros) sale de este cuaderno, no de v4. v4 reparte el mismo tope entre España y Portugal, así que la muestra española no coincide.

## Ingesta y análisis con base de datos

### `ingesta_gbif_mysql.ipynb`

Fase A del pipeline MySQL descrito en `documentacion_del_pipeline_gbif_y_mysql_8.md`. Resuelve el taxón, pagina ocurrencias (por defecto *Canis lupus*, ES y PT, 2000–2026, máximo 1.000 por país) y llama a `src/volcarEndpoints.py`. Hace falta MySQL 8, el esquema `docs/schema_gbif.sql` y `src/db_config.py`.

### `analisis_offline_gbif.ipynb`

Fase B. Lee MySQL con `src/consulta_gbif.py`: resumen, ocurrencias, filtro de lobo silvestre, territorio, datasets, campos dentro de `raw_json` y mapa Folium. No llama a la API.

La copia renderizada de estos dos cuadernos está en `docs/exportaciones/`.

### `gbif_especies_por_clase_es_pt.ipynb`

Catálogo para ver especies antes de lanzar el multi-especie. Usa la misma función que el botón **Especies con coordenadas** de la interfaz: cinco especies con coordenadas de Mammalia, Squamata, Amphibia, Insecta, Magnoliopsida, Liliopsida y Aves, en España y Portugal (2000–2026). Muestra clase, familia y el recuento, y guarda `salidas_gbif_multiespecie/especies_por_clase_es_pt.csv`. No descarga ocurrencias ni crea base de datos. Si una clase no responde, se omite y la celda termina con el resto. Los nombres se pueden copiar a `ESPECIES_OBJETIVO` de `gbif_multiespecie_es_pt.ipynb`. El kernel tiene que ser **Python (biodiversidad)**.

### `gbif_multiespecie_es_pt.ipynb`

Recorre una lista fija:

- *Canis lupus*
- *Lynx pardinus*
- *Ursus arctos*
- *Gypaetus barbatus*

Para cada una resuelve `/v1/species/match` y descarga `/v1/occurrence/search` en España y Portugal, con coordenadas y con un máximo de 600 registros por país. Limpia URLs de `media`, escribe un CSV por especie y un CSV maestro `gbif_multiespecie_es_pt.csv`, y genera un mapa HTML por especie más `mapa_comparativo_multiespecie_es_pt.html` (una capa por especie). Todo queda en `salidas_gbif_multiespecie/`.

No crea tablas. Si solo necesitas archivos y mapas, usa este.

### `gbif_multiespecie_es_pt_sqlite_mysql.ipynb`

Es el mismo pipeline multi-especie y añade la sección 5 de persistencia. El nombre anterior era `gbif_multiespecie_es_pt (1).ipynb`; se renombró para que no parezca un duplicado de Windows.

Después de los CSV y los mapas:

- crea `salidas_gbif_multiespecie/biodiversidad_gbif.db` (SQLite) con `taxones`, `ocurrencias`, `ocurrencia_media` y la vista `vw_ocurrencias_completas`;
- si `ACTIVAR_MYSQL = True` y existe un `.env` con `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD` y `MYSQL_DATABASE`, repite la carga en MySQL 8.

Ese esquema no es el de `docs/schema_gbif_sqlite.sql`. La base que usan `src/` y la interfaz es `datos/gbif_biodiversidad.sqlite` (taxones, organizaciones, datasets y ocurrencias, con el JSON completo del Registry). No mezcles las dos.

## Lectura de los resultados

Un recuento de filas es un recuento de registros GBIF, no de individuos. *Canis lupus* incluye perros mientras no se filtre `specificEpithet`. El año en curso está incompleto. Si el total que anuncia la API supera el máximo del cuaderno, las cifras describen la muestra descargada.
