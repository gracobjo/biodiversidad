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


ESPECIES_POR_CLASE = 5
# Las aves copan el ranking global. Estas clases se piden aparte.
# En las ocurrencias de GBIF los lagartos y las serpientes van en Squamata,
# no en una clase Reptilia con registros.
CLASES_A_MOSTRAR = (
    "Mammalia",
    "Squamata",
    "Amphibia",
    "Insecta",
    "Magnoliopsida",
    "Liliopsida",
    "Aves",
)


def listar_especies_con_coordenadas(
    paises: list[str] | None = None,
    year_range: str | None = None,
    limite: int = ESPECIES_POR_CLASE,
    on_progreso=None,
) -> list[dict]:
    """Especies con coordenadas: cinco de cada clase, no solo las más numerosas.

    La clave de cada clase sale de GET /v1/species/match?rank=CLASS.
    Las especies, de GET /v1/occurrence/search con classKey, facet=speciesKey
    y hasCoordinate=true. El nombre y la familia salen de GET /v1/species/{speciesKey}.
    """
    paises_consulta = list(paises or PAISES)
    sesion = crear_sesion_gbif()

    def aviso(mensaje: str) -> None:
        if on_progreso is not None:
            on_progreso(mensaje)

    def parametros_base() -> list[tuple[str, str]]:
        base = [("limit", "0"), ("hasCoordinate", "true")]
        base.extend(("country", pais) for pais in paises_consulta)
        if year_range:
            base.append(("year", year_range))
        return base

    pendientes: list[tuple[str, int]] = []
    vistos: set[str] = set()
    for nombre_clase in CLASES_A_MOSTRAR:
        aviso(f"GET {GBIF_API}/species/match  name={nombre_clase}  rank=CLASS")
        coincidencia = sesion.get(
            f"{GBIF_API}/species/match",
            params={"name": nombre_clase, "rank": "CLASS", "strict": "true"},
            timeout=20,
        )
        coincidencia.raise_for_status()
        taxon_clase = coincidencia.json()
        clave_clase = taxon_clase.get("usageKey")
        if not clave_clase or str(taxon_clase.get("rank", "")).upper() != "CLASS":
            aviso(f"{nombre_clase}: GBIF no devolvió una clase. Se omite.")
            continue
        aviso(
            f"GET {GBIF_API}/occurrence/search  facet=speciesKey  classKey={clave_clase}  "
            f"{nombre_clase}  limite={limite}"
        )
        busqueda = sesion.get(
            f"{GBIF_API}/occurrence/search",
            params=[
                *parametros_base(),
                ("classKey", str(clave_clase)),
                ("facet", "speciesKey"),
                ("facetLimit", str(limite)),
            ],
            timeout=40,
        )
        busqueda.raise_for_status()
        faceta_especies = busqueda.json().get("facets") or []
        conteos = faceta_especies[0].get("counts", []) if faceta_especies else []
        for item in conteos:
            clave = str(item.get("name") or "")
            if not clave or clave in vistos:
                continue
            vistos.add(clave)
            pendientes.append((clave, int(item.get("count") or 0)))

    especies: list[dict] = []
    for indice, (clave, total) in enumerate(pendientes, start=1):
        aviso(f"GET {GBIF_API}/species/{clave}  ({indice}/{len(pendientes)})")
        ficha = sesion.get(f"{GBIF_API}/species/{clave}", timeout=20)
        ficha.raise_for_status()
        taxon = ficha.json()
        nombre = taxon.get("canonicalName") or taxon.get("scientificName") or clave
        especies.append(
            {
                "nombre_cientifico": nombre,
                "clase": taxon.get("class") or "",
                "familia": taxon.get("family") or "",
                "taxon_key": int(clave),
                "ocurrencias_con_coordenadas": total,
                "endpoint": f"{GBIF_API}/species/{clave}",
            }
        )
    return _alternar_por_clase(especies, CLASES_A_MOSTRAR)


def _alternar_por_clase(especies: list[dict], orden_clases: tuple[str, ...]) -> list[dict]:
    """Una especie de cada clase en cada vuelta, para que las aves no ocupen toda la tabla."""
    grupos: dict[str, list[dict]] = {}
    for especie in especies:
        grupos.setdefault(especie.get("clase") or "", []).append(especie)
    for grupo in grupos.values():
        grupo.sort(key=lambda fila: fila["ocurrencias_con_coordenadas"], reverse=True)
    orden = [clase for clase in orden_clases if grupos.get(clase)]
    orden.extend(clase for clase in grupos if clase not in orden)
    mezcla: list[dict] = []
    while any(grupos[clase] for clase in orden):
        for clase in orden:
            if grupos[clase]:
                mezcla.append(grupos[clase].pop(0))
    return mezcla


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