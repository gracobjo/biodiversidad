# 📚 Índice de Documentación - Biodiversidad GBIF

Bienvenido a la documentación completa del proyecto de exploración de biodiversidad con la API pública de GBIF.

---

## 🗂️ Estructura de Documentación

### 1. **[MANUAL_USUARIO.md](./MANUAL_USUARIO.md)** 👤
**Para:** Usuarios finales, investigadores, analistas de datos.

**Contenido:**
- ✅ **Requisitos Funcionales (RF):** 9 RF detalladas (resolución taxonómica, consulta multicriterio, sesión HTTP, normalización territorial, etc.)
- ✅ **Requisitos No Funcionales (FNF):** 8 FNF (rendimiento, confiabilidad, escalabilidad, reproducibilidad, interoperabilidad, usabilidad, seguridad, mantenibilidad)
- ✅ **Casos de Uso (CU):** 5 escenarios principales con flujos completos
  - CU1: Exploración general de especies
  - CU2: Análisis de mortalidad
  - CU3: Comparativa lobo vs. perro
  - CU4: Validación de calidad de datos
  - CU5: Integración en pipeline ETL
- ✅ **Diagramas UML:**
  - Diagrama de clases conceptual
  - Diagrama de secuencia del flujo de descarga
  - Diagrama de entidad-relación
  - Diagrama de flujo de transformación de datos
- ✅ **Guía de inicio rápido:** Instalación paso a paso en Windows
- ✅ **Troubleshooting:** Solución de problemas comunes

**Lectura recomendada:** 15-20 minutos

---

### 2. **[GUIA_API_GBIF.md](./GUIA_API_GBIF.md)** 🌍
**Para:** Desarrolladores, científicos de datos, arquitectos técnicos, educadores.

**Contenido:**
- ✅ **¿Qué es GBIF?** Historia, visión, estándares (Darwin Core)
- ✅ **¿Para qué sirve la API?** 6 usos principales (automatizar descargas, consultas dinámicas, pipelines ETL, validación taxonómica, herramientas interactivas, educación)
- ✅ **Arquitectura del API:** Diagrama de sub-APIs organizadas por dominio
- ✅ **Sub-APIs principales:**
  - **Occurrence API** (`/v1/occurrence/search`): Búsqueda de registros con 20+ parámetros de filtro
  - **Species API** (`/v1/species/match`): Validación taxonómica
  - **Registry API**: Datasets y organizaciones
- ✅ **Flujo de consulta típico:** Visualización paso a paso de cómo encajan las sub-APIs
- ✅ **Limitaciones y sesgos importantes:** 7 limitaciones críticas con ejemplos concretos
  - Registros ≠ individuos
  - Sesgo geográfico (Galicia vs. Extremadura)
  - Sesgo taxonómico
  - Ambigüedad de *Canis lupus* (315 lobos vs. 285 perros)
  - Ofuscación de coordenadas en especies sensibles
  - Datos históricos y calidad variable
- ✅ **Casos de uso del mundo real:** 5 ejemplos con código Python pseudocódigo
  - Monitoreo de especies invasoras
  - Epidemiología de zoonosis
  - Agricultura de precisión
  - Educación ambiental
  - Investigación sistemática

**Lectura recomendada:** 25-30 minutos

---

### 3. **[diccionario_datos_gbif.md](./diccionario_datos_gbif.md)** 📖
**Para:** Analistas de datos, auditores de calidad, usuarios avanzados.

**Contenido:**
- 130 campos del JSON bruto devuelto por GBIF
- Para cada campo: nombre, tipo de dato, descripción, cobertura (%), utilidad analítica
- Ejemplos de valores reales
- Referencias a Darwin Core
- Notas sobre campos derivados/transformados

**Lectura recomendada:** Consulta según necesidad (referencia)

---

## 🚀 Rutas de Lectura Recomendadas

### 🎯 Si eres **usuario final/investigador:**
1. Comienza con **MANUAL_USUARIO.md** (secciones 1-3: RF, FNF, CU)
2. Lee "Guía de inicio rápido" (sección 5)
3. Consulta "Troubleshooting" según necesites

**Tiempo:** ~20 minutos

---

### 👨‍💻 Si eres **desarrollador/ingeniero de datos:**
1. Lee **GUIA_API_GBIF.md** completo (arquitectura, sub-APIs, limitaciones)
2. Consulta **MANUAL_USUARIO.md** secciones 4 (Diagramas UML) y 5 (inicio rápido)
3. Usa **diccionario_datos_gbif.md** como referencia mientras codificas

**Tiempo:** ~40 minutos + exploración práctica

---

### 📚 Si eres **educador/docente:**
1. Lee **GUIA_API_GBIF.md** sección "Casos de uso del mundo real" (educación ambiental)
2. Consulta **MANUAL_USUARIO.md** sección 5 (inicio rápido)
3. Adapta ejemplos del notebook para tu audiencia

