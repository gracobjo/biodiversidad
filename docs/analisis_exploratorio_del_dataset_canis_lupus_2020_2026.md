# Análisis Exploratorio de Datos: Presencia de *Canis lupus* en España y Portugal (2020–2026)

* **Archivo analizado:** `canis_lupus_es_pt_2020_2026_darwin_core.csv`
* **Ámbito geográfico:** España (`ES`) y Portugal (`PT`)
* **Periodo temporal:** 2020 – 2026 (hasta el 25 de octubre de 2026)
* **Estándar:** Darwin Core (GBIF)

---

## 1. Resumen del Conjunto de Datos

Para este conjunto de datos conviene combinar gráficos temporales, geográficos y de calidad del dato para obtener una visión completa más allá del conteo bruto de observaciones.

| Métrica | Valor | Detalle |
| :--- | :---: | :--- |
| **Registros totales** | **1.121** | Ocurrencias georreferenciadas bajo estándar Darwin Core |
| **Cobertura temporal** | **7 años** | Periodo `2020–2026` |
| **Registros en España (`ES`)** | **1.025** | 91,4 % del total del dataset |
| **Registros en Portugal (`PT`)** | **96** | 8,6 % del total del dataset |

### Condicionantes de interpretación científica
1. **Registros frente a individuos:** Los 1.121 registros corresponden a eventos de observación o detección, no necesariamente a 1.121 ejemplares distintos.
2. **Sesgo de esfuerzo de muestreo:** El volumen de registros depende directamente de la actividad de seguimiento, redes de cámaras de fototrampeo, número de observadores activos y plataformas de ciencia ciudadana.

---

## 2. Visualizaciones Recomendadas y Panel Exploratorio

Se proponen seis perspectivas visuales complementarias para explorar el comportamiento temporal, espacial, metodológico y multimedia del conjunto de datos:

![Panel exploratorio de registros de Canis lupus en España y Portugal (2020-2026)](./img/panel_exploratorio_canis_lupus_2020_2026.png)
*Figura 1. Panel de seis visualizaciones exploratorias generado a partir de `canis_lupus_es_pt_2020_2026_darwin_core.csv`.*

1. **Evolución anual de las observaciones** (Gráfico de barras verticales)
2. **Distribución mensual / estacional** (Gráfico de barras verticales)
3. **Distribución territorial por región** (Gráfico de barras horizontales)
4. **Método de observación (`basisOfRecord`)** (Gráfico circular de anillo)
5. **Distribución geográfica e incertidumbre espacial** (Mapa / diagrama de dispersión lat-lon)
6. **Disponibilidad de fotografías y material multimedia** (Gráfico circular de anillo)

---

## 3. Interpretación Detallada de Cada Gráfico

### Gráfico 1. Evolución anual de las observaciones
* **Idoneidad:** Muy adecuado.
* **Tipo de visualización:** Gráfico de barras verticales (comparación entre años discretos).
* **Patrones principales:**
  * **2025** es el año con mayor volumen de registros (**247**).
  * **2023** presenta una caída muy marcada con únicamente **55** registros.
  * **2024** muestra una fuerte recuperación alcanzando **185** registros.
  * **2026** acumula **159** registros, pero constituye un año incompleto (último registro fechado el 25 de octubre).
* **Interpretación:** Se observa una variabilidad interanual significativa en la actividad de registro. No puede inferirse un aumento o descenso real de la población de lobo ibérico sin incorporar datos de seguimiento poblacional sistemático y esfuerzo de muestreo estandarizado.

### Gráfico 2. Distribución mensual
* **Idoneidad:** Muy adecuado.
* **Tipo de visualización:** Gráfico de barras verticales a lo largo del calendario anual.
* **Patrones principales:**
  * **Febrero** lidera el volumen mensual con **159** registros.
  * **Marzo** ocupa el segundo lugar con **134** registros.
  * **Mayo** registra **128** observaciones, y se aprecia un repunte secundario en **septiembre** (**117** registros).
  * **Noviembre** es el mes con menor actividad (**42** registros).
