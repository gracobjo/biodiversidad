# Especies por clase en España y Portugal (GBIF)

Este cuaderno se apoya en el pipeline multi-especie de [`gbif_multiespecie_es_pt.ipynb`](../../notebooks/gbif_multiespecie_es_pt.ipynb): mismos países (`ES`, `PT`), mismos años y la misma carpeta de salida. No descarga el lote de ocurrencias ni pinta el mapa comparativo.

Sirve para **ver las especies** antes de elegir cuáles bajar. Un ranking único de `/v1/occurrence/search` se llena de aves. Aquí se piden cinco especies con coordenadas de cada clase, aunque tengan menos registros:

- Mammalia
- Squamata (lagartos y serpientes; en GBIF no salen como clase Reptilia)
- Amphibia
- Insecta
- Magnoliopsida y Liliopsida
- Aves

La misma lista la muestra la interfaz, en el botón **Especies con coordenadas**.

El entorno virtual es la carpeta `.venv`. El kernel del cuaderno es **Python (biodiversidad)** (intérprete `.venv\Scripts\python.exe`). Si una celda se queda en `[*]` y no imprime el intérprete, interrumpe la ejecución y vuelve a lanzarla con ese kernel. Si una clase no responde, se omite y la celda termina con el resto.

```python
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

from ingesta_gbif_sqlite import (
    CLASES_A_MOSTRAR,
    ESPECIES_POR_CLASE,
    listar_especies_con_coordenadas,
)

PAISES = ["ES", "PT"]
YEAR_RANGE = "2000,2026"
CARPETA_SALIDA = RAIZ / "salidas_gbif_multiespecie"
CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

print("Intérprete:", sys.executable, flush=True)
print("Clases:", ", ".join(CLASES_A_MOSTRAR), flush=True)
print(f"Especies por clase: {ESPECIES_POR_CLASE}", flush=True)
print(f"Salida: {CARPETA_SALIDA}", flush=True)
```

    Intérprete: e:\Users\gracobjo\Documents\proyectosMios\biodiversidad\.venv\Scripts\python.exe
    Clases: Mammalia, Squamata, Amphibia, Insecta, Magnoliopsida, Liliopsida, Aves
    Especies por clase: 5
    Salida: e:\Users\gracobjo\Documents\proyectosMios\biodiversidad\salidas_gbif_multiespecie

## 1. Catálogo

Endpoints:

- `GET /v1/species/match?rank=CLASS` resuelve la clave de cada clase.
- `GET /v1/occurrence/search?classKey={clave}&facet=speciesKey&hasCoordinate=true` devuelve las especies con coordenadas de esa clase.
- `GET /v1/species/{speciesKey}` aporta el nombre, la clase y la familia.

