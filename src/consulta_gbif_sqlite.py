from contextlib import contextmanager
from pathlib import Path
import pandas as pd
from sqlalchemy import bindparam, create_engine, event, text
from sqlalchemy.engine import Engine

from db_sqlite_config import RUTA_DB_SQLITE


def crear_engine_sqlite(ruta_db: Path = RUTA_DB_SQLITE) -> Engine:
    """Crea un motor SQLAlchemy para SQLite activando PRAGMA foreign_keys = ON."""
    if not ruta_db.exists():
        raise FileNotFoundError(
            f"No existe la base de datos SQLite en '{ruta_db}'. Ejecuta primero la ingesta."
        )

    engine = create_engine(f"sqlite:///{ruta_db.as_posix()}")

    @event.listens_for(engine, "connect")
    def _activar_fk(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@contextmanager
def obtener_engine_sqlite(ruta_db: Path = RUTA_DB_SQLITE):
    engine = crear_engine_sqlite(ruta_db)
    try:
        yield engine
    finally:
        engine.dispose()


def _clausula_especie(especie: str | None, alias: str = "") -> tuple[str, dict]:
    nombre = (especie or "").strip()
    if not nombre:
        return "1 = 1", {}
    prefijo = f"{alias}." if alias else ""
    sql = (
        f"({prefijo}scientific_name = :especie OR {prefijo}scientific_name LIKE :especie_como "
        f"OR {prefijo}accepted_scientific_name = :especie "
        f"OR {prefijo}accepted_scientific_name LIKE :especie_como)"
    )
    return sql, {"especie": nombre, "especie_como": f"{nombre}%"}


def obtener_resumen_general(especie: str | None = None) -> pd.DataFrame:
    clausula, params = _clausula_especie(especie)
    if not params:
        sql = """
            SELECT 'taxones' AS tabla, COUNT(*) AS total FROM taxones
            UNION ALL
            SELECT 'organizaciones', COUNT(*) FROM organizaciones
            UNION ALL
            SELECT 'datasets', COUNT(*) FROM datasets
            UNION ALL
            SELECT 'ocurrencias', COUNT(*) FROM ocurrencias
        """
        consulta = text(sql)
    else:
        sql = f"""
            SELECT 'taxones' AS tabla, COUNT(*) AS total FROM taxones
            WHERE scientific_name = :especie OR scientific_name LIKE :especie_como
               OR canonical_name = :especie OR canonical_name LIKE :especie_como
            UNION ALL
            SELECT 'organizaciones', COUNT(DISTINCT organization_key) FROM ocurrencias
            WHERE {clausula}
            UNION ALL
            SELECT 'datasets', COUNT(DISTINCT dataset_key) FROM ocurrencias
            WHERE {clausula}
            UNION ALL
            SELECT 'ocurrencias', COUNT(*) FROM ocurrencias
            WHERE {clausula}
        """
        consulta = text(sql)
    with obtener_engine_sqlite() as engine:
        return _marcar_especie(pd.read_sql(consulta, engine, params=params), especie)


def cargar_ocurrencias(
    paises: tuple[str, ...] | list[str] = ("ES", "PT"),
    solo_lobo_silvestre: bool = False,
    anio_min: int | None = None,
    especie: str | None = None,
) -> pd.DataFrame:
    filtros = ["o.country_code IN :paises"]
    params: dict = {"paises": list(paises)}
    clausula, extra = _clausula_especie(especie, "o")
    if extra:
        filtros.append(clausula)
        params.update(extra)

    if solo_lobo_silvestre:
        filtros.append("o.specific_epithet = 'lupus'")
        filtros.append("(o.infraspecific_epithet IS NULL OR o.infraspecific_epithet <> 'familiaris')")

    if anio_min is not None:
        filtros.append("o.year >= :anio_min")
        params["anio_min"] = anio_min

    where_clause = " AND ".join(filtros)

    sql = f"""
        SELECT
            o.occurrence_key AS key,
            o.taxon_key AS taxonKey,
            o.scientific_name AS scientificName,
            o.accepted_scientific_name AS acceptedScientificName,
            o.taxon_rank AS taxonRank,
            o.specific_epithet AS specificEpithet,
            o.infraspecific_epithet AS infraspecificEpithet,
            o.country_code AS countryCode,
            o.state_province AS stateProvince,
            o.comunidad_gadm,
            o.provincia_gadm,
            o.municipio_gadm,
            o.locality,
            o.decimal_latitude AS decimalLatitude,
            o.decimal_longitude AS decimalLongitude,
            o.coordinate_uncertainty_m AS coordinateUncertaintyInMeters,
            o.event_date AS eventDate,
            o.year,
            o.month,
            o.day,
            o.basis_of_record AS basisOfRecord,
            o.occurrence_status AS occurrenceStatus,
            o.vitality,
            o.individual_count AS individualCount,
            o.sex,
            o.life_stage AS lifeStage,
            o.recorded_by AS recordedBy,
            o.identified_by AS identifiedBy,
            o.catalog_number AS catalogNumber,
            o.institution_code AS institutionCode,
            o.license,
            o.gbif_url,
            json_extract(o.raw_json, '$.media[0].identifier') AS url_imagen,
            COALESCE(json_array_length(o.raw_json, '$.media'), 0) AS num_media,
            d.title AS dataset_title,
            d.dataset_type,
            org.title AS publishing_org_title,
            org.country AS org_country
        FROM ocurrencias o
        LEFT JOIN datasets d ON o.dataset_key = d.dataset_key
        LEFT JOIN organizaciones org ON o.organization_key = org.organization_key
        WHERE {where_clause}
        ORDER BY o.year DESC, o.occurrence_key DESC
    """
    stmt = text(sql).bindparams(bindparam("paises", expanding=True))

    with obtener_engine_sqlite() as engine:
        return _marcar_especie(pd.read_sql(stmt, engine, params=params), especie)


def resumen_territorial_por_comunidad(pais: str = "ES", especie: str | None = None) -> pd.DataFrame:
    clausula, extra = _clausula_especie(especie)
    sql = f"""
        SELECT
            COALESCE(comunidad_gadm, state_province, 'Sin asignar') AS region,
            basis_of_record AS tipo_evidencia,
            COUNT(*) AS total_registros,
            MIN(year) AS desde_anio,
            MAX(year) AS hasta_anio
        FROM ocurrencias
        WHERE country_code = :pais AND {clausula}
        GROUP BY region, basis_of_record
        ORDER BY total_registros DESC
    """
    with obtener_engine_sqlite() as engine:
        df = pd.read_sql(text(sql), engine, params={"pais": pais, **extra})
    return _marcar_especie(df, especie)


def top_datasets_publicadores(limite: int = 10, especie: str | None = None) -> pd.DataFrame:
    clausula, extra = _clausula_especie(especie, "o")
    sql = f"""
        SELECT
            d.title AS dataset,
            org.title AS organizacion,
            org.country AS pais_org,
            d.license AS licencia,
            COUNT(o.occurrence_key) AS registros_en_bd
        FROM ocurrencias o
        JOIN datasets d ON o.dataset_key = d.dataset_key
        LEFT JOIN organizaciones org ON d.organization_key = org.organization_key
        WHERE {clausula}
        GROUP BY d.dataset_key, d.title, org.title, org.country, d.license
        ORDER BY registros_en_bd DESC
        LIMIT :limite
    """
    with obtener_engine_sqlite() as engine:
        df = pd.read_sql(text(sql), engine, params={"limite": limite, **extra})
    return _marcar_especie(df, especie)


def consultar_campos_raw_json(limite: int = 15, especie: str | None = None) -> pd.DataFrame:
    clausula, extra = _clausula_especie(especie)
    sql = f"""
        SELECT
            occurrence_key,
            country_code,
            year,
            scientific_name,
            json_extract(raw_json, '$.habitat') AS habitat_json,
            json_extract(raw_json, '$.eventRemarks') AS comentarios_evento,
            COALESCE(json_array_length(raw_json, '$.media'), 0) AS num_archivos_media,
            json_extract(raw_json, '$.media[0].identifier') AS url_primera_foto,
            gbif_url
        FROM ocurrencias
        WHERE ({clausula})
          AND (
            COALESCE(json_array_length(raw_json, '$.media'), 0) > 0
            OR json_extract(raw_json, '$.habitat') IS NOT NULL
          )
        LIMIT :limite
    """
    with obtener_engine_sqlite() as engine:
        df = pd.read_sql(text(sql), engine, params={"limite": limite, **extra})
    return _marcar_especie(df, especie)


def _marcar_especie(df: pd.DataFrame, especie: str | None) -> pd.DataFrame:
    nombre = (especie or "").strip()
    if not nombre:
        return df
    salida = df.copy()
    if "especie" in salida.columns:
        salida = salida.drop(columns=["especie"])
    salida.insert(0, "especie", nombre)
    return salida