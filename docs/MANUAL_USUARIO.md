# 📋 Manual de Usuario: Exploración de Biodiversidad con API GBIF

Este manual es la guía de uso. La especificación vigente, los casos de uso y los diagramas están en documentos propios:

- [CUADERNOS.md](./CUADERNOS.md): qué hace cada cuaderno y cómo ejecutarlo.
- [ESPECIFICACION_REQUISITOS.md](./ESPECIFICACION_REQUISITOS.md): requisitos funcionales y no funcionales, incluidos SQLite, MySQL, la interfaz y el filtro de ocurrencias.
- [CASOS_DE_USO.md](./CASOS_DE_USO.md): flujos CU-01 a CU-15.
- [UML.md](./UML.md): casos de uso, componentes, secuencia, actividad y entidad-relación.

La aplicación consulta cualquier especie, en cualquier país y en un año o un intervalo de fechas. Guarda en SQLite o en MySQL, y la ventana `app_tkinter.py` abre, por este orden, Traer datos de GBIF, Consultar e Indicadores. *Canis lupus* es la especie de partida y el caso en el que hay que separar lobo y perro; no es el límite de la aplicación.

Las secciones 1 a 4 de este manual describen los cuadernos 01 (mortalidad en España) y 04 (archivo del catálogo ES+PT), con su muestra de 600 registros. Los requisitos vigentes son RF-01 a RF-22 y los casos CU-01 a CU-15. Si estas secciones discrepan de esos documentos, mandan los documentos específicos.

## 1. Requisitos Funcionales (RF)

### RF1: Resolución Taxonómica Dinámica
- **Descripción:** El sistema debe permitir consultar cualquier especie proporcionando su nombre científico, validando automáticamente contra la taxonomía de GBIF mediante el endpoint `/v1/species/match`.
- **Criterios de aceptación:**
  - Aceptar nombres científicos en formato `Género especie`.
  - Validar que la coincidencia sea exacta (`matchType == "EXACT"`).
  - Rechazar homónimos o coincidencias aproximadas con mensaje de error descriptivo.
  - Devolver el `usageKey` (identificador único en GBIF) y el nombre oficial normalizado.

### RF2: Consulta Multicriterio de Ocurrencias
- **Descripción:** Implementar búsqueda de registros de biodiversidad filtrando simultáneamente por especie, país, período temporal y propiedades espaciales.
- **Criterios de aceptación:**
  - Permitir filtros combinados: `taxonKey`, `country`, `year`, `hasCoordinate`, `hasGeospatialIssue`.
  - Realizar diagnóstico progresivo: mostrar el impacto de cada filtro en el número de registros.
  - Respetar el límite de 300 registros por petición HTTP.
  - Manejar paginación automática mediante `offset` y `limit`.
  - Permitir limitar el número máximo de registros descargados (ej: 600).

### RF3: Gestión de Sesión HTTP Persistente
- **Descripción:** Mantener una conexión reutilizable a lo largo de múltiples consultas para optimizar la velocidad y respetar las políticas de rate limiting de GBIF.
- **Criterios de aceptación:**
  - Crear una sesión única con headers HTTP apropiados (User-Agent).
  - Incluir pausa entre peticiones (configurables, por defecto 0.2 segundos).
  - Implementar timeouts para evitar bloqueos indefinidos.

### RF4: Normalización Territorial GADM
- **Descripción:** Reemplazar el campo heterogéneo `stateProvince` (con 21% de valores ausentes) por jerarquía administrativa normalizada de GADM.
- **Criterios de aceptación:**
  - Extraer `gadm.level1.name` (comunidad autónoma) con cobertura > 98%.
  - Extraer `gadm.level2.name` (provincia) cuando esté disponible.
  - Extraer `gadm.level3.name` (municipio) cuando esté disponible.
  - Validar consistencia territorial antes de exportar.

