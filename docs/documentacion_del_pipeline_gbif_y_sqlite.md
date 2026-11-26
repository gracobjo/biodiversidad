# Documentación Técnica: Pipeline ETL y Análisis Offline de Biodiversidad (GBIF + SQLite)

Documento paralelo a [`documentacion_del_pipeline_gbif_y_mysql_8.md`](./documentacion_del_pipeline_gbif_y_mysql_8.md). El diseño de tablas, el orden de carga y la capa de consulta son los mismos. Cambia el motor: el archivo `datos/gbif_biodiversidad.sqlite`, sin servidor ni credenciales.

La base tiene que estar iniciada antes de poblarla o consultarla. Iniciarla es crear el archivo y aplicar el esquema (sección 3, o el botón Crear de la interfaz). El archivo de la raíz del proyecto, `gbif_biodiversidad.sqlite`, no es esa base: la interfaz y `src/` no lo leen ni lo escriben.

## 1. Visión General y Arquitectura

El proyecto implementa una arquitectura **ETL (Extract, Transform, Load) + caché relacional local** para trabajar con datos de biodiversidad procedentes de la API pública de GBIF (*Global Biodiversity Information Facility*).

El flujo se divide en **dos fases desacopladas**:

1. **Fase A (Online / Ingesta):** Consulta los *endpoints* de taxonomía, ocurrencias y metadatos del *Registry* de GBIF y persiste la información de forma idempotente en **`gbif_biodiversidad.sqlite`**.
2. **Fase B (Offline / Análisis):** Lee los datos directamente desde ese archivo mediante `SQLAlchemy` y `pandas`, sin nuevas llamadas a la API.

```text
docs/schema_gbif_sqlite.sql
        │
        ▼
src/gbif_biodiversidad_sqlite.py     crea el archivo y las tablas (vacías)
        │
        ▼
src/ingesta_gbif_sqlite.py           descarga GBIF
        │
        ▼
src/guardar_en_sqlite.py             vuelca taxón, organizaciones, datasets y ocurrencias
        │
        ▼
gbif_biodiversidad.sqlite
        │
        ▼
src/consulta_gbif_sqlite.py          consultas → DataFrame
        │
        ▼
src/prueba_lectura_sqlite.py         batería de lectura por consola
```

---

## 2. Estructura del Proyecto

```text
biodiversidad/
├── interfaz_gbif.py                   # Ventana de escritorio (API, base, consultas, exportación)
├── src/
│   ├── db_sqlite_config.py              # Rutas del archivo SQLite y del DDL
│   ├── gbif_biodiversidad_sqlite.py     # Crea el archivo y aplica el esquema
│   ├── ingesta_gbif_sqlite.py           # Fase A: descarga paginada desde la API
│   ├── guardar_en_sqlite.py             # Inserción idempotente (no se ejecuta solo)
│   ├── consulta_gbif_sqlite.py          # Fase B: consultas SQLAlchemy + pandas
│   └── prueba_lectura_sqlite.py         # Batería de lectura por consola
├── docs/
│   ├── schema_gbif_sqlite.sql           # DDL de las cuatro tablas e índices
│   └── documentacion_del_pipeline_gbif_y_sqlite.md
├── datos/gbif_biodiversidad.sqlite      # Base generada por el pipeline de src/
└── pyproject.toml
```

Las rutas no dependen del directorio de trabajo. `db_sqlite_config.py` las resuelve desde la ubicación del propio módulo:

| Constante | Valor |
| :--- | :--- |
| `RUTA_DB_SQLITE` | `<raíz del proyecto>/datos/gbif_biodiversidad.sqlite` |
| `RUTA_SCHEMA_SQLITE` | `<raíz del proyecto>/docs/schema_gbif_sqlite.sql` |

### Dependencias

* `requests` y `urllib3`: peticiones HTTP con reintentos.
* `truststore`: hace que `requests` confíe en el almacén de certificados de Windows. Imprescindible en la red de la Junta (ver sección 5).
* `sqlalchemy`: motor de conexión para `pandas.read_sql()`.
* `pandas`: resultado tabular de las consultas.

---

## 3. Cómo crear la base de datos

Este paso inicia la base. Hasta que no se ha hecho, las consultas de `consulta_gbif_sqlite.py` y la pestaña Consultas de la interfaz no tienen archivo que abrir.

Desde la raíz del proyecto:

```powershell
python .\src\gbif_biodiversidad_sqlite.py
```

El script lee `docs/schema_gbif_sqlite.sql` y lo ejecuta con `executescript` sobre `datos/gbif_biodiversidad.sqlite`. Si el archivo no existe, SQLite lo crea. La salida esperada es:

```text
[SQLite] Esquema aplicado correctamente en: E:\...\biodiversidad\datos\gbif_biodiversidad.sqlite
```

