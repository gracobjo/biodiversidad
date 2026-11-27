# Documentación Técnica: Pipeline ETL y Análisis Offline de Biodiversidad (GBIF + MySQL 8)

La variante local sin servidor está en [`documentacion_del_pipeline_gbif_y_sqlite.md`](./documentacion_del_pipeline_gbif_y_sqlite.md): creación del archivo, el fallo de certificado en la ingesta, la prueba de lectura y las consultas.

La base tiene que estar iniciada antes de poblarla o consultarla. En MySQL eso significa dos cosas: el servidor MySQL 8 está en marcha, y la base `gbif_biodiversidad` ya existe porque se ha aplicado `docs/schema_gbif.sql` o se ha pulsado Crear en la interfaz. Si el servidor está parado, Crear, Poblar y las consultas fallan y no se escribe nada.

## 1. Visión General y Arquitectura

El proyecto implementa una arquitectura **ETL (Extract, Transform, Load) + caché relacional local** para trabajar con datos de biodiversidad procedentes de la API pública de GBIF (*Global Biodiversity Information Facility*).

El flujo se divide en **dos fases desacopladas**:
1. **Fase A (Online / Ingesta):** Consulta los *endpoints* de taxonomía, ocurrencias y metadatos del *Registry* de GBIF y persiste la información de forma idempotente en una instancia local de **MySQL 8**.
2. **Fase B (Offline / Análisis):** Lee las tablas locales con SQLAlchemy ORM (`get_session` y `BiodiversidadRepository`). `consulta_gbif.py` traduce las entidades a `DataFrame` para filtrados taxonómicos, agregaciones territoriales, campos JSON y mapas `folium`. `src/kpis/` calcula los indicadores de la misma base. Ninguna de las dos vías vuelve a llamar a la API.

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
│   ├── gui_tk.py                          # Ventana: Consultar, Indicadores y Traer datos de GBIF
│   ├── mapa_enlaces.py                    # Reenvía el clic del mapa al navegador
│   ├── kpis/                              # Indicadores ORM, un módulo por tema
│   │   ├── filtros.py                     # FiltroKpi, el mismo recorte que la ventana
│   │   ├── volumen.py                     # País, año, mes
│   │   ├── territorio.py                  # Comunidad, provincia, municipio
│   │   ├── cobertura.py                   # Porcentaje de filas con cada campo
│   │   ├── evidencia.py                   # Evidencia, vitalidad, sexo, fase vital
│   │   ├── taxonomia.py                   # Lobo, perro y fichas
│   │   ├── calidad.py                     # Foto, hábitat e incertidumbre
│   │   ├── publicadores.py                # Datasets, organizaciones, registradores
│   │   ├── vista.py                       # Filas de la pestaña Indicadores
│   │   └── salida.py                      # Impresión compartida de los lanzadores
│   ├── kpi_volumen.py                     # Lanzador de consola
│   ├── kpi_territorio.py
│   ├── kpi_cobertura.py
│   ├── kpi_evidencia.py
│   ├── kpi_taxonomia.py
│   ├── kpi_calidad.py
│   └── kpi_publicadores.py
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
* `contar_ocurrencias` usa el mismo filtro que `buscar_ocurrencias` y no aplica el límite de la tabla. Acepta cualquier país, `anio_max` y, para un día concreto, `fecha_desde` y `fecha_hasta`. Sin países, no filtra por país. La ventana lo usa para separar las filas cargadas del total.
* `buscar_ocurrencias` ordena solo `occurrence_key` (y año o provincia). Después carga las entidades por lotes de 500, sin `ORDER BY` y sin el `raw_json` de taxón, dataset y organización. Así MySQL no desborda el búfer de ordenación (error 1038) cuando el JSON de la ocurrencia viaja en la fila.
* `muestras_con_media_o_habitat` selecciona primero las claves que tienen `$.media` o `$.habitat` y reutiliza esa carga por claves.
* `listar_paises`, `listar_taxones` y `listar_comunidades` alimentan los filtros de la ventana. `listar_comunidades` sin países devuelve las comunidades de toda la base.

