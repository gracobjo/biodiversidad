# Documentación Técnica: Pipeline ETL y Análisis Offline de Biodiversidad (GBIF + MySQL 8)

La variante local sin servidor está en [`documentacion_del_pipeline_gbif_y_sqlite.md`](./documentacion_del_pipeline_gbif_y_sqlite.md): creación del archivo, el fallo de certificado en la ingesta, la prueba de lectura y las consultas.

La base tiene que estar iniciada antes de poblarla o consultarla. En MySQL eso significa dos cosas: el servidor MySQL 8 está en marcha, y la base `gbif_biodiversidad` ya existe porque se ha aplicado `docs/schema_gbif.sql` o se ha pulsado Crear en la interfaz. Si el servidor está parado, Crear, Poblar y las consultas fallan y no se escribe nada.

## 1. Visión General y Arquitectura

El proyecto implementa una arquitectura **ETL (Extract, Transform, Load) + caché relacional local** para trabajar con datos de biodiversidad procedentes de la API pública de GBIF (*Global Biodiversity Information Facility*).

El flujo se divide en **dos fases desacopladas**:
1. **Fase A (Online / Ingesta):** Consulta los *endpoints* de taxonomía, ocurrencias y metadatos del *Registry* de GBIF y persiste la información de forma idempotente en una instancia local de **MySQL 8**.
2. **Fase B (Offline / Análisis):** Lee las tablas locales con SQLAlchemy ORM (`get_session` y `BiodiversidadRepository`). `consulta_gbif.py` traduce las entidades a `DataFrame` para filtrados taxonómicos, agregaciones territoriales, campos JSON y mapas `folium`, sin volver a llamar a la API.

---

## 2. Estructura del Proyecto

```text
biodiversidad/
├── .env                                   # DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME (no se versiona)
├── app_tkinter.py                         # Arranque de la ventana ORM: python app_tkinter.py
├── src/
│   ├── db_config.py                       # Lee .env y expone DB_CONFIG
│   ├── database.py                        # engine, SessionLocal y get_session()
│   ├── models.py                          # Taxon, Organizacion, Dataset, Ocurrencia
│   ├── repository.py                      # BiodiversidadRepository: upserts y consultas
│   ├── volcarEndpoints.py                 # Registry de GBIF y persistencia vía el repositorio
│   ├── consulta_gbif.py                   # Fachada pandas para los cuadernos
│   ├── gui_tk.py                          # Ventana: Consultar y Traer datos de GBIF
│   └── mapa_enlaces.py                    # Reenvía el clic del mapa al navegador
├── salidas_gbif_multiespecie/
│   └── mapa_ocurrencias_gbif.html
├── notebooks/ingesta_gbif_mysql.ipynb     # Fase A
├── notebooks/analisis_offline_gbif.ipynb  # Fase B
├── prueba_orm.py                          # Prueba de sesión y repositorio
└── pyproject.toml
```

La ventana se abre desde la raíz con `python app_tkinter.py`. Ese archivo solo añade `src/` al `sys.path` y llama a `lanzar_gui()`.

### Dependencias del entorno (`uv`)
* `requests` y `urllib3`: Peticiones HTTP con reintentos.
* `mysql-connector-python`: Driver de MySQL 8 usado por el dialecto `mysql+mysqlconnector`.
* `sqlalchemy`: ORM, sesión y `INSERT ... ON DUPLICATE KEY UPDATE`.
* `python-dotenv`: Carga de `.env`.
* `pandas`: Tablas de los cuadernos.
* `folium`: Mapas (OpenStreetMap y Esri).

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

La conexión MySQL ya no se abre con un `Engine` suelto ni con `pandas.read_sql`. El camino es siempre el mismo: `get_session()` entrega una `Session` y `BiodiversidadRepository` lee o escribe las entidades de `models.py`. Al salir del `with`, la sesión hace commit, o rollback si hay un error, y se cierra.

### 4.1. `src/db_config.py` y `.env`
`db_config.py` busca `.env` en la raíz del proyecto y rellena `DB_CONFIG` (`host`, `port`, `user`, `password`, `database`). Las claves del archivo son `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` y `DB_NAME`. La contraseña vive solo en `.env`, que no se versiona. El propio `db_config.py` sigue en `.gitignore`: un clon necesita ese archivo, que ya no guarda secretos, o hay que quitar esa línea del ignore. El cuaderno puede importar `DB_CONFIG` para mostrar el destino; la sesión ORM no recibe ese diccionario, lo lee ella misma.

### 4.2. `src/database.py`
Construye la URL `mysql+mysqlconnector://...` y el `engine` (`pool_pre_ping=True`). `SessionLocal` tiene `expire_on_commit=False` para poder usar las entidades después del commit. `get_session()` es el único context manager que deben usar cuadernos, `volcarEndpoints` y la ventana.

