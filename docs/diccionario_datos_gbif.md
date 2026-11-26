# Diccionario de Datos del JSON de GBIF (`datos/registros_gbif_brutos.json`)

Este documento describe la estructura y cobertura de los **600 registros** descargados desde el endpoint `/v1/occurrence/search` de la API pública de GBIF para `taxonKey=5219173` (*Canis lupus* en España, 2020–2026).

El archivo JSON bruto contiene **130 campos de nivel superior**, que al aplanarse con `pd.json_normalize()` generan **181 columnas**. Tras la limpieza y creación de variables derivadas en el notebook, el DataFrame principal `df` conserva **42 columnas** organizadas en seis bloques temáticos.

---

## 1. Taxonomía e identificación

| Campo en JSON / DataFrame | Cobertura (600 reg.) | Tipo | Significado y utilidad práctica |
| :--- | :---: | :---: | :--- |
| **`key`** / `gbifID` | 100 % | `string` / `int` | Identificador único del registro en GBIF (`https://www.gbif.org/occurrence/<key>`). |
| **`specificEpithet`** | 100 % | `string` | Epíteto específico del nombre suministrado. **Clave para subconsultas:** permite separar lobo salvaje (`lupus`, 315 reg.) de perro doméstico/asilvestrado (`familiaris`, 285 reg.). |
| **`acceptedScientificName`** | 100 % | `string` | Nombre científico válido según el *GBIF Backbone Taxonomy* (`Canis lupus Linnaeus, 1758` frente a `Canis lupus familiaris Linnaeus, 1758`). |
| **`scientificName`** | 100 % | `string` | Nombre tal como fue publicado originalmente por la fuente (incluye sinónimos como `Canis familiaris Linnaeus, 1758`). |
| **`taxonomicStatus`** | 100 % | `string` | Estado taxonómico en GBIF: `ACCEPTED` (315) o `SYNONYM` (285, aplicado a *Canis familiaris*). |
| **`taxonRank`** | 100 % | `string` | Rango taxonómico resuelto (`SPECIES`, `SUBSPECIES`). |
| **`vernacularName`** | 21,3 % | `string` | Nombre común informado por el proveedor (p. ej., `Feral Dog` en Observation.org). |
| *Otros en JSON bruto* | 100 % | Varios | `kingdom`, `phylum`, `class`, `order`, `family`, `genus`, `species`, sus respectivas claves (`*Key`), `iucnRedListCategory` (`LC` para lobo, `NE` para perro) y la jerarquía completa en `classifications`. |

---

## 2. Espacio y división administrativa

| Campo en JSON / DataFrame | Cobertura (600 reg.) | Tipo | Significado y utilidad práctica |
| :--- | :---: | :---: | :--- |
| **`decimalLatitude`** | 100 % | `float` | Latitud decimal en datum WGS84. |
| **`decimalLongitude`** | 100 % | `float` | Longitud decimal en datum WGS84. |
| **`coordinateUncertaintyInMeters`** | 91,3 % | `float` | Radio de incertidumbre espacial en metros (desde `2.0` m en puntos exactos hasta `~27500` m cuando iNaturalist ofusca coordenadas de especies protegidas). |
| **`informationWithheld`** | 36,8 % | `string` | Motivo por el que se ha degradado la precisión espacial (p. ej., *"Coordinate uncertainty increased to 27661m to protect threatened taxon"*). |
| **`comunidad_gadm`** (`gadm.level1.name`) | 98,8 % | `string` | Comunidad Autónoma normalizada por GBIF mediante cartografía GADM (elimina variantes como *Asturias* vs. *Principado de Asturias*). |
| **`provincia_gadm`** (`gadm.level2.name`) | 98,8 % | `string` | Provincia normalizada por GBIF (Zamora, Ourense, Asturias, Jaén, Albacete, etc.). |
| **`comarca_gadm`** (`gadm.level3.name`) | 98,8 % | `string` | Subdivisión administrativa de nivel 3 (comarca o municipio según disponibilidad de GADM; en algunos códigos figura como `n.a. (código)`). |
| **`stateProvince`** | 79,0 % | `string` | Región o comunidad tal como la escribió el proveedor original. |
| **`locality`** | 33,0 % | `string` | Nombre del paraje, término municipal o localidad puntual. |
| *Otros en JSON bruto* | Variable | Varios | `gadm.level0` (`ESP`), códigos `gid` de cada nivel GADM, `verbatimLocality` (54,5 %, texto original sin normalizar), `municipality` (1,8 %) y `county` (1,8 %). |

---

## 3. Dimensión temporal

