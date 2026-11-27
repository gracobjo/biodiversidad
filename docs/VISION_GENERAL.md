# 🎯 Visión General - Documentación de Biodiversidad GBIF

La aplicación consulta cualquier especie en GBIF, elige país y periodo, persiste en SQLite o MySQL y mide indicadores. *Canis lupus* es el ejemplo del cuaderno 01 (600 registros en España, 2020–2026), con la separación de lobo y perro. Este archivo inventaría el primer paquete documental. El índice vivo es [README.md](./README.md): cuadernos, requisitos RF-01 a RF-22, casos CU-01 a CU-15, UML y los dos pipelines (SQLite y MySQL).

## ¿Qué tiene en sus manos?

Ha recibido una **documentación profesional completa** sobre una **aplicación Python que explora biodiversidad mediante la API pública de GBIF**. 

Esta documentación está diseñada para:
- ✅ **Usuarios finales:** Entender qué hace la aplicación
- ✅ **Desarrolladores:** Comprender la arquitectura y el API
- ✅ **Educadores:** Enseñar sobre biodiversidad y APIs REST
- ✅ **Data stewards:** Auditar calidad de datos

---

## 📦 Lo que se ha entregado

### 6 Documentos Markdown (~82 KB total)

| # | Documento | Tamaño | Propósito | Lectura |
|----|-----------|--------|-----------|---------|
| 1️⃣ | **[INICIO_RAPIDO.md](./INICIO_RAPIDO.md)** ⭐ | 11 KB | 🎯 Punto de entrada: rutas personalizadas por rol | 10 min |
| 2️⃣ | **[README.md](./README.md)** | 8 KB | 📚 Índice general y mapa de navegación | 10 min |
| 3️⃣ | **[MANUAL_USUARIO.md](./MANUAL_USUARIO.md)** | 23 KB | 📋 Manual técnico: RF, FNF, Casos de Uso, UML | 20 min |
| 4️⃣ | **[GUIA_API_GBIF.md](./GUIA_API_GBIF.md)** | 21 KB | 🌍 Explicación del API GBIF en lenguaje natural | 25 min |
| 5️⃣ | **[diccionario_datos_gbif.md](./diccionario_datos_gbif.md)** | 8 KB | 📖 Referencia de 130 campos de datos | Consulta |
| 6️⃣ | **[RESUMEN_EJECUTIVO.md](./RESUMEN_EJECUTIVO.md)** | 11 KB | 📊 Síntesis de contenido y métricas | 10 min |

---

## 🎓 Contenido por Documento

### 1. MANUAL_USUARIO.md - El Corazón Técnico

**¿Qué contiene?**
- 9 **Requisitos Funcionales (RF1-RF9)**: Qué debe hacer el sistema
  - Resolución taxonómica, consulta multicriterio, sesión HTTP, normalización territorial, etc.
  
- 8 **Requisitos No Funcionales (FNF1-FNF8)**: Cómo debe comportarse
  - Rendimiento, confiabilidad, escalabilidad, reproducibilidad, interoperabilidad, etc.
  
- 5 **Casos de Uso (CU1-CU5)** con flujos completos:
  - CU1: Exploración general (ecólogo estudiando distribución)
  - CU2: Análisis de mortalidad (veterinario)
  - CU3: Comparativa lobo vs perro (especialista en canis)
  - CU4: Validación de calidad (data steward)
  - CU5: Pipeline ETL corporativo (ingeniero de datos)
  
- 4 **Diagramas UML** ASCII:
  - Diagrama de clases conceptual
  - Diagrama de secuencia del flujo de descarga
  - Diagrama de entidad-relación
  - Diagrama de flujo de transformación de datos
  
- **Guía de instalación paso a paso** (Windows con `uv`)
- **Troubleshooting** de errores comunes

**Para quién?** Usuarios técnicos, investigadores, implementadores.

---

### 2. GUIA_API_GBIF.md - La Arquitectura Explicada

**¿Qué contiene?**
- **¿Qué es GBIF?** (historia, visión, estándares Darwin Core)
  - 60+ países, 1000+ instituciones, 2+ mil millones de registros
  
