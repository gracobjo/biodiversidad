# 🚀 Inicio Rápido - Documentación Biodiversidad GBIF

La aplicación consulta cualquier especie de GBIF, en cualquier país y en un año o un intervalo de fechas. Guarda en SQLite o en MySQL, y `python app_tkinter.py` abre Consultar, Indicadores y Traer datos de GBIF. *Canis lupus* en España (2020–2026, 600 registros) es la muestra del cuaderno 01, no el límite del programa.

Los apartados de abajo orientan la primera documentación (manual del cuaderno, guía del API y diccionario de esa muestra). El índice vivo es [README.md](./README.md).

## ¿Qué acabo de descargar?

Has recibido **3 documentos completos** sobre la exploración de biodiversidad con la API de GBIF:

```
📂 docs/
├── 📄 README.md ..................... Índice y mapa de navegación
├── 📋 MANUAL_USUARIO.md ............. Manual técnico completo
├── 🌍 GUIA_API_GBIF.md .............. Explicación del API GBIF
└── 📖 diccionario_datos_gbif.md ..... Referencia de 130 campos de datos
```

---

## ⏱️ Tiempo de Lectura por Documento

| Documento | Duración | Audiencia |
|-----------|----------|-----------|
| **README.md** | 10 min | Todos |
| **MANUAL_USUARIO.md** | 20 min | Usuarios, investigadores, analistas |
| **GUIA_API_GBIF.md** | 25 min | Desarrolladores, arquitectos, educadores |
| **diccionario_datos_gbif.md** | Consulta | Referencias técnicas |

---

## 🎯 Elige tu Ruta de Lectura

### 👤 Soy Investigador / Científico
**Quiero entender qué hace la aplicación y cómo usarla**

```
1️⃣  MANUAL_USUARIO.md
    └─ Secciones: 1 (RF), 2 (FNF), 3 (Casos de Uso), 5 (Inicio Rápido)
    └─ Tiempo: ~15 minutos

2️⃣  Después: abre la ventana o el cuaderno de partida
    └─ Ventana: python app_tkinter.py (Consultar, Indicadores, Traer datos de GBIF)
    └─ Cuaderno: notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb
    └─ Tiempo: ~10 minutos (descarga) + análisis
```

---

### 👨‍💻 Soy Desarrollador / Ingeniero de Datos
**Quiero entender la arquitectura técnica y el API**

```
1️⃣  GUIA_API_GBIF.md
    └─ Secciones completas: Qué es GBIF, arquitectura, sub-APIs, limitaciones
    └─ Tiempo: ~25 minutos

2️⃣  MANUAL_USUARIO.md
    └─ Secciones: 4 (Diagramas UML), 5 (Inicio Rápido)
    └─ Tiempo: ~15 minutos

3️⃣  diccionario_datos_gbif.md
    └─ Para referencia: Qué significa cada campo JSON
    └─ Tiempo: Consulta según necesites
```

---

### 📚 Soy Docente / Educador
**Quiero enseñar sobre biodiversidad y APIs REST**

```
1️⃣  GUIA_API_GBIF.md
    └─ Secciones: "¿Qué es GBIF?", "Para qué sirve", "Casos de uso"
    └─ Tiempo: ~20 minutos

2️⃣  MANUAL_USUARIO.md
    └─ Sección: 5 (Inicio Rápido - instalación paso a paso)
    └─ Sección: Troubleshooting (solución de errores)
    └─ Tiempo: ~15 minutos
```

---

### 🔍 Soy Data Steward / Auditor de Calidad
**Quiero validar la calidad y cobertura de los datos**

```
1️⃣  MANUAL_USUARIO.md
    └─ Sección: 3 → Caso de Uso 4 (Validación de calidad)
    └─ Tiempo: ~10 minutos

2️⃣  diccionario_datos_gbif.md
    └─ Revisar cobertura (%) de cada campo
    └─ Tiempo: ~20 minutos
```

---

## 📊 Contenido Resumido por Documento

### 📄 README.md
✅ **Índice de documentación** con enlaces  
✅ **Rutas de lectura personalizadas**  
✅ **Archivos de datos generados**  
✅ **Enlaces externos de referencia**  
✅ **Convenciones y terminología**  

**Mejor para:** Orientación inicial y navegación

---

### 📋 MANUAL_USUARIO.md (19 KB)
✅ **9 Requisitos Funcionales** detallados  
✅ **8 Requisitos No Funcionales**  
✅ **5 Casos de Uso** con flujos completos  
✅ **4 Diagramas UML:**
   - Diagrama de clases
   - Diagrama de secuencia
   - Diagrama E-R
   - Diagrama de flujo de transformación

✅ **Guía de instalación paso a paso** (Windows)  
✅ **Troubleshooting** de errores comunes  

**Mejor para:** Implementación y validación de requisitos

---

