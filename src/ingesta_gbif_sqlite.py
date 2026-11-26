import sys
import time
from pathlib import Path
import requests
import truststore
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# El proxy de inspección (Netskope) firma el tráfico con una CA que está en
# el almacén de Windows, no en el paquete certifi que usa requests.
truststore.inject_into_ssl()

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


def obtener_taxon(especie: str, sesion: requests.Session | None = None) -> dict:
    """Resuelve el nombre científico en /v1/species/match."""
    http = sesion or crear_sesion_gbif()
    respuesta = http.get(
        f"{GBIF_API}/species/match",
        params={"name": especie, "strict": "false"},
        timeout=20,
    )
    respuesta.raise_for_status()
    taxon = respuesta.json()
    if not taxon.get("usageKey"):
        raise ValueError(f"GBIF no devolvió usageKey para '{especie}'.")
    return taxon


def descargar_desde_gbif(
    especie: str = ESPECIE_OBJETIVO,
    paises: list[str] | None = None,
    year_range: str | None = YEAR_RANGE,
    max_registros_por_pais: int | None = MAX_REGISTROS_POR_PAIS,
    has_coordinate: bool = True,
    on_progreso=None,
) -> tuple[dict, list[dict], requests.Session]:
    """Descarga el taxón y las ocurrencias paginadas. No escribe en la base de datos."""
    paises_consulta = list(paises or PAISES)
    sesion = crear_sesion_gbif()

    def aviso(mensaje: str) -> None:
        if on_progreso is not None:
            on_progreso(mensaje)

    aviso(f"GET {GBIF_API}/species/match  name={especie}")
    taxon = obtener_taxon(especie, sesion)
    clave_taxon = taxon["usageKey"]
    aviso(f"Taxón {taxon.get('scientificName')}  usageKey={clave_taxon}  status={taxon.get('status')}")

    registros_crudos: list[dict] = []
    for pais in paises_consulta:
        offset = 0
        descargados_pais = 0
        total_anunciado = None
        while True:
            limite = 300 if max_registros_por_pais is None else min(300, max_registros_por_pais - descargados_pais)
            if limite <= 0:
                break
            params = {"taxonKey": clave_taxon, "country": pais, "limit": limite, "offset": offset}
            if year_range:
                params["year"] = year_range
            if has_coordinate:
                params["hasCoordinate"] = "true"
            aviso(f"GET {GBIF_API}/occurrence/search  country={pais} offset={offset} limit={limite}")
            respuesta = sesion.get(f"{GBIF_API}/occurrence/search", params=params, timeout=30)
            respuesta.raise_for_status()
            payload = respuesta.json()
            if total_anunciado is None:
                total_anunciado = payload.get("count")
            lote = payload.get("results", [])
            if not lote:
                break
            registros_crudos.extend(lote)
            descargados_pais += len(lote)
            offset += len(lote)
            aviso(f"{pais}: {descargados_pais} descargados de {total_anunciado} que anuncia GBIF")
            if payload.get("endOfRecords", False):
                break
            time.sleep(0.2)

    aviso(f"Descarga lista: {len(registros_crudos)} ocurrencias")
    return taxon, registros_crudos, sesion


def ejecutar_ingesta_sqlite() -> None:
    taxon, registros_crudos, sesion = descargar_desde_gbif()
    guardar_en_sqlite(taxon_info=taxon, registros_crudos=registros_crudos, session=sesion, gbif_api=GBIF_API)


if __name__ == "__main__":
    ejecutar_ingesta_sqlite()