### RF5: Separación de Taxones Ambiguos
- **Descripción:** Distinguir entre *Canis lupus lupus* (lobo salvaje) y *Canis lupus familiaris* (perro doméstico), que comparten el mismo `taxonKey` en GBIF.
- **Criterios de aceptación:**
  - Filtrar por campo `specificEpithet` para separar `lupus` de `familiaris`.
  - Documentar el porcentaje de registros de cada subespecie.
  - Permitir análisis por separado.

### RF6: Extracción de Evidencias Científicas
- **Descripción:** Unificar metodologías y tipos de evidencia de observación directa, fototrampeo, ciencia ciudadana e iNaturalist en un campo analítico único.
- **Criterios de aceptación:**
  - Combinar `samplingProtocol` con `dynamicProperties.evidenceOfPresence`.
  - Mapear evidencias indirectas: `scat` (excrementos), `track` (huellas), `bone` (hueso), `organism` (organismo).
  - Crear variable `metodo_o_evidencia` sin valores nulos.

### RF7: Auditoría de Mortalidad
- **Descripción:** Identificar y analizar registros de individuos muertos para estudios de mortalidad.
- **Criterios de aceptación:**
  - Filtrar registros con `vitality == "dead"`.
  - Incluir contexto en `occurrenceRemarks`.
  - Documentar causas estimadas (ej: sarna sarcóptica, atropello).

### RF8: Exportación a CSV
- **Descripción:** Generar dataset tabulado listo para análisis BI, SQL y herramientas estadísticas.
- **Criterios de aceptación:**
  - Exportar como UTF-8 con delimitador `,`.
  - Incluir todas las variables normalizadas.
  - Mantener trazabilidad (anotación de transformaciones).

### RF9: Cartografía Interactiva
- **Descripción:** Generar mapa HTML con Folium visualizando la distribución espacial de registros.
- **Criterios de aceptación:**
  - Separar puntos por subespecie (lobo vs. perro) con colores distintos.
  - Incluir clustering de marcadores para evitar saturación visual.
  - Permitir interacción: zoom, pan, tooltips con metadatos.

---

## 2. Requisitos No Funcionales (FNF)

### FNF1: Rendimiento
- **Criterios:**
  - Descarga de 600 registros < 10 segundos.
  - Paginación automática sin intervención del usuario.
  - Sesión HTTP persistente reutilizable.

### FNF2: Confiabilidad
- **Criterios:**
  - Manejo de errores HTTP (timeouts, 429 rate limit, 404 no encontrado).
  - Validación de respuestas JSON antes de procesar.
  - Logs de diagnóstico en cada paso.

### FNF3: Escalabilidad
- **Criterios:**
  - Compatible con descarga de miles de registros.
  - Gestión eficiente de memoria (uso de paginación).
  - Parámetros configurables para ajustar tamaño de páginas.

### FNF4: Reproducibilidad
- **Criterios:**
  - Semilla de aleatoriedad fija (si aplica).
  - Snapshot JSON guardado como fuente única de verdad.
  - Transformaciones documentadas.

### FNF5: Interoperabilidad
- **Criterios:**
  - Cumplir con estándar Darwin Core (TDWG).
  - Usar estándar ISO 8601 para fechas.
  - Exportar a formatos abiertos (CSV, JSON).

### FNF6: Usabilidad
- **Criterios:**
  - Interfaz de Jupyter Notebook intuitiva.
  - Mensajes de error descriptivos.
  - Documentación integrada con ejemplos.

### FNF7: Seguridad
- **Criterios:**
  - No almacenar credenciales en el código.
  - User-Agent identificable para respetar políticas GBIF.
  - Validación de entrada (ej: taxon name, year range).

### FNF8: Mantenibilidad
- **Criterios:**
  - Código modular con funciones reutilizables.
  - Tipado estático con `typing` de Python 3.14+.
  - Docstrings detallados.

---

## 3. Casos de Uso Principales

### CU1: Exploración General de una Especie (Usuario Científico)

**Actor:** Ecólogo interesado en la distribución de *Canis lupus* en España.

