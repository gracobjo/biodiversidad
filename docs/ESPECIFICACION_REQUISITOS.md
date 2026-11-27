# Especificación de requisitos

Sistema de consulta, ingesta y análisis de ocurrencias de biodiversidad a partir de la API pública de GBIF. Cubre los cuadernos de `notebooks/`, el código de `src/` y dos ventanas en la raíz: `app_tkinter.py` (MySQL con SQLAlchemy ORM) e `interfaz_gbif.py` (API, SQLite, MySQL y exportación).

Los casos de uso están en [CASOS_DE_USO.md](./CASOS_DE_USO.md). Los diagramas están en [UML.md](./UML.md). El manual operativo sigue en [MANUAL_USUARIO.md](./MANUAL_USUARIO.md).

## 1. Alcance

Dentro del alcance:

- Resolver un nombre científico contra el Backbone Taxonomy de GBIF.
- Descargar ocurrencias georreferenciadas, paginadas, para uno o varios países.
- Separar lobo silvestre y perro doméstico cuando el taxón es *Canis lupus*.
- Normalizar territorio con GADM cuando la respuesta lo trae.
- Exportar CSV, JSON y mapas HTML.
- Persistir de forma idempotente en SQLite o en MySQL 8.
- Consultar la base local sin volver a llamar a la API.
- Filtrar un listado de ocurrencias ya cargado por país, año, provincia y epíteto.
- Repetir la descarga para un catálogo corto de especies y compararlas en un mapa.

Fuera del alcance:

- Sustituir el portal de GBIF o republicar datasets.
- Estimar abundancia o tamaño de población.
- Editar registros en GBIF.
- Autenticación de usuarios de la aplicación.

## 2. Actores

| Actor | Qué hace |
|---|---|
| Persona investigadora | Elige especie, ámbito y periodo, interpreta tablas y mapas. |
| Persona analista | Valida cobertura, nulos, epíteto y territorio. |
| Persona ingeniera de datos | Crea la base, lanza la ingesta y revisa la idempotencia. |
| API GBIF | Fuente externa. No forma parte del sistema. |
| MySQL 8 | Destino opcional. Tiene que estar instalado, en marcha y con la base `gbif_biodiversidad` creada antes de poblar o consultar. |
| SQLite del pipeline | Archivo `datos/gbif_biodiversidad.sqlite`. Tiene que estar iniciado (esquema aplicado) antes de las consultas. El archivo homónimo de la raíz no es esta base. |

## 3. Requisitos funcionales

### Consulta a la API

| ID | Requisito |
|---|---|
| RF-01 | El sistema resuelve un nombre científico con `GET /v1/species/match` y usa `usageKey` como `taxonKey`. No se escribe el identificador a mano. |
| RF-02 | La descarga de ocurrencias usa `GET /v1/occurrence/search`, pagina con `limit` máximo 300 y se detiene con `endOfRecords` o con el máximo configurado. |
| RF-03 | La sesión HTTP reintenta 429 y errores 5xx. En la red de la Junta, la verificación TLS usa el almacén de Windows (`truststore`) porque el proxy Netskope sustituye el certificado. |
| RF-04 | Se puede limitar por uno o varios países (código ISO de dos letras, no solo `ES` y `PT`), por un año, por un intervalo de años o por un intervalo de fechas (`2018-03-01`), y por presencia de coordenadas. En la ventana, Hasta vacío llega hasta hoy. |
| RF-05 | De cada registro se conservan los campos Darwin Core usados en el análisis y, en el pipeline de `src/`, el JSON íntegro en `raw_json`. |
| RF-06 | Si el taxón es *Canis lupus*, el sistema puede quedarse solo con `specificEpithet = lupus` y excluir el epíteto infraespecífico `familiaris`. |
| RF-07 | El territorio de análisis preferente es `gadm` (comunidad, provincia, municipio). `stateProvince` se conserva porque no siempre equivale a una comunidad autónoma. |
| RF-08 | Se puede extraer evidencia de presencia (`dynamicProperties` / `samplingProtocol`) y vitalidad (`vitality`) cuando el registro las trae. |

### Exportación y mapas

| ID | Requisito |
|---|---|
| RF-09 | Un resultado tabular se exporta a CSV (UTF-8 con BOM) y a JSON. |
| RF-10 | Un resultado con coordenadas se exporta a HTML de Folium, con teselas que no exigen clave (OpenStreetMap y Esri) y un enlace a la ficha GBIF. |
| RF-11 | El cuaderno multi-especie escribe un CSV y un mapa por especie, más un CSV maestro y un mapa con una capa por especie. |

### Persistencia

| ID | Requisito |
|---|---|
| RF-12 | Se puede crear `datos/gbif_biodiversidad.sqlite` ejecutando `docs/schema_gbif_sqlite.sql`. Volver a ejecutarlo no borra datos. |
| RF-13 | Se puede crear el mismo modelo en MySQL 8 con `docs/schema_gbif.sql`. |
| RF-14 | La ingesta de `src/` inserta taxón, organizaciones (`/v1/organization/{key}`), datasets (`/v1/dataset/{key}`) y ocurrencias, en ese orden, con upsert por clave primaria. |
| RF-15 | Las consultas de análisis (resumen, ocurrencias, territorio, ranking de datasets y campos JSON) funcionan contra SQLite y contra MySQL sin llamar a la API. |
| RF-16 | El cuaderno `gbif_multiespecie_es_pt_sqlite_mysql.ipynb` puede guardar el lote multi-especie en `salidas_gbif_multiespecie/biodiversidad_gbif.db` y, si se activa, en MySQL. Ese esquema es distinto del de RF-12. |