- **¿Para qué sirve la API GBIF?** (6 usos principales)
  - Automatizar descargas, consultas dinámicas, pipelines ETL, validación taxonómica, herramientas interactivas, educación
  
- **Arquitectura del API** con diagrama de sub-APIs
  - Occurrence API (búsqueda de registros)
  - Species API (validación taxonómica)
  - Registry API (metadatos)
  
- **Sub-APIs explicadas en detalle:**
  - 20+ parámetros de filtro de Occurrence API
  - Respuestas JSON completas con ejemplos
  - Significado de campos críticos
  
- **Flujo de consulta típico** paso a paso
  
- **7 Limitaciones y sesgos importantes:**
  - Registros ≠ individuos
  - Sesgo geográfico (Galicia vs Extremadura)
  - Ambigüedad *Canis lupus* (315 lobos vs 285 perros en la muestra)
  - Ofuscación de coordenadas en especies sensibles
  - Datos históricos heterogéneos
  - Calidad variable
  
- **5 Casos de uso del mundo real** con pseudocódigo:
  - Monitoreo de especies invasoras
  - Epidemiología de zoonosis
  - Agricultura de precisión
  - Educación ambiental
  - Investigación sistemática

**Para quién?** Desarrolladores, arquitectos, educadores, investigadores técnicos.

---

### 3. INICIO_RAPIDO.md - Tu Brújula Personal

**¿Qué contiene?**
- **4 Rutas de lectura personalizadas:**
  - 👤 Investigador → 15 minutos
  - 👨‍💻 Desarrollador → 40 minutos
  - 📚 Educador → 30 minutos
  - 🔍 Data Steward → 25 minutos
  
- **Resumen visual de contenido por documento**
- **Pasos prácticos de instalación**
- **Preguntas frecuentes (FAQ)**
- **Convenciones y terminología**

**Para quién?** TODOS - Comienza siempre aquí.

---

### 4. diccionario_datos_gbif.md - La Referencia

**¿Qué contiene?**
- **130 campos del JSON** devueltos por GBIF
- Para cada campo:
  - Nombre (terminología Darwin Core)
  - Tipo de dato
  - Descripción detallada
  - Cobertura (%)
  - Utilidad analítica
  - Ejemplos reales
  
- **Notas sobre campos derivados/transformados**
- **Referencias a Darwin Core Standard**

**Para quién?** Analistas de datos, auditores, usuarios avanzados.

---

### 5. README.md - El Índice

**¿Qué contiene?**
- **Mapa de navegación centralizado**
- **Rutas de lectura por rol** (breve)
- **Archivos de datos generados** (JSON, CSV, HTML)
- **Enlaces externos** a documentación oficial GBIF
- **Convenciones** (RF, FNF, CU, Darwin Core, etc.)
- **Notas por proyecto** (especie, período, geografía)

**Para quién?** Navegación rápida y referencia general.

---

### 6. RESUMEN_EJECUTIVO.md - La Síntesis

**¿Qué contiene?**
- **Resumen de cada documento**
- **Hallazgos principales de la muestra** (600 registros)
- **Métricas de documentación** (RF, FNF, CU, UML, campos, etc.)
- **Características destacadas**
- **Próximos pasos sugeridos**
- **Validación de completitud**

**Para quién?** Ejecutivos, gerentes, revisores.

---

## 🎯 ¿Por Dónde Empezar?

### Opción 1: Siguiendo una ruta (RECOMENDADO)
👉 Abre **[INICIO_RAPIDO.md](./INICIO_RAPIDO.md)** y elige tu rol

**Tiempo:** 10 minutos de lectura + tu ruta personalizada

---

### Opción 2: Por interés
- **Interesa: ¿Qué es GBIF?** → [GUIA_API_GBIF.md](./GUIA_API_GBIF.md) sección 1
- **Interesa: Requisitos y arquitectura** → [MANUAL_USUARIO.md](./MANUAL_USUARIO.md) secciones 1-4
- **Interesa: Instalación y primeros pasos** → [MANUAL_USUARIO.md](./MANUAL_USUARIO.md) sección 5
- **Interesa: Significado de los datos** → [diccionario_datos_gbif.md](./diccionario_datos_gbif.md)
- **Interesa: Visión general rápida** → [RESUMEN_EJECUTIVO.md](./RESUMEN_EJECUTIVO.md)