### 4.5. `src/volcarEndpoints.py`
`guardar_en_mysql(...)` sigue siendo la función que llaman el cuaderno de ingesta y `servicio_bd`. Descarga una vez cada organización y cada dataset del Registry, anula `publishingOrganizationKey` si esa organización no se ha guardado, y dentro de `get_session()` llama al repositorio: taxón, organizaciones, datasets y ocurrencias. El argumento `db_config` se conserva para no romper las llamadas antiguas; la sesión usa `.env`.

### 4.6. `src/consulta_gbif.py`
Fachada para los cuadernos. Cada función abre `get_session()`, pide los datos al repositorio y devuelve un `DataFrame` con alias Darwin Core (`decimalLatitude`, `scientificName`, `basisOfRecord`, `gbif_url`) más `dataset_title`, `publishing_org_title`, `url_imagen` y `num_media`.

* `obtener_resumen_general()`
* `cargar_ocurrencias(paises, solo_lobo_silvestre, anio_min, anio_max, fecha_desde, fecha_hasta, taxon_key)`. `paises=None` no filtra por país. Un año concreto es `anio_min` y `anio_max` iguales. Un intervalo de fechas usa `datetime.date` en `fecha_desde` y `fecha_hasta`.
* `resumen_territorial_por_comunidad(pais)`
* `top_datasets_publicadores(limite)`
* `consultar_campos_raw_json(limite)`

`solo_lobo_silvestre=True` deja `specific_epithet = lupus` y excluye `infraspecific_epithet = familiaris`.

### 4.7. `app_tkinter.py` y `src/gui_tk.py`
`app_tkinter.py` abre la ventana «Biodiversidad GBIF». Al arrancar consulta MySQL y muestra la tabla.

* **Consultar:** filtros de especie, país (cualquier código ISO, varios a la vez, o Todos), comunidad y tiempo. El tiempo puede ser un año (`2018` en Desde y en Hasta), un intervalo de años (`2010` y `2018`) o un intervalo de fechas (`2018-03-01` y `2018-06-30`). Hasta vacío llega hasta hoy. El contador distingue las filas cargadas del total del filtro (`contar_ocurrencias`). La ficha de la derecha resume la fila; si el epíteto es `familiaris`, avisa de que es perro doméstico. Doble clic abre la ficha en GBIF. «Ver mapa» y «Exportar CSV» usan las filas que están en pantalla y dejan el HTML y el CSV en `salidas_gbif_multiespecie/`.
* **Indicadores:** al abrir la pestaña calcula el volumen de toda la base. A la izquierda están Volumen, Territorio, Cobertura de campos, Evidencia y estado, Taxonomía, Calidad del registro y Quién publica. País en Todos, fechas vacías y «Todas las especies» no recortan. El tiempo usa las mismas reglas que Consultar, y «Excluir perro doméstico» solo aparece si la especie es todas o *Canis lupus*. La línea inferior dice cuántos registros entran en el filtro. `src/kpis/vista.py` prepara las filas; la ventana no llama a GBIF ni escribe en MySQL.
* **Traer datos de GBIF:** los mismos países y las mismas fechas. Resuelve el taxón, pagina `/v1/occurrence/search` con barra de progreso y botón Cancelar, y hace el mismo upsert que `guardar_en_mysql`. Si se cancela antes de guardar, no escribe. Al terminar refresca los conteos y la consulta.

La otra ventana, `interfaz_gbif.py`, sigue sirviendo para SQLite, el catálogo por clases y la exportación. Cuando toca MySQL, también acaba en `guardar_en_mysql` y en `consulta_gbif`, o sea en el ORM.

### 4.8. `src/mapa_enlaces.py`
`activar_enlaces_externos(mapa)` añade al mapa un script que, dentro del iframe del cuaderno, reenvía el clic de la ficha o de la foto al documento del cuaderno. El visor de Jupyter no deja que ese iframe abra GBIF. El HTML guardado en `salidas_gbif_multiespecie/` no necesita el reenvío: el enlace abre el navegador por sí solo.

### 4.9. Indicadores (`src/kpis/` y `src/kpi_*.py`)