**Flujo:**
1. Abrir el notebook.
2. Cambiar el nombre científico en la función `obtener_taxon_key()`.
3. Ajustar filtros (`country`, `year`, `hasCoordinate`) según necesidad.
4. Ejecutar todas las celdas en orden.
5. Revisar diagnóstico progresivo para entender qué filtro reduce más los resultados.
6. Descargar CSV exportado y abrirlo en Excel / Power BI.
7. Generar mapa interactivo HTML.

**Resultado esperado:** 
- JSON con 600 registros brutos descargados.
- CSV normalizado con 60+ campos analíticos.
- Mapa Folium con 315 puntos de lobo vs 285 de perro.

---

### CU2: Análisis de Mortalidad por Especie

**Actor:** Veterinario o biólogo estudiando causas de muerte.

**Flujo:**
1. Usar el notebook con filtro de mortalidad.
2. Buscar registros con `vitality == 'dead'`.
3. Extraer comentarios de `occurrenceRemarks`.
4. Cruzar con `dynamicProperties` para tipo de evidencia (ej: "bone found").
5. Generar tabla de mortalidad con causa, fecha, provincia.
6. Exportar a CSV para análisis estadístico.

**Resultado esperado:**
- Tabla de 7-10 casos de mortalidad documentados.
- Causas identificadas (ej: sarna, atropello).
- Distribución geográfica de puntos de muerte.

---

### CU3: Comparativa Lobo vs. Perro

**Actor:** Especialista en canis buscando distinguir registros.

**Flujo:**
1. Generar dos CSV: uno con `specificEpithet == 'lupus'`, otro con `familiaris`.
2. Comparar distribución geográfica (lobo concentrado en noroeste, perro distribuido).
3. Comparar metodologías (lobo: fototrampeo + indicios; perro: observación visual).
4. Crear mapas separados para cada subespecie.

**Resultado esperado:**
- 315 registros de lobo en Galicia, Castilla y León, Asturias.
- 285 registros de perro en ciudades y periferias.
- Tablas comparativas de evidencias.

---

### CU4: Validación de Calidad de Datos

**Actor:** Data steward responsable de auditar GBIF.

**Flujo:**
1. Revisar campos `issues` (incidencias señaladas por GBIF).
2. Validar cobertura de `coordinateUncertaintyInMeters`.
3. Verificar que no haya valores ausentes en variables críticas.
4. Documentar porcentaje de registros con `informationWithheld` (ofuscación de iNaturalist).
5. Generar reporte de calidad.

**Resultado esperado:**
- Reporte mostrando 98.8% de cobertura en datos GADM.
- 27.6 km de incertidumbre media en registros sensibles.
- Lista de incidencias detectadas por GBIF.

---

### CU5: Integración en Pipeline ETL Corporativo

**Actor:** Ingeniero de datos construyendo data warehouse de biodiversidad.

**Flujo:**
1. Usar funciones auxiliares (`obtener_taxon_key()`, `descargar_avistamientos_paginados()`) en scripts Python reutilizables.
2. Integrar en orquestador (Airflow, dbt, etc.).
3. Cargar CSV a base de datos (PostgreSQL, BigQuery).
4. Crear vistas analíticas por provincia, año, especie.
5. Generar reportes automáticos.

**Resultado esperado:**
- Pipeline reproducible que actualiza datos cada mes.
- Base de datos sincronizada con GBIF.
- Reportes automáticos de nuevos registros.

---

## 4. Diagramas UML Principales

### 4.1 Diagrama de Clases (Conceptual)