| Campo en JSON / DataFrame | Cobertura (600 reg.) | Tipo | Significado y utilidad práctica |
| :--- | :---: | :---: | :--- |
| **`eventDate`** | 100 % | `string` | Fecha (y en ocasiones hora) del evento en formato ISO 8601. |
| **`eventDateParsed`** *(derivada)* | 29,8 % | `datetime` | Conversión estricta a fecha UTC en Pandas para los registros con formato ISO completo. |
| **`eventTime`** | 77,2 % | `string` | Hora exacta del registro con desplazamiento horario (p. ej., `14:29:08+01:00` o intervalo `12:05/13:04`). |
| **`hora_evento`** *(derivada)* | 77,2 % | `float/int` | Hora entera (`0` a `23`) extraída de `eventTime` para analizar patrones de actividad diurna, crepuscular y nocturna. |
| **`year`**, **`month`**, **`day`** | 100 % | `int` | Año, mes y día desglosados como enteros. |
| **`startDayOfYear`** | 100 % | `int` | Día juliano del año (`1` a `366`), útil para comparar fenología y estacionalidad interanual. |

---

## 4. Biología, estado vital y evidencia de presencia

| Campo en JSON / DataFrame | Cobertura (600 reg.) | Tipo | Significado y utilidad práctica |
| :--- | :---: | :---: | :--- |
| **`vitality`** | 4,7 % (28 reg.) | `string` | Estado vital del ejemplar: `alive` (18), `dead` (7 — atropellos, hallazgos de cadáveres/huesos) y `undetermined` (3). |
| **`individualCount`** | 32,8 % | `float/int` | Número de individuos detectados en ese evento cuando se contabilizan. |
| **`lifeStage`** | 22,8 % | `string` | Clase de edad (`Adult`, `Juvenile`, `Unknown`). |
| **`sex`** | 0,7 % (4 reg.) | `string` | Sexo del animal cuando ha podido determinarse (`Female`, `Male`). |
| **`dynamicProperties`** | 60,8 % | `string` (JSON) | Cadena JSON con metadatos adicionales del proveedor; en iNaturalist recoge **`evidenceOfPresence`** (`organism`, `scat` [excremento], `track` [huella], `bone` [hueso]). |
| **`basisOfRecord`** | 100 % | `string` | Naturaleza del registro Darwin Core (`HUMAN_OBSERVATION`, `MACHINE_OBSERVATION`, `PRESERVED_SPECIMEN`, etc.). |
| **`occurrenceStatus`** | 100 % | `string` | Presencia o ausencia (`DETECTED` / `PRESENT`). |

---

## 5. Metodología, esfuerzo y contexto ambiental

| Campo en JSON / DataFrame | Cobertura (600 reg.) | Tipo | Significado y utilidad práctica |
| :--- | :---: | :---: | :--- |
| **`samplingProtocol`** | 41,8 % | `string` | Método o protocolo de muestreo empleado: `paw prints` (huellas), `Fototrampeo General`, `Camera trap`, `excreta` (excrementos), `seen` (avistamiento directo), `Multiespecie en un punto`, etc. |
| **`samplingEffort`** | 20,3 % | `string` | Esfuerzo invertido en el muestreo (p. ej., `70 camera-trap days`, `49 camera-trap days`, `20 minutes`, `Distancia 0.6 km; Tiempo 56 min`). |
| **`habitat`** | 21,2 % | `string` | Descripción del hábitat consignada en el muestreo. |
| *Otros en JSON bruto* | 0,2 %–18,3 % | `string` | `occurrenceRemarks` (18,3 %, notas de campo del observador), `fieldNotes` (0,2 %), `behavior` (0,2 %, p. ej. `call` [aullido]) y `preparations` (0,2 %, p. ej. `field recording`). |

---

## 6. Procedencia, auditoría y calidad de datos

| Campo en JSON / DataFrame | Cobertura (600 reg.) | Tipo | Significado y utilidad práctica |
| :--- | :---: | :---: | :--- |
| **`issues`** (`issues_str` y `num_issues`) | 79,0 % con avisos | `list` / `string` | Banderas de validación automática de GBIF (`COORDINATE_ROUNDED`, `TAXON_ID_NOT_FOUND`, `CONTINENT_DERIVED_FROM_COORDINATES`, etc.). |
| **`institutionCode`** / **`datasetName`** | 78,7 % | `string` | Plataforma o institución que publica el dato (p. ej. `iNaturalist`) y nombre del conjunto de datos. |
| **`publishingCountry`** | 100 % | `string` | País del publicador en GBIF (`ES`, `US` para iNaturalist global, `NL` para Observation.org, `PT`). |
| **`recordedBy`** / **`identifiedBy`** | 98,0 % / 56,2 % | `string` | Autor de la observación y persona que validó la identificación taxonómica. |
| **`references`** | 56,3 % | `string` (URL) | Enlace directo a la observación original (p. ej., ficha en iNaturalist con fotografías). |
| **`license`** | 100 % | `string` | Licencia Creative Commons aplicable al uso y redistribución del registro. |
| *Otros en JSON bruto* | Variable | Varios | `media` / `extensions` (74,5 %, enlaces directos a imágenes JPEG), `datasetKey`, `lastCrawled`, `lastParsed` y metadatos internos de ingesta (`http://unknown.org/*`, `crawlId`). |