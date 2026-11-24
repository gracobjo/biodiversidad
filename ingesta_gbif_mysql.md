# Fase A: Ingesta de Datos GBIF a MySQL 8

Este cuaderno ejecuta la extracción desde la API pública de GBIF (`/v1/species/match`, `/v1/occurrence/search` y catálogos del *Registry*) y persiste los datos de forma idempotente en la base de datos local `gbif_biodiversidad` mediante `src/volcarEndpoints.py`.


```python
import sys
import time
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Añadir carpeta src/ al path para importar volcarEndpoints y db_config
ruta_src = Path("src").resolve()
if str(ruta_src) not in sys.path:
    sys.path.append(str(ruta_src))

from volcarEndpoints import guardar_en_mysql
from db_config import DB_CONFIG

print(f"Ruta src cargada: {ruta_src}")
print(f"Base de datos destino: {DB_CONFIG['database']} en {DB_CONFIG['host']}:{DB_CONFIG['port']}")
```

    Ruta src cargada: C:\Users\chuwi\Documents\biodiversidad\src
    Base de datos destino: gbif_biodiversidad en localhost:3306
    

## 1. Configuración de parámetros de extracción

Define aquí la especie, los países (`ES`, `PT`, etc.), el rango temporal y el límite máximo de registros por país (`None` para descargar todos los disponibles).


```python
GBIF_API = "https://api.gbif.org/v1"

ESPECIE_OBJETIVO = "Canis lupus"
PAISES = ["ES", "PT"]          # España y Portugal
YEAR_RANGE = "2000,2026"      # Rango de años (o None para todos)
HAS_COORDINATE = True         # Solo registros georreferenciados
MAX_REGISTROS_POR_PAIS = 1000 # Pon None si deseas descargar el 100% de ocurrencias
PAGE_SIZE = 300               # Máximo permitido por página en GBIF API
```

## 2. Sesión HTTP con reintentos y funciones de descarga


```python
def crear_sesion_gbif() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "BiodiversidadGBIF-ETL/1.0 (Python; MySQL8)",
        "Accept": "application/json"
    })
    retry = Retry(
        total=5,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def obtener_taxon(session: requests.Session, nombre_cientifico: str) -> dict:
    resp = session.get(
        f"{GBIF_API}/species/match",
        params={"name": nombre_cientifico, "strict": "false"},
        timeout=20
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("usageKey"):
        raise ValueError(f"No se encontró usageKey para '{nombre_cientifico}': {data}")
    return data


def descargar_ocurrencias(
    session: requests.Session,
    taxon_key: int,
    country: str,
    year_range: str | None = None,
    has_coordinate: bool = True,
    max_registros: int | None = None,
    page_size: int = 300
) -> list[dict]:
    registros = []
    offset = 0

    while True:
        limite_actual = page_size
        if max_registros is not None:
            restantes = max_registros - len(registros)
            if restantes <= 0:
                break
            limite_actual = min(page_size, restantes)

        params = {
            "taxonKey": taxon_key,
            "country": country,
            "hasCoordinate": str(has_coordinate).lower(),
            "limit": limite_actual,
            "offset": offset
        }
        if year_range:
            params["year"] = year_range

        resp = session.get(f"{GBIF_API}/occurrence/search", params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        resultados = payload.get("results", [])
        total_disponible = payload.get("count", 0)

        if offset == 0:
            print(f"[{country}] Total disponible en GBIF: {total_disponible:,} registros.")

        if not resultados:
            break

        registros.extend(resultados)
        offset += len(resultados)
        print(f"[{country}] Descargados {len(registros)} registros...")

        if payload.get("endOfRecords", False):
            break
        time.sleep(0.2)

    return registros
```

## 3. Ejecución de descarga y volcado a MySQL 8