```
┌─────────────────────────────────────────┐
│          APIConsumer (Abstracto)         │
│─────────────────────────────────────────│
│ - session: requests.Session              │
│ - base_url: str                          │
│ - timeout: int                           │
├─────────────────────────────────────────┤
│ + query(): dict                          │
│ + paginate(): list                       │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────────┐  ┌──────────────────────┐
│  SpeciesAPI      │  │  OccurrenceAPI       │
│──────────────────│  │──────────────────────│
│+ match_taxon()   │  │+ search_occurrences()│
│  → usageKey      │  │  → results[]         │
└──────────────────┘  └──────────────────────┘

┌─────────────────────────────────────────┐
│       Record (OccurrenceRecord)          │
│─────────────────────────────────────────│
│ - key: int (occurrenceID)                │
│ - taxonKey: int                          │
│ - scientificName: str                    │
│ - specificEpithet: str (lupus|familiaris)│
│ - eventDate: datetime                    │
│ - decimalLatitude: float                 │
│ - decimalLongitude: float                │
│ - gadm: GADM (nested)                    │
│ - vitality: str (alive|dead)             │
│ - samplingProtocol: str                  │
│ - issues: list[str]                      │
│ - dynamicProperties: dict                │
├─────────────────────────────────────────┤
│ + is_valid(): bool                       │
│ + extract_evidence(): str                │
│ + normalize_territory(): GADM            │
└─────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│          GADM (Territory)                 │
│──────────────────────────────────────────│
│ - level1: {name: str, id: str}           │
│ - level2: {name: str, id: str}           │
│ - level3: {name: str, id: str}           │
└──────────────────────────────────────────┘
```

---

### 4.2 Diagrama de Secuencia: Flujo de Descarga

```
Usuario
  │
  ├─→ obtener_taxon_key("Canis lupus")
  │     │
  │     └─→ SpeciesAPI.match()
  │           │ HTTP GET /v1/species/match
  │           │ ← {usageKey: 5219173, matchType: "EXACT"}
  │           └─→ Validar matchType == "EXACT"
  │
  ├─→ contar_registros_gbif(params)
  │     │
  │     ├─ OccurrenceAPI.search(limit=1, offset=0)
  │     │ HTTP GET /v1/occurrence/search
  │     │ ← {count: 2390, results: [...]}
  │
  ├─→ descargar_avistamientos_paginados(params)
  │     │
  │     ├─ Offset=0: OccurrenceAPI.search(limit=200)
  │     │   ← {results: 200 records, endOfRecords: false}
  │     │
  │     ├─ Offset=200: OccurrenceAPI.search(limit=200)
  │     │   ← {results: 200 records, endOfRecords: false}
  │     │
  │     ├─ Offset=400: OccurrenceAPI.search(limit=200)
  │     │   ← {results: 200 records, endOfRecords: true}
  │     │
  │     └─→ return [600 registros], count=2390
  │
  ├─→ pd.json_normalize(registros_crudos)
  │     → DataFrame (600 filas × 180+ columnas)
  │
  ├─→ Filtrar specificEpithet == 'lupus'
  │     → 315 registros de lobo
  │
  ├─→ Exportar a CSV
  │     → registros_biodiversidad_gbif.csv
  │
  └─→ Generar mapa Folium
        → mapa_avistamientos_gbif.html
```

---

### 4.3 Diagrama de Entidad-Relación (Conceptual)

```
┌──────────────────────────────────┐
│         Occurrence               │
│  (Registro de Presencia)         │
├──────────────────────────────────┤
│ PK: occurrenceID (int)           │
│ FK: taxonKey (int)               ├──────┐
│ FK: datasetKey (uuid)            │      │
│ eventDate (datetime)             │      │
│ decimalLatitude (float)          │      │
│ decimalLongitude (float)         │      │
│ vitality (enum)                  │      │
│ samplingProtocol (str)           │      │
│ coordinateUncertaintyInMeters    │      │
│ informationWithheld (bool)       │      │
└──────────────────────────────────┘      │
         │                                 │
         │ 1:N                             │
         ▼                                 │
┌──────────────────────────────────┐      │
│    Taxon                         │      │
│ (Especie)                        │      │
├──────────────────────────────────┤      │
│ PK: usageKey (int)              │◄─────┘
│ scientificName (str)             │
│ specificEpithet (str)            │
│ kingdom (str)                    │
│ phylum (str)                     │
│ class (str)                      │
│ order (str)                      │
│ family (str)                     │
│ genus (str)                      │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│    Dataset (Proveedor)           │
├──────────────────────────────────┤
│ PK: datasetKey (uuid)            │
│ datasetName (str)                │
│ organization (str)               │
│ contactEmail (str)               │
│ rights (str)                     │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│    Territory (GADM)              │
├──────────────────────────────────┤
│ gid_1 (str)                      │
│ name_1 (str) ← Comunidad Aut.    │
│ gid_2 (str)                      │
│ name_2 (str) ← Provincia         │
│ gid_3 (str)                      │
│ name_3 (str) ← Municipio         │
└──────────────────────────────────┘
```

