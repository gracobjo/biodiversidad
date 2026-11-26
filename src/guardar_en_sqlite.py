import json
import math
import sqlite3
from pathlib import Path
import requests

from db_sqlite_config import RUTA_DB_SQLITE, RUTA_SCHEMA_SQLITE


def _limpiar_val(val):
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    return val


def _extraer_gadm(registro: dict, nivel: str):
    gadm = registro.get("gadm")
    if isinstance(gadm, dict) and isinstance(gadm.get(nivel), dict):
        return gadm[nivel].get("name")
    return None


def inicializar_bd_sqlite(
    ruta_db: Path = RUTA_DB_SQLITE,
    ruta_sql: Path = RUTA_SCHEMA_SQLITE,
) -> Path:
    """Crea la base de datos y las tablas desde docs/schema_gbif_sqlite.sql."""
    if not ruta_sql.exists():
        raise FileNotFoundError(f"No se encuentra el esquema DDL en: {ruta_sql}")

    ruta_db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(ruta_db)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(ruta_sql.read_text(encoding="utf-8"))

    return ruta_db


def guardar_en_sqlite(
    taxon_info: dict,
    registros_crudos: list[dict],
    ruta_db: Path = RUTA_DB_SQLITE,
    session: requests.Session | None = None,
    gbif_api: str = "https://api.gbif.org/v1",
) -> None:
    """Descarga catálogos del Registry y vuelca ocurrencias de forma idempotente en SQLite."""
    inicializar_bd_sqlite(ruta_db=ruta_db)

    http = session or requests.Session()
    conn = sqlite3.connect(str(ruta_db))
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    try:
        # 1. Taxón
        taxon_key = taxon_info.get("usageKey") or taxon_info.get("key")
        cursor.execute(
            """
            INSERT INTO taxones (
                taxon_key, scientific_name, canonical_name, taxon_rank,
                taxonomic_status, kingdom, phylum, class_name, order_name,
                family, genus, species, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(taxon_key) DO UPDATE SET
                scientific_name = excluded.scientific_name,
                canonical_name = excluded.canonical_name,
                taxonomic_status = excluded.taxonomic_status,
                raw_json = excluded.raw_json,
                updated_at = datetime('now')
            """,
            (
                taxon_key,
                taxon_info.get("scientificName"),
                taxon_info.get("canonicalName"),
                taxon_info.get("rank"),
                taxon_info.get("status"),
                taxon_info.get("kingdom"),
                taxon_info.get("phylum"),
                taxon_info.get("class"),
                taxon_info.get("order"),
                taxon_info.get("family"),
                taxon_info.get("genus"),
                taxon_info.get("species"),
                json.dumps(taxon_info, ensure_ascii=False),
            ),
        )

        # 2. Organizaciones únicas
        org_keys = {r["publishingOrgKey"] for r in registros_crudos if r.get("publishingOrgKey")}
        for ok in org_keys:
            resp = http.get(f"{gbif_api}/organization/{ok}", timeout=20)
            if resp.status_code == 200:
                org = resp.json()
                homepage = org.get("homepage")[0] if org.get("homepage") else None
                cursor.execute(
                    """
                    INSERT INTO organizaciones (
                        organization_key, title, country, city, latitude, longitude, homepage, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(organization_key) DO UPDATE SET
                        title = excluded.title,
                        country = excluded.country,
                        city = excluded.city,
                        raw_json = excluded.raw_json,
                        updated_at = datetime('now')
                    """,
                    (
                        ok,
                        org.get("title", "Sin título"),
                        _limpiar_val(org.get("country")),
                        _limpiar_val(org.get("city")),
                        _limpiar_val(org.get("latitude")),
                        _limpiar_val(org.get("longitude")),
                        _limpiar_val(homepage),
                        json.dumps(org, ensure_ascii=False),
                    ),
                )

        # 3. Datasets únicos
        dataset_keys = {r["datasetKey"] for r in registros_crudos if r.get("datasetKey")}
        for dk in dataset_keys:
            resp = http.get(f"{gbif_api}/dataset/{dk}", timeout=20)
            if resp.status_code == 200:
                ds = resp.json()
                pub_org = ds.get("publishingOrganizationKey")
                if pub_org and pub_org not in org_keys:
                    pub_org = None
                cursor.execute(
                    """
                    INSERT INTO datasets (
                        dataset_key, organization_key, title, dataset_type, license, doi, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(dataset_key) DO UPDATE SET
                        title = excluded.title,
                        license = excluded.license,
                        doi = excluded.doi,
                        raw_json = excluded.raw_json,
                        updated_at = datetime('now')
                    """,
                    (
                        dk,
                        pub_org,
                        ds.get("title", "Sin título"),
                        _limpiar_val(ds.get("type")),
                        _limpiar_val(ds.get("license")),
                        _limpiar_val(ds.get("doi")),
                        json.dumps(ds, ensure_ascii=False),
                    ),
                )

        # 4. Ocurrencias en lote
        filas_occ = []
        for r in registros_crudos:
            occ_key = r.get("key")
            if not occ_key:
                continue
            filas_occ.append(
                (
                    occ_key,
                    taxon_key,
                    _limpiar_val(r.get("datasetKey")),
                    _limpiar_val(r.get("publishingOrgKey")),
                    _limpiar_val(r.get("scientificName")),
                    _limpiar_val(r.get("acceptedScientificName")),
                    _limpiar_val(r.get("taxonRank")),
                    _limpiar_val(r.get("specificEpithet")),
                    _limpiar_val(r.get("infraspecificEpithet")),
                    _limpiar_val(r.get("countryCode")),
                    _limpiar_val(r.get("stateProvince")),
                    _limpiar_val(_extraer_gadm(r, "level1")),
                    _limpiar_val(_extraer_gadm(r, "level2")),
                    _limpiar_val(_extraer_gadm(r, "level3")),
                    _limpiar_val(r.get("locality")),
                    _limpiar_val(r.get("decimalLatitude")),
                    _limpiar_val(r.get("decimalLongitude")),
                    _limpiar_val(r.get("coordinateUncertaintyInMeters")),
                    _limpiar_val(r.get("eventDate")),
                    _limpiar_val(r.get("year")),
                    _limpiar_val(r.get("month")),
                    _limpiar_val(r.get("day")),
                    _limpiar_val(r.get("basisOfRecord")),
                    _limpiar_val(r.get("occurrenceStatus")),
                    _limpiar_val(r.get("vitality")),
                    _limpiar_val(r.get("individualCount")),
                    _limpiar_val(r.get("sex")),
                    _limpiar_val(r.get("lifeStage")),
                    _limpiar_val(r.get("recordedBy")),
                    _limpiar_val(r.get("identifiedBy")),
                    _limpiar_val(r.get("catalogNumber")),
                    _limpiar_val(r.get("institutionCode")),
                    _limpiar_val(r.get("license")),
                    f"https://www.gbif.org/occurrence/{occ_key}",
                    json.dumps(r, ensure_ascii=False),
                )
            )

        cursor.executemany(
            """
            INSERT INTO ocurrencias (
                occurrence_key, taxon_key, dataset_key, organization_key,
                scientific_name, accepted_scientific_name, taxon_rank,
                specific_epithet, infraspecific_epithet,
                country_code, state_province, comunidad_gadm, provincia_gadm, municipio_gadm,
                locality, decimal_latitude, decimal_longitude, coordinate_uncertainty_m,
                event_date, year, month, day,
                basis_of_record, occurrence_status, vitality, individual_count,
                sex, life_stage, recorded_by, identified_by,
                catalog_number, institution_code, license, gbif_url, raw_json
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
            ON CONFLICT(occurrence_key) DO UPDATE SET
                vitality = excluded.vitality,
                occurrence_status = excluded.occurrence_status,
                coordinate_uncertainty_m = excluded.coordinate_uncertainty_m,
                raw_json = excluded.raw_json,
                updated_at = datetime('now')
            """,
            filas_occ,
        )
        conn.commit()
        print(
            f"[SQLite] Carga completada en '{ruta_db}': 1 taxón, "
            f"{len(org_keys)} organizaciones, {len(dataset_keys)} datasets y {len(filas_occ)} ocurrencias."
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()