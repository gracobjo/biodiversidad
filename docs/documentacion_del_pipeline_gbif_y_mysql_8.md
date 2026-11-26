# Documentación Técnica: Pipeline ETL y Análisis Offline de Biodiversidad (GBIF + MySQL 8)

La variante local sin servidor está en [`documentacion_del_pipeline_gbif_y_sqlite.md`](./documentacion_del_pipeline_gbif_y_sqlite.md): creación del archivo, el fallo de certificado en la ingesta, la prueba de lectura y las consultas.

## 1. Visión General y Arquitectura

El proyecto implementa una arquitectura **ETL (Extract, Transform, Load) + caché relacional local** para trabajar con datos de biodiversidad procedentes de la API pública de GBIF (*Global Biodiversity Information Facility*).

El flujo se divide en **dos fases desacopladas**:
1. **Fase A (Online / Ingesta):** Consulta los *endpoints* de taxonomía, ocurrencias y metadatos del *Registry* de GBIF y persiste la información de forma idempotente en una instancia local de **MySQL 8**.
2. **Fase B (Offline / Análisis):** Lee los datos directamente desde la base de datos local mediante `SQLAlchemy` y `pandas` para realizar filtrados taxonómicos, agregaciones territoriales, consultas sobre campos JSON nativos y generación de mapas interactivos con `folium`, sin depender de conexión a internet ni de límites de velocidad de la API.

---

## 2. Estructura del Proyecto

```text
biodiversidad/
├── src/                                   # Marcado como Sources Root en PyCharm
│   ├── db_config.py                       # Credenciales de conexión a MySQL (excluido en .gitignore)
│   ├── volcarEndpoints.py                 # Lógica de descarga de catálogos e inserción idempotente en MySQL
│   └── consulta_gbif.py                   # Capa de acceso a datos (SQLAlchemy + consultas parametrizadas)
├── salidas_gbif_multiespecie/             # Carpeta generada automáticamente para exportaciones HTML
│   └── mapa_ocurrencias_gbif.html         # Mapa interactivo generado con Folium
├── schema_gbif.sql                        # Script DDL de creación de la base de datos y tablas en MySQL 8
├── notebooks/ingesta_gbif_mysql.ipynb     # Cuaderno Fase A: Descarga desde API GBIF y volcado a MySQL
├── notebooks/analisis_offline_gbif.ipynb  # Cuaderno Fase B: Exploración offline, SQL/JSON y mapas Folium
├── prueba_lectura_mysql.py                # Script CLI de validación de consultas contra MySQL
├── pyproject.toml                         # Dependencias gestionadas con uv
└── DOCUMENTACION_PIPELINE_GBIF.md         # Este documento
```

### Dependencias del entorno (`uv`)
* `requests` y `urllib3`: Peticiones HTTP con política de reintentos automáticos (*backoff*).
* `mysql-connector-python`: Driver oficial de conexión a MySQL 8.
* `sqlalchemy`: Motor de conexión recomendado para interoperabilidad con `pandas.read_sql()`.
* `pandas`: Manipulación y análisis tabular.
* `folium`: Generación de mapas interactivos sin necesidad de API Keys (OpenStreetMap + Esri).

---

## 3. Diseño de la Base de Datos (`schema_gbif.sql`)

La base de datos `gbif_biodiversidad` utiliza el conjunto de caracteres `utf8mb4` (`utf8mb4_unicode_ci`) y motor `InnoDB` con integridad referencial.

### Mapeo de *Endpoints* de GBIF a Tablas Relacionales

| Tabla MySQL | *Endpoint* GBIF | Clave Primaria (PK) | Claves Foráneas (FK) y Propósito |
| :--- | :--- | :--- | :--- |
| **`taxones`** | `/v1/species/match` | `taxon_key` (`INT`) | Jerarquía taxonómica (`kingdom` hasta `species`), rango y estado taxonómico. |
| **`organizaciones`** | `/v1/organization/{key}` | `organization_key` (`CHAR(36)`) | Instituciones publicadoras (`title`, `country`, `city`, coordenadas, `homepage`). |
| **`datasets`** | `/v1/dataset/{key}` | `dataset_key` (`CHAR(36)`) | **FK:** `organization_key`. Conjuntos de datos (`title`, `dataset_type`, `license`, `doi`). |
| **`ocurrencias`** | `/v1/occurrence/search` | `occurrence_key` (`BIGINT`) | **FK:** `taxon_key`, `dataset_key`, `organization_key`. Registros Darwin Core georreferenciados + índices de búsqueda. |

### Estrategia Híbrida Relacional + JSON Nativo (`raw_json`)
Todas las tablas incorporan una columna **`raw_json JSON`** que almacena la respuesta íntegra devuelta por la API de GBIF. Esto permite:
* Consultar con alta velocidad los campos normalizados e indexados (`country_code`, `year`, `comunidad_gadm`, `specific_epithet`, `basis_of_record`).
* Extraer dinámicamente atributos no normalizados (como fotografías en `$.media[0].identifier` o `$.habitat`) mediante `JSON_EXTRACT()` sin alterar el esquema de tablas.

---

## 4. Descripción de los Módulos Python (`src/`)

### 4.1. `src/db_config.py`
Centraliza el diccionario `DB_CONFIG` con los parámetros de conexión (`host`, `port`, `user`, `password`, `database`). Debe mantenerse en `.gitignore` para no exponer credenciales en el control de versiones.