---

### 4.4 Diagrama de Flujo de Transformación de Datos

```
START
  ↓
┌─────────────────────────────────────┐
│ 1. Descargar JSON (API GBIF)        │
│    - 600 registros                  │
│    - 130 campos (Darwin Core)       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 2. Guardar JSON Bruto               │
│    registros_gbif_brutos.json       │
│    (muestra del cuaderno 01)        │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 3. Normalizar JSON con pandas       │
│    - Aplanar campos anidados        │
│    - Crear DataFrame (600×180+)     │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 4. Separar Taxones                  │
│    - 315 registros: lupus           │
│    - 285 registros: familiaris      │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 5. Normalizar Territorio            │
│    - Reemplazar stateProvince       │
│    - Usar gadm.level1/2/3.name      │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 6. Extraer Evidencias               │
│    - samplingProtocol               │
│    - dynamicProperties.evidence     │
│    - Crear metodo_o_evidencia       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 7. Validar Calidad                  │
│    - Revisar issues                 │
│    - Validar coordenadas            │
│    - Detectar ofuscación            │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 8. Exportar CSV                     │
│    registros_biodiversidad_gbif.csv │
│    - UTF-8, delimitador ','         │
│    - 600 filas × 60+ columnas       │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 9. Generar Mapa Interactivo         │
│    mapa_avistamientos_gbif.html     │
│    - Folium + Leaflet JS            │
│    - Clustering + PopUps            │
└──────────────┬──────────────────────┘
               ↓
        END (Resultados listos)
        ✓ JSON
        ✓ CSV
        ✓ HTML Map
```

---

## 5. Guía de Inicio Rápido

### Instalación (Windows con `uv`):
```bash
cd C:\Users\chuwi\Documents\biodiversidad

# Crear entorno virtual Python 3.14
uv venv --python 3.14 .venv

# Activar (PowerShell)
.venv\Scripts\Activate.ps1

# Instala exactamente lo declarado en pyproject.toml (matplotlib, seaborn e ipykernel incluidos).
# Si no sabes si el entorno ya tiene todas las librerías, vuelve a lanzarlo.
uv sync --system-certs

# Registrar kernel para Jupyter
.venv\Scripts\python.exe -m ipykernel install --user --name=biodiversidad --display-name="Python (biodiversidad)"
```

El entorno virtual es la carpeta `.venv`. El kernel **Python (biodiversidad)** es el nombre con el que Jupyter muestra el intérprete `.venv\Scripts\python.exe`. En la red de la Junta, `uv` necesita `--system-certs`. Si no, el certificado del proxy Netskope corta la descarga de paquetes.

### Ejecución:
1. Abrir `notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb`.
2. Seleccionar el kernel **Python (biodiversidad)**.
3. Ejecutar todas las celdas en orden.
4. Revisar salidas en `datos/` y `salidas_gbif_multiespecie/`.

Dos ventanas de escritorio, desde la raíz del proyecto:

```powershell
python app_tkinter.py
python interfaz_gbif.py
```