---

### Opción 3: Por rol (tabla rápida)
| Tu Rol | Comienza con | Luego lee | Tiempo |
|--------|--------------|-----------|--------|
| 👤 Investigador | MANUAL_USUARIO.md (1-3) | Notebook | 25 min |
| 👨‍💻 Desarrollador | GUIA_API_GBIF.md (todo) | MANUAL_USUARIO.md (4-5) | 40 min |
| 📚 Educador | GUIA_API_GBIF.md (CU) | MANUAL_USUARIO.md (5) | 30 min |
| 🔍 Data Steward | MANUAL_USUARIO.md (CU4) | diccionario_datos_gbif.md | 25 min |

---

## 📊 Hallazgos Clave de Tu Proyecto

### Muestra Analizada: 600 registros
- **Ubicación:** España, 2020-2026
- **Especie:** *Canis lupus* (lobo Euroasiático)
- **Distribución:** Concentrada en noroeste (Galicia 161 registros)

### Composición Interesante
- **47.5% perros domésticos** (`Canis lupus familiaris`)
- **52.5% lobos salvajes** (`Canis lupus lupus`)
- Ambos comparten `taxonKey=5219173` en GBIF → ¡Cuidado con la ambigüedad!

### Evidencias de Observación
- **Indicios indirectos dominan:** excrementos (104), huellas (13)
- **Fototrampeo sistemático:** 64 registros "General", 23 "Multiespecie"
- **Mortalidad documentada:** 7 registros con `vitality == 'dead'`

### Calidad de Datos
- **Cobertura territorial:** 98.8% con normalización GADM (excelente)
- **Incertidumbre espacial:** 27.6 km media en registros sensibles (ofuscación iNaturalist)
- **Registros útiles:** 2,390 cumplen filtros en GBIF (descargaste 600 máximo)

---

## 🚀 Próximas Acciones

### Inmediato (Hoy)
1. ✅ Lee **[INICIO_RAPIDO.md](./INICIO_RAPIDO.md)** (10 min)
2. ✅ Elige tu ruta de lectura personalizada
3. ✅ Lee el primer documento de tu ruta (20-25 min)

### Corto plazo (Hoy/Mañana)
1. Instala Python 3.14 + dependencias (5 min)
2. Ejecuta el notebook principal (10 min)
3. Explora CSV y mapa HTML generados (5 min)
4. Lee documentos complementarios según necesites (20-30 min)

### Mediano plazo (Esta semana)
1. Personaliza filtros para tu caso de uso
2. Descarga datos para tu especie/región de interés
3. Integra en tu workflow de análisis
4. Consulta diccionario de datos según necesites

---

## ✨ Lo Especial de Esta Documentación

✅ **Multiaudiencia:** Cada rol encuentra su camino sin perderse  
✅ **Modular:** Puedes leer un documento aislado o toda la suite  
✅ **Visual:** Diagramas UML, tablas, ejemplos ASCII  
✅ **Interconectada:** Hipervínculos entre documentos  
✅ **Completa:** Desde conceptos básicos hasta detalles técnicos  
✅ **Práctica:** Incluye guía de instalación y troubleshooting  
✅ **Basada en datos reales:** Ejemplos concretos de tu proyecto  
✅ **Actualizada:** Fecha 2026-11-22, referencias actuales a GBIF  

---

## 📌 Recordatorios Importantes

### 1. Registros ≠ Individuos
Un lobo fotografiado en 5 cámaras = 5 registros. No es 5 lobos.

### 2. Sesgos en GBIF
- Galicia tiene más registros porque hay más institutos publicadores
- Esto ≠ hay más lobos en Galicia (aunque probablemente sí)

### 3. Ambigüedad de *Canis lupus*
El `taxonKey=5219173` incluye lobos y perros. Usa `specificEpithet` para distinguir:
- `specificEpithet == 'lupus'` → lobo salvaje
- `specificEpithet == 'familiaris'` → perro doméstico