Los indicadores leen MySQL ya cargada. No llaman a GBIF y no escriben en la base. La pestaña Indicadores los muestra con `src/kpis/vista.py`. Cada función de consulta recibe una `Session` de `get_session()` y, si hace falta acotar, un `FiltroKpi`. Sin filtro miden toda la base: la pestaña nace con País en Todos, fechas vacías y todas las especies, y no hereda el país ni el año de Consultar.

Un conteo de ocurrencias mide esfuerzo de publicación. No es abundancia, densidad ni tamaño de población. El año en curso está incompleto y no se compara con un año cerrado.

`FiltroKpi` (`src/kpis/filtros.py`) reutiliza `BiodiversidadRepository._filtros_ocurrencias`, así que el recorte es el de Consultar:

| Campo | Efecto si se rellena |
| :--- | :--- |
| `paises` | Uno o varios códigos ISO (`("ES",)` o `("ES", "PT")`). Vacío: todos los países de la base. |
| `anio_min`, `anio_max` | Año o intervalo de años. El mismo valor en los dos deja solo ese año. Incluye registros de ese año aunque falten mes o día. |
| `fecha_desde`, `fecha_hasta` | `datetime.date`. Si hay alguna de las dos, los años no se aplican además. |
| `comunidad` | Nombre GADM de nivel 1. |
| `taxon_key` | Una ficha concreta. |
| `solo_lobo_silvestre` | Por defecto `False`, así el perro doméstico sigue en el total. `True` deja `specific_epithet = lupus` y excluye el epíteto infraespecífico `familiaris`. |

Las funciones devuelven dataclasses, no `DataFrame`. El porcentaje de un `Conteo` es sobre el total del recorte, salvo donde la tabla de abajo dice otra cosa.

| Módulo | Función | Qué devuelve |
| :--- | :--- | :--- |
| `volumen` | `por_pais`, `por_anio`, `por_pais_y_anio` | Registros por país, por año y la serie país-año. |
| `volumen` | `por_mes` | Enero a diciembre. El porcentaje es entre las filas que traen mes. |
| `territorio` | `por_comunidad`, `por_provincia`, `por_municipio` | GADM nivel 1, 2 y municipio. `por_municipio` devuelve 30 filas. `por_provincia` acepta `limite`. El porcentaje de un ranking recortado se calcula sobre el total filtrado, así que esas filas no suman 100. |
| `cobertura` | `cobertura_campos` | Filas con valor y porcentaje, para año, mes, día, coordenadas, incertidumbre, comunidad, provincia, municipio, tipo de evidencia, vitalidad, sexo, fase vital, individuos, quién registró, licencia, taxón enlazado, fotografía (`$.media`) y hábitat (`$.habitat`). |
| `evidencia` | `por_evidencia`, `por_vitalidad`, `por_sexo`, `por_fase_vital` | Reparto de `basis_of_record`, `vitality`, `sex` y `life_stage`. La categoría «Sin dato» entra en el porcentaje. |
| `evidencia` | `individuos_declarados` | Cuántas filas traen `individual_count`, su suma y la media de esas filas. La suma no es un censo. |
| `taxonomia` | `lobo_y_perro` | Lobo (`lupus` y el infraespecífico no es `familiaris`), perro (`familiaris` en el epíteto específico o en el infraespecífico) y el resto. |
| `taxonomia` | `por_taxon`, `sin_taxon_en_catalogo` | Registros por `taxon_key`, y cuántas ocurrencias se quedaron sin ficha en `taxones`. |
| `taxonomia` | `taxones_sin_ocurrencias` | Fichas del catálogo sin ninguna ocurrencia. No usa el filtro. |
| `calidad` | `fotos_y_habitat` | Registros con al menos una imagen o con hábitat en `raw_json`. |
| `calidad` | `bandas_incertidumbre` | Mediana en metros (solo filas con dato) y bandas: sin dato, hasta 100 m, de 100 m a 1 km, de 1 km a 10 km, más de 10 km. Las bandas suman el total filtrado. |
| `publicadores` | `por_dataset` | Ranking de datasets con licencia, DOI, tipo y organización. El porcentaje es sobre todas las ocurrencias filtradas, también si se pasa `limite`. |
| `publicadores` | `catalogo_datasets` | Cuatro números del catálogo: datasets, con licencia, con DOI y con tipo. No depende del filtro de ocurrencias. |
| `publicadores` | `por_organizacion` | Institución publicadora. El país es el de la institución, no el del avistamiento. |
| `publicadores` | `pais_publicador_y_pais_avistamiento` | Cruce del país de la organización con `country_code`. |
| `publicadores` | `top_registradores` | Los 20 textos de `recorded_by` con más registros. El campo no está normalizado: la misma persona puede salir en varias filas. El porcentaje es sobre el total filtrado. |