### Interfaz de escritorio

| ID | Requisito |
|---|---|
| RF-17 | La interfaz muestra el resultado de `/v1/species/match` y de `/v1/occurrence/search`. |
| RF-18 | Permite crear y poblar la base elegida (SQLite o MySQL) con los parámetros de la ventana. La base tiene que estar iniciada: archivo SQLite creado o servidor MySQL en marcha con la base creada. |
| RF-19 | Permite lanzar las consultas de RF-15, limitadas a la especie elegida, y exportar la tabla de esa especie a CSV, JSON y HTML. El nombre del fichero y el contenido identifican la especie. |
| RF-20 | Con un listado de ocurrencias ya en pantalla, se puede filtrar por `country_code`, `year`, `state_province` y `specific_epithet`. País y año son exactos. Provincia y epíteto admiten un fragmento, sin distinguir mayúsculas ni tildes. Quitar el filtro restaura el listado cargado. |
| RF-21 | El catálogo de especies con coordenadas muestra cinco especies de Mammalia, Squamata, Amphibia, Insecta, Magnoliopsida, Liliopsida y Aves, con clase y familia, aunque no sean las más registradas del país. |

## 4. Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF-01 | Python 3.14. Dependencias declaradas en `pyproject.toml`. |
| RNF-02 | La paginación y la pausa entre páginas respetan el límite de GBIF. Una ingesta de referencia (1.000 por país, dos países) termina en el orden de unas decenas de segundos cuando la red responde. |
| RNF-03 | Una carga interrumpida no deja una transacción a medias: SQLite y MySQL hacen commit al final o rollback. |
| RNF-04 | Repetir la ingesta con las mismas claves no duplica filas. |
| RNF-05 | Las consultas locales no necesitan red. La descarga sí. |
| RNF-06 | La contraseña de MySQL está en `.env` y no se versiona. `src/db_config.py` solo la lee. |
| RNF-07 | Los cuadernos y la interfaz se pueden volver a ejecutar cambiando especie, países, años y máximo. |
| RNF-08 | Los textos de la interfaz y de los mensajes de error están en español. |
| RNF-09 | La interfaz no bloquea la ventana durante la descarga ni durante las consultas. |

## 5. Datos persistentes

Modelo de `src/` (SQLite y MySQL), una fila por clave de GBIF:

| Tabla | Clave | Origen |
|---|---|---|
| `taxones` | `taxon_key` | `/v1/species/match` |
| `organizaciones` | `organization_key` | `/v1/organization/{key}` |
| `datasets` | `dataset_key` | `/v1/dataset/{key}` |
| `ocurrencias` | `occurrence_key` | `/v1/occurrence/search` |

`ocurrencias` referencia a las otras tres. En MySQL esas claves foráneas son anulables: si el registro cita un taxón, un dataset o una organización que no está en el catálogo, el ORM deja la clave vacía y guarda la ocurrencia. En SQLite las claves foráneas solo se comprueban si la conexión ejecuta `PRAGMA foreign_keys = ON`. `raw_json` guarda la respuesta original (tipo `TEXT` en SQLite y `JSON` en MySQL). Las clases `Taxon`, `Organizacion`, `Dataset` y `Ocurrencia` de `src/models.py` mapean estas tablas.

Modelo del cuaderno multi-especie con base de datos: `taxones`, `ocurrencias`, `ocurrencia_media`, vista `vw_ocurrencias_completas`, archivo `salidas_gbif_multiespecie/biodiversidad_gbif.db`.

## 6. Interfaces externas

| Interfaz | Uso |
|---|---|
| `https://api.gbif.org/v1/species/match` | Resolución taxonómica. |
| `https://api.gbif.org/v1/occurrence/search` | Ocurrencias. `limit` ≤ 300. |
| `https://api.gbif.org/v1/organization/{key}` | Institución publicadora, solo en la ingesta de `src/`. |
| `https://api.gbif.org/v1/dataset/{key}` | Metadatos del dataset, solo en la ingesta de `src/`. |
| MySQL 8, host y credenciales de `.env` (`app_tkinter.py`, cuadernos y `interfaz_gbif.py`) | Destino opcional. La sesión la abre `src/database.get_session`. |
| Sistema de archivos | `datos/`, `salidas_gbif_multiespecie/`, `notebooks/`. |

## 7. Restricciones

- Un registro GBIF no es un individuo.
- El `taxonKey` de *Canis lupus* mezcla lobo y perro hasta que se filtra el epíteto.
- El máximo de registros es una muestra. El campo `count` de la API es el total disponible.
- Las coordenadas de observaciones sensibles pueden estar ofuscadas (`coordinateUncertaintyInMeters` de decenas de kilómetros).
- En la red corporativa, sin `truststore`, la descarga falla con `CERTIFICATE_VERIFY_FAILED`.
- MySQL solo funciona si el servidor acepta la conexión. SQLite no necesita servidor.

## 8. Criterios de aceptación de la ingesta de referencia

Con *Canis lupus*, ES y PT, años 2000–2026, solo con coordenadas y máximo 1.000 por país, `datos/gbif_biodiversidad.sqlite` queda con 1 taxón, las organizaciones y datasets distintos de ese lote, y 2.000 ocurrencias. `src/prueba_lectura_sqlite.py` imprime esos conteos y las cinco consultas sin error.
