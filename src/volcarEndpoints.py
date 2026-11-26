import json
import math
import mysql.connector
import requests
import truststore

# El proxy de inspección (Netskope) firma el tráfico con una CA que está en
# el almacén de Windows, no en el paquete certifi que usa requests.
truststore.inject_into_ssl()


def _limpiar_val(val):
    """Convierte NaN o cadenas vacías en None (NULL en MySQL)."""
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    return val


def _extraer_gadm(registro: dict, nivel: str):
    """Extrae el nombre administrativo de la estructura anidada gadm."""
    gadm = registro.get("gadm")
    if isinstance(gadm, dict) and isinstance(gadm.get(nivel), dict):
        return gadm[nivel].get("name")
    return None


def guardar_en_mysql(
    db_config: dict,
    taxon_info: dict,
    registros_crudos: list[dict],
    session: requests.Session | None = None,
    gbif_api: str = "https://api.gbif.org/v1",
):
    """
    Descarga catálogos asociados (organizaciones y datasets) y guarda todo
    de forma idempotente en MySQL 8.
    """
    http = session or requests.Session()
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # ------------------------------------------------------------------
        # 1. INSERTAR / ACTUALIZAR TAXÓN
        # ------------------------------------------------------------------
        taxon_key = taxon_info.get("usageKey") or taxon_info.get("key")
        sql_taxon = """
            INSERT INTO taxones (
                taxon_key, scientific_name, canonical_name, taxon_rank,
                taxonomic_status, kingdom, phylum, class_name, order_name,
                family, genus, species, raw_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                scientific_name = VALUES(scientific_name),
                canonical_name = VALUES(canonical_name),
                taxonomic_status = VALUES(taxonomic_status),
                raw_json = VALUES(raw_json)
        """
        cursor.execute(
            sql_taxon,
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

        # ------------------------------------------------------------------
        # 2. DESCARGAR E INSERTAR ORGANIZACIONES ÚNICAS
        # ------------------------------------------------------------------
        org_keys = {
            r["publishingOrgKey"]
            for r in registros_crudos
            if r.get("publishingOrgKey")
        }
        sql_org = """
            INSERT INTO organizaciones (
                organization_key, title, country, city, latitude, longitude, homepage, raw_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                country = VALUES(country),
                city = VALUES(city),
                raw_json = VALUES(raw_json)
        """
        for ok in org_keys:
            resp = http.get(f"{gbif_api}/organization/{ok}", timeout=20)
            if resp.status_code == 200:
                org = resp.json()
                homepage = org.get("homepage")[0] if org.get("homepage") else None
                cursor.execute(
                    sql_org,
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

        # ------------------------------------------------------------------
        # 3. DESCARGAR E INSERTAR DATASETS ÚNICOS
        # ------------------------------------------------------------------
        dataset_keys = {
            r["datasetKey"] for r in registros_crudos if r.get("datasetKey")
        }
        sql_dataset = """
            INSERT INTO datasets (
                dataset_key, organization_key, title, dataset_type, license, doi, raw_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                license = VALUES(license),
                doi = VALUES(doi),
                raw_json = VALUES(raw_json)
        """
        for dk in dataset_keys:
            resp = http.get(f"{gbif_api}/dataset/{dk}", timeout=20)
            if resp.status_code == 200:
                ds = resp.json()
                pub_org = ds.get("publishingOrganizationKey")
                # Garantizar FK si la org del dataset no estaba en el lote
                if pub_org and pub_org not in org_keys:
                    pub_org = None
                cursor.execute(
                    sql_dataset,
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

        # ------------------------------------------------------------------
        # 4. INSERTAR / ACTUALIZAR OCURRENCIAS EN LOTE
        # ------------------------------------------------------------------
        sql_occ = """
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
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                vitality = VALUES(vitality),
                occurrence_status = VALUES(occurrence_status),
                coordinate_uncertainty_m = VALUES(coordinate_uncertainty_m),
                raw_json = VALUES(raw_json)
        """
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

        cursor.executemany(sql_occ, filas_occ)
        conn.commit()
        print(
            f"Carga completada: 1 taxón, {len(org_keys)} organizaciones, "
            f"{len(dataset_keys)} datasets y {len(filas_occ)} ocurrencias."
        )

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()