### 4.3. `src/models.py`
Cuatro entidades mapean las tablas de la sección 3:

| Clase | Tabla | Relaciones |
| :--- | :--- | :--- |
| `Taxon` | `taxones` | 1:N con `Ocurrencia` |
| `Organizacion` | `organizaciones` | 1:N con `Dataset` y con `Ocurrencia` |
| `Dataset` | `datasets` | N:1 con `Organizacion`; 1:N con `Ocurrencia` |
| `Ocurrencia` | `ocurrencias` | N:1 con taxón, dataset y organización. Las tres claves foráneas admiten `NULL` (`ON DELETE SET NULL`) |

`Ocurrencia` expone `url_primera_imagen`, `habitat_json` y `es_lobo_silvestre` a partir de `raw_json` y del epíteto, para no repetir esa lectura en la interfaz y en los cuadernos.

### 4.4. `src/repository.py`
`BiodiversidadRepository(session)` concentra la persistencia y las consultas.

Ingesta, idempotente con `INSERT ... ON DUPLICATE KEY UPDATE`:

* `upsert_taxon`, `upsert_organizaciones`, `upsert_datasets`.
* `upsert_ocurrencias` escribe en lotes de 250. Si una ocurrencia cita un `taxon_key`, un dataset o una organización que no está en el catálogo, esa clave se deja vacía y el registro se inserta igual, o se actualiza si la ocurrencia ya existía. El aviso sale en una sola línea, sin el volcado SQL de la clave foránea.

Consultas:

* `resumen_conteo_tablas`, `conteo_por_comunidad`, `resumen_territorial`, `top_datasets_publicadores`.
* `contar_ocurrencias` usa el mismo filtro que `buscar_ocurrencias` y no aplica el límite de la tabla. La ventana lo usa para separar las filas cargadas del total («200 de 3.637», por ejemplo).
* `buscar_ocurrencias` ordena solo `occurrence_key` (y año o provincia). Después carga las entidades por lotes de 500, sin `ORDER BY` y sin el `raw_json` de taxón, dataset y organización. Así MySQL no desborda el búfer de ordenación (error 1038) cuando el JSON de la ocurrencia viaja en la fila.
* `muestras_con_media_o_habitat` selecciona primero las claves que tienen `$.media` o `$.habitat` y reutiliza esa carga por claves.
* `listar_taxones` y `listar_comunidades` alimentan los filtros de la ventana.

### 4.5. `src/volcarEndpoints.py`
`guardar_en_mysql(...)` sigue siendo la función que llaman el cuaderno de ingesta y `servicio_bd`. Descarga una vez cada organización y cada dataset del Registry, anula `publishingOrganizationKey` si esa organización no se ha guardado, y dentro de `get_session()` llama al repositorio: taxón, organizaciones, datasets y ocurrencias. El argumento `db_config` se conserva para no romper las llamadas antiguas; la sesión usa `.env`.

### 4.6. `src/consulta_gbif.py`
Fachada para los cuadernos. Cada función abre `get_session()`, pide los datos al repositorio y devuelve un `DataFrame` con alias Darwin Core (`decimalLatitude`, `scientificName`, `basisOfRecord`, `gbif_url`) más `dataset_title`, `publishing_org_title`, `url_imagen` y `num_media`.

* `obtener_resumen_general()`
* `cargar_ocurrencias(paises, solo_lobo_silvestre, anio_min, comunidad)`
* `resumen_territorial_por_comunidad(pais)`
* `top_datasets_publicadores(limite)`
* `consultar_campos_raw_json(limite)`

`solo_lobo_silvestre=True` deja `specific_epithet = lupus` y excluye `infraspecific_epithet = familiaris`.

### 4.7. `app_tkinter.py` y `src/gui_tk.py`
`app_tkinter.py` abre la ventana «Biodiversidad GBIF». Al arrancar consulta MySQL y muestra la tabla.

* **Consultar:** filtros de especie, país, año y comunidad. El contador distingue las filas cargadas del total del filtro (`contar_ocurrencias`). La ficha de la derecha resume la fila; si el epíteto es `familiaris`, avisa de que es perro doméstico. Doble clic abre la ficha en GBIF. «Ver mapa» y «Exportar CSV» usan las filas que están en pantalla y dejan el HTML y el CSV en `salidas_gbif_multiespecie/`.
* **Traer datos de GBIF:** resuelve el taxón, pagina `/v1/occurrence/search` con barra de progreso y botón Cancelar, y hace el mismo upsert que `guardar_en_mysql`. Si se cancela antes de guardar, no escribe. Al terminar refresca los conteos y la consulta.

La otra ventana, `interfaz_gbif.py`, sigue sirviendo para SQLite, el catálogo por clases y la exportación. Cuando toca MySQL, también acaba en `guardar_en_mysql` y en `consulta_gbif`, o sea en el ORM.