### 4.2. `src/volcarEndpoints.py`
Contiene la función principal `guardar_en_mysql(...)`, encargada de la persistencia:
1. **Inserta/actualiza el taxón** en `taxones`.
2. **Extrae los UUID únicos** (`publishingOrgKey` y `datasetKey`) presentes en los registros descargados, consulta `/v1/organization/{uuid}` y `/v1/dataset/{uuid}` una sola vez por identificador y los guarda en `organizaciones` y `datasets`.
3. **Inserta en lote las ocurrencias** (`executemany`) respetando el orden de claves foráneas.
4. **Idempotencia:** Utiliza `INSERT INTO ... ON DUPLICATE KEY UPDATE`, permitiendo reejecutar ingestas para ampliar años, añadir países o actualizar registros sin duplicar claves primarias.

### 4.3. `src/consulta_gbif.py`
Proporciona la capa de acceso a datos para los cuadernos y scripts de análisis:
* `crear_engine_gbif()` y `obtener_engine()`: Crea y libera de forma segura el motor `SQLAlchemy` usando `URL.create(drivername="mysql+mysqlconnector", ...)`.
* `obtener_resumen_general()`: Devuelve el conteo de filas de las 4 tablas.
* `cargar_ocurrencias(paises, solo_lobo_silvestre, anio_min)`:
  * Devuelve un `DataFrame` con alias compatibles con Darwin Core (`decimalLatitude`, `scientificName`, `basisOfRecord`, `gbif_url`, etc.) enriquecido con `dataset_title` y `publishing_org_title`.
  * Extrae directamente desde `raw_json` la URL de la primera imagen (`url_imagen`) y el contador de archivos multimedia (`num_media`).
  * Cuando `solo_lobo_silvestre=True`, filtra `specific_epithet = 'lupus'` excluyendo `infraspecific_epithet = 'familiaris'` (perro doméstico).
* `resumen_territorial_por_comunidad(pais)`: Agrupa registros por región GADM (`comunidad_gadm`) y tipo de evidencia (`basis_of_record`).
* `top_datasets_publicadores(limite)`: Ranking de datasets y organizaciones según el volumen de registros en la base de datos.
* `consultar_campos_raw_json(limite)`: Consulta directa sobre campos JSON (`$.habitat`, `$.eventRemarks`, `$.media`).

---

## 5. Cuadernos Jupyter y Scripts Ejecutables

### 5.1. `ingesta_gbif_mysql.ipynb` (Fase A: Ingesta)
Cuaderno paramétrico para poblar la base de datos:
1. **Configuración:** Define `ESPECIE_OBJETIVO` (ej. `"Canis lupus"`), `PAISES` (`["ES", "PT"]`), `YEAR_RANGE` (`"2000,2026"`), `HAS_COORDINATE` y `MAX_REGISTROS_POR_PAIS`.
2. **Descarga paginada:** Utiliza `requests.Session` con `Retry` para resolver el `taxonKey` y recorrer `/v1/occurrence/search` en páginas de `PAGE_SIZE = 300`.
3. **Volcado:** Llama a `guardar_en_mysql(...)` para almacenar taxón, organizaciones, datasets y ocurrencias.
4. **Verificación:** Ejecuta un `GROUP BY` sobre `ocurrencias` para validar los totales cargados por país y rango taxonómico.

### 5.2. `analisis_offline_gbif.ipynb` (Fase B: Análisis Offline)
Cuaderno de exploración que opera 100 % contra MySQL sin llamadas a internet:
1. **Estado de la BD:** Verifica los totales en cada tabla con `obtener_resumen_general()`.
2. **Carga en DataFrame:** Invoca `cargar_ocurrencias()` para comparar el total de registros frente al subconjunto filtrado de lobo silvestre.
3. **Análisis territorial y fuentes:** Muestra la distribución por comunidades autónomas y los principales datasets publicadores.
4. **Inspección JSON:** Extrae enlaces a fotografías y comentarios de campo almacenados en `raw_json`.
5. **Mapa interactivo (`Folium`):**
   * Crea el directorio `salidas_gbif_multiespecie/` y exporta el mapa a `salidas_gbif_multiespecie/mapa_ocurrencias_gbif.html`.
   * Incluye capas base gratuitas sin API key (**OpenStreetMap**, **Esri World Imagery** y **Esri World Street Map**).
   * Diferencia visualmente los marcadores con fotografía (**rojo**) de los registros sin multimedia (**verde**), incrustando en el *popup* la miniatura de la imagen, el enlace directo a la fotografía original (`url_imagen`) y el enlace a la ficha de GBIF (`gbif_url`).

### 5.3. `prueba_lectura_mysql.py`
Script de consola para ejecutar de forma rápida la batería de pruebas de lectura sobre todas las funciones de `src/consulta_gbif.py`.

---

## 6. Notas Técnicas y Solución de Problemas Resueltos

1. **Resolución de rutas en PyCharm:** La carpeta `src/` se marcó como *Sources Root* (`Mark Directory as -> Sources Root`) para que el analizador estático del IDE reconozca las importaciones de `volcarEndpoints`, `db_config` y `consulta_gbif` sin errores de referencia.
2. **Compatibilidad de `pandas.read_sql` con MySQL:** Se sustituyó la conexión directa de `mysql.connector` por un motor `SQLAlchemy` (`mysql+mysqlconnector`) para eliminar los avisos `UserWarning` de `pandas`.
3. **Expansión de listas en cláusulas `IN`:** Dado que `mysql-connector-python` no convierte tuplas nativas en cláusulas `IN :paises`, se configuró `text(sql).bindparams(bindparam("paises", expanding=True))` pasando `list(paises)`.
4. **Apertura de enlaces externos desde mapas Folium:** Los visores *sandboxed* de Jupyter/PyCharm bloquean enlaces externos (`target="_blank"`) dentro del `iframe` del cuaderno mostrando una pantalla en blanco. Exportar el mapa a `salidas_gbif_multiespecie/mapa_ocurrencias_gbif.html` permite abrirlo directamente en el navegador web con plena funcionalidad de enlaces y miniaturas.