**Tiempo:** ~15 minutos + preparación de lección

---

### 🔍 Si necesitas **validación de calidad de datos:**
1. Lee **MANUAL_USUARIO.md** sección 3 (CU4: Validación de calidad)
2. Consulta **diccionario_datos_gbif.md** para cada campo a auditar
3. Revisa **GUIA_API_GBIF.md** sección "Limitaciones y sesgos" para contexto

**Tiempo:** ~25 minutos

---

## 📊 Archivo de Datos Generados

| Archivo | Tipo | Descripción | Uso |
|---------|------|-------------|-----|
| `registros_gbif_brutos.json` | JSON | Respuesta raw del API (600 registros, 130 campos) | Fuente única de verdad; reutilizable offline |
| `registros_biodiversidad_gbif.csv` | CSV | Dataset normalizado y transformado | Análisis BI, SQL, herramientas estadísticas |
| `mapa_avistamientos_gbif.html` | HTML | Mapa interactivo Folium | Visualización web; compartir con stakeholders |

---

## 🔗 Enlaces Externos de Referencia

| Recurso | URL | Descripción |
|---------|-----|-------------|
| **GBIF Homepage** | https://www.gbif.org | Sitio oficial |
| **Developer Portal** | https://www.gbif.org/developer/summary | Documentación técnica general |
| **Occurrence API (OpenAPI 3.1)** | https://techdocs.gbif.org/en/openapi/v1/occurrence | Spec interactiva de endpoints |
| **Species API (OpenAPI 3.1)** | https://techdocs.gbif.org/en/openapi/v1/species | Spec interactiva para validación taxonómica |
| **Darwin Core Standard** | https://dwc.tdwg.org | Estándar de términología usado por GBIF |
| **GBIF Data Portal** | https://www.gbif.org/occurrence/search | Interfaz web para buscar registros |
| **GBIF Dashboard** | https://www.gbif.org/en/analytics | Estadísticas globales de GBIF |

---

## 📝 Notas por Proyecto

### Especie Actual: *Canis lupus* (Lobo Euroasiático)
- **Nombre científico:** Canis lupus Linnaeus, 1758
- **usageKey (GBIF):** 5219173
- **Registros descargados:** 600 (de 2,390 disponibles en GBIF para España 2020-2026)
- **Distribución en muestra:** Noroeste (Galicia, Asturias, Castilla y León)
- **Hallazgo crítico:** 47.5% de los registros son *Canis lupus familiaris* (perro doméstico)

### Período de Análisis
- **Rango temporal:** 2020-2026
- **Nota:** 2026 está en curso al momento de ejecución del notebook

### Geografía
- **País:** España (ES)
- **Normalización territorial:** GADM nivel 1 (comunidad autónoma) con 98.8% cobertura

---

## ✍️ Convenciones de Documentación

- **RF = Requisito Funcional** (qué debe hacer el sistema)
- **FNF = Requisito No Funcional** (cómo debe comportarse: rendimiento, seguridad, etc.)
- **CU = Caso de Uso** (escenario de usuario con flujo)
- **Darwin Core** = Estándar internacional TDWG para términos de biodiversidad
- **usageKey / taxonKey** = Identificador único de especie en GBIF (sinónimos)
- **offset/limit** = Parámetros de paginación HTTP (offset = posición de inicio, limit = registros por página)
- **endOfRecords** = Booleano en respuesta JSON indicando si es la última página

---

## 🐛 Reporte de Errores / Sugerencias

Si encuentras:
- **Errores en documentación:** Abre un issue en GitHub
- **Bugs en código:** Revisa el notebook y proporciona stack trace
- **Sugerencias de mejora:** Contacta al equipo de desarrollo

---

## 📄 Versionado de Documentación

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-11-22 | Creación inicial: MANUAL_USUARIO.md, GUIA_API_GBIF.md, este índice |

---

## 👥 Autoría

- **Análisis técnico:** Copilot SDK
- **Validación científica:** gracobjo
- **Fuente de datos:** GBIF Global Biodiversity Information Facility

---

**Última actualización:** 2026-11-22  
**Ubicación:** `docs/` (esta carpeta)

---

## 🎓 Aprende Más

¿Listo para empezar? Sigue estos pasos:

1. **Comprende el problema:** Lee [MANUAL_USUARIO.md](./MANUAL_USUARIO.md) secciones 1-3
2. **Entiende la API:** Lee [GUIA_API_GBIF.md](./GUIA_API_GBIF.md) secciones 1-3
3. **Ejecuta el código:** Abre `exploracion_biodiversidad_gbif_v7_mortalidad.ipynb`
4. **Explora los datos:** Abre `registros_biodiversidad_gbif.csv` en Excel/pandas
5. **Visualiza:** Abre `mapa_avistamientos_gbif.html` en el navegador

¡Que disfrutes explorando la biodiversidad! 🌿🦁🌍
