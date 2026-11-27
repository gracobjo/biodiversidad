# Diagramas UML

Los diagramas describen el sistema tal como está en `app_tkinter.py`, `interfaz_gbif.py`, `src/` y `notebooks/`. MySQL se lee y se escribe con las entidades de `models.py` y `BiodiversidadRepository`. SQLite sigue en funciones y `DataFrame`. Los requisitos y los casos de uso están en [ESPECIFICACION_REQUISITOS.md](./ESPECIFICACION_REQUISITOS.md) y [CASOS_DE_USO.md](./CASOS_DE_USO.md).

## 1. Casos de uso

```mermaid
flowchart LR
  inv[Persona investigadora]
  ana[Persona analista]
  ing[Persona ingeniera de datos]
  gbif[API GBIF]
  mysql[MySQL 8]

  inv --> CU01[CU-01 Explorar especie en España]
  inv --> CU04[CU-04 Catálogo ibérico]
  inv --> CU06[CU-06 Comparar especies]
  inv --> CU12[CU-12 Exportar tabla y mapa]
  inv --> CU14[CU-14 Ver especies de varias clases]
  ana --> CU03[CU-03 Separar lobo y perro]
  ana --> CU11[CU-11 Filtrar ocurrencias]
  ana --> CU10[CU-10 Analizar sin red]
  ana --> CU13[CU-13 Validar la muestra]
  ing --> CU08[CU-08 Poblar SQLite]
  ing --> CU09[CU-09 Poblar MySQL]
  ing --> CU07[CU-07 Guardar lote multi-especie]

  CU01 --> gbif
  CU04 --> gbif
  CU06 --> gbif
  CU14 --> gbif
  CU08 --> gbif
  CU09 --> gbif
  CU09 --> mysql
  CU07 --> mysql
```

## 2. Componentes

```mermaid
flowchart TB
  subgraph cuadernos [notebooks]
    n01[01 Canis lupus España, mortalidad]
    n02[02 catálogo especies ES+PT]
    n03[03 Canis lupus altitud]
    n04[04 archivo catálogo ES+PT]
    multi[multi-especie CSV y mapas]
    clases[especies por clase]
    multibd[multi-especie SQLite y MySQL]
    ingesta[ingesta MySQL]
    offline[análisis offline MySQL]
  end

  ui[interfaz_gbif.py]
  orm[app_tkinter.py]

  subgraph codigo [src]
    servicio[servicio_bd]
    descarga[ingesta_gbif_sqlite]
    sqlite[guardar_en_sqlite]
    mysqlpy[volcarEndpoints]
    csqlite[consulta_gbif_sqlite]
    cmysql[consulta_gbif]
    repo[repository]
    sesion[database.get_session]
    exporta[exportacion_gbif]
    ventana[gui_tk]
  end

  ui --> servicio
  ui --> descarga
  ui --> csqlite
  ui --> cmysql
  ui --> exporta
  orm --> ventana
  ventana --> sesion
  servicio --> descarga
  servicio --> sqlite
  servicio --> mysqlpy
  ingesta --> mysqlpy
  offline --> cmysql
  mysqlpy --> sesion
  cmysql --> sesion
  sesion --> repo
  multibd --> salidas[(biodiversidad_gbif.db)]
  sqlite --> datos[(datos/gbif_biodiversidad.sqlite)]
  csqlite --> datos
  repo --> mysql[(MySQL gbif_biodiversidad)]
  descarga --> gbif[API GBIF]
  n01 --> gbif
  n02 --> gbif
  n03 --> gbif
  n04 --> gbif
  multi --> gbif
  clases --> gbif
  clases --> html
  exporta --> html[salidas_gbif_multiespecie]
```

## 3. Clases y módulos de la interfaz

`interfaz_gbif.py` trabaja con `DataFrame` y con las funciones de cada módulo. El modelo persistente de MySQL está en la sección 3.1.

