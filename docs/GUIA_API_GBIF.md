# 🌍 Guía Explicativa del API GBIF: Global Biodiversity Information Facility

## Tabla de Contenidos
1. [¿Qué es GBIF?](#qué-es-gbif)
2. [¿Para qué sirve la API de GBIF?](#para-qué-sirve-la-api-de-gbif)
3. [Arquitectura del API](#arquitectura-del-api)
4. [Sub-APIs principales](#sub-apis-principales)
5. [Flujo de consulta típico](#flujo-de-consulta-típico)
6. [Limitaciones y sesgos importantes](#limitaciones-y-sesgos-importantes)
7. [Casos de uso del mundo real](#casos-de-uso-del-mundo-real)

---

## ¿Qué es GBIF?

**GBIF** (*Global Biodiversity Information Facility*) es una infraestructura internacional de código abierto que **agrega datos de biodiversidad procedentes de miles de instituciones científicas, agencias gubernamentales y ciudadanos de todo el mundo**.

### Visión
Poner a disposición de cualquier persona, en cualquier lugar, información sobre cualquier especie de la Tierra. GBIF actúa como un **repositorio centralizado y gratuito** donde se publican observaciones de vida silvestre, especímenes de museos, trampas de cámara, datos genómicos, y registros de herbarios.

### Fundado
- **Año:** 2001 por la OCDE (Organización para la Cooperación y el Desarrollo Económico).
- **Secretaría:** Copenhague, Dinamarca.
- **Participantes:** 60+ países + 1000+ instituciones.

### Estándares
GBIF normaliza todos sus datos bajo el estándar **Darwin Core**, un vocabulario internacional mantenido por TDWG (Taxonomic Databases Working Group) que define cómo describir un avistamiento o especímen:
- Especie (nombre científico, identificador taxonómico).
- Dónde (latitud, longitud, país, provincia).
- Cuándo (fecha, hora).
- Cómo (metodología de observación).
- Quién (observador, institución que publicó).

---

## ¿Para qué sirve la API de GBIF?

La **API REST pública de GBIF** permite a programadores, científicos e ingenieros de datos:

### 1. **Automatizar descargas**
En lugar de navegar por la web de GBIF y hacer clic en botones, puedes escribir un script Python/R/JavaScript que descargue **miles de registros en segundos**.

### 2. **Consultar dinámicamente**
- *¿Cuántos registros de *Canis lupus* hay en España entre 2020 y 2026?*
- *¿Dónde se han visto especies invasoras en Italia?*
- *¿Qué registros de pájaros en peligro de extinción existen en mi provincia?*

Responde el API, sin esperar respuesta manual.

### 3. **Integrar en pipelines de datos**
Los ecólogos, biólogos computacionales e ingenieros de datos pueden **actualizar automáticamente sus bases de datos** cada semana/mes con nuevos registros de GBIF.

### 4. **Validar taxonomía en tiempo real**
¿No estás seguro del `taxonKey` de una especie? El API te dice el identificador correcto y si el nombre científico es válido o está deprecado.

### 5. **Construir herramientas interactivas**
Mapas web, dashboards, aplicaciones móviles que muestren registros de biodiversidad de forma interactiva.

### 6. **Fines educativos**
Enseñar biología, ecología, ciencia de datos con datos reales de biodiversidad.

---

## Arquitectura del API

GBIF expone **múltiples sub-APIs** organizadas en dominios funcionales:

```
┌────────────────────────────────────────────────────┐
│          GBIF REST API (api.gbif.org)              │
├────────────────────────────────────────────────────┤
│                                                    │
│  Versión: v1 (actual)                             │
│  Protocolo: HTTP/HTTPS                            │
│  Formato: JSON (con OpenAPI 3.1)                  │
│                                                    │
├─── Dominio 1: OCCURRENCE (Presencia de Especie) ──┤
│  ├─ /v1/occurrence/search                         │
│  │  └─ Buscar registros de avistamientos          │
│  ├─ /v1/occurrence/{key}                          │
│  │  └─ Obtener detalles de 1 registro             │
│  └─ /v1/occurrence/{key}/related                  │
│     └─ Registros relacionados del mismo sitio     │
│                                                    │
├─── Dominio 2: SPECIES/TAXON (Taxonomía) ───────────┤
│  ├─ /v1/species/match                             │
│  │  └─ Validar nombre y obtener usageKey          │
│  ├─ /v1/species/{key}                             │
│  │  └─ Obtener info completa de una especie       │
│  └─ /v1/species/{key}/related                     │
│     └─ Especies relacionadas (sinónimos, etc)     │
│                                                    │
├─── Dominio 3: REGISTRY (Metadatos) ────────────────┤
│  ├─ /v1/dataset                                   │
│  │  └─ Listar datasets (colecciones de GBIF)      │
│  ├─ /v1/organization                              │
│  │  └─ Listar organizaciones publicadoras         │
│  └─ /v1/installation                              │
│     └─ Listar instalaciones técnicas (nodos)      │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## Sub-APIs principales

### 1️⃣ Occurrence API (`/v1/occurrence/search`)

**¿Qué es?**  
El "corazón" de GBIF. Busca registros de avistamientos, especímenes, o evidencias de especies.

**¿Qué devuelve?**  
Una lista de **ocurrencias** (cada una es un avistamiento único) con 130+ campos en formato JSON.

**Parámetros de filtro más comunes:**

| Parámetro | Tipo | Ejemplo | Descripción |
|-----------|------|---------|-------------|
| `taxonKey` | int | `5219173` | ID único de la especie (obtenido de Species API) |
| `country` | str | `ES` | Código ISO 2 del país |
| `year` | str | `2020,2026` | Rango de años (separado por coma) |
| `hasCoordinate` | bool | `true` | Solo registros con latitud/longitud |
| `hasGeospatialIssue` | bool | `false` | Excluir registros con problemas geoespaciales |
| `basisOfRecord` | str | `HUMAN_OBSERVATION` | Tipo de dato: observación, especímen, fósil, etc. |
| `samplingProtocol` | str | `Camera trap` | Metodología de captura |
| `eventDate` | str | `2024-01-01,2024-12-31` | Rango de fechas ISO 8601 |
| `limit` | int | `300` | Registros por página (máx 300) |
| `offset` | int | `0` | Paginación (posición de inicio) |

**Respuesta típica:**
```json
{
  "offset": 0,
  "limit": 300,
  "endOfRecords": false,
  "count": 2390,
  "results": [
    {
      "key": 3889711882,
      "datasetKey": "7629de6e-11f1-45e8-8b6e-50334cdd5467",
      "occurrenceID": "...",
      "kingdom": "Animalia",
      "phylum": "Chordata",
      "class": "Mammalia",
      "order": "Carnivora",
      "family": "Canidae",
      "genus": "Canis",
      "species": "Canis lupus",
      "specificEpithet": "lupus",
      "scientificName": "Canis lupus Linnaeus, 1758",
      "taxonKey": 5219173,
      "eventDate": "2023-05-15",
      "eventTime": "14:30:00",
      "decimalLatitude": 42.5126,
      "decimalLongitude": -6.2746,
      "coordinateUncertaintyInMeters": 100,
      "country": "Spain",
      "countryCode": "ES",
      "stateProvince": "Galicia",
      "county": "Pontevedra",
      "municipality": "Vigo",
      "samplingProtocol": "Camera trap network",
      "basisOfRecord": "HUMAN_OBSERVATION",
      "vitality": "alive",
      "individualCount": 1,
      "occurrenceRemarks": "Single wolf, nighttime",
      "issues": [],
      "gadm": {
        "level1": {
          "name": "Galicia",
          "gid": "ESP.14_1"
        },
        "level2": {
          "name": "Pontevedra",
          "gid": "ESP.14.1_1"
        }
      },
      "institutionCode": "MOMAT",
      "institutionKey": "..."
    }
    // ... más registros
  ]
}
```

**Notas importantes:**
- `endOfRecords: false` → hay más páginas disponibles. Incrementa `offset` y repite.
- `endOfRecords: true` → última página.
- `count` = **total de registros que cumplen los filtros** (puede ser mucho mayor que `limit`).

---

### 2️⃣ Species API (`/v1/species/match`)

**¿Qué es?**  
Validador taxonómico. Convierte nombres científicos en identificadores únicos (`usageKey` o `taxonKey`).

**¿Por qué es crítico?**  
En GBIF, cada especie tiene un ID único. No puedes buscar por nombre de texto libre en Occurrence API; necesitas el `taxonKey`. Además, elimina ambigüedades:
- ¿*Canis lupus* o *Canis lupus lupus*?
- ¿Especie actual o sinónimo deprecado?

**Parámetros:**

| Parámetro | Tipo | Ejemplo | Descripción |
|-----------|------|---------|-------------|
| `name` | str | `Canis lupus` | Nombre científico |
| `kingdom` | str | `Animalia` | Reino (opcional, desambigua homónimos) |
| `strict` | bool | `true` | Si `true`, exige coincidencia exacta |

**Respuesta:**
```json
{
  "usageKey": 5219173,
  "scientificName": "Canis lupus Linnaeus, 1758",
  "canonicalName": "Canis lupus",
  "rank": "SPECIES",
  "status": "ACCEPTED",
  "confidence": 100,
  "matchType": "EXACT",
  "kingdom": "Animalia",
  "phylum": "Chordata",
  "class": "Mammalia",
  "order": "Carnivora",
  "family": "Canidae",
  "genus": "Canis",
  "species": "Canis lupus"
}
```

**Significado de campos:**
- `usageKey` = el ID que necesitas para buscar en Occurrence API.
- `matchType`:
  - `EXACT` = coincidencia perfecta. ✅ Usar sin dudas.
  - `FUZZY` = "parecido pero no exacto". ⚠️ Revisa.
  - `HIGHERRANK` = match en género, no especie. ⚠️ No es lo que buscas.
- `status`:
  - `ACCEPTED` = especie vigente.
  - `SYNONYM` = es un sinónimo, pero GBIF lo mapea a la aceptada.
  - `DOUBTFUL` = cuestionable.

---

### 3️⃣ Registry API (Datasets y Organizaciones)

**Endpoints:**
- `/v1/dataset` → listar colecciones de datos en GBIF.
- `/v1/organization` → listar organizaciones que publican datos.

**Uso típico:**
Averiguar **quién publicó** un registro. Cada ocurrencia tiene un `datasetKey`. Usarlo en `/v1/dataset/{datasetKey}` para ver metadatos:
```json
{
  "key": "7629de6e-11f1-45e8-8b6e-50334cdd5467",
  "title": "MOMAT Camera Trap Network - Spain",
  "description": "Long-term ecological monitoring...",
  "organizationKey": "...",
  "contactEmail": "info@momat.org",
  "rights": "CC-BY-4.0",
  "pubDate": "2020-01-01",
  "recordCount": 50000
}
```

---

## Flujo de consulta típico

Visualicemos cómo encajan las sub-APIs en un flujo real:

```
USUARIO: "Quiero todos los lobos en España de 2020 a 2026"

PASO 1: Resolver taxonómicamente
  ┌─────────────────────────────────────────┐
  │ INPUT: "Canis lupus"                    │
  │ ENDPOINT: /v1/species/match             │
  │ OUTPUT: usageKey = 5219173              │
  └─────────────────────────────────────────┘
            ↓
            
PASO 2: Contar registros
  ┌─────────────────────────────────────────┐
  │ PARAMS:                                 │
  │  - taxonKey = 5219173                   │
  │  - country = ES                         │
  │  - year = 2020,2026                     │
  │  - hasCoordinate = true                 │
  │ ENDPOINT: /v1/occurrence/search         │
  │  (limit=1, offset=0)                    │
  │ OUTPUT: count = 2390                    │
  └─────────────────────────────────────────┘
            ↓

PASO 3: Descargar paginando (hasta 300 por página)
  ┌─────────────────────────────────────────┐
  │ Página 1: offset=0,   limit=300         │
  │           → 300 registros                │
  │           → endOfRecords = false         │
  │                                          │
  │ Página 2: offset=300, limit=300         │
  │           → 300 registros                │
  │           → endOfRecords = false         │
  │                                          │
  │ ... (hasta llenar el máximo solicitado)  │
  │                                          │
  │ Página N: offset=..., limit=...         │
  │           → N registros restantes        │
  │           → endOfRecords = true          │
  └─────────────────────────────────────────┘
            ↓

PASO 4: (Opcional) Enriquecer con metadatos
  ┌─────────────────────────────────────────┐
  │ Para cada registro, si necesitas info    │
  │ de la institución:                       │
  │                                          │
  │ ENDPOINT: /v1/dataset/{datasetKey}      │
  │ OUTPUT: Nombre, contacto, derechos      │
  └─────────────────────────────────────────┘
            ↓

RESULTADO FINAL
  ┌─────────────────────────────────────────┐
  │ 2390 registros en GBIF cumplen filtros  │
  │ → CSV, JSON, o visualización            │
  │ → Listo para análisis                   │
  └─────────────────────────────────────────┘
```

---

## Limitaciones y sesgos importantes

### ⚠️ 1. REGISTROS ≠ INDIVIDUOS

Un mismo lobo puede generar múltiples registros:
- Capturado en 5 cámaras de fototrampeo diferentes = 5 registros.
- Rastros hallados en 10 puntos = 10 registros.
- Visto una sola vez pero reportado a GBIF 3 veces = 3 registros.

**Conclusión:** No puedes estimar población contando registros.

---

### ⚠️ 2. SESGO GEOGRÁFICO

GBIF agrega datos de instituciones, voluntarios e iniciativas ciudadanas. La cobertura es muy desigual:
- **Países desarrollados, institutos ricos:** 1000+ registros de algunas especies.
- **Países en desarrollo o áreas remotas:** 0-10 registros.

En España:
- Galicia (con proyecto MOMAT): 161 registros de lobo.
- Extremadura (poca cobertura): 15-20 registros.

Esto **no significa que no hay lobos en Extremadura**, sino que **hay menos esfuerzo de muestreo publicado**.

---

### ⚠️ 3. SESGO TAXONÓMICO

Algunos grupos taxonómicos están sobre-representados:
- **Aves:** bien documentadas (millones de registros).
- **Peces de agua dulce:** moderados (cientos de miles).
- **Hongos, insectos pequeños:** escasos.

---

### ⚠️ 4. AMBIGÜEDAD TAXONÓMICA EN CANIS LUPUS

El `taxonKey=5219173` en GBIF agrupa:
- *Canis lupus lupus* (lobo salvaje Euroasiático).
- *Canis lupus familiaris* (perro doméstico).
- *Canis lupus dingo* (dingo australiano).

**Precaución:** En v7 se usa `specificEpithet` para agrupar registros con valores `lupus` y `familiaris`, pero este campo es el epíteto específico, no una identificación infalible de subespecie. Revisa también `scientificName`, `acceptedScientificName`, el rango y la ficha de cada registro antes de atribuirlo a lobo o perro. En v4 la ficha del mapa muestra el nombre del taxón consultado, que puede ser distinto del nombre del registro.

En la muestra de v7 de 600 registros de España observada el 23 de noviembre de 2026 había 315 con `specificEpithet == 'lupus'` y 285 con `specificEpithet == 'familiaris'`. Son recuentos de esa muestra limitada, no estimaciones de población; pueden cambiar al ejecutar de nuevo. Para comparar con v4, consulta [Comparación de los cuadernos y mapas](./MANUAL_USUARIO.md#comparación-de-los-cuadernos-y-mapas).

---

### ⚠️ 5. OFUSCACIÓN DE COORDENADAS

GBIF protege especies sensibles (en peligro de extinción, con valor comercial) ofuscando sus coordenadas:
- Registros de iNaturalist pueden estar desplazados ±27.6 km.
- Campo `informationWithheld: true` indica ocultamiento.
- Campo `coordinateUncertaintyInMeters` muestra el radio de incertidumbre.

---

### ⚠️ 6. DATOS HISTÓRICOS PUEDE SER VIEJOS

GBIF contiene especímenes de museos datados en 1800. Si filtras `year=2020,2026`, evitas la mayoría de datos históricos, pero algunos datasets no actualizan fechas regularmente.

---

### ⚠️ 7. CALIDAD VARIABLE

Algunos registros pueden tener:
- Coordenadas completamente erróneas (ej: (0, 0) = punta de África).
- Identificaciones cuestionables (ej: taxónomo novato).
- Duplicados (mismo individuo reportado múltiples veces a GBIF).

**Solución:** Revisar campo `issues` (lista de incidencias detectadas automáticamente por GBIF).

---

## Casos de uso del mundo real

### 📍 Caso 1: Monitoreo de Especie Invasora

**Escenario:** Un biólogo quiere saber dónde está expandiéndose la *Saccharosydne ocenica* (cigarra de la caña de azúcar) en América del Sur.

**Flujo:**
```python
# 1. Validar especie
species_api.match("Saccharosydne ocenica")  # → usageKey=12345

# 2. Buscar en Brasil, Colombia, Perú
for country in ["BR", "CO", "PE"]:
    results = occurrence_api.search(
        taxonKey=12345,
        country=country,
        year="2010,2026"
    )
    mapear_expansion_temporal(results)
```

**Valor:** Alertar tempranamente sobre invasión de plagas.

---

### 🏥 Caso 2: Epidemiología de Enfermedades Zoonóticas

**Escenario:** Un epidemiólogo estudia la distribución de murciélagos portadores de coronavirus.

**Flujo:**
```python
# 1. Buscar todas las especies de murciélagos
bats = occurrence_api.search(
    taxonKey=bat_family_key,
    country="CN",
    year="2015,2023"
)

# 2. Cruzar con mapa de focos de COVID
# 3. Correlacionar distribución con brotes históricos
```

**Valor:** Predecir dónde pueden surgir nuevas zoonosis.

---

### 🌱 Caso 3: Agricultura de Precisión

**Escenario:** Un agrónomo quiere saber qué polinizadores hay en su zona.

**Flujo:**
```python
# 1. Buscar abejas, mariposas, escarabajos
for group in ["Apidae", "Papilionidae", "Scarabaeidae"]:
    results = occurrence_api.search(
        family=group,
        country="ES",
        stateProvince="Castilla y León",
        basisOfRecord="HUMAN_OBSERVATION"
    )
    # 2. Visualizar en mapa de cultivos
```

**Valor:** Optimizar rotación de cultivos para atraer polinizadores.

---

### 📚 Caso 4: Educación Ambiental

**Escenario:** Un profesor de primaria quiere mostrar a los niños dónde viven los animales de su región.

**Flujo:**
```python
# Descargar todos los registros de la provincia
results = occurrence_api.search(
    country="ES",
    stateProvince="Galicia"
)

# Visualizar con Folium
map = folium.Map()
for record in results:
    folium.Marker(
        location=[record["decimalLatitude"], record["decimalLongitude"]],
        popup=record["scientificName"]
    ).add_to(map)
map.save("biodiversity_map.html")
```

**Valor:** Lección interactiva sobre biodiversidad local.

---

### 🔬 Caso 5: Investigación Sistemática

**Escenario:** Un equipo de investigación publica un paper sobre cambio climático y rango de distribución de especies.

**Flujo:**
```python
# Comparar rangos históricos vs actuales
species_list = [
    "Pinus sylvestris",
    "Lynx lynx",
    "Parnassius apollo",
    "Salamandra salamandra"
]

for species in species_list:
    # Descargar pre-2000
    old = occurrence_api.search(taxonKey=..., year="1980,2000")
    
    # Descargar 2010-2026
    new = occurrence_api.search(taxonKey=..., year="2010,2026")
    
    # Calcular corrimiento de rangos altitudinales/latitudinales
    analyze_range_shift(old, new)
```

**Valor:** Documentar cambios en distribución de especies.

---

## Resumen

| Aspecto | Descripción |
|---------|-------------|
| **¿Qué?** | GBIF es un repositorio global de biodiversidad con 2+ mil millones de registros. |
| **¿Cómo?** | Mediante REST API con endpoints para buscar registros, validar especies, y consultar metadatos. |
| **¿Para qué?** | Investigación, monitoreo, educación, alertas tempranas, decisiones de conservación. |
| **¿Gratuito?** | Sí, 100% gratis y bajo CC0 (dominio público) o licencias abiertas. |
| **¿Requisitos?** | Conexión a internet, conocimiento de HTTP/REST, Python/R/JavaScript. |
| **¿Limitaciones?** | Sesgo geográfico, calidad variable, registros ≠ individuos, ofuscación de datos sensibles. |
| **¿Dónde aprender más?** | https://www.gbif.org/developer/summary + OpenAPI specs en techdocs.gbif.org |

---

**Versión:** 1.0  
**Última actualización:** 2026-11-22  
**Referencia:** https://www.gbif.org/developer/summary
