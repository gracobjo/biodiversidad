# Fase B: Análisis Offline de Biodiversidad desde MySQL 8

Este cuaderno lee los datos almacenados localmente en la base de datos `gbif_biodiversidad` mediante `src/consulta_gbif.py`, sin realizar peticiones externas a la API de GBIF.

```python
import sys
from pathlib import Path
import pandas as pd

# Asegurar que Python encuentra la carpeta src/
ruta_src = (Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent) / "src".resolve()
if str(ruta_src) not in sys.path:
    sys.path.append(str(ruta_src))

from consulta_gbif import (
    cargar_ocurrencias,
    consultar_campos_raw_json,
    obtener_resumen_general,
    resumen_territorial_por_comunidad,
    top_datasets_publicadores,
)

pd.set_option("display.max_columns", 20)
pd.set_option("display.max_colwidth", 60)
```

## 1. Estado de la base de datos local

```python
df_resumen_bd = obtener_resumen_general()
df_resumen_bd
```

                tabla  total
    0         taxones      1
    1  organizaciones     12
    2        datasets     17
    3     ocurrencias   2000

## 2. Carga de ocurrencias (`cargar_ocurrencias`)

Carga los registros de España (`ES`) y Portugal (`PT`) filtrando únicamente el lobo silvestre (`solo_lobo_silvestre=True`) o el conjunto completo (`solo_lobo_silvestre=False`).

```python
# Carga completa (ES + PT)
df_todos = cargar_ocurrencias(paises=("ES", "PT"), solo_lobo_silvestre=False)

# Carga filtrada: solo lobo silvestre (excluye Canis lupus familiaris)
df = cargar_ocurrencias(paises=("ES", "PT"), solo_lobo_silvestre=True, anio_min=2000)

print(f"Total registros en BD (ES + PT): {len(df_todos):,}")
print(f"Registros de lobo silvestre (>= 2000): {len(df):,}")

df[
    [
        "key",
        "countryCode",
        "year",
        "scientificName",
        "comunidad_gadm",
        "provincia_gadm",
        "basisOfRecord",
        "publishing_org_title",
        "gbif_url",
    ]
].head(10)
```

    Total registros en BD (ES + PT): 2,000
    Registros de lobo silvestre (>= 2000): 880

              key countryCode  year              scientificName  \
    0  6907542303          ES  2026  Canis lupus Linnaeus, 1758   
    1  6885782502          PT  2026  Canis lupus Linnaeus, 1758   
    2  6885119513          ES  2026  Canis lupus Linnaeus, 1758   
    3  6871713228          ES  2026  Canis lupus Linnaeus, 1758   
    4  6871646127          PT  2026  Canis lupus Linnaeus, 1758   
    5  6871558851          ES  2026  Canis lupus Linnaeus, 1758   
    6  6871537048          PT  2026  Canis lupus Linnaeus, 1758   
    7  6871476663          ES  2026  Canis lupus Linnaeus, 1758   
    8  6871167428          ES  2026  Canis lupus Linnaeus, 1758   
    9  6871055072          ES  2026  Canis lupus Linnaeus, 1758   

               comunidad_gadm   provincia_gadm      basisOfRecord  \
    0         Castilla y León           Zamora  HUMAN_OBSERVATION   
    1                   Braga  Terras de Bouro  HUMAN_OBSERVATION   
    2  Principado de Asturias         Asturias  HUMAN_OBSERVATION   
    3                     NaN              NaN  HUMAN_OBSERVATION   
    4         Castilla y León           Zamora  HUMAN_OBSERVATION   
    5  Principado de Asturias         Asturias  HUMAN_OBSERVATION   
    6                 Galicia          Ourense  HUMAN_OBSERVATION   
    7         Castilla y León             León  HUMAN_OBSERVATION   
    8         Castilla y León           Zamora  HUMAN_OBSERVATION   
    9  Principado de Asturias         Asturias  HUMAN_OBSERVATION   

      publishing_org_title                                    gbif_url  
    0      iNaturalist.org  https://www.gbif.org/occurrence/6907542303  
    1      iNaturalist.org  https://www.gbif.org/occurrence/6885782502  
    2      iNaturalist.org  https://www.gbif.org/occurrence/6885119513  
    3      iNaturalist.org  https://www.gbif.org/occurrence/6871713228  
    4      iNaturalist.org  https://www.gbif.org/occurrence/6871646127  
    5      iNaturalist.org  https://www.gbif.org/occurrence/6871558851  
    6      iNaturalist.org  https://www.gbif.org/occurrence/6871537048  
    7      iNaturalist.org  https://www.gbif.org/occurrence/6871476663  
    8      iNaturalist.org  https://www.gbif.org/occurrence/6871167428  
    9      iNaturalist.org  https://www.gbif.org/occurrence/6871055072  