`app_tkinter.py` es la ventana de MySQL. Al abrirla ya hay una consulta. En Consultar el país es un código ISO (`FR`), varios (`ES, PT`) o Todos, y el tiempo es un año, un intervalo de años o un intervalo de fechas (`2018-03-01`). Hasta vacío llega hasta hoy. La pestaña muestra la ficha del registro, el mapa y el CSV de lo que está en pantalla. Las pestañas van en este orden: Traer datos de GBIF, Consultar e Indicadores. Indicadores calcula, al entrar, el volumen de toda la base. A la izquierda se elige territorio, cobertura de campos, evidencia y estado, taxonomía, calidad del registro o quién publica. La tabla queda arriba y el gráfico debajo. Si el tema tiene varios gráficos, los botones de la zona del gráfico eligen uno: en Volumen, por país, por año, por mes o país y año. Contraer datos oculta la tabla para que el gráfico use ese espacio; Mostrar datos la devuelve. La división entre tabla y gráfico se arrastra, y si el gráfico no cabe aparece una barra para recorrerlo. País en Todos y fechas vacías miden toda la base; el mismo valor en Desde y Hasta deja solo ese año o ese día. La línea de abajo recuerda que un conteo de registros mide publicación, no abundancia. Traer datos de GBIF explica cómo se descarga: `/v1/species/match`, luego `/v1/occurrence/search` por país (solo con coordenadas y con el periodo escrito, hasta el máximo), y al final el taxón, las organizaciones, los datasets y las ocurrencias en MySQL. Cargar especies disponibles lista hasta cinco especies de cada clase con coordenadas para esos países y esas fechas; pulsar una fila rellena Especie. Hay barra de progreso y se puede cancelar antes de escribir. La conexión sale de `.env` a través de `src/database.py`. `interfaz_gbif.py` consulta la API, crea y puebla SQLite o MySQL, filtra el listado y exporta a CSV, JSON y HTML. El detalle está en [CUADERNOS.md](./CUADERNOS.md) y en [documentacion_del_pipeline_gbif_y_mysql_8.md](./documentacion_del_pipeline_gbif_y_mysql_8.md).

Los mismos indicadores se pueden imprimir por consola, con el entorno activado y la base ya cargada. Desde la raíz del proyecto:

```powershell
.venv\Scripts\Activate.ps1
python src\kpi_volumen.py
python src\kpi_territorio.py
python src\kpi_cobertura.py
python src\kpi_evidencia.py
python src\kpi_taxonomia.py
python src\kpi_calidad.py
python src\kpi_publicadores.py
```

Sin cambios, cada script mide toda la base. País, año o intervalo se acotan con `FiltroKpi` dentro del script. La sección 4.9 del documento de MySQL describe cada consulta.

**Especies con coordenadas** lista cinco especies de cada clase (mamíferos, escamosos, anfibios, insectos, plantas y aves), con su familia. Pulsar una fila la escribe arriba. **Limpiar** devuelve *Canis lupus*. Ver taxón, Ver ocurrencias, Poblar y la pestaña Consultas usan esa especie. La exportación propone un fichero con su nombre (`turdus_merula.csv`, `.json` o `.html`) y lo repite dentro del archivo: columna en el CSV, campo `especie` en el JSON y recuadro en el mapa. El mismo catálogo, sin descargar ocurrencias, está en [`gbif_especies_por_clase_es_pt.ipynb`](../notebooks/gbif_especies_por_clase_es_pt.ipynb).

La base tiene que estar iniciada antes de usar Poblar o la pestaña Consultas.

- SQLite no tiene servidor. Iniciarla es pulsar Crear (o `python src\gbif_biodiversidad_sqlite.py`). El archivo que usa el proyecto es `datos/gbif_biodiversidad.sqlite`. El `gbif_biodiversidad.sqlite` de la raíz es otra copia y no recibe la carga.
- MySQL 8 tiene que estar en marcha, con la base `gbif_biodiversidad` creada, antes de Crear, Poblar o Consultas.

### Comparación de los cuadernos y mapas