```mermaid
classDiagram
  class AplicacionGbif {
    +df_actual
    +df_ocurrencias
    +ver_taxon()
    +ver_ocurrencias()
    +crear_base()
    +poblar_base()
    +consultar()
    +filtrar_ocurrencias_vista()
    +exportar()
  }
  class ServicioBd {
    +crear_base(motor)
    +poblar_base(motor, parametros)
    +filtrar_ocurrencias(df, pais, anio, provincia, epiteto)
    +tabla_desde_registros_gbif(registros)
  }
  class DescargaGbif {
    +obtener_taxon(nombre)
    +listar_especies_con_coordenadas(paises, anios, limite)
    +descargar_desde_gbif(especie, paises, anios, maximo)
  }
  class GuardarSqlite {
    +inicializar_bd_sqlite()
    +guardar_en_sqlite(taxon, registros)
  }
  class GuardarMysql {
    +guardar_en_mysql(config, taxon, registros)
  }
  class Consulta {
    +obtener_resumen_general()
    +cargar_ocurrencias()
    +resumen_territorial_por_comunidad()
    +top_datasets_publicadores()
    +consultar_campos_raw_json()
  }
  class Exportacion {
    +exportar_csv(df, ruta)
    +exportar_json(df, ruta)
    +exportar_mapa_html(df, ruta)
  }

  AplicacionGbif --> ServicioBd
  AplicacionGbif --> DescargaGbif
  AplicacionGbif --> Consulta
  AplicacionGbif --> Exportacion
  ServicioBd --> DescargaGbif
  ServicioBd --> GuardarSqlite
  ServicioBd --> GuardarMysql
```

`Consulta` está implementada dos veces, con el mismo contrato: `consulta_gbif_sqlite.py` (SQL sobre SQLite) y `consulta_gbif.py` (fachada que abre `get_session` y delega en el repositorio).

## 3.1. ORM de MySQL

`app_tkinter.py` llama a `lanzar_gui()`. La ventana y los cuadernos de MySQL comparten sesión y repositorio.

```mermaid
classDiagram
  class BiodiversidadApp {
    +consultar()
    +ver_mapa()
    +exportar_csv()
    +descargar()
    +abrir_ficha()
  }
  class Session {
    +commit()
    +rollback()
    +close()
  }
  class BiodiversidadRepository {
    +upsert_taxon()
    +upsert_organizaciones()
    +upsert_datasets()
    +upsert_ocurrencias()
    +buscar_ocurrencias()
    +contar_ocurrencias()
    +listar_paises()
    +resumen_conteo_tablas()
    +resumen_territorial()
    +top_datasets_publicadores()
  }
  class Taxon {
    +taxon_key
    +scientific_name
    +taxon_rank
  }
  class Organizacion {
    +organization_key
    +title
  }
  class Dataset {
    +dataset_key
    +title
    +publishing_organization_key
  }
  class Ocurrencia {
    +occurrence_key
    +taxon_key
    +dataset_key
    +organization_key
    +raw_json
    +url_primera_imagen
    +es_lobo_silvestre
  }

  BiodiversidadApp --> Session : get_session()
  BiodiversidadApp --> BiodiversidadRepository
  BiodiversidadRepository --> Session
  BiodiversidadRepository --> Taxon
  BiodiversidadRepository --> Organizacion
  BiodiversidadRepository --> Dataset
  BiodiversidadRepository --> Ocurrencia
  Ocurrencia --> Taxon
  Ocurrencia --> Dataset
  Ocurrencia --> Organizacion
  Dataset --> Organizacion
```

`taxon_key`, `dataset_key` y `organization_key` de `Ocurrencia` admiten nulo. Si el registro cita una clave que no está en el catálogo, el repositorio la vacía y la ocurrencia se guarda.

## 4. Secuencia: poblar SQLite desde la interfaz