El DDL usa `CREATE TABLE IF NOT EXISTS` y `CREATE INDEX IF NOT EXISTS`, así que volver a lanzarlo no borra datos.

Este paso **solo crea el esquema**. Las cuatro tablas quedan a 0 filas. `guardar_en_sqlite()` vuelve a aplicar el mismo SQL antes de insertar, de modo que la ingesta también crea el archivo si todavía no existe.

### Tablas

SQLite no tiene tipo `JSON`: la respuesta íntegra de la API se guarda en `raw_json TEXT` y se consulta con `json_extract` y `json_array_length`. Las claves foráneas solo se comprueban si cada conexión ejecuta `PRAGMA foreign_keys = ON`. Tanto la creación como la ingesta y la lectura lo hacen.

| Tabla | *Endpoint* GBIF | Clave primaria | Papel |
| :--- | :--- | :--- | :--- |
| **`taxones`** | `/v1/species/match` | `taxon_key` (`INTEGER`) | Jerarquía taxonómica, rango y estado. |
| **`organizaciones`** | `/v1/organization/{key}` | `organization_key` (`TEXT`, 36 caracteres) | Institución publicadora. |
| **`datasets`** | `/v1/dataset/{key}` | `dataset_key` (`TEXT`, 36 caracteres) | **FK** `organization_key`. Conjunto de datos, licencia y DOI. |
| **`ocurrencias`** | `/v1/occurrence/search` | `occurrence_key` (`INTEGER`) | **FK** `taxon_key`, `dataset_key`, `organization_key`. Registro Darwin Core. |

Índices de lectura: `(country_code, year)`, `(taxon_rank, specific_epithet)`, `comunidad_gadm`, `basis_of_record` y coordenadas.

---

## 4. Cómo se ingieren los datos

El punto de entrada es `src/ingesta_gbif_sqlite.py`. Desde `src/`:

```powershell
python .\ingesta_gbif_sqlite.py
```

### Parámetros de extracción

Definidos al inicio del script:

| Parámetro | Valor actual |
| :--- | :--- |
| `ESPECIE_OBJETIVO` | `Canis lupus` |
| `PAISES` | `ES`, `PT` (una búsqueda por país) |
| `YEAR_RANGE` | `2000,2026` |
| Coordenadas | `hasCoordinate=true` |
| `MAX_REGISTROS_POR_PAIS` | `1000` (páginas de 300, tope de la API) |

Pasos:

1. `GET /v1/species/match?name=Canis+lupus` y se toma `usageKey` como `taxonKey`.
2. `GET /v1/occurrence/search` paginado por país, con reintentos ante HTTP 429 y 5xx y una pausa de 0,2 s entre páginas.
3. `guardar_en_sqlite()` vuelca, en una sola transacción y en este orden (lo exigen las claves foráneas):
   1. el taxón;
   2. cada `publishingOrgKey` distinta, consultando `/v1/organization/{key}`;
   3. cada `datasetKey` distinta, consultando `/v1/dataset/{key}`;
   4. las ocurrencias en lote (`executemany`).

La carga es idempotente: `INSERT ... ON CONFLICT DO UPDATE`. Repetir la ingesta no duplica claves. En ocurrencias, el `UPDATE` solo refresca vitalidad, estado, incertidumbre de la coordenada, `raw_json` y `updated_at`.

*Canis lupus* en GBIF incluye al perro doméstico (`familiaris`). La ingesta guarda ambos. El corte de lobo silvestre se hace al consultar, no al cargar.

Una ingesta correcta termina así:

```text
[SQLite] Carga completada en 'E:\...\biodiversidad\datos\gbif_biodiversidad.sqlite': 1 taxón, 12 organizaciones, 17 datasets y 2000 ocurrencias.
```

Esos 2000 registros son el tope configurado (1000 de España y 1000 de Portugal), no el total disponible en GBIF.

### Qué no hay que ejecutar

`guardar_en_sqlite.py` solo define funciones. No tiene bloque `if __name__ == "__main__"`. Lanzarlo no descarga nada y no escribe filas. Si después de crearlo la base sigue a cero, la ingesta que falta es `ingesta_gbif_sqlite.py`.

---

## 5. Problema de la ingesta: certificado SSL de Netskope

En la red de la Junta, la primera petición a `https://api.gbif.org` falla con:

```text
requests.exceptions.SSLError: certificate verify failed: self-signed certificate in certificate chain
```

No es un fallo de GBIF ni de la URL. El proxy de inspección **Netskope** sustituye el certificado de `api.gbif.org` por uno emitido por `ca.accyl.goskope.com` (Junta de Castilla y León), que a su vez cuelga de la raíz `*.fra2.goskope.com` (Netskope Inc.). Esa raíz está en el almacén de certificados de Windows, por eso el navegador entra en GBIF. `requests` no consulta ese almacén: solo confía en el paquete `certifi`, que no incluye la CA corporativa.

