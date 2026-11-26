# Diagramas UML

Los diagramas describen el sistema tal como está en `interfaz_gbif.py` (raíz), `src/` y `notebooks/`. Los requisitos y los casos de uso que aparecen aquí están detallados en [ESPECIFICACION_REQUISITOS.md](./ESPECIFICACION_REQUISITOS.md) y [CASOS_DE_USO.md](./CASOS_DE_USO.md).

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
    v7[v7 mortalidad España]
    v6[v4 y v6 catálogo ES+PT]
    v5[v5 altitud]
    multi[multi-especie CSV y mapas]
    clases[especies por clase]
    multibd[multi-especie SQLite y MySQL]
    ingesta[ingesta MySQL]
    offline[análisis offline MySQL]
  end

  ui[interfaz_gbif.py]

  subgraph codigo [src]
    servicio[servicio_bd]
    descarga[ingesta_gbif_sqlite]
    sqlite[guardar_en_sqlite]
    mysqlpy[volcarEndpoints]
    csqlite[consulta_gbif_sqlite]
    cmysql[consulta_gbif]
    exporta[exportacion_gbif]
  end

  ui --> servicio
  ui --> descarga
  ui --> csqlite
  ui --> cmysql
  ui --> exporta
  servicio --> descarga
  servicio --> sqlite
  servicio --> mysqlpy
  ingesta --> mysqlpy
  offline --> cmysql
  multibd --> salidas[(biodiversidad_gbif.db)]
  sqlite --> datos[(datos/gbif_biodiversidad.sqlite)]
  csqlite --> datos
  cmysql --> mysql[(MySQL gbif_biodiversidad)]
  mysqlpy --> mysql
  descarga --> gbif[API GBIF]
  v7 --> gbif
  multi --> gbif
  clases --> gbif
  clases --> html
  exporta --> html[salidas_gbif_multiespecie]
```

## 3. Clases y módulos de la interfaz

No hay un modelo de dominio con clases persistentes. La unidad de trabajo es el `DataFrame` y las funciones de cada módulo.

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

`Consulta` está implementada dos veces, con el mismo contrato: `consulta_gbif_sqlite.py` y `consulta_gbif.py`.

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
