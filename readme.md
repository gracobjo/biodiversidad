# 🐺 Exploración de Biodiversidad en España con la API Pública de GBIF

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458?style=flat-square&logo=pandas&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-Interactive_Maps-77B829?style=flat-square&logo=leaflet&logoColor=white)
![GBIF API](https://img.shields.io/badge/GBIF-OpenAPI_v1-4BA82E?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

Pipeline reproducible en Python para consultar, auditar, normalizar y cartografiar registros de presencia de *Canis lupus* en España (2020–2026) a través de la API REST pública de **GBIF** (*Global Biodiversity Information Facility*).

---

## 🎯 ¿Qué resuelve este proyecto?

Trabajar con datos abiertos de biodiversidad requiere ir más allá de descargar una tabla y pintar puntos en un mapa. Este repositorio implementa un flujo completo de ingeniería y análisis de datos científicos (**ETL + EDA + Cartografía**) que aborda los sesgos habituales en repositorios agregados:

1. **Resolución taxonómica dinámica (`/v1/species/match`):** evita codificar identificadores internos (`taxonKey`) a mano, validando coincidencias exactas frente al *GBIF Backbone Taxonomy*.
2. **Diagnóstico progresivo y paginación robusta (`/v1/occurrence/search`):** evalúa el impacto de cada filtro antes de descargar y gestiona la paginación mediante `offset`/`limit` con sesiones HTTP persistentes (`requests.Session`).
3. **Auditoría taxonómica crítica (*Lobo vs. Perro*):** en GBIF, `taxonKey=5219173` (*Canis lupus*) agrupa tanto lobo salvaje (`specificEpithet == 'lupus'`) como perros domésticos o asilvestrados (`specificEpithet == 'familiaris'`). En la muestra descargada de 600 registros, **el 47,5 % (285 registros) corresponden a perro doméstico**. El cuaderno separa ambos taxones antes de extraer conclusiones ecológicas.
4. **Normalización territorial GADM:** sustituye el campo heterogéneo `stateProvince` (ausente en el 21 % de los registros) por la jerarquía administrativa normalizada de GBIF (`gadm.level1.name` y `gadm.level2.name`, con **98,8 % de cobertura**).
5. **Unificación de esfuerzo científico y ciencia ciudadana:** combina `samplingProtocol` (fototrampeo en Proyecto MOMAT, transectos en Observation.org) con el campo JSON incrustado `dynamicProperties -> evidenceOfPresence` de iNaturalist (`scat`, `track`, `bone`, `organism`) en una variable analítica sin valores nulos (`metodo_o_evidencia`), además de auditar mortalidad (`vitality == 'dead'`) y notas de campo (`occurrenceRemarks`).

---

## 🗂️ Estructura del repositorio

```text
├── app_tkinter.py                     # Ventana MySQL: Consultar y Traer datos de GBIF
├── interfaz_gbif.py                   # Ventana de escritorio (API, SQLite, MySQL y exportación)
├── notebooks/                         # Cuadernos. Guía: docs/CUADERNOS.md
│   ├── exploracion_01_canis_lupus_espana_mortalidad.ipynb  # empieza aquí
│   ├── exploracion_02_catalogo_especies_es_pt.ipynb
│   ├── exploracion_03_canis_lupus_es_pt_altitud.ipynb
│   ├── exploracion_04_archivo_catalogo_es_pt.ipynb        # archivo, no empezar aquí
│   ├── gbif_especies_por_clase_es_pt.ipynb
│   ├── gbif_multiespecie_es_pt.ipynb
│   └── gbif_multiespecie_es_pt_sqlite_mysql.ipynb
├── src/                               # ORM MySQL, ingesta y consultas
│   ├── database.py                    # Motor SQLAlchemy y get_session()
│   ├── models.py                      # Taxon, Organizacion, Dataset, Ocurrencia
│   ├── repository.py                  # Upserts y consultas del repositorio
│   ├── gui_tk.py                      # Ventana que abre app_tkinter.py
│   └── mapa_enlaces.py                # Abre las fichas GBIF desde el mapa del cuaderno
├── datos/                             # SQLite del pipeline, JSON bruto y CSV archivado
├── salidas_gbif_multiespecie/         # CSV, HTML y la SQLite del cuaderno multi-especie
├── docs/                              # Manual, requisitos, casos de uso, UML y diccionario
└── readme.md
```

MySQL se consulta y se escribe con SQLAlchemy ORM. Las credenciales están en `.env` (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`); `src/db_config.py` las carga y `src/database.py` abre la sesión con `get_session()`. La ventana de ese camino es `python app_tkinter.py`. Al abrirla, la pestaña Consultar muestra la tabla, cuántas filas hay con el filtro y la ficha del registro. El país puede ser cualquier código ISO, varios a la vez o todos los de la base; Desde y Hasta aceptan un año o una fecha, y el mismo valor en los dos deja solo ese año o ese día. Desde ahí se exporta el CSV y el mapa. La pestaña Traer datos de GBIF descarga con esos mismos criterios, con barra de progreso, y se puede cancelar antes de escribir en MySQL. `python interfaz_gbif.py` sigue siendo la ventana que también trabaja con SQLite y exporta CSV, JSON y HTML. Antes de poblar o consultar, la base tiene que estar iniciada: `datos/gbif_biodiversidad.sqlite` ya creado, o MySQL 8 en marcha con la base `gbif_biodiversidad`. **Especies con coordenadas** muestra cinco especies de cada clase, con familia; las consultas y la exportación siguen a la especie elegida. El catálogo también está en `notebooks/gbif_especies_por_clase_es_pt.ipynb`. El cuaderno de mortalidad está en `notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb`. El JSON bruto está en `datos/registros_gbif_brutos.json`. El detalle del ORM está en [`docs/documentacion_del_pipeline_gbif_y_mysql_8.md`](./docs/documentacion_del_pipeline_gbif_y_mysql_8.md).

---

## 🚀 Instalación y ejecución rápida

El proyecto está diseñado para **Python 3.14** utilizando un entorno virtual aislado.

El entorno virtual es la carpeta `.venv` de la raíz del proyecto. `uv sync` (o `pip`, en la opción B) instala ahí las dependencias de `pyproject.toml`. En un cuaderno se elige el kernel **Python (biodiversidad)**: es el nombre con el que se registra el intérprete `.venv\Scripts\python.exe` en Windows (`.venv/bin/python` en Linux y macOS).

### Opción A: Usando `uv` (recomendado)

```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio

uv venv --python 3.14 .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
# source .venv/bin/activate

uv sync --system-certs
.venv\Scripts\python.exe -m ipykernel install --user --name=biodiversidad --display-name="Python (biodiversidad)"
```

`uv sync` instala exactamente lo declarado en `pyproject.toml` (`matplotlib`, `seaborn` e `ipykernel` incluidos). Si no sabes si `.venv` ya tiene todas las librerías, vuelve a lanzarlo: completa lo que falte. En la red de la Junta hace falta `--system-certs`.

### Opción B: Usando `venv` y `pip`

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

> **Modo offline:** Si deseas explorar los datos sin realizar peticiones HTTP a la API de GBIF, carga directamente `datos/registros_gbif_brutos.json` desde la Sección 2b del cuaderno `exploracion_01_canis_lupus_espana_mortalidad.ipynb`.

---

## 📊 Principales hallazgos sobre la muestra analizada (`n = 600`)

| Dimensión analizada | Resultado clave en la muestra |
| :--- | :--- |
| **Composición taxonómica** | **315** registros de lobo salvaje (`lupus`) frente a **285** de perro (`familiaris`). |
| **Distribución real del lobo (`lupus`)** | Concentrada en el cuadrante noroeste: **Galicia** (161), **Castilla y León** (72) y **Principado de Asturias** (40). |
| **Evidencias y metodologías (lobo)** | Predominan los indicios indirectos en ciencia ciudadana (`scat`: 104 excrementos, `track`: 13 huellas) y el fototrampeo sistemático (`Fototrampeo General`: 64, `Multiespecie en un punto`: 23). |
| **Incertidumbre espacial** | En registros sensibles de iNaturalist, las coordenadas se ofuscan automáticamente (`coordinateUncertaintyInMeters ≈ 27,6 km`, documentado en `informationWithheld`). |
| **Mortalidad documentada** | 7 registros con `vitality == 'dead'`, incluyendo un ejemplar de lobo salvaje hallado junto a una carretera en León con síntomas compatibles con sarna sarcóptica. |

---

## ⚠️ Lectura responsable de los datos

* **Registros $\neq$ Individuos:** Un conteo de ocurrencias en GBIF mide esfuerzo de muestreo y reporte, nunca densidad ni tamaño poblacional. Un mismo ejemplar puede generar múltiples detecciones en cámaras de fototrampeo o rastros.
* **Año 2026 en curso:** Los registros correspondientes a 2026 representan un año natural incompleto y no deben compararse directamente con series anuales cerradas.
* **Consulta de metadatos:** Para conocer la definición exacta, tipo de dato y porcentaje de cobertura de cada columna del JSON bruto y del CSV exportado, consulta [`diccionario_datos_gbif.md`](./docs/diccionario_datos_gbif.md).

---

## 📚 Referencias técnicas

* [GBIF Developer Portal](https://www.gbif.org/developer/summary)
* [GBIF Occurrence API v1 (OpenAPI 3.1)](https://techdocs.gbif.org/en/openapi/v1/occurrence)
* [GBIF Species API v1 (OpenAPI 3.1)](https://techdocs.gbif.org/en/openapi/v1/species)
* [Estándar Darwin Core (TDWG)](https://dwc.tdwg.org/)