* **Interpretación:** Se perfila una mayor concentración de registros entre **febrero y mayo**. No obstante, al agregar todos los años se incluye 2026 (incompleto en noviembre y diciembre), por lo que se recomienda repetir el cálculo excluyendo 2026 y trabajando con frecuencias relativas (%).

### Gráfico 3. Distribución territorial
* **Idoneidad:** Muy adecuado.
* **Tipo de visualización:** Gráfico de barras horizontales ordenadas por frecuencia.
* **Patrones principales:**

| Región (`stateProvince`) | Registros | % sobre el total (1.121) |
| :--- | :---: | :---: |
| **Galicia** | 564 | 50,3 % |
| **Araba/Álava** | 110 *(+15 como Álava)* | 9,8 % *(11,2 % unificado)* |
| **Castilla y León** | 68 | 6,1 % |
| **Viana do Castelo** (PT) | 41 | 3,7 % |
| **Norte** (PT) | 25 | 2,2 % |
| **Principado de Asturias** | 24 | 2,1 % |

* **Hallazgos de calidad de datos:**
  * Existen **181 registros** sin provincia o región informada (`Sin provincia`).
  * **Araba/Álava** figura dividida bajo dos denominaciones distintas (**110** como `Araba/Álava` y **15** como `Álava`), por lo que requiere normalización previa (p. ej., mediante capas GADM) antes de consolidar rankings territoriales.
* **Interpretación:** Galicia concentra aproximadamente la mitad de todo el conjunto de datos, reflejando tanto la presencia consolidada de la especie en el noroeste ibérico como una alta intensidad de muestreo y reporte.

### Gráfico 4. Método de observación (`basisOfRecord`)
* **Idoneidad:** Muy adecuado.
* **Tipo de visualización:** Gráfico circular de anillo (*donut chart*).
* **Distribución por categoría Darwin Core:**

| Método (`basisOfRecord`) | Registros | Porcentaje |
| :--- | :---: | :---: |
| `HUMAN_OBSERVATION` | 936 | 83,5 % |
| `MACHINE_OBSERVATION` | 185 | 16,5 % |

* **Interpretación:** Predominan ampliamente las observaciones humanas directas o indicios reportados por observadores (83,5 %). El 16,5 % restante corresponde a detección automática (cámaras de fototrampeo y sensores), un subconjunto clave para auditar programas de seguimiento sistemático.

### Gráfico 5. Distribución geográfica
* **Idoneidad:** Muy adecuado.
* **Tipo de visualización:** Diagrama de dispersión geográfica (`decimalLongitude` en eje X, `decimalLatitude` en eje Y) o mapa base con capas territoriales.
* **Patrones principales:**
  * Fuerte densidad de registros en el **noroeste peninsular**, destacando Galicia.
  * Presencia adicional en otras áreas de la mitad norte e interior de España.
  * En Portugal, las observaciones aparecen concentradas en núcleos relativamente localizados del norte.
* **Limitación espacial crítica:** La mediana de `coordinateUncertaintyInMeters` es de **27.661 metros (~27,7 km)** (debido principalmente al enmascaramiento de coordenadas de especies sensibles en plataformas como iNaturalist). Por ello, cada punto representa un área aproximada y no la ubicación exacta del animal. En aplicaciones cartográficas conviene dibujar círculos de incertidumbre o mallas hexagonales/cuadrículas UTM.

### Gráfico 6. Disponibilidad de fotografías y multimedia
* **Idoneidad:** Muy adecuado.
* **Tipo de visualización:** Gráfico circular de anillo (*donut chart*).
* **Distribución de cobertura multimedia:**

| Disponibilidad | Registros | Porcentaje |
| :--- | :---: | :---: |
| **Con material multimedia** | 801 | 71,5 % |
| **Sin material multimedia** | 320 | 28,5 % |