```mermaid
sequenceDiagram
  actor Persona
  participant UI as Interfaz
  participant Descarga as descargar_desde_gbif
  participant GBIF as API GBIF
  participant Guardar as guardar_en_sqlite
  participant BD as datos/gbif_biodiversidad.sqlite

  Persona->>UI: Poblar, motor SQLite
  UI->>Descarga: especie, países, años, máximo
  Descarga->>GBIF: GET /v1/species/match
  GBIF-->>Descarga: usageKey
  loop por país y página de 300
    Descarga->>GBIF: GET /v1/occurrence/search
    GBIF-->>Descarga: results, count, endOfRecords
  end
  Descarga-->>UI: taxón y registros
  UI->>Guardar: taxón, registros, sesión
  Guardar->>BD: esquema si no existe
  loop organización y dataset distintos
    Guardar->>GBIF: GET /organization y /dataset
  end
  Guardar->>BD: upsert taxón, organizaciones, datasets, ocurrencias
  Guardar-->>Persona: conteos de la carga
```

## 5. Secuencia: filtrar ocurrencias ya cargadas

```mermaid
sequenceDiagram
  actor Persona
  participant UI as Interfaz
  participant Filtro as filtrar_ocurrencias

  Persona->>UI: Ocurrencias
  UI->>UI: guarda el listado completo
  Persona->>UI: country_code, year, state_province, specific_epithet
  UI->>Filtro: listado completo y criterios
  Filtro-->>UI: subconjunto
  UI-->>Persona: tabla, estado "X de N"
  Persona->>UI: Quitar filtro
  UI-->>Persona: listado completo, sin nueva descarga
```

## 6. Actividad de la ingesta

```mermaid
flowchart TD
  A[Nombre científico] --> B[species/match]
  B --> C{¿Hay usageKey?}
  C -->|No| Z[Error de taxón]
  C -->|Sí| D[Página de occurrence/search]
  D --> E{¿Hay resultados y queda cupo?}
  E -->|Sí| D
  E -->|No| F[Organizaciones distintas]
  F --> G[Datasets distintos]
  G --> H[Upsert de ocurrencias]
  H --> I{¿Commit correcto?}
  I -->|Sí| J[Base lista para consulta local]
  I -->|No| K[Rollback]
```

## 7. Modelo entidad-relación del pipeline `src/`

Es el esquema de `docs/schema_gbif_sqlite.sql` y de `docs/schema_gbif.sql`.

```mermaid
erDiagram
  TAXONES ||--o{ OCURRENCIAS : clasifica
  ORGANIZACIONES ||--o{ DATASETS : publica
  ORGANIZACIONES ||--o{ OCURRENCIAS : firma
  DATASETS ||--o{ OCURRENCIAS : contiene

  TAXONES {
    int taxon_key PK
    string scientific_name
    string canonical_name
    string taxon_rank
    string taxonomic_status
    string kingdom
    string genus
    string species
    text raw_json
  }
  ORGANIZACIONES {
    string organization_key PK
    string title
    string country
    string city
    float latitude
    float longitude
    text raw_json
  }
  DATASETS {
    string dataset_key PK
    string organization_key FK
    string title
    string dataset_type
    string license
    string doi
    text raw_json
  }
  OCURRENCIAS {
    int occurrence_key PK
    int taxon_key FK
    string dataset_key FK
    string organization_key FK
    string scientific_name
    string specific_epithet
    string infraspecific_epithet
    string country_code
    string state_province
    string comunidad_gadm
    float decimal_latitude
    float decimal_longitude
    int year
    string basis_of_record
    string vitality
    text raw_json
  }
```

## 8. Modelo del cuaderno multi-especie con base de datos

Solo lo crea `gbif_multiespecie_es_pt_sqlite_mysql.ipynb`. No tiene organizaciones ni datasets del Registry. La multimedia va en una tabla propia.

```mermaid
erDiagram
  TAXONES ||--o{ OCURRENCIAS : clasifica
  OCURRENCIAS ||--o{ OCURRENCIA_MEDIA : adjunta

  TAXONES {
    int taxon_key PK
    string nombre_buscado
    string scientific_name
    string rank
  }
  OCURRENCIAS {
    int gbif_id PK
    int taxon_key FK
    string country_code
    string state_province
    int year
    float latitud
    float longitud
  }
  OCURRENCIA_MEDIA {
    int id PK
    int gbif_id FK
    string url
  }
```

La vista `vw_ocurrencias_completas` une taxón, ocurrencia y multimedia para no repetir esos join en cada consulta del cuaderno.