| Característica | 01: mortalidad en España | 04: archivo del catálogo ES+PT |
|---|---|---|
| Cuaderno | [`exploracion_01_canis_lupus_espana_mortalidad.ipynb`](../notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb) | [`exploracion_04_archivo_catalogo_es_pt.ipynb`](../notebooks/exploracion_04_archivo_catalogo_es_pt.ipynb) |
| Ámbito por defecto | España (`country=ES`) | España y Portugal (`country=ES` y `country=PT`) |
| Consulta principal | *Canis lupus*, 2020–2026, con coordenadas y sin incidencias geoespaciales señaladas por GBIF | Mismos filtros de especie, periodo y calidad espacial, pero para ambos países. La especie y el periodo se configuran en el cuaderno |
| Límite | Hasta 600 registros para ES | Hasta 600 registros **en total** para ES+PT, no 600 por país |
| CSV | `registros_biodiversidad_gbif.csv`: campos enriquecidos, entre ellos `acceptedScientificName`, `specificEpithet`, `vitality` y territorios GADM | `registros_<especie>_es_pt.csv`: 13 columnas seleccionadas, entre ellas `scientificName`, `countryCode` y `stateProvince` |
| Mapa | `mapa_avistamientos_gbif.html`: verde para `specificEpithet == "lupus"` y marrón para los demás valores; la ficha muestra el nombre aceptado cuando está disponible | `mapa_<especie>_es_pt.html`: verde para ES y rojo para PT; la ficha muestra el nombre oficial del taxón consultado, **no necesariamente el nombre propio del registro** |

La coincidencia de filtros para España no implica que ambas **muestras** españolas sean iguales: al pedir ES+PT, los registros portugueses ocupan parte del límite de 600 y cambia el conjunto de resultados paginados. El límite es global y no garantiza una cuota para cada país. El orden, los datos publicados en GBIF y los totales pueden cambiar entre ejecuciones.

**Ejemplo observado el 22–23 de noviembre de 2026**, con *Canis lupus* (`taxonKey=5219173`):

- GBIF indicaba 2.390 registros para ES y 296 para PT con los filtros principales; 2.686 para ES+PT. Estos son totales disponibles, no tamaños de las descargas.
- El mapa del cuaderno 01 contenía 600 registros de ES. El del cuaderno 04 contenía 534 de ES y 66 de PT. Compartían los 534 registros españoles, con las mismas coordenadas; los otros 66 registros españoles del 01 no aparecían en el 04.
- Ambas muestras eran parciales. Los agrupamientos de marcadores y el encuadre también pueden cambiar la apariencia al variar el zoom o el ámbito.
- Por ejemplo, la ficha GBIF `6131493059` aparecía en ambos mapas: el cuaderno 01 mostraba *Canis lupus familiaris* como nombre aceptado, mientras el 04 mostraba *Canis lupus* por ser el nombre consultado. El nombre registrado en ambos CSV era *Canis familiaris*. No debe interpretarse la etiqueta del 04 como identificación individual del registro.

Los nombres binomiales simples se normalizan antes de consultar GBIF y se comprueba la coincidencia del nombre canónico. Para otros formatos, como nombres con autor, revisa el taxón resuelto. El `taxonKey` puede incluir registros relacionados con perros; consulta los campos taxonómicos de cada registro antes de sacar conclusiones.

Para comparar resultados, usa los identificadores `key` y las coordenadas, mantén los mismos filtros y ámbito, y comprueba `total_disponible_gbif` y `MAX_REGISTROS`. Si el total supera el límite, las estadísticas sólo describen la muestra descargada, no todas las ocurrencias disponibles.

### Otros cuadernos

