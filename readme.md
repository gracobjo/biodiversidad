# Exploración de Biodiversidad con la API Pública de GBIF

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458?style=flat-square&logo=pandas&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-Interactive_Maps-77B829?style=flat-square&logo=leaflet&logoColor=white)
![GBIF API](https://img.shields.io/badge/GBIF-OpenAPI_v1-4BA82E?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

Aplicación en Python (`gracobjo/biodiversidad`) para consultar la API REST pública de **GBIF** (*Global Biodiversity Information Facility*), persistir las ocurrencias en **MySQL 8** (mediante **SQLAlchemy 2**) o en **SQLite**, explorarlas sin depender de la red, cartografiarlas y calcular indicadores ecológicos y de calidad de datos. La especie, el país y el periodo se configuran dinámicamente en cada consulta.

---

## 🎯 ¿Qué resuelve este proyecto?

Trabajar con datos abiertos de biodiversidad requiere ir más allá de descargar una tabla y pintar puntos en un mapa. Este repositorio cubre la descarga, la persistencia relacional-documental, la consulta *offline* y la auditoría de los sesgos habituales en repositorios agregados:

1. **Resolución taxonómica dinámica (`/v1/species/match`):** cualquier nombre científico se resuelve contra el *GBIF Backbone Taxonomy* sin codificar `taxonKey` a mano. Incluye un catálogo por clases (mamíferos, escamosos, anfibios, insectos, plantas y aves, cinco especies por clase).
2. **Consulta multicriterio y paginada (`/v1/occurrence/search`):** permite filtrar por uno o varios códigos ISO de país, un año, un intervalo de años o de fechas, paginando con `offset`/`limit` sobre una sesión HTTP persistente con reintentos (`urllib3.Retry`).
3. **Doble motor de persistencia y doble interfaz de escritorio:**
   * **`python app_tkinter.py` (MySQL 8 + SQLAlchemy 2):** pestañas, por este orden, para ingesta online en segundo plano (*Traer datos de GBIF*), exploración filtrada (*Consultar*) y cálculo visual de métricas (*Indicadores*), con exportación a CSV y mapas HTML.
   * **`python interfaz_gbif.py` (SQLite + MySQL):** gestión sobre `datos/gbif_biodiversidad.sqlite` y exportación directa a CSV, JSON y HTML.
4. **Indicadores de calidad y esfuerzo (`src/kpis/`):** análisis de volumen, cobertura territorial GADM, completitud de campos, tipo de evidencia, desambiguación taxonómica, incertidumbre espacial y entidades publicadoras. Un conteo de registros mide esfuerzo de publicación, no abundancia.
5. **Desambiguación lobo vs. perro (*Canis lupus*):** `taxonKey=5219173` agrupa lobo silvestre (`specificEpithet == 'lupus'`) y perro doméstico (`familiaris`), permitiendo aislar ambos grupos en consultas, mapas e indicadores. En la muestra de 600 registros del cuaderno 01, el 47,5 % (285 registros) corresponde a perro doméstico. Esa cifra es de esa descarga, no de toda la base.

---

## 📈 Evolución arquitectónica del proyecto

El sistema ha evolucionado a través de **cinco etapas progresivas**, cada una resolviendo una limitación técnica de la anterior:

| Fase | Hito técnico | Problema resuelto | Artefactos clave |
| :--- | :--- | :--- | :--- |
| **1. Exploración API REST** | Consulta directa a los endpoints `/v1/species/match`, `/v1/occurrence/search`, `/v1/organization` y `/v1/dataset` con paginación y backoff. | Obtener registros Darwin Core georreferenciados en la península ibérica (`ES`, `PT`) y resolver la taxonomía antes de descargar. | Sesiones `requests.Session` con `HTTPAdapter`. |
| **2. Análisis en Notebooks** | Tabulación en `pandas`, desambiguación de `familiaris`, gráficos con `matplotlib`/`seaborn` y mapas interactivos con `folium`. | Evitar repetir descargas de miles de registros cada vez que se ajustaba una gráfica o filtro analítico. | `notebooks/exploracion_01_*.ipynb` a `04_*.ipynb`, `gbif_multiespecie_es_pt.ipynb`. |
| **3. Persistencia híbrida (MySQL 8 y SQLite)** | Esquema normalizado (`taxones`, `organizaciones`, `datasets`, `ocurrencias`) combinado con columna nativa `JSON` (`raw_json`) e ingesta idempotente. | Separar la **Fase A (Ingesta Online)** de la **Fase B (Análisis Offline)**, garantizando integridad referencial sin perder campos anidados de GBIF (multimedia, hábitat, GADM). | `src/esquema_actual.sql`, `docs/schema_gbif.sql`, `datos/gbif_biodiversidad.sqlite`, `.env`. |
| **4. Capa ORM con SQLAlchemy 2** | Sustitución del SQL manual por modelos declarativos tipados (`DeclarativeBase`, `Mapped`, `mapped_column`), relaciones y un Repositorio centralizado. | Eliminar SQL duplicado, prevenir consultas N+1 mediante `joinedload` y encapsular lógica de dominio (extracción de fotografías desde `raw_json`). | `src/database.py`, `src/models.py`, `src/repository.py`, `prueba_orm.py`. |
| **5. Unificación, KPIs y GUI** | Refactorización de adaptadores heredados, creación de módulos de indicadores (`src/kpis/`) e interfaz Tkinter con la descarga en un hilo aparte. | Permitir ingesta en segundo plano (cancelable y con barra de progreso), exploración filtrada y un gráfico por tema desde una única fuente de verdad. | `app_tkinter.py`, `src/gui_tk.py`, `src/kpis/`, `src/kpi_*.py`. |

---

## 🗂️ Estructura del repositorio

```text
biodiversidad/
├── .env                               # Credenciales aisladas (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
├── pyproject.toml / uv.lock           # Gestión reproducible de dependencias con uv
├── app_tkinter.py                     # Ventana MySQL (ORM): Traer datos de GBIF, Consultar e Indicadores
├── interfaz_gbif.py                   # Ventana de escritorio (API, SQLite, MySQL y exportación CSV/JSON/HTML)
├── prueba_orm.py                      # Validación de integración del mapeo ORM y relaciones
├── notebooks/                         # Cuadernos Jupyter (Guía en docs/CUADERNOS.md)
│   ├── exploracion_01_canis_lupus_espana_mortalidad.ipynb  # Punto de partida (auditoría n=600)
│   ├── exploracion_02_catalogo_especies_es_pt.ipynb
│   ├── exploracion_03_canis_lupus_es_pt_altitud.ipynb
│   ├── exploracion_04_archivo_catalogo_es_pt.ipynb        # Archivo histórico
│   ├── gbif_especies_por_clase_es_pt.ipynb
│   ├── gbif_multiespecie_es_pt.ipynb
│   └── gbif_multiespecie_es_pt_sqlite_mysql.ipynb
├── src/                               # Núcleo ORM, ingesta, adaptadores, GUI e indicadores
│   ├── db_config.py                   # Carga de variables de entorno desde .env con python-dotenv
│   ├── database.py                    # Motor SQLAlchemy, SessionLocal y contextmanager get_session()
│   ├── models.py                      # Entidades ORM: Taxon, Organizacion, Dataset, Ocurrencia
│   ├── repository.py                  # BiodiversidadRepository (upserts masivos y consultas tipadas)
│   ├── esquema_actual.sql             # Volcado de la base MySQL 8 ya creada
│   ├── volcarEndpoints.py             # Adaptador Fase A (Registry + ocurrencias -> ORM)
│   ├── consulta_gbif.py               # Adaptador Fase B (consultas ORM -> pandas.DataFrame)
│   ├── gui_tk.py                      # Controladores y vistas Tkinter (ttk.Notebook)
│   ├── mapa_enlaces.py                # Apertura de fichas GBIF desde mapas generados en cuadernos
│   ├── kpis/                          # Consultas analíticas de indicadores, un módulo por tema
│   ├── kpi_volumen.py                 # CLI: distribución por país, año y mes
│   ├── kpi_territorio.py              # CLI: desglose GADM (comunidad, provincia, municipio)
│   ├── kpi_cobertura.py               # CLI: porcentaje de completitud por campo Darwin Core
│   ├── kpi_evidencia.py               # CLI: basisOfRecord, vitalidad, sexo y fase vital
│   ├── kpi_taxonomia.py               # CLI: desambiguación lobo vs. perro y fichas
│   ├── kpi_calidad.py                 # CLI: disponibilidad de foto, hábitat e incertidumbre espacial
│   └── kpi_publicadores.py            # CLI: ranking de datasets, organizaciones y registradores
├── datos/                             # Base SQLite del pipeline, JSON bruto y CSV archivado
├── salidas_gbif_multiespecie/         # Exportaciones CSV, mapas HTML y SQLite multi-especie
├── docs/                              # Manual de usuario, requisitos, UML, schema_gbif.sql y diccionario
└── readme.md
```

El script de creación está en [`docs/schema_gbif.sql`](./docs/schema_gbif.sql). `src/esquema_actual.sql` es un volcado de la base ya creada, no ese script.

---

## 🧩 Patrones de diseño y flujo de datos

### Patrones aplicados
* **Repository Pattern (`BiodiversidadRepository`):** Centraliza en `src/repository.py` todas las operaciones de persistencia y consulta (`upsert_ocurrencias`, `buscar_ocurrencias`, `listar_taxones`, `listar_comunidades`, `conteo_por_comunidad`), aislando del dialecto SQL tanto a la interfaz Tkinter como a los cuadernos y módulos KPI.
* **Unit of Work / Session Context Manager (`get_session`):** Implementado en `src/database.py` con `@contextmanager`, asegurando `commit()` automático o `rollback()` limpio ante fallos y cierre garantizado de conexiones.
* **Data Mapper & Hybrid Relational-JSON Modeling (`src/models.py`):** Mapea las 4 tablas InnoDB (`CHAR(36)` para UUIDs, `DECIMAL(10,7)` para coordenadas e índices compuestos) junto con propiedades calculadas (`@property` como `url_primera_imagen`, `es_lobo_silvestre`, `habitat_json`) que extraen atributos directamente del diccionario `raw_json`.
* **Adapter / Facade Pattern (`volcarEndpoints.py` y `consulta_gbif.py`):** Mantiene intactas las firmas y alias Darwin Core (`decimalLatitude`, `scientificName`, `basisOfRecord`) que consumen los cuadernos, delegando internamente en SQLAlchemy 2.
* **Descarga en segundo plano (`src/gui_tk.py`):** La descarga HTTP paginada y los *upserts* por lotes (`tamano_lote=250`) corren en un `threading.Thread`. El progreso y el resto de cambios de la ventana se encolan en una lista; el hilo principal la vacía cada 150 ms. En este Python, llamar a `after()` desde el hilo de la descarga no programa nada. Cancelar usa un `threading.Event`: si se cancela antes de guardar, no se escribe.

### Flujo operativo y exportación
1. **Fase A (Ingesta Idempotente):** Resuelve el `usageKey`, pagina las ocurrencias con coordenadas y consulta una única vez cada `publishingOrgKey` y `datasetKey` en el *Registry* de GBIF. Inserta mediante `ON DUPLICATE KEY UPDATE`, permitiendo ampliar años o países sin duplicar registros.
2. **Fase B (Consulta, Indicadores y Exportación):**
   * **Interfaz Tkinter (`app_tkinter.py`):** Filtra por especie, códigos ISO de país, rango de fechas o de años y comunidad GADM. La tabla de Consultar arranca ordenada por año, del más reciente al más antiguo; pulsar una columna cambia ese orden. En Traer datos, Cargar especies disponibles lista hasta cinco especies de cada clase para esos países y ese periodo, y pulsar una fila rellena la especie. Indicadores muestra la tabla y un gráfico del mismo recuento: si el tema tiene varios, se elige uno. Contraer datos oculta la tabla y la división entre las dos se puede arrastrar. Desde Consultar se exporta a **CSV** y a un **mapa HTML**, y se abre la ficha de GBIF o la fotografía de `raw_json`.
   * **Consola CLI (`src/kpi_*.py`):** Ejecuta los mismos indicadores de `src/kpis/` en terminal, sin dibujar el gráfico.

---

## 🚀 Instalación y ejecución rápida

El proyecto está preparado para **Python 3.14** utilizando un entorno virtual aislado (`.venv`) en la raíz del proyecto y el kernel registrado **Python (biodiversidad)** para Jupyter.

### 1. Configuración de variables de entorno (`.env`)
Antes de iniciar MySQL 8, crea el archivo `.env` en la raíz del proyecto (excluido en `.gitignore`):

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_contrasena_mysql
DB_NAME=gbif_biodiversidad
```

### 2. Instalación con `uv` (recomendado)

```bash
git clone https://github.com/gracobjo/biodiversidad.git
cd biodiversidad

uv venv --python 3.14 .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
# source .venv/bin/activate

uv sync --system-certs
.venv\Scripts\python.exe -m ipykernel install --user --name=biodiversidad --display-name="Python (biodiversidad)"
```

*(En entornos corporativos con certificados propios, `--system-certs` asegura la validación TLS con la API de GBIF).*

### 3. Instalación alternativa con `venv` y `pip`

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install requests pandas folium matplotlib seaborn ipykernel truststore sqlalchemy mysql-connector-python python-dotenv urllib3
python -m ipykernel install --user --name=biodiversidad --display-name="Python (biodiversidad)"
```

### 4. Arranque de aplicaciones
```bash
# Interfaz principal conectada a MySQL 8 vía SQLAlchemy
uv run python app_tkinter.py

# Interfaz dual con soporte SQLite y exportación CSV/JSON/HTML
uv run python interfaz_gbif.py
```

> **Modo offline sin red:** Puedes explorar los datos sin peticiones HTTP cargando `datos/registros_gbif_brutos.json` desde la Sección 2b de `notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb`, o consultando directamente las bases locales ya pobladas.

---

## 📊 Auditoría de la muestra inicial (*Canis lupus* en España, `n = 600`)

Las siguientes métricas proceden de `notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb` y `datos/registros_gbif_brutos.json` (corresponden exclusivamente a esa muestra exploratoria inicial y no al total de especies almacenadas en MySQL):

| Dimensión analizada | Hallazgo en la muestra (`n = 600`) |
| :--- | :--- |
| **Composición taxonómica** | **315** registros de lobo silvestre (`lupus`) frente a **285** (47,5 %) de perro doméstico (`familiaris`). |
| **Cobertura territorial GADM** | `stateProvince` faltaba en el 21 % de los registros, mientras que `gadm.level1.name` y `level2.name` cubrían el **98,8 %**. |
| **Distribución del lobo (`lupus`)** | Concentrada en el noroeste peninsular: **Galicia** (161), **Castilla y León** (72) y **Principado de Asturias** (40). |
| **Evidencias y metodologías** | Predominan indicios indirectos en ciencia ciudadana (`scat`: 104 excrementos, `track`: 13 huellas) y fototrampeo sistemático (`Fototrampeo General`: 64, `Multiespecie en un punto`: 23). |
| **Incertidumbre espacial** | En observaciones sensibles de iNaturalist, las coordenadas se generalizan automáticamente (`coordinateUncertaintyInMeters ≈ 27,6 km`, documentado en `informationWithheld`). |
| **Mortalidad documentada** | **7** registros con `vitality == 'dead'`, incluyendo un ejemplar de lobo silvestre hallado junto a una carretera en León con signos compatibles con sarna sarcóptica. |

---

## 🌐 Evolución hacia un entorno web

Esta fase **no está en el código**. No hay `src/api.py`, ni `app_web.py`, ni FastAPI, ni Celery, ni un frontend. Lo que sigue es un camino posible, no una pieza del repositorio.

El acceso a datos y la lógica analítica ya viven en `src/` (`database.py`, `models.py`, `repository.py` y `src/kpis/`). Una interfaz web podría reutilizar ese núcleo sin reescribir el modelo ni las consultas ORM.

### A. Backend API REST + frontend, si se construye
* **API:** una dependencia de sesión envolvería `get_session()` en cada petición. Esquemas de salida podrían serializar las entidades ORM, incluidas propiedades como `url_primera_imagen`.
* **Tareas largas:** la descarga de GBIF, que hoy corre en un hilo de `gui_tk.py`, pasaría a una tarea en segundo plano del servidor.
* **Frontend:** tablas paginadas y un mapa en el navegador sustituirían el `ttk.Treeview` y el HTML de Folium.

### B. Cuadro de mando en Python, si se construye
Una aplicación Streamlit o Dash importaría `BiodiversidadRepository` y `src/kpis/` y trasladaría los filtros de `gui_tk.py` a controles de esa librería. Ese fichero tampoco existe.

| Capa del sistema | Lo que hay ahora | Lo que una web tendría que añadir |
| :--- | :--- | :--- |
| **Base de datos** | MySQL 8 local o SQLite | El mismo esquema. `docs/schema_gbif.sql` no cambiaría por el hecho de servir HTTP. |
| **ORM y repositorio** | `src/models.py`, `src/repository.py`, `src/kpis/` | Reutilizables. La paginación web pediría `offset` en `buscar_ocurrencias`. |
| **Tareas en segundo plano** | `threading.Thread` y una lista que vacía el hilo principal | Un mecanismo del servidor, todavía no escrito. |
| **Visualización** | `ttk.Treeview`, un gráfico matplotlib por tema y Folium en HTML | Por decidir. No hay API JSON ni mapa Leaflet en el repositorio. |
| **Credenciales** | `.env` local, fuera de git | Seguirían fuera del código. No hay autenticación de usuarios. |

---

## ⚠️ Lectura responsable de los datos y documentación adicional

* **Registros $\neq$ Individuos:** Un conteo de ocurrencias en GBIF mide esfuerzo de muestreo y reporte, nunca densidad ni tamaño poblacional.
* **Año 2026 en curso:** Los datos de 2026 corresponden a un año natural incompleto y no deben compararse directamente con series anuales cerradas.
* **Documentación técnica interna:**
  * Guía de cuadernos: [`docs/CUADERNOS.md`](./docs/CUADERNOS.md)
  * Diccionario de datos Darwin Core y JSON: [`docs/diccionario_datos_gbif.md`](./docs/diccionario_datos_gbif.md)
  * Documentación del pipeline ORM e indicadores: [`docs/documentacion_del_pipeline_gbif_y_mysql_8.md`](./docs/documentacion_del_pipeline_gbif_y_mysql_8.md)
* **Referencias externas:** [GBIF Developer Portal](https://www.gbif.org/developer/summary) · [GBIF Occurrence API v1](https://techdocs.gbif.org/en/openapi/v1/occurrence) · [GBIF Species API v1](https://techdocs.gbif.org/en/openapi/v1/species) · [Estándar Darwin Core (TDWG)](https://dwc.tdwg.org/)