## 3. Distribución territorial y fuentes publicadoras

```python
df_territorial_es = resumen_territorial_por_comunidad(pais="ES")
display(df_territorial_es.head(15))

df_top_datasets = top_datasets_publicadores(limite=10)
display(df_top_datasets)
```

                            region       tipo_evidencia  total_registros  \
    0                    Andalucía    HUMAN_OBSERVATION              293   
    1                      Galicia    HUMAN_OBSERVATION              232   
    2              Castilla y León    HUMAN_OBSERVATION               76   
    3                     Cataluña    HUMAN_OBSERVATION               46   
    4              Castilla y León  MACHINE_OBSERVATION               44   
    5                      Galicia  MACHINE_OBSERVATION               40   
    6           Castilla-La Mancha    HUMAN_OBSERVATION               39   
    7   Comunidad Foral de Navarra    HUMAN_OBSERVATION               33   
    8       Principado de Asturias    HUMAN_OBSERVATION               32   
    9       Principado de Asturias  MACHINE_OBSERVATION               25   
    10                  País Vasco    HUMAN_OBSERVATION               24   
    11            Región de Murcia    HUMAN_OBSERVATION               18   
    12                      Aragón    HUMAN_OBSERVATION               15   
    13                   Andalucía  MACHINE_OBSERVATION               15   
    14                    La Rioja  MACHINE_OBSERVATION               12   

        desde_anio  hasta_anio  
    0         2024        2026  
    1         2024        2026  
    2         2024        2026  
    3         2024        2026  
    4         2024        2025  
    5         2024        2025  
    6         2024        2026  
    7         2024        2026  
    8         2024        2026  
    9         2024        2025  
    10        2024        2025  
    11        2024        2026  
    12        2024        2026  
    13        2024        2025  
    14        2025        2025  

                                                           dataset  \
    0                      iNaturalist Research-grade Observations   
    1  Long-term monitoring of mammal communities in the Peneda...   
    2           Observation.org, Nature data from around the World   
    3       Wildlife inventory in the Azores using camera trapping   
    4  Mammals – Camera Trap Surveys – Spain – 2014–2026 – MOMA...   
    5  EDP Baixo Sabor: Construction and Reservoir Filling Phas...   
    6  EDP Baixo Sabor: Construction and Reservoir Filling Phas...   
    7  Mammals – Transect Sign Surveys – Spain – 2022–2025 – MO...   
    8  Mammals – Point Surveys – Spain – 2023–2025 – MOMAT Project   
    9  Data collected on citizen science web portal www.ornitho...   

                                                      organizacion pais_org  \
    0                                              iNaturalist.org       US   
    1                                    Biodiversity Data Journal       BG   
    2                                              Observation.org       NL   
    3                                      Universidade dos Açores       PT   
    4  Sociedad Ibérica para la Conservación y Estudio de los M...       ES   
    5                                                          EDP       PT   
    6                                                          EDP       PT   
    7  Sociedad Ibérica para la Conservación y Estudio de los M...       ES   
    8  Sociedad Ibérica para la Conservación y Estudio de los M...       ES   
    9  ICO-Institut Català d'Ornitologia (Catalan Ornithologica...       ES   

                                                         licencia  registros_en_bd  
    0     http://creativecommons.org/licenses/by-nc/4.0/legalcode              609  
    1        http://creativecommons.org/licenses/by/4.0/legalcode              398  
    2     http://creativecommons.org/licenses/by-nc/4.0/legalcode              248  
    3        http://creativecommons.org/licenses/by/4.0/legalcode              210  
    4        http://creativecommons.org/licenses/by/4.0/legalcode              148  
    5        http://creativecommons.org/licenses/by/4.0/legalcode              130  
    6        http://creativecommons.org/licenses/by/4.0/legalcode              101  
    7        http://creativecommons.org/licenses/by/4.0/legalcode               55  
    8        http://creativecommons.org/licenses/by/4.0/legalcode               54  
    9  http://creativecommons.org/publicdomain/zero/1.0/legalcode               24  