* **Interpretación:** Siete de cada diez registros incorporan evidencia gráfica o sonora. Esto habilita funcionalidades de alto valor en una aplicación interactiva:
  * Previsualización de fotografías en los marcadores del mapa.
  * Filtro booleano *"Solo registros con evidencia multimedia"*.
  * Galería cronológica y geográfica de avistamientos verificables.

---

## 4. Auditoría Adicional de Calidad y Procedencia de los Datos

Al profundizar en los metadatos del CSV se detectan tres dimensiones relevantes para el modelado y filtrado:

1. **Calidad y precisión espacial (`coordinateUncertaintyInMeters`):**
   * Los **1.121** registros disponen de coordenadas válidas (`decimalLatitude`, `decimalLongitude`).
   * **961** registros informan explícitamente su radio de incertidumbre, con una **mediana de 27,7 km**. Es imprescindible ofrecer un filtro de precisión máxima (p. ej., `< 1.000 m` o `< 5.000 m`) para análisis ecológicos locales.
2. **Conteo de individuos (`individualCount`):**
   * Solo **201 registros** (17,9 %) contienen este campo informado.
   * Entre los informados, la media es de **1,08 individuos** y el máximo de **4 ejemplares**. Dado el alto porcentaje de valores ausentes (82,1 %), no debe utilizarse para estimar tamaños de manada globales.
3. **Origen y proyectos publicadores:**
   * **747 registros** (66,6 %) provienen de ciencia ciudadana (**iNaturalist**).
   * **157 registros** (14,0 %) corresponden a campañas de fototrampeo del **proyecto MOMAT**.
   * **111 registros** (9,9 %) pertenecen al conjunto **Lobo en Álava**.
   * Esta composición explica tanto la alta proporción de multimedia (iNaturalist) como la concentración territorial en Galicia y Álava.

---

## 5. Especificación para Aplicación Interactiva de Biodiversidad

Para evolucionar este análisis estático hacia una aplicación interactiva (por ejemplo, un dashboard en **Plotly / Dash** o **Streamlit**) conectada a la API de GBIF o a la base de datos local, se establece la siguiente priorización de componentes:

| Prioridad | Visualización | Función Analítica Principal |
| :---: | :--- | :--- |
| **1** | **Mapa interactivo con capas** | Distribución geográfica en España y Portugal con radio de incertidumbre |
| **2** | **Gráfico de evolución anual** | Detección de tendencias y variaciones en el esfuerzo de registro |
| **3** | **Gráfico de distribución mensual** | Exploración de patrones estacionales (con opción de excluir años incompletos) |
| **4** | **Barras horizontales por provincia** | Comparativa de concentración territorial normalizada |
| **5** | **Anillo de método de observación** | Proporción entre ciencia ciudadana (`HUMAN`) y fototrampeo (`MACHINE`) |
| **6** | **Anillo / galería multimedia** | Filtrado y consulta visual de evidencias fotográficas |

**Filtros interactivos recomendados:** Año (`year`), País (`ES`/`PT`), Comunidad/Provincia normalizada, Método de observación (`basisOfRecord`), Incertidumbre máxima en metros y Disponibilidad de multimedia.

---

## 6. Conclusiones

1. **Concentración territorial:** Galicia reúne más de la mitad de todas las observaciones registradas (50,3 %).
2. **Variabilidad temporal:** 2025 marca el máximo histórico de actividad (247 registros) frente al mínimo acusado de 2023 (55 registros).
3. **Predominio de ciencia ciudadana:** El 83,5 % de los registros son observaciones humanas, con iNaturalist aportando dos tercios del total.
4. **Rigor metodológico:** Cualquier visualización derivada debe advertir al usuario que el mapa refleja **distribución de observaciones** condicionadas por el esfuerzo de muestreo y una incertidumbre mediana de ~27,7 km, y no la distribución poblacional exacta de *Canis lupus*.