### 🌍 GUIA_API_GBIF.md (19 KB)
✅ **¿Qué es GBIF?** (historia, visión, estándares)  
✅ **¿Para qué sirve la API?** (6 usos principales)  
✅ **Arquitectura del API** con diagrama  
✅ **Sub-APIs principales:**
   - Occurrence API (búsqueda de registros)
   - Species API (validación taxonómica)
   - Registry API (metadatos)

✅ **Flujo de consulta típico** con visualización paso a paso  
✅ **7 Limitaciones y sesgos importantes** con ejemplos reales  
✅ **5 Casos de uso del mundo real** con pseudocódigo  

**Mejor para:** Comprensión conceptual y arquitectónica

---

### 📖 diccionario_datos_gbif.md
✅ **130 campos del JSON** devueltos por GBIF  
✅ Para cada campo:
   - Nombre (original Darwin Core)
   - Tipo de dato
   - Descripción detallada
   - Cobertura (%)
   - Utilidad analítica
   - Ejemplos reales

✅ **Notas sobre campos derivados**  
✅ **Referencias a Darwin Core**  

**Mejor para:** Referencia técnica y auditoría de datos

---

## 🎓 Conceptos Clave Explicados

### Requisitos del cuaderno de exploración (RF1-RF9)
*Lo que hace el cuaderno 01. La aplicación completa está en RF-01 a RF-22 de ESPECIFICACION_REQUISITOS.md.*
- RF1: Resolver nombres científicos a identificadores
- RF2: Consultar con múltiples filtros
- RF3: Mantener sesión HTTP persistente
- RF4: Normalizar territorio (GADM)
- RF5: Separar taxones ambiguos (*lupus* vs *familiaris*)
- RF6: Extraer evidencias científicas
- RF7: Auditar mortalidad
- RF8: Exportar a CSV
- RF9: Generar cartografía interactiva

---

### Requisitos No Funcionales (FNF)
*Cómo debe comportarse (cualidades)*
- FNF1: **Rendimiento** (600 registros < 10 seg)
- FNF2: **Confiabilidad** (manejo de errores HTTP)
- FNF3: **Escalabilidad** (compatible con miles de registros)
- FNF4: **Reproducibilidad** (el JSON conserva la muestra del cuaderno 01)
- FNF5: **Interoperabilidad** (Darwin Core, ISO 8601, CSV abiertos)
- FNF6: **Usabilidad** (interfaz Jupyter intuitiva)
- FNF7: **Seguridad** (sin credenciales en código)
- FNF8: **Mantenibilidad** (código modular, tipado, documentado)

---

### Casos del primer manual (CU1-CU5)
*La aplicación completa llega hasta CU-15, en CASOS_DE_USO.md.*
1. **CU1:** Exploración general (ecólogo estudiando distribución)
2. **CU2:** Análisis de mortalidad (veterinario estudiando causas de muerte)
3. **CU3:** Comparativa lobo vs perro (especialista en canis)
4. **CU4:** Validación de calidad (data steward auditando GBIF)
5. **CU5:** Pipeline ETL corporativo (ingeniero de datos en data warehouse)

---

## 🌟 Hallazgos del cuaderno 01 (600 registros de *Canis lupus* en España)

| Aspecto | Resultado |
|---------|-----------|
| **Distribución de lobo** | Noroeste: Galicia (161), Castilla y León (72), Asturias (40) |
| **Composición taxonómica** | 315 lobos salvaje (`lupus`) vs 285 perros (`familiaris`) |
| **Evidencias dominantes** | Indicios indirectos en ciencia ciudadana (heces 104, huellas 13) |
| **Fototrampeo** | 64 registros "Fototrampeo General", 23 "Multiespecie en un punto" |
| **Incertidumbre espacial** | 27.6 km media en registros sensibles de iNaturalist |
| **Mortalidad documentada** | 7 registros con `vitality == 'dead'` |
| **Cobertura territorial** | 98.8% en datos GADM (normalización perfecta) |

---

## 📥 Descargas y Resultados

### Archivos Generados Automáticamente

```
datos/registros_gbif_brutos.json
├─ 600 registros
├─ 130 campos (Darwin Core)
├─ Formato: JSON con indentación
├─ Propósito: conservar la muestra del cuaderno 01
└─ Uso: Reutilizable sin volver a consultar API

registros_biodiversidad_gbif.csv
├─ 600 filas
├─ 60+ columnas normalizadas
├─ Formato: UTF-8, delimitador ','
├─ Propósito: Análisis con Excel, SQL, BI
└─ Transformaciones: Territorio GADM, evidencias unificadas

mapa_avistamientos_gbif.html
├─ Mapa interactivo Folium
├─ Colores según el epíteto taxonómico del registro
├─ Clustering de marcadores
├─ Tooltips con metadatos
└─ Uso: Abrir en navegador web
```

---

## 🔗 Enlaces Rápidos