### 4. Ofuscación de Coordenadas
Especies sensibles tienen coordenadas alteradas (±27.6 km). Campo `informationWithheld` lo indica.

### 5. API es Gratuito pero Respeta Límites
- Máximo 300 registros por petición
- Incluye pausa entre peticiones (0.2-1.0 segundos)
- Identifícate con User-Agent apropiado

---

## 🔗 Referencia Rápida de Enlaces

**Dentro de esta documentación:**
- 📋 Manual Usuario: [MANUAL_USUARIO.md](./MANUAL_USUARIO.md)
- 🌍 Guía del API: [GUIA_API_GBIF.md](./GUIA_API_GBIF.md)
- 📖 Diccionario datos: [diccionario_datos_gbif.md](./diccionario_datos_gbif.md)
- 📄 Índice: [README.md](./README.md)

**Externos (oficiales GBIF):**
- 🌐 Portal: https://www.gbif.org
- 👨‍💻 Developers: https://www.gbif.org/developer/summary
- 📊 Occurrence API (OpenAPI): https://techdocs.gbif.org/en/openapi/v1/occurrence
- 📊 Species API (OpenAPI): https://techdocs.gbif.org/en/openapi/v1/species
- 📚 Darwin Core: https://dwc.tdwg.org

---

## 🎓 Preguntas que Esta Documentación Responde

**¿Qué hace la aplicación?**  
→ [MANUAL_USUARIO.md](./MANUAL_USUARIO.md) secciones 1-3

**¿Cómo funciona la API de GBIF?**  
→ [GUIA_API_GBIF.md](./GUIA_API_GBIF.md) secciones 2-4

**¿Qué es GBIF exactamente?**  
→ [GUIA_API_GBIF.md](./GUIA_API_GBIF.md) sección 1

**¿Cuáles son las limitaciones de los datos?**  
→ [GUIA_API_GBIF.md](./GUIA_API_GBIF.md) sección 6

**¿Cómo instalo y ejecuto esto?**  
→ [MANUAL_USUARIO.md](./MANUAL_USUARIO.md) sección 5

**¿Qué significa cada campo de datos?**  
→ [diccionario_datos_gbif.md](./diccionario_datos_gbif.md)

**¿Qué casos de uso tiene?**  
→ [MANUAL_USUARIO.md](./MANUAL_USUARIO.md) sección 3 + [GUIA_API_GBIF.md](./GUIA_API_GBIF.md) sección 7

**¿Dónde comienzo?**  
→ **[INICIO_RAPIDO.md](./INICIO_RAPIDO.md)** ⭐

---

## ✅ Validación de Completitud

La documentación cubre:
- ✅ Requisitos (Funcionales y No Funcionales)
- ✅ Casos de Uso (Escenarios reales)
- ✅ Diagramas de Arquitectura (UML)
- ✅ Explicación del API (Lenguaje natural)
- ✅ Referencia de Datos (Diccionario de 130 campos)
- ✅ Guía Práctica (Instalación y troubleshooting)
- ✅ Rutas Personalizadas (Por rol de usuario)
- ✅ Ejemplo Completo (600 registros de *Canis lupus* en España)

---

## 🎉 Conclusión

Tienes en tus manos una **documentación profesional, completa e interconectada** que te permite:

✅ Entender qué hace la aplicación (RF, FNF, CU)  
✅ Aprender cómo funciona GBIF (conceptual + técnico)  
✅ Ver diagramas de la arquitectura (UML)  
✅ Instalar y ejecutar la solución (paso a paso)  
✅ Explorar y analizar tus datos (referencia completa)  
✅ Adaptar para tu caso de uso (filtros, especie, período)  

**Ahora, tu siguiente paso:** 👉 Abre **[INICIO_RAPIDO.md](./INICIO_RAPIDO.md)**

---

**Estado:** ✅ DOCUMENTACIÓN COMPLETA  
**Versión:** 1.0  
**Fecha:** 2026-11-22  
**Ubicación:** `C:\Users\chuwi\Documents\biodiversidad\docs\`

¡Que disfrutes explorando la biodiversidad! 🌿🦁🌍