| Cuaderno | Para qué usarlo |
|---|---|
| [`exploracion_02_catalogo_especies_es_pt.ipynb`](../notebooks/exploracion_02_catalogo_especies_es_pt.ipynb) | Catálogo vigente de ES+PT y descarga de una especie. Para trabajo nuevo, usa este y no el 04. |
| [`exploracion_03_canis_lupus_es_pt_altitud.ipynb`](../notebooks/exploracion_03_canis_lupus_es_pt_altitud.ipynb) | *Canis lupus* en ES y PT, 2020–2026, solo entre 1.000 y 3.000 m, sin perro doméstico. |
| [`gbif_especies_por_clase_es_pt.ipynb`](../notebooks/gbif_especies_por_clase_es_pt.ipynb) | Ver cinco especies de cada clase (mamíferos, escamosos, anfibios, insectos, plantas y aves) antes de descargarlas. |
| [`gbif_multiespecie_es_pt.ipynb`](../notebooks/gbif_multiespecie_es_pt.ipynb) | Lobo, lince, oso y quebrantahuesos: CSV por especie, CSV maestro y mapas, sin base de datos. |
| [`gbif_multiespecie_es_pt_sqlite_mysql.ipynb`](../notebooks/gbif_multiespecie_es_pt_sqlite_mysql.ipynb) | El mismo lote multi-especie más SQLite (`biodiversidad_gbif.db`) y, en opción, MySQL. Antes se llamaba `gbif_multiespecie_es_pt (1).ipynb`. |
| [`ingesta_gbif_mysql.ipynb`](../notebooks/ingesta_gbif_mysql.ipynb) y [`analisis_offline_gbif.ipynb`](../notebooks/analisis_offline_gbif.ipynb) | Pipeline MySQL del esquema de `src/` (ingesta y análisis sin red). |

Esa base multi-especie no es `datos/gbif_biodiversidad.sqlite`. La segunda la crean `src/ingesta_gbif_sqlite.py` y la interfaz, con organizaciones y datasets del Registry.

### Modo Offline (si ya tienes `datos/registros_gbif_brutos.json`):
```python
import json
with open("datos/registros_gbif_brutos.json", encoding="utf-8") as f:
    registros_crudos = json.load(f)
# Luego ejecutar solo las celdas de análisis (Sección 3+)
```

---

## 6. Referencias y Recursos

| Recurso | URL |
|---------|-----|
| Documentación oficial GBIF | https://www.gbif.org/developer/summary |
| Occurrence API (OpenAPI 3.1) | https://techdocs.gbif.org/en/openapi/v1/occurrence |
| Species API (OpenAPI 3.1) | https://techdocs.gbif.org/en/openapi/v1/species |
| Darwin Core Standard | https://dwc.tdwg.org/ |
| Diccionario de datos GBIF | docs/diccionario_datos_gbif.md |
| Mapa interactivo generado | mapa_avistamientos_gbif.html |

---

## 7. Troubleshooting

### Problema: "GBIF no ha encontrado un taxón"
**Solución:** Verificar nombre científico (ej: `Canis lupus`, no `Canis lupus lupus`).

### Problema: Timeout en descarga
**Solución:** Aumentar `timeout=30` → `timeout=60` en las funciones API.

### Problema: Rate limit (429 Too Many Requests)
**Solución:** Aumentar `pausa_segundos` de 0.2 a 1.0 en `descargar_avistamientos_paginados()`.

### Problema: "Registros descargados: 0"
**Solución:** Revisar diagnóstico progresivo. Algún filtro está dejando 0 resultados.

### Problema: `CERTIFICATE_VERIFY_FAILED` / certificado autofirmado
**Solución:** En esta red, Netskope intercepta HTTPS. `src/ingesta_gbif_sqlite.py` y `src/volcarEndpoints.py` cargan `truststore` para usar el almacén de Windows. Instala `truststore` en el mismo intérprete si el cuaderno no pasa por esos módulos.

### Problema: Poblar o Consultas no ven la base
**Solución:** La base tiene que estar iniciada. En SQLite, pulsa Crear y abre `datos/gbif_biodiversidad.sqlite`, no el archivo homónimo de la raíz. En MySQL, arranca el servidor y pulsa Crear antes de poblar.

### Problema: la base SQLite existe pero las tablas están a cero
**Solución:** `guardar_en_sqlite.py` no descarga nada si se ejecuta solo. La ingesta es `python src\ingesta_gbif_sqlite.py` o el botón Poblar de la interfaz. El archivo vigente es `datos/gbif_biodiversidad.sqlite`.

---

**Versión:** 1.3  
**Última actualización:** 2026-11-26  
**Autor:** Copilot SDK + gracobjo
