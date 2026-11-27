# Exploración de biodiversidad con la API pública de GBIF

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458?style=flat-square&logo=pandas&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-Interactive_Maps-77B829?style=flat-square&logo=leaflet&logoColor=white)
![GBIF API](https://img.shields.io/badge/GBIF-OpenAPI_v1-4BA82E?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

Aplicación en Python para consultar la API REST pública de **GBIF** (*Global Biodiversity Information Facility*), guardar las ocurrencias en SQLite o en MySQL 8, consultarlas sin volver a la red, cartografiarlas y calcular indicadores. La especie, el país y el periodo se eligen en cada consulta. El cuaderno de partida estudia *Canis lupus* en España (2020–2026); las cifras de lobo y de perro de más abajo describen esa muestra, no el resto de la aplicación.

---

## 🎯 ¿Qué resuelve este proyecto?

Trabajar con datos abiertos de biodiversidad requiere ir más allá de descargar una tabla y pintar puntos en un mapa. Este repositorio cubre la descarga, la persistencia, la consulta y la lectura de los sesgos habituales en repositorios agregados:

1. **Cualquier especie (`/v1/species/match`):** el nombre científico se resuelve contra el *GBIF Backbone Taxonomy*. No se escribe el `taxonKey` a mano. El catálogo por clases lista mamíferos, escamosos, anfibios, insectos, plantas y aves, cinco especies de cada una.
2. **Cualquier país y cualquier periodo (`/v1/occurrence/search`):** uno o varios códigos ISO, un año, un intervalo de años o un intervalo de fechas. La descarga pagina con `offset`/`limit` y una sesión HTTP persistente.
3. **Dos bases y dos ventanas:** SQLite en `datos/gbif_biodiversidad.sqlite` y MySQL 8 (`gbif_biodiversidad`), con taxones, organizaciones, datasets y ocurrencias. `python app_tkinter.py` consulta, mide indicadores y trae datos de GBIF. `python interfaz_gbif.py` también trabaja con SQLite y exporta CSV, JSON y HTML.
4. **Indicadores de lo ya guardado:** volumen, territorio GADM, cobertura de campos, evidencia, taxonomía, calidad de la coordenada y quién publica. Un conteo de registros mide esfuerzo de publicación, no abundancia.
5. **Lobo y perro, cuando el taxón es *Canis lupus*:** `taxonKey=5219173` agrupa lobo (`specificEpithet == 'lupus'`) y perro (`familiaris`). En la muestra de 600 registros del cuaderno 01, **el 47,5 % (285 registros) corresponden a perro doméstico**. Esa auditoría es de esa descarga.
6. **Territorio y evidencia en esa misma muestra:** `stateProvince` faltaba en el 21 % de las filas; GADM (`gadm.level1.name` y `gadm.level2.name`) cubría el **98,8 %**. El cuaderno 01 reúne protocolo de muestreo, evidencia de presencia de iNaturalist y mortalidad (`vitality == 'dead'`).

---

## 🗂️ Estructura del repositorio

```text
├── app_tkinter.py                     # Ventana MySQL: Consultar, Indicadores y Traer datos de GBIF
├── interfaz_gbif.py                   # Ventana de escritorio (API, SQLite, MySQL y exportación)
├── notebooks/                         # Cuadernos. Guía: docs/CUADERNOS.md
│   ├── exploracion_01_canis_lupus_espana_mortalidad.ipynb  # empieza aquí
│   ├── exploracion_02_catalogo_especies_es_pt.ipynb
│   ├── exploracion_03_canis_lupus_es_pt_altitud.ipynb
│   ├── exploracion_04_archivo_catalogo_es_pt.ipynb        # archivo, no empezar aquí
│   ├── gbif_especies_por_clase_es_pt.ipynb
│   ├── gbif_multiespecie_es_pt.ipynb
│   └── gbif_multiespecie_es_pt_sqlite_mysql.ipynb
├── src/                               # ORM MySQL, ingesta, consultas e indicadores
│   ├── database.py                    # Motor SQLAlchemy y get_session()
│   ├── models.py                      # Taxon, Organizacion, Dataset, Ocurrencia
│   ├── repository.py                  # Upserts y consultas del repositorio
│   ├── gui_tk.py                      # Ventana que abre app_tkinter.py
│   ├── mapa_enlaces.py                # Abre las fichas GBIF desde el mapa del cuaderno
│   ├── kpis/                          # Consultas de indicadores, un módulo por tema
│   ├── kpi_volumen.py                 # Consola: país, año, mes
│   ├── kpi_territorio.py              # Consola: comunidad, provincia, municipio
│   ├── kpi_cobertura.py               # Consola: porcentaje de filas con cada campo
│   ├── kpi_evidencia.py               # Consola: evidencia, vitalidad, sexo, fase vital
│   ├── kpi_taxonomia.py               # Consola: lobo, perro y fichas
│   ├── kpi_calidad.py                 # Consola: foto, hábitat e incertidumbre
│   └── kpi_publicadores.py            # Consola: datasets, organizaciones, registradores
├── datos/                             # SQLite del pipeline, JSON bruto y CSV archivado
├── salidas_gbif_multiespecie/         # CSV, HTML y la SQLite del cuaderno multi-especie
├── docs/                              # Manual, requisitos, casos de uso, UML y diccionario
└── readme.md
```

MySQL se consulta y se escribe con SQLAlchemy ORM. Las credenciales están en `.env` (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`); `src/db_config.py` las carga y `src/database.py` abre la sesión con `get_session()`. La ventana de ese camino es `python app_tkinter.py`. Al abrirla, la pestaña Consultar muestra la tabla, cuántas filas hay con el filtro y la ficha del registro. El país puede ser cualquier código ISO, varios a la vez o todos los de la base; Desde y Hasta aceptan un año o una fecha, y el mismo valor en los dos deja solo ese año o ese día. Desde ahí se exporta el CSV y el mapa. La pestaña Traer datos de GBIF explica los pasos de la descarga (nombre, ocurrencias con coordenadas, organización, dataset y escritura en MySQL). Cargar especies disponibles lista hasta cinco especies de cada clase para esos países y ese periodo; pulsar una fila rellena la especie. La descarga tiene barra de progreso y se puede cancelar antes de escribir. `python interfaz_gbif.py` sigue siendo la ventana que también trabaja con SQLite y exporta CSV, JSON y HTML. Antes de poblar o consultar, la base tiene que estar iniciada: `datos/gbif_biodiversidad.sqlite` ya creado, o MySQL 8 en marcha con la base `gbif_biodiversidad`. **Especies con coordenadas** muestra cinco especies de cada clase, con familia; las consultas y la exportación siguen a la especie elegida. El catálogo también está en `notebooks/gbif_especies_por_clase_es_pt.ipynb`. El cuaderno de mortalidad está en `notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb`. El JSON bruto está en `datos/registros_gbif_brutos.json`. La pestaña Indicadores muestra el volumen, el territorio, la cobertura, la evidencia, la taxonomía, la calidad y quién publica. Al abrirla calcula el volumen de toda la base; el país, las fechas y la especie acotan el resto. Esas consultas viven en `src/kpis/` y también se imprimen por consola con `kpi_volumen.py` y los otros `kpi_*.py`. Un conteo de ocurrencias mide esfuerzo de publicación, no abundancia. El detalle del ORM y de esos indicadores está en [`docs/documentacion_del_pipeline_gbif_y_mysql_8.md`](./docs/documentacion_del_pipeline_gbif_y_mysql_8.md).

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

## 📊 Muestra del cuaderno 01 (*Canis lupus* en España, `n = 600`)

Estas cifras salen de `notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb` y de `datos/registros_gbif_brutos.json`. No describen la base MySQL, ni el catálogo por clases, ni el cuaderno de varias especies.

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