Estas consultas usan `JSON_EXTRACT` y `JSON_LENGTH` de MySQL 8. No están portadas a SQLite.

Para verlas en consola, el directorio de trabajo es `src/` (ahí resuelven `database` y `kpis`):

```powershell
cd src
..\.venv\Scripts\python.exe kpi_volumen.py
..\.venv\Scripts\python.exe kpi_territorio.py
..\.venv\Scripts\python.exe kpi_cobertura.py
..\.venv\Scripts\python.exe kpi_evidencia.py
..\.venv\Scripts\python.exe kpi_taxonomia.py
..\.venv\Scripts\python.exe kpi_calidad.py
..\.venv\Scripts\python.exe kpi_publicadores.py
```

`python -m kpis.volumen`, desde la misma carpeta, imprime país, año y mes. El lanzador `kpi_volumen.py` añade la serie país-año.

Dentro de otro programa el filtro se pasa en la llamada. Este ejemplo deja solo España en 2018:

```python
from database import get_session
from kpis import FiltroKpi
from kpis.territorio import por_comunidad

with get_session() as session:
    filas = por_comunidad(session, FiltroKpi(paises=("ES",), anio_min=2018, anio_max=2018))
```

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

### 5.4. Indicadores en la ventana y por consola
La pestaña Indicadores de `python app_tkinter.py` es la vía habitual. Al entrar muestra el volumen; el resto de temas se elige en la lista. País, fechas y especie están en la propia pestaña.

Cada `src/kpi_*.py` abre `get_session()`, llama a las funciones de su módulo en `src/kpis/` e imprime el mismo resultado. Con el entorno activado, desde la raíz: `python src\kpi_volumen.py` (y el mismo patrón para territorio, cobertura, evidencia, taxonomía, calidad y publicadores). Sin cambios miden toda la base. Para un país o un año se edita el `FiltroKpi` dentro de `main()`, como en la sección 4.9. Hace falta MySQL en marcha, la base `gbif_biodiversidad` cargada y `.env` en la raíz.

---

## 6. Notas Técnicas y Solución de Problemas Resueltos

1. **Ruta de `src/` en el cuaderno:** El directorio de trabajo puede ser la raíz o `notebooks/`. Se resuelve `Path` a `src` y después se llama a `.resolve()`. Encadenar `/"src".resolve()` falla porque `resolve` no existe en una cadena.
2. **La sesión es la conexión de la aplicación:** `consulta_gbif` y `guardar_en_mysql` abren `get_session()`. Si el kernel ya importó `repository`, hay que volver a ejecutar la primera celda: los cuadernos de ingesta y de análisis offline recargan el módulo. La celda de verificación del cuaderno de ingesta sigue haciendo un `GROUP BY` con `pandas.read_sql`; esa consulta no escribe.
3. **Error 1452 (`fk_occ_taxon`):** No significa que la ocurrencia esté duplicada. El `ON DUPLICATE KEY UPDATE` ya cubre la clave primaria. El fallo es una clave foránea: la búsqueda de *Canis lupus* trae registros de taxones relacionados, por ejemplo *Canis familiaris* (`taxon_key` 5219200), que no se insertaron en `taxones`. `upsert_ocurrencias` deja esa clave vacía y guarda el registro.
4. **Error 1038 (Out of sort memory):** Un `ORDER BY` que arrastra `raw_json` no cabe en el búfer de ordenación. `buscar_ocurrencias` ordena solo las claves y luego carga las filas por lotes.
5. **Fichas GBIF en el mapa del cuaderno:** El mapa embebido vive en un iframe que no abre ventanas. `mapa_enlaces.activar_enlaces_externos` reenvía el clic. El HTML de `salidas_gbif_multiespecie/` se abre en el navegador y el enlace funciona sin ese puente.