```python
sesion_gbif = crear_sesion_gbif()

# 1. Resolver taxón en GBIF
taxon = obtener_taxon(sesion_gbif, ESPECIE_OBJETIVO)
clave_taxon = taxon["usageKey"]
print(f"Taxón resuelto: {taxon.get('scientificName')} (taxonKey={clave_taxon}, rank={taxon.get('rank')})")

# 2. Descargar ocurrencias por cada país configurado
registros_crudos = []
for pais in PAISES:
    lote = descargar_ocurrencias(
        session=sesion_gbif,
        taxon_key=clave_taxon,
        country=pais,
        year_range=YEAR_RANGE,
        has_coordinate=HAS_COORDINATE,
        max_registros=MAX_REGISTROS_POR_PAIS,
        page_size=PAGE_SIZE
    )
    registros_crudos.extend(lote)

print(f"\nTotal registros listos para volcar: {len(registros_crudos)}")

# 3. Persistir taxón, organizaciones, datasets y ocurrencias en MySQL 8
guardar_en_mysql(
    db_config=DB_CONFIG,
    taxon_info=taxon,
    registros_crudos=registros_crudos,
    session=sesion_gbif,
    gbif_api=GBIF_API
)
```

    Taxón resuelto: Canis lupus Linnaeus, 1758 (taxonKey=5219173, rank=SPECIES)
    [ES] Total disponible en GBIF: 4,468 registros.
    [ES] Descargados 300 registros...
    [ES] Descargados 600 registros...
    [ES] Descargados 900 registros...
    [ES] Descargados 1000 registros...
    [PT] Total disponible en GBIF: 1,090 registros.
    [PT] Descargados 300 registros...
    [PT] Descargados 600 registros...
    [PT] Descargados 900 registros...
    [PT] Descargados 1000 registros...
    
    Total registros listos para volcar: 2000
    Carga completada: 1 taxón, 12 organizaciones, 17 datasets y 2000 ocurrencias.
    

## 4. Verificación rápida en MySQL


```python
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

url_conexion = URL.create(
    drivername="mysql+mysqlconnector",
    username=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    host=DB_CONFIG["host"],
    port=DB_CONFIG["port"],
    database=DB_CONFIG["database"],
)

engine = create_engine(url_conexion)

resumen_sql = """
SELECT
    country_code AS pais,
    taxon_rank AS rango,
    specific_epithet AS epiteto,
    COUNT(*) AS total_registros,
    MIN(year) AS anio_min,
    MAX(year) AS anio_max
FROM ocurrencias
GROUP BY country_code, taxon_rank, specific_epithet
ORDER BY pais, total_registros DESC;
"""

df_verificacion = pd.read_sql(resumen_sql, engine)
engine.dispose()

df_verificacion
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>pais</th>
      <th>rango</th>
      <th>epiteto</th>
      <th>total_registros</th>
      <th>anio_min</th>
      <th>anio_max</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>ES</td>
      <td>SPECIES</td>
      <td>familiaris</td>
      <td>526</td>
      <td>2024</td>
      <td>2026</td>
    </tr>
    <tr>
      <th>1</th>
      <td>ES</td>
      <td>SPECIES</td>
      <td>lupus</td>
      <td>423</td>
      <td>2024</td>
      <td>2026</td>
    </tr>
    <tr>
      <th>2</th>
      <td>ES</td>
      <td>SUBSPECIES</td>
      <td>lupus</td>
      <td>51</td>
      <td>2024</td>
      <td>2025</td>
    </tr>
    <tr>
      <th>3</th>
      <td>PT</td>
      <td>SUBSPECIES</td>
      <td>lupus</td>
      <td>470</td>
      <td>2013</td>
      <td>2023</td>
    </tr>
    <tr>
      <th>4</th>
      <td>PT</td>
      <td>SPECIES</td>
      <td>lupus</td>
      <td>457</td>
      <td>2011</td>
      <td>2026</td>
    </tr>
    <tr>
      <th>5</th>
      <td>PT</td>
      <td>SPECIES</td>
      <td>familiaris</td>
      <td>73</td>
      <td>2011</td>
      <td>2026</td>
    </tr>
  </tbody>
</table>
</div>


