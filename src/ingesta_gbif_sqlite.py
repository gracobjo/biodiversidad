import sys
import time
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ruta_src = Path(__file__).resolve().parent / "src"
if str(ruta_src) not in sys.path:
    sys.path.append(str(ruta_src))

from guardar_en_sqlite import guardar_en_sqlite

GBIF_API = "https://api.gbif.org/v1"
ESPECIE_OBJETIVO = "Canis lupus"
PAISES = ["ES", "PT"]
YEAR_RANGE = "2000,2026"
MAX_REGISTROS_POR_PAIS = 1000


def crear_sesion_gbif() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "BiodiversidadGBIF-SQLite/1.0", "Accept": "application/json"})
    retry = Retry(total=5, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def ejecutar_ingesta_sqlite() -> None:
    sesion = crear_sesion_gbif()
    resp_taxon = sesion.get(f"{GBIF_API}/species/match", params={"name": ESPECIE_OBJETIVO, "strict": "false"}, timeout=20)
    resp_taxon.raise_for_status()
    taxon = resp_taxon.json()
    clave_taxon = taxon["usageKey"]

    registros_crudos = []
    for pais in PAISES:
        offset = 0
        descargados_pais = 0
        while True:
            limite = 300 if MAX_REGISTROS_POR_PAIS is None else min(300, MAX_REGISTROS_POR_PAIS - descargados_pais)
            if limite <= 0:
                break
            r = sesion.get(
                f"{GBIF_API}/occurrence/search",
                params={"taxonKey": clave_taxon, "country": pais, "hasCoordinate": "true", "year": YEAR_RANGE, "limit": limite, "offset": offset},
                timeout=30,
            )
            r.raise_for_status()
            payload = r.json()
            lote = payload.get("results", [])
            if not lote:
                break
            registros_crudos.extend(lote)
            descargados_pais += len(lote)
            offset += len(lote)
            if payload.get("endOfRecords", False):
                break
            time.sleep(0.2)

    guardar_en_sqlite(taxon_info=taxon, registros_crudos=registros_crudos, session=sesion, gbif_api=GBIF_API)


if __name__ == "__main__":
    ejecutar_ingesta_sqlite()