`ingesta_gbif_sqlite.py` (y `volcarEndpoints.py`, el equivalente MySQL) lo resuelven al arrancar, antes de abrir la sesión HTTP:

```python
import truststore
truststore.inject_into_ssl()
```

`truststore` hace que Python use el almacén de Windows. La verificación TLS sigue activa; no se desactiva con `verify=False`. La dependencia está declarada en `pyproject.toml` (`truststore>=0.10.5`). Si el entorno se recrea:

```powershell
python -m pip install "truststore>=0.10.5"
```

Sin esta llamada, los cinco reintentos del adaptador HTTP agotan el tiempo y la ingesta no llega a crear filas. El esquema, si se aplicó antes, permanece vacío.

---

## 6. Cómo se prueba

La prueba de lectura no llama a la API. Desde `src/`:

```powershell
python .\prueba_lectura_sqlite.py
```

`prueba_lectura_sqlite.py` ejecuta las cinco funciones de `consulta_gbif_sqlite.py` e imprime cada resultado. Requiere `sqlalchemy` y `pandas` (`python -m pip install "sqlalchemy>=2.1.9" "pandas>=3.1.1"` si el intérprete no los tiene).

| Bloque de la salida | Función | Qué comprueba |
| :--- | :--- | :--- |
| 1. Conteo general | `obtener_resumen_general()` | Filas de las cuatro tablas. Tras la ingesta de referencia: 1, 12, 17 y 2000. |
| 2. Ocurrencias ES+PT frente a lobo silvestre | `cargar_ocurrencias()` | Total del lote y subconjunto con `solo_lobo_silvestre=True` y `anio_min=2015`. Muestra 5 filas. |
| 3. Distribución territorial en España | `resumen_territorial_por_comunidad("ES")` | Las 10 primeras regiones por volumen y tipo de evidencia. |
| 4. Top 5 datasets | `top_datasets_publicadores(5)` | Datasets con más registros, organización y licencia. |
| 5. JSON nativo | `consultar_campos_raw_json(5)` | Hábitat, comentarios y primera foto leídos de `raw_json`. |

Si el bloque 1 muestra ceros, el esquema existe y la ingesta no se ha ejecutado (o se lanzó `guardar_en_sqlite.py` en lugar de `ingesta_gbif_sqlite.py`).

---

## 7. Cómo se lista

`consulta_gbif_sqlite.py` no se ejecuta solo. Cada función abre `gbif_biodiversidad.sqlite`, activa las claves foráneas y devuelve un `DataFrame`. Si el archivo no existe, lanza `FileNotFoundError` indicando que hay que ingestar antes.

Ejemplo mínimo, con el directorio de trabajo en `src/`:

```python
from consulta_gbif_sqlite import (
    obtener_resumen_general,
    cargar_ocurrencias,
    resumen_territorial_por_comunidad,
    top_datasets_publicadores,
    consultar_campos_raw_json,
)

obtener_resumen_general()
cargar_ocurrencias(paises=("ES", "PT"), solo_lobo_silvestre=True, anio_min=2015)
resumen_territorial_por_comunidad(pais="ES")
top_datasets_publicadores(limite=10)
consultar_campos_raw_json(limite=15)
```

| Función | Qué lista |
| :--- | :--- |
| `obtener_resumen_general()` | Conteo de `taxones`, `organizaciones`, `datasets` y `ocurrencias`. |
| `cargar_ocurrencias(paises=("ES", "PT"), solo_lobo_silvestre=False, anio_min=None)` | Ocurrencias con alias Darwin Core (`countryCode`, `decimalLatitude`, `scientificName`, …), título del dataset, organización, `url_imagen` y `num_media`. Orden: año descendente. Con `solo_lobo_silvestre=True` exige `specific_epithet = 'lupus'` y descarta `infraspecific_epithet = 'familiaris'`. |
| `resumen_territorial_por_comunidad(pais="ES")` | Región (`comunidad_gadm`, o `state_province` si falta, o `Sin asignar`) por `basis_of_record`, con total y rango de años. |
| `top_datasets_publicadores(limite=10)` | Ranking de datasets: título, organización, país de la organización, licencia y número de registros. |
| `consultar_campos_raw_json(limite=15)` | Filas con hábitat o multimedia. Extrae `$.habitat`, `$.eventRemarks` y `$.media[0].identifier`. |

La cláusula `country_code IN :paises` usa `bindparam("paises", expanding=True)` y una lista, igual que en `consulta_gbif.py` para MySQL. Así `IN` recibe un marcador por país.
