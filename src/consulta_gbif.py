from contextlib import contextmanager
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy import bindparam, create_engine, text
from db_config import DB_CONFIG


def crear_engine_gbif() -> Engine:
    """Crea un motor SQLAlchemy seguro para MySQL 8 usando mysql-connector-python."""
    url_conexion = URL.create(
        drivername="mysql+mysqlconnector",
        username=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
    )
    return create_engine(url_conexion, pool_pre_ping=True)


@contextmanager
def obtener_engine():
    """Gestor de contexto que abre y libera el motor automáticamente."""
    engine = crear_engine_gbif()
    try:
        yield engine
    finally:
        engine.dispose()


def obtener_resumen_general() -> pd.DataFrame:
    """Devuelve el conteo total de registros almacenados en las 4 tablas."""
    sql = """
        SELECT 'taxones' AS tabla, COUNT(*) AS total FROM taxones
        UNION ALL
        SELECT 'organizaciones', COUNT(*) FROM organizaciones
        UNION ALL
        SELECT 'datasets', COUNT(*) FROM datasets
        UNION ALL
        SELECT 'ocurrencias', COUNT(*) FROM ocurrencias;
    """
    with obtener_engine() as engine:
        return pd.read_sql(text(sql), engine)


def cargar_ocurrencias(
    paises: tuple[str, ...] | list[str] = ("ES", "PT"),
    solo_lobo_silvestre: bool = False,
    anio_min: int | None = None,
) -> pd.DataFrame:
    """
    Carga ocurrencias enriquecidas con el título del dataset, la organización
    publicadora y los metadatos multimedia extraídos de raw_json.
    Mantiene los nombres de columna Darwin Core del cuaderno.
    """
    filtros = ["o.country_code IN :paises"]
    params: dict = {"paises": list(paises)}

    if solo_lobo_silvestre:
        # Excluye Canis lupus familiaris (perro doméstico)
        filtros.append("o.specific_epithet = 'lupus'")
        filtros.append("(o.infraspecific_epithet IS NULL OR o.infraspecific_epithet <> 'familiaris')")

    if anio_min is not None:
        filtros.append("o.year >= :anio_min")
        params["anio_min"] = anio_min

    where_clause = " AND ".join(filtros)

    sql = f"""
        SELECT
            o.occurrence_key AS `key`,
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
            JSON_UNQUOTE(JSON_EXTRACT(o.raw_json, '$.media[0].identifier')) AS url_imagen,
            COALESCE(JSON_LENGTH(JSON_EXTRACT(o.raw_json, '$.media')), 0) AS num_media,
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

    with obtener_engine() as engine:
        return pd.read_sql(stmt, engine, params=params)


def resumen_territorial_por_comunidad(pais: str = "ES") -> pd.DataFrame:
    """Agrupa ocurrencias por comunidad autónoma / región GADM y tipo de evidencia."""
    sql = """
        SELECT
            COALESCE(comunidad_gadm, state_province, 'Sin asignar') AS region,
            basis_of_record AS tipo_evidencia,
            COUNT(*) AS total_registros,
            MIN(year) AS desde_anio,
            MAX(year) AS hasta_anio
        FROM ocurrencias
        WHERE country_code = :pais
        GROUP BY region, basis_of_record
        ORDER BY total_registros DESC;
    """
    with obtener_engine() as engine:
        return pd.read_sql(text(sql), engine, params={"pais": pais})


def top_datasets_publicadores(limite: int = 10) -> pd.DataFrame:
    """Devuelve los datasets con mayor volumen de registros cargados y su organización."""
    sql = """
        SELECT
            d.title AS dataset,
            org.title AS organizacion,
            org.country AS pais_org,
            d.license AS licencia,
            COUNT(o.occurrence_key) AS registros_en_bd
        FROM ocurrencias o
        JOIN datasets d ON o.dataset_key = d.dataset_key
        LEFT JOIN organizaciones org ON d.organization_key = org.organization_key
        GROUP BY d.dataset_key, d.title, org.title, org.country, d.license
        ORDER BY registros_en_bd DESC
        LIMIT :limite;
    """
    with obtener_engine() as engine:
        return pd.read_sql(text(sql), engine, params={"limite": limite})


def consultar_campos_raw_json(limite: int = 15) -> pd.DataFrame:
    """
    Demuestra cómo consultar atributos almacenados dentro de la columna raw_json
    de MySQL 8 (por ejemplo, multimedia, habitat o comportamiento) sin modificar el esquema.
    """
    sql = """
        SELECT
            occurrence_key,
            country_code,
            year,
            scientific_name,
            JSON_UNQUOTE(JSON_EXTRACT(raw_json, '$.habitat')) AS habitat_json,
            JSON_UNQUOTE(JSON_EXTRACT(raw_json, '$.eventRemarks')) AS comentarios_evento,
            JSON_LENGTH(JSON_EXTRACT(raw_json, '$.media')) AS num_archivos_media,
            JSON_UNQUOTE(JSON_EXTRACT(raw_json, '$.media[0].identifier')) AS url_primera_foto,
            gbif_url
        FROM ocurrencias
        WHERE JSON_LENGTH(JSON_EXTRACT(raw_json, '$.media')) > 0
           OR JSON_EXTRACT(raw_json, '$.habitat') IS NOT NULL
        LIMIT :limite;
    """
    with obtener_engine() as engine:
        return pd.read_sql(text(sql), engine, params={"limite": limite})