```python
import time

def progreso(mensaje: str) -> None:
    print(mensaje, flush=True)

inicio = time.perf_counter()
filas = listar_especies_con_coordenadas(
    paises=PAISES,
    year_range=YEAR_RANGE,
    limite=ESPECIES_POR_CLASE,
    on_progreso=progreso,
)
print(
    f"Catálogo listo: {len(filas)} especies en {time.perf_counter() - inicio:.0f} s.",
    flush=True,
)
df_especies = pd.DataFrame(filas)
df_especies
```

    Clase 1/7: Mammalia
    Clase 2/7: Squamata
    Clase 3/7: Amphibia
    Clase 4/7: Insecta
    Clase 5/7: Magnoliopsida
    Clase 6/7: Liliopsida
    Clase 7/7: Aves
    Nombres de 35 especies
    Catálogo listo: 35 especies en 2 s.

              nombre_cientifico          clase           familia  taxon_key  \
    0                Sus scrofa       Mammalia            Suidae    7705930   
    1     Tarentola mauritanica       Squamata  Phyllodactylidae    2445034   
    2         Pelophylax perezi       Amphibia           Ranidae    2426658   
    3         Popillia japonica        Insecta      Scarabaeidae    4425774   
    4             Quercus suber  Magnoliopsida          Fagaceae    2879411   
    5              Arundo donax     Liliopsida           Poaceae    2703041   
    6         Passer domesticus           Aves        Passeridae    5231190   
    7             Vulpes vulpes       Mammalia           Canidae    5219243   
    8      Psammodromus algirus       Squamata        Lacertidae    2469763   
    9         Epidalea calamita       Amphibia         Bufonidae    2422507   
    10  Thaumetopoea pityocampa        Insecta      Notodontidae    1824131   
    11            Olea europaea  Magnoliopsida          Oleaceae    5415040   
    12            Smilax aspera     Liliopsida       Smilacaceae    5295044   
    13            Turdus merula           Aves          Turdidae    2490719   
    14      Capreolus capreolus       Mammalia          Cervidae    5220126   
    15            Teira dugesii       Squamata        Lacertidae    2468700   
    16    Salamandra salamandra       Amphibia     Salamandridae    2431776   
    17          Pararge aegeria        Insecta       Nymphalidae    8049830   
    18     Quercus rotundifolia  Magnoliopsida          Fagaceae    2881550   
    19         Ruscus aculeatus     Liliopsida      Asparagaceae    2769766   
    20          Hirundo rustica           Aves      Hirundinidae    9515886   
    21           Cervus elaphus       Mammalia          Cervidae    2440958   
    22            Timon lepidus       Squamata        Lacertidae    2468542   
    23            Bufo spinosus       Amphibia         Bufonidae    9421513   
    24             Pieris rapae        Insecta          Pieridae    1920496   
    25       Pistacia lentiscus  Magnoliopsida     Anacardiaceae    3190583   
    26       Dactylis glomerata     Liliopsida           Poaceae    2705308   
    27             Larus fuscus           Aves           Laridae    2481174   
    28          Capra pyrenaica       Mammalia           Bovidae    2441054   
    29  Malpolon monspessulanus       Squamata     Psammophiidae    8796529   
    30      Alytes obstetricans       Amphibia          Alytidae    2426612   
    31           Colias croceus        Insecta          Pieridae    5137612   
    32           Vitis vinifera  Magnoliopsida          Vitaceae    5372392   
    33    Asparagus acutifolius     Liliopsida      Asparagaceae    2768995   
    34       Sylvia atricapilla           Aves         Sylviidae    2492956   

        ocurrencias_con_coordenadas                                 endpoint  
    0                        631190  https://api.gbif.org/v1/species/7705930  
    1                         36537  https://api.gbif.org/v1/species/2445034  
    2                         43977  https://api.gbif.org/v1/species/2426658  
    3                         96319  https://api.gbif.org/v1/species/4425774  
    4                        199743  https://api.gbif.org/v1/species/2879411  
    5                         33863  https://api.gbif.org/v1/species/2703041  
    6                       1663718  https://api.gbif.org/v1/species/5231190  
    7                        485885  https://api.gbif.org/v1/species/5219243  
    8                         32720  https://api.gbif.org/v1/species/2469763  
    9                         23925  https://api.gbif.org/v1/species/2422507  
    10                        70875  https://api.gbif.org/v1/species/1824131  
    11                       140293  https://api.gbif.org/v1/species/5415040  
    12                        24220  https://api.gbif.org/v1/species/5295044  
    13                      1625179  https://api.gbif.org/v1/species/2490719  
    14                       332608  https://api.gbif.org/v1/species/5220126  
    15                        18714  https://api.gbif.org/v1/species/2468700  
    16                        20466  https://api.gbif.org/v1/species/2431776  
    17                        58896  https://api.gbif.org/v1/species/8049830  
    18                       135473  https://api.gbif.org/v1/species/2881550  
    19                        23334  https://api.gbif.org/v1/species/2769766  
    20                      1365921  https://api.gbif.org/v1/species/9515886  
    21                       246110  https://api.gbif.org/v1/species/2440958  
    22                        15953  https://api.gbif.org/v1/species/2468542  
    23                        18159  https://api.gbif.org/v1/species/9421513  
    24                        45230  https://api.gbif.org/v1/species/1920496  
    25                        56007  https://api.gbif.org/v1/species/3190583  
    26                        22699  https://api.gbif.org/v1/species/2705308  
    27                      1349281  https://api.gbif.org/v1/species/2481174  
    28                        94327  https://api.gbif.org/v1/species/2441054  
    29                        14109  https://api.gbif.org/v1/species/8796529  
    30                         8217  https://api.gbif.org/v1/species/2426612  
    31                        42683  https://api.gbif.org/v1/species/5137612  
    32                        48471  https://api.gbif.org/v1/species/5372392  
    33                        21001  https://api.gbif.org/v1/species/2768995  
    34                      1304561  https://api.gbif.org/v1/species/2492956  

## 2. Ver las clases y las familias

Cada bloque es una clase. La familia permite distinguir, dentro de los mamíferos, cánidos, suidos o cérvidos, y dentro de las aves, el grupo de cada especie.

```python
resumen_clases = (
    df_especies.groupby("clase", sort=False)
    .agg(
        especies=("nombre_cientifico", "count"),
        ocurrencias_con_coordenadas=("ocurrencias_con_coordenadas", "sum"),
    )
    .reset_index()
)
display(resumen_clases)

for clase, bloque in df_especies.groupby("clase", sort=False):
    print(f"\n{clase}")
    display(
        bloque[
            [
                "familia",
                "nombre_cientifico",
                "taxon_key",
                "ocurrencias_con_coordenadas",
            ]
        ].reset_index(drop=True)
    )
```

               clase  especies  ocurrencias_con_coordenadas
    0       Mammalia         5                      1790120
    1       Squamata         5                       118033
    2       Amphibia         5                       114744
    3        Insecta         5                       314003
    4  Magnoliopsida         5                       579987
    5     Liliopsida         5                       125117
    6           Aves         5                      7308660

    Mammalia

        familia    nombre_cientifico  taxon_key  ocurrencias_con_coordenadas
    0    Suidae           Sus scrofa    7705930                       631190
    1   Canidae        Vulpes vulpes    5219243                       485885
    2  Cervidae  Capreolus capreolus    5220126                       332608
    3  Cervidae       Cervus elaphus    2440958                       246110
    4   Bovidae      Capra pyrenaica    2441054                        94327

    Squamata

                familia        nombre_cientifico  taxon_key  \
    0  Phyllodactylidae    Tarentola mauritanica    2445034   
    1        Lacertidae     Psammodromus algirus    2469763   
    2        Lacertidae            Teira dugesii    2468700   
    3        Lacertidae            Timon lepidus    2468542   
    4     Psammophiidae  Malpolon monspessulanus    8796529   

       ocurrencias_con_coordenadas  
    0                        36537  
    1                        32720  
    2                        18714  
    3                        15953  
    4                        14109  

    Amphibia

             familia      nombre_cientifico  taxon_key  \
    0        Ranidae      Pelophylax perezi    2426658   
    1      Bufonidae      Epidalea calamita    2422507   
    2  Salamandridae  Salamandra salamandra    2431776   
    3      Bufonidae          Bufo spinosus    9421513   
    4       Alytidae    Alytes obstetricans    2426612   

       ocurrencias_con_coordenadas  
    0                        43977  
    1                        23925  
    2                        20466  
    3                        18159  
    4                         8217  

    Insecta

            familia        nombre_cientifico  taxon_key  \
    0  Scarabaeidae        Popillia japonica    4425774   
    1  Notodontidae  Thaumetopoea pityocampa    1824131   
    2   Nymphalidae          Pararge aegeria    8049830   
    3      Pieridae             Pieris rapae    1920496   
    4      Pieridae           Colias croceus    5137612   

       ocurrencias_con_coordenadas  
    0                        96319  
    1                        70875  
    2                        58896  
    3                        45230  
    4                        42683  

    Magnoliopsida

             familia     nombre_cientifico  taxon_key  ocurrencias_con_coordenadas
    0       Fagaceae         Quercus suber    2879411                       199743
    1       Oleaceae         Olea europaea    5415040                       140293
    2       Fagaceae  Quercus rotundifolia    2881550                       135473
    3  Anacardiaceae    Pistacia lentiscus    3190583                        56007
    4       Vitaceae        Vitis vinifera    5372392                        48471

    Liliopsida

            familia      nombre_cientifico  taxon_key  ocurrencias_con_coordenadas
    0       Poaceae           Arundo donax    2703041                        33863
    1   Smilacaceae          Smilax aspera    5295044                        24220
    2  Asparagaceae       Ruscus aculeatus    2769766                        23334
    3       Poaceae     Dactylis glomerata    2705308                        22699
    4  Asparagaceae  Asparagus acutifolius    2768995                        21001

    Aves

            familia   nombre_cientifico  taxon_key  ocurrencias_con_coordenadas
    0    Passeridae   Passer domesticus    5231190                      1663718
    1      Turdidae       Turdus merula    2490719                      1625179
    2  Hirundinidae     Hirundo rustica    9515886                      1365921
    3       Laridae        Larus fuscus    2481174                      1349281
    4     Sylviidae  Sylvia atricapilla    2492956                      1304561

## 3. Guardar el catálogo y elegir especies para el cuaderno multi-especie

El CSV queda en `salidas_gbif_multiespecie/especies_por_clase_es_pt.csv`. La lista de nombres se puede copiar en `ESPECIES_OBJETIVO` de `gbif_multiespecie_es_pt.ipynb` para descargar ocurrencias y mapas. Conviene no copiar las 35 a la vez: ese cuaderno baja hasta 600 registros por país y por especie.

```python
ruta_csv = CARPETA_SALIDA / "especies_por_clase_es_pt.csv"
df_especies.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
print(ruta_csv)

print("\nESPECIES_OBJETIVO = [")
for nombre in df_especies["nombre_cientifico"]:
    print(f'    "{nombre}",')
print("]")
```

    e:\Users\gracobjo\Documents\proyectosMios\biodiversidad\salidas_gbif_multiespecie\especies_por_clase_es_pt.csv

    ESPECIES_OBJETIVO = [
        "Sus scrofa",
        "Tarentola mauritanica",
        "Pelophylax perezi",
        "Popillia japonica",
        "Quercus suber",
        "Arundo donax",
        "Passer domesticus",
        "Vulpes vulpes",
        "Psammodromus algirus",
        "Epidalea calamita",
        "Thaumetopoea pityocampa",
        "Olea europaea",
        "Smilax aspera",
        "Turdus merula",
        "Capreolus capreolus",
        "Teira dugesii",
        "Salamandra salamandra",
        "Pararge aegeria",
        "Quercus rotundifolia",
        "Ruscus aculeatus",
        "Hirundo rustica",
        "Cervus elaphus",
        "Timon lepidus",
        "Bufo spinosus",
        "Pieris rapae",
        "Pistacia lentiscus",
        "Dactylis glomerata",
        "Larus fuscus",
        "Capra pyrenaica",
        "Malpolon monspessulanus",
        "Alytes obstetricans",
        "Colias croceus",
        "Vitis vinifera",
        "Asparagus acutifolius",
        "Sylvia atricapilla",
    ]