## 4. Consulta dinámica sobre `raw_json` (multimedia y hábitat)

```python
df_multimedia = consultar_campos_raw_json(limite=15)
print(f"Registros encontrados con multimedia o hábitat en JSON: {len(df_multimedia)}")
df_multimedia
```

    Registros encontrados con multimedia o hábitat en JSON: 15

        occurrence_key country_code  year                        scientific_name  \
    0       1703216132           PT  2017             Canis lupus Linnaeus, 1758   
    1       1850963606           PT  2014             Canis lupus Linnaeus, 1758   
    2       1950006002           PT  2018             Canis lupus Linnaeus, 1758   
    3       2251866928           PT  2019             Canis lupus Linnaeus, 1758   
    4       2427354900           PT  2013  Canis lupus familiaris Linnaeus, 1758   
    5       2427354916           PT  2013  Canis lupus familiaris Linnaeus, 1758   
    6       2427354922           PT  2013  Canis lupus familiaris Linnaeus, 1758   
    7       2427354937           PT  2013  Canis lupus familiaris Linnaeus, 1758   
    8       2427354939           PT  2013  Canis lupus familiaris Linnaeus, 1758   
    9       2427354945           PT  2013  Canis lupus familiaris Linnaeus, 1758   
    10      2427354951           PT  2013  Canis lupus familiaris Linnaeus, 1758   
    11      2427355014           PT  2013  Canis lupus familiaris Linnaeus, 1758   
    12      2427356179           PT  2014  Canis lupus familiaris Linnaeus, 1758   
    13      2427357246           PT  2013  Canis lupus familiaris Linnaeus, 1758   
    14      2427357389           PT  2013  Canis lupus familiaris Linnaeus, 1758   

                                 habitat_json comentarios_evento  \
    0                                     NaN                NaN   
    1                                     NaN                NaN   
    2                                     NaN                NaN   
    3                                     NaN                NaN   
    4   Forestry plantation (Cryptomeria sp.)          TER_13-15   
    5   Forestry plantation (Cryptomeria sp.)          TER_13-15   
    6   Forestry plantation (Cryptomeria sp.)          TER_13-15   
    7   Forestry plantation (Cryptomeria sp.)          TER_13-15   
    8   Forestry plantation (Cryptomeria sp.)          TER_13-15   
    9   Forestry plantation (Cryptomeria sp.)          TER_13-15   
    10  Forestry plantation (Cryptomeria sp.)          TER_13-15   
    11  Forestry plantation (Cryptomeria sp.)          TER_13-15   
    12        Exotic forest (Pittosporum sp.)          TER_13-15   
    13                    Seminatural pasture          TER_13-15   
    14                    Seminatural pasture          TER_13-15   

        num_archivos_media  \
    0                    1   
    1                    1   
    2                    1   
    3                    1   
    4                    0   
    5                    0   
    6                    0   
    7                    0   
    8                    0   
    9                    0   
    10                   0   
    11                   0   
    12                   0   
    13                   0   
    14                   0   

                                                   url_primera_foto  \
    0   https://inaturalist-open-data.s3.amazonaws.com/photos/12...   
    1   https://inaturalist-open-data.s3.amazonaws.com/photos/19...   
    2   https://inaturalist-open-data.s3.amazonaws.com/photos/29...   
    3   https://inaturalist-open-data.s3.amazonaws.com/photos/39...   
    4                                                           NaN   
    5                                                           NaN   
    6                                                           NaN   
    7                                                           NaN   
    8                                                           NaN   
    9                                                           NaN   
    10                                                          NaN   
    11                                                          NaN   
    12                                                          NaN   
    13                                                          NaN   
    14                                                          NaN   

                                          gbif_url  
    0   https://www.gbif.org/occurrence/1703216132  
    1   https://www.gbif.org/occurrence/1850963606  
    2   https://www.gbif.org/occurrence/1950006002  
    3   https://www.gbif.org/occurrence/2251866928  
    4   https://www.gbif.org/occurrence/2427354900  
    5   https://www.gbif.org/occurrence/2427354916  
    6   https://www.gbif.org/occurrence/2427354922  
    7   https://www.gbif.org/occurrence/2427354937  
    8   https://www.gbif.org/occurrence/2427354939  
    9   https://www.gbif.org/occurrence/2427354945  
    10  https://www.gbif.org/occurrence/2427354951  
    11  https://www.gbif.org/occurrence/2427355014  
    12  https://www.gbif.org/occurrence/2427356179  
    13  https://www.gbif.org/occurrence/2427357246  
    14  https://www.gbif.org/occurrence/2427357389  

## 5. Mapa interactivo rápido con Folium (sin API Key)

```python
from pathlib import Path
import folium
from folium.plugins import MarkerCluster

# 1. Crear carpeta de salida si no existe
carpeta_salida = (Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent) / "salidas_gbif_multiespecie"
carpeta_salida.mkdir(parents=True, exist_ok=True)
ruta_mapa_html = carpeta_salida / "mapa_ocurrencias_gbif.html"

# 2. Filtrar registros con coordenadas válidas
df_mapa = df.dropna(subset=["decimalLatitude", "decimalLongitude"]).copy()

mapa = folium.Map(
    location=[41.8, -5.5],
    zoom_start=6,
    tiles="OpenStreetMap"
)

# Capas base gratuitas sin API key
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery",
    name="Satélite (Esri)",
    overlay=False,
    control=True,
).add_to(mapa)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Street Map",
    name="Callejero (Esri)",
    overlay=False,
    control=True,
).add_to(mapa)

cluster = MarkerCluster(name="Ocurrencias Canis lupus").add_to(mapa)

for _, fila in df_mapa.iterrows():
    url_img = fila.get("url_imagen")
    tiene_imagen = isinstance(url_img, str) and url_img.startswith("http")

    bloque_imagen = ""
    if tiene_imagen:
        bloque_imagen = (
            f"<div style='margin:6px 0;'>"
            f"<a href='{url_img}' target='_blank' rel='noopener noreferrer'>"
            f"<img src='{url_img}' alt='Foto avistamiento' "
            f"style='width:220px; max-height:150px; object-fit:cover; border-radius:4px; display:block; margin-bottom:4px;'>"
            f"Ver imagen original ({int(fila.get('num_media', 1))} media)</a>"
            f"</div>"
        )

    popup_html = (
        f"<div style='font-family: Arial, sans-serif; font-size: 12px;'>"
        f"<b>{fila['scientificName']}</b><br>"
        f"País: {fila['countryCode']} | Año: {fila['year']}<br>"
        f"Región: {fila['comunidad_gadm'] or 'N/D'}<br>"
        f"Evidencia: {fila['basisOfRecord']}<br>"
        f"Fuente: {fila['publishing_org_title'] or 'N/D'}<br>"
        f"{bloque_imagen}"
        f"<a href='{fila['gbif_url']}' target='_blank' rel='noopener noreferrer'>Ver ficha completa en GBIF</a>"
        f"</div>"
    )

    folium.CircleMarker(
        location=[fila["decimalLatitude"], fila["decimalLongitude"]],
        radius=6 if tiene_imagen else 5,
        color="#d00000" if tiene_imagen else "#1b4332",
        fill=True,
        fill_color="#e63946" if tiene_imagen else "#2d6a4f",
        fill_opacity=0.85,
        popup=folium.Popup(popup_html, max_width=260),
    ).add_to(cluster)

folium.LayerControl().add_to(mapa)

# 3. Guardar mapa en salidas_gbif_multiespecie/
mapa.save(str(ruta_mapa_html))
print(f"Mapa guardado correctamente en: {ruta_mapa_html.resolve()}")
print(f"Registros con imagen directa: {df_mapa['url_imagen'].notna().sum()} de {len(df_mapa)}")

mapa
```

    Mapa guardado correctamente en: C:\Users\chuwi\Documents\biodiversidad\salidas_gbif_multiespecie\mapa_ocurrencias_gbif.html
    Registros con imagen directa: 524 de 880

    Salida interactiva omitida en esta copia (mapa HTML de 1805899 caracteres). El cuaderno la escribe en salidas_gbif_multiespecie/mapa_ocurrencias_gbif.html.