**Dentro de esta documentación:**
- 📋 Manual de Usuario → [MANUAL_USUARIO.md](./MANUAL_USUARIO.md)
- 🌍 Guía del API GBIF → [GUIA_API_GBIF.md](./GUIA_API_GBIF.md)
- 📖 Diccionario de datos → [diccionario_datos_gbif.md](./diccionario_datos_gbif.md)

**Externos (oficiales GBIF):**
- 🌐 Portal GBIF → https://www.gbif.org
- 👨‍💻 Developer Portal → https://www.gbif.org/developer/summary
- 📊 Occurrence API (OpenAPI) → https://techdocs.gbif.org/en/openapi/v1/occurrence
- 📊 Species API (OpenAPI) → https://techdocs.gbif.org/en/openapi/v1/species
- 📚 Darwin Core Standard → https://dwc.tdwg.org

---

## ⚡ Próximos Pasos

### 1. Instalar el entorno (5 min)
```bash
cd C:\Users\chuwi\Documents\biodiversidad
uv venv --python 3.14 .venv
.venv\Scripts\Activate.ps1
uv sync --system-certs
.venv\Scripts\python.exe -m ipykernel install --user --name=biodiversidad --display-name="Python (biodiversidad)"
```

El entorno virtual es la carpeta `.venv`. `uv sync` instala ahí exactamente lo declarado en `pyproject.toml`. Si no sabes si ya tiene todas las librerías, vuelve a lanzarlo. En Jupyter o VS Code elige el kernel **Python (biodiversidad)**, que usa `.venv\Scripts\python.exe`. `--system-certs` hace falta en la red de la Junta.

### 2. Leer documentación (20-30 min)
Elige tu ruta según tu rol (arriba).

### 3. Ejecutar el notebook (10-15 min)
Abre `notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb`. Qué hace cada cuaderno: [CUADERNOS.md](./CUADERNOS.md).

### 4. Explorar resultados (5 min)
- Abre `registros_biodiversidad_gbif.csv` en Excel
- Abre `mapa_avistamientos_gbif.html` en navegador

### 5. Adaptar para tu caso (variable)
Personaliza filtros, especie, período según tu investigación.

---

## 💬 Preguntas Frecuentes

**P: ¿Puedo usar los datos con otra especie?**  
R: Sí. Simplemente cambia el nombre científico en `obtener_taxon_key("tu-especie")`.

**P: ¿Qué pasa si cambio los filtros (año, país)?**  
R: La descarga se reajusta automáticamente. Revisa el diagnóstico progresivo para ver cuántos registros tienes.

**P: ¿Por qué difieren los mapas de España y ES+PT?**

R: El límite de 600 registros se aplica a ámbitos distintos, y los colores tienen significados diferentes. Consulta [la comparación de los cuadernos](./MANUAL_USUARIO.md#comparación-de-los-cuadernos-y-mapas).

**P: ¿Cuál es la diferencia entre JSON y CSV?**  
R: JSON es la respuesta bruta del API (130 campos, estructura compleja). CSV es una tabla simplificada con 60+ campos normalizados, lista para Excel/SQL.

**P: ¿Es seguro consultar GBIF frecuentemente?**  
R: Sí, GBIF es un servicio público y gratuito. Pero respeta sus límites de rate (incluye pausa entre peticiones).

**P: ¿Puedo confiar en los datos de GBIF?**  
R: Parcialmente. Lee la sección "Limitaciones y sesgos" en GUIA_API_GBIF.md. Los datos tienen sesgos geográficos, taxonómicos y de calidad variable.

---

## ✍️ Convenciones Usadas

| Término | Significado |
|---------|-------------|
| `taxonKey` / `usageKey` | Identificador único de especie en GBIF |
| `specificEpithet` | Epíteto específico (*lupus*, *familiaris*, *dingo*) |
| `Darwin Core` | Estándar TDWG para términos de biodiversidad |
| `GADM` | Global Administrative Divisions (jerarquía territorial) |
| `offset` / `limit` | Parámetros de paginación HTTP |
| `endOfRecords` | Booleano indicando fin de resultados |
| `informationWithheld` | Indica ofuscación de coordenadas |

---

## 📞 Soporte

**Para errores en el notebook:**
- Revisa "Troubleshooting" en MANUAL_USUARIO.md sección 7

**Para dudas sobre el API GBIF:**
- Consulta GUIA_API_GBIF.md o https://www.gbif.org/developer/summary

**Para cuestiones de datos:**
- Abre diccionario_datos_gbif.md y busca el campo en cuestión

---

## 🎉 ¡Listo para empezar!

Ahora tienes:
✅ **Comprensión completa** del sistema  
✅ **Documentación técnica y conceptual**  
✅ **Diagramas UML** de la arquitectura  
✅ **Casos de uso** reales  
✅ **Guía de instalación** paso a paso  

**¿Siguiente paso?** Abre **README.md** para elegir tu ruta de lectura personalizada.

---

**Versión:** 1.0  
**Creado:** 2026-11-22  
**Ubicación:** `docs/`

¡Que disfrutes explorando la biodiversidad! 🌿🦁🌍