### 4.8. `src/mapa_enlaces.py`
`activar_enlaces_externos(mapa)` añade al mapa un script que, dentro del iframe del cuaderno, reenvía el clic de la ficha o de la foto al documento del cuaderno. El visor de Jupyter no deja que ese iframe abra GBIF. El HTML guardado en `salidas_gbif_multiespecie/` no necesita el reenvío: el enlace abre el navegador por sí solo.

---

## 5. Cuadernos Jupyter y Scripts Ejecutables

### 5.1. `ingesta_gbif_mysql.ipynb` (Fase A: Ingesta)
Cuaderno paramétrico para poblar la base de datos:
1. **Configuración:** Define `ESPECIE_OBJETIVO` (ej. `"Canis lupus"`), `PAISES` (`["ES", "PT"]`), `YEAR_RANGE` (`"2000,2026"`), `HAS_COORDINATE` y `MAX_REGISTROS_POR_PAIS`.
2. **Descarga paginada:** Utiliza `requests.Session` con `Retry` para resolver el `taxonKey` y recorrer `/v1/occurrence/search` en páginas de `PAGE_SIZE = 300`.
3. **Volcado:** Llama a `guardar_en_mysql(...)`, que persiste con el repositorio ORM. Si el catálogo ya existe y alguna ocurrencia cita un taxón que no está en `taxones`, la clave se deja vacía y la carga continúa.
4. **Verificación:** Un `GROUP BY` sobre `ocurrencias` comprueba los totales por país y rango. Esa lectura de control usa `pandas.read_sql`. La escritura ya se hizo en el paso anterior, con el repositorio.

### 5.2. `analisis_offline_gbif.ipynb` (Fase B: Análisis Offline)
Cuaderno de exploración que opera 100 % contra MySQL sin llamadas a internet:
1. **Estado de la BD:** Verifica los totales en cada tabla con `obtener_resumen_general()`.
2. **Carga en DataFrame:** Invoca `cargar_ocurrencias()` para comparar el total de registros frente al subconjunto filtrado de lobo silvestre.
3. **Análisis territorial y fuentes:** Muestra la distribución por comunidades autónomas y los principales datasets publicadores.
4. **Inspección JSON:** Extrae enlaces a fotografías y comentarios de campo almacenados en `raw_json`.
5. **Mapa interactivo (`Folium`):**
   * Crea el directorio `salidas_gbif_multiespecie/` y exporta el mapa a `salidas_gbif_multiespecie/mapa_ocurrencias_gbif.html`.
   * Incluye capas base gratuitas sin API key (**OpenStreetMap**, **Esri World Imagery** y **Esri World Street Map**).
   * Los marcadores con fotografía van en rojo y los que no tienen multimedia, en verde. El popup lleva la miniatura, `url_imagen` y `gbif_url`. `activar_enlaces_externos` hace que ese clic funcione dentro del cuaderno.

### 5.3. `prueba_lectura_mysql.py`
Script de consola para ejecutar de forma rápida la batería de pruebas de lectura sobre todas las funciones de `src/consulta_gbif.py`.

---

## 6. Notas Técnicas y Solución de Problemas Resueltos

1. **Ruta de `src/` en el cuaderno:** El directorio de trabajo puede ser la raíz o `notebooks/`. Se resuelve `Path` a `src` y después se llama a `.resolve()`. Encadenar `/"src".resolve()` falla porque `resolve` no existe en una cadena.
2. **La sesión es la conexión de la aplicación:** `consulta_gbif` y `guardar_en_mysql` abren `get_session()`. Si el kernel ya importó `repository`, hay que volver a ejecutar la primera celda: los cuadernos de ingesta y de análisis offline recargan el módulo. La celda de verificación del cuaderno de ingesta sigue haciendo un `GROUP BY` con `pandas.read_sql`; esa consulta no escribe.
3. **Error 1452 (`fk_occ_taxon`):** No significa que la ocurrencia esté duplicada. El `ON DUPLICATE KEY UPDATE` ya cubre la clave primaria. El fallo es una clave foránea: la búsqueda de *Canis lupus* trae registros de taxones relacionados, por ejemplo *Canis familiaris* (`taxon_key` 5219200), que no se insertaron en `taxones`. `upsert_ocurrencias` deja esa clave vacía y guarda el registro.
4. **Error 1038 (Out of sort memory):** Un `ORDER BY` que arrastra `raw_json` no cabe en el búfer de ordenación. `buscar_ocurrencias` ordena solo las claves y luego carga las filas por lotes.
5. **Fichas GBIF en el mapa del cuaderno:** El mapa embebido vive en un iframe que no abre ventanas. `mapa_enlaces.activar_enlaces_externos` reenvía el clic. El HTML de `salidas_gbif_multiespecie/` se abre en el navegador y el enlace funciona sin ese puente.