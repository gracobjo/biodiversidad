"""Creación y carga de la base GBIF, en SQLite o en MySQL."""

import unicodedata
from pathlib import Path

import pandas as pd

from gbif_biodiversidad_sqlite import inicializar_sqlite
from ingesta_gbif_sqlite import GBIF_API, descargar_desde_gbif, obtener_taxon

RAIZ = Path(__file__).resolve().parent.parent
RUTA_SCHEMA_MYSQL = RAIZ / "docs" / "schema_gbif.sql"


def crear_base(motor: str, config_mysql: dict | None = None) -> str:
    if motor == "sqlite":
        ruta = inicializar_sqlite()
        return f"Esquema SQLite aplicado en {ruta}"
    if motor == "mysql":
        if not config_mysql:
            raise ValueError("Faltan los datos de conexión a MySQL.")
        _crear_esquema_mysql(config_mysql)
        return (
            f"Esquema MySQL aplicado en {config_mysql['database']} "
            f"({config_mysql['host']}:{config_mysql['port']})."
        )
    raise ValueError(f"Motor no reconocido: {motor}")


def poblar_base(
    motor: str,
    config_mysql: dict | None,
    especie: str,
    paises: list[str],
    year_range: str | None,
    max_registros_por_pais: int,
    has_coordinate: bool,
    on_progreso=None,
) -> str:
    taxon, registros, sesion = descargar_desde_gbif(
        especie=especie,
        paises=paises,
        year_range=year_range,
        max_registros_por_pais=max_registros_por_pais,
        has_coordinate=has_coordinate,
        on_progreso=on_progreso,
    )
    if on_progreso is not None:
        on_progreso(
            "GET /v1/organization/{key} y GET /v1/dataset/{key} "
            "para las claves distintas del lote."
        )
    if motor == "sqlite":
        from guardar_en_sqlite import guardar_en_sqlite

        guardar_en_sqlite(
            taxon_info=taxon,
            registros_crudos=registros,
            session=sesion,
            gbif_api=GBIF_API,
        )
        return f"SQLite cargada con {len(registros)} ocurrencias de {especie}."
    if motor == "mysql":
        if not config_mysql:
            raise ValueError("Faltan los datos de conexión a MySQL.")
        from volcarEndpoints import guardar_en_mysql

        guardar_en_mysql(
            config_mysql,
            taxon_info=taxon,
            registros_crudos=registros,
            session=sesion,
            gbif_api=GBIF_API,
        )
        return f"MySQL cargada con {len(registros)} ocurrencias de {especie}."
    raise ValueError(f"Motor no reconocido: {motor}")


def consultar_taxon(especie: str) -> dict:
    return obtener_taxon(especie)


def tabla_taxon(taxon: dict) -> pd.DataFrame:
    campos = [
        "usageKey",
        "scientificName",
        "canonicalName",
        "rank",
        "status",
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
        "genus",
        "species",
        "confidence",
        "matchType",
    ]
    return pd.DataFrame(
        [{"campo": campo, "valor": taxon.get(campo)} for campo in campos]
    )


def tabla_desde_registros_gbif(registros: list[dict]) -> pd.DataFrame:
    """Aplana el JSON de /v1/occurrence/search a columnas de la interfaz."""
    filas = []
    for registro in registros:
        gadm = registro.get("gadm") if isinstance(registro.get("gadm"), dict) else {}
        media = registro.get("media") if isinstance(registro.get("media"), list) else []
        primera = media[0] if media and isinstance(media[0], dict) else {}
        clave = registro.get("key")
        filas.append(
            {
                "key": clave,
                "scientificName": registro.get("scientificName"),
                "countryCode": registro.get("countryCode"),
                "year": registro.get("year"),
                "stateProvince": registro.get("stateProvince"),
                "comunidad_gadm": _nombre_gadm(gadm, "level1"),
                "provincia_gadm": _nombre_gadm(gadm, "level2"),
                "decimalLatitude": registro.get("decimalLatitude"),
                "decimalLongitude": registro.get("decimalLongitude"),
                "basisOfRecord": registro.get("basisOfRecord"),
                "specificEpithet": registro.get("specificEpithet"),
                "publishingOrgKey": registro.get("publishingOrgKey"),
                "datasetKey": registro.get("datasetKey"),
                "url_imagen": primera.get("identifier"),
                "num_media": len(media),
                "gbif_url": f"https://www.gbif.org/occurrence/{clave}" if clave else None,
            }
        )
    return pd.DataFrame(filas)


def _nombre_gadm(gadm: dict, nivel: str):
    nodo = gadm.get(nivel)
    if isinstance(nodo, dict):
        return nodo.get("name")
    return None


def _crear_esquema_mysql(config: dict) -> None:
    if not RUTA_SCHEMA_MYSQL.exists():
        raise FileNotFoundError(f"No se encuentra el esquema en {RUTA_SCHEMA_MYSQL}")
    import mysql.connector

    sql = RUTA_SCHEMA_MYSQL.read_text(encoding="utf-8")
    conexion = mysql.connector.connect(
        host=config["host"],
        port=int(config["port"]),
        user=config["user"],
        password=config["password"],
    )
    try:
        cursor = conexion.cursor()
        for _ in cursor.execute(sql, multi=True):
            pass
        conexion.commit()
        cursor.close()
    finally:
        conexion.close()


def filtrar_ocurrencias(
    df: pd.DataFrame,
    country_code: str = "",
    year: int | None = None,
    state_province: str = "",
    specific_epithet: str = "",
) -> pd.DataFrame:
    """Acota un listado de ocurrencias. Los textos vacíos no filtran.

    country_code y year coinciden de forma exacta. state_province y
    specific_epithet admiten un fragmento, sin distinguir mayúsculas ni tildes.
    """
    if df is None:
        raise ValueError("No hay ocurrencias cargadas.")
    trabajo = df
    paises = [parte.strip().upper() for parte in country_code.split(",") if parte.strip()]
    if paises:
        columna = _columna_ocurrencia(trabajo, "countryCode", "country_code")
        serie = trabajo[columna].astype("string").str.strip().str.upper()
        trabajo = trabajo[serie.isin(paises)]
    if year is not None:
        if "year" not in trabajo.columns:
            raise ValueError("Esta tabla no tiene la columna year.")
        anios = pd.to_numeric(trabajo["year"], errors="coerce")
        trabajo = trabajo[anios == year]
    provincia = state_province.strip()
    if provincia:
        columna = _columna_ocurrencia(trabajo, "stateProvince", "state_province")
        trabajo = trabajo[_contiene(trabajo[columna], provincia)]
    epiteto = specific_epithet.strip()
    if epiteto:
        columna = _columna_ocurrencia(trabajo, "specificEpithet", "specific_epithet")
        trabajo = trabajo[_contiene(trabajo[columna], epiteto)]
    return trabajo.copy()


def _columna_ocurrencia(df: pd.DataFrame, *nombres: str) -> str:
    for nombre in nombres:
        if nombre in df.columns:
            return nombre
    raise ValueError(f"Esta tabla no tiene la columna {nombres[-1]}.")


def _contiene(serie: pd.Series, fragmento: str) -> pd.Series:
    objetivo = _sin_acentos(fragmento)

    def coincide(valor) -> bool:
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return False
        try:
            if pd.isna(valor):
                return False
        except TypeError:
            pass
        return objetivo in _sin_acentos(str(valor))

    return serie.map(coincide)


def _sin_acentos(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto)
    plano = "".join(caracter for caracter in descompuesto if unicodedata.category(caracter) != "Mn")
    return plano.casefold()
