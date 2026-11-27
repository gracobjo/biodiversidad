from __future__ import annotations

from typing import Any, Sequence

import pandas as pd

from database import get_session
from models import Ocurrencia
from repository import BiodiversidadRepository


def _numero(valor: Any) -> float | None:
    if valor is None:
        return None
    return float(valor)


def _fila_ocurrencia(occ: Ocurrencia) -> dict[str, Any]:
    """Traduce una entidad ORM a los alias Darwin Core que usan los cuadernos."""
    media: list[Any] = []
    if isinstance(occ.raw_json, dict):
        bruto = occ.raw_json.get("media") or []
        if isinstance(bruto, list):
            media = bruto

    return {
        "key": occ.occurrence_key,
        "taxonKey": occ.taxon_key,
        "scientificName": occ.scientific_name,
        "acceptedScientificName": occ.accepted_scientific_name,
        "taxonRank": occ.taxon_rank,
        "specificEpithet": occ.specific_epithet,
        "infraspecificEpithet": occ.infraspecific_epithet,
        "countryCode": occ.country_code,
        "stateProvince": occ.state_province,
        "comunidad_gadm": occ.comunidad_gadm,
        "provincia_gadm": occ.provincia_gadm,
        "municipio_gadm": occ.municipio_gadm,
        "locality": occ.locality,
        "decimalLatitude": _numero(occ.decimal_latitude),
        "decimalLongitude": _numero(occ.decimal_longitude),
        "coordinateUncertaintyInMeters": _numero(occ.coordinate_uncertainty_m),
        "eventDate": occ.event_date,
        "year": occ.year,
        "month": occ.month,
        "day": occ.day,
        "basisOfRecord": occ.basis_of_record,
        "occurrenceStatus": occ.occurrence_status,
        "vitality": occ.vitality,
        "individualCount": occ.individual_count,
        "sex": occ.sex,
        "lifeStage": occ.life_stage,
        "recordedBy": occ.recorded_by,
        "identifiedBy": occ.identified_by,
        "catalogNumber": occ.catalog_number,
        "institutionCode": occ.institution_code,
        "license": occ.license,
        "gbif_url": occ.gbif_url,
        "dataset_title": occ.dataset.title if occ.dataset else None,
        "dataset_type": occ.dataset.dataset_type if occ.dataset else None,
        "publishing_org_title": occ.organizacion.title if occ.organizacion else None,
        "org_country": occ.organizacion.country if occ.organizacion else None,
        "url_imagen": occ.url_primera_imagen,
        "num_media": len(media),
    }


def obtener_resumen_general() -> pd.DataFrame:
    """Devuelve el conteo total de registros almacenados en las 4 tablas vía ORM."""
    with get_session() as session:
        conteos = BiodiversidadRepository(session).resumen_conteo_tablas()

    return pd.DataFrame([{"tabla": tabla, "total": total} for tabla, total in conteos.items()])


def cargar_ocurrencias(
    paises: Sequence[str] | None = ("ES", "PT"),
    solo_lobo_silvestre: bool = False,
    anio_min: int | None = None,
    taxon_key: int | None = None,
    anio_max: int | None = None,
    fecha_desde=None,
    fecha_hasta=None,
) -> pd.DataFrame:
    """
    Carga ocurrencias con dataset y organización publicadora mediante la sesión ORM.
    Mantiene los nombres de columna Darwin Core de los cuadernos, más url_imagen y num_media.
    paises vacío o None no filtra por país. anio_max cierra el intervalo de años.
    fecha_desde y fecha_hasta son datetime.date y afinan por mes y día.
    """
    with get_session() as session:
        ocurrencias = BiodiversidadRepository(session).buscar_ocurrencias(
            paises=paises,
            solo_lobo_silvestre=solo_lobo_silvestre,
            anio_min=anio_min,
            taxon_key=taxon_key,
            anio_max=anio_max,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        filas = [_fila_ocurrencia(occ) for occ in ocurrencias]

    df = pd.DataFrame(filas)
    for col in ("decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def resumen_territorial_por_comunidad(pais: str = "ES") -> pd.DataFrame:
    """Agrupa ocurrencias por comunidad autónoma / región GADM y tipo de evidencia."""
    with get_session() as session:
        filas = BiodiversidadRepository(session).resumen_territorial(pais=pais)

    return pd.DataFrame(
        filas,
        columns=["region", "tipo_evidencia", "total_registros", "desde_anio", "hasta_anio"],
    )


def top_datasets_publicadores(limite: int = 10) -> pd.DataFrame:
    """Devuelve los datasets con mayor volumen de registros cargados y su organización."""
    with get_session() as session:
        filas = BiodiversidadRepository(session).top_datasets_publicadores(limite=limite)

    return pd.DataFrame(
        filas,
        columns=["dataset", "organizacion", "pais_org", "licencia", "registros_en_bd"],
    )


def consultar_campos_raw_json(limite: int = 15) -> pd.DataFrame:
    """
    Lee hábitat, comentarios y la primera foto desde la entidad ORM
    (propiedades sobre raw_json), sin una conexión SQL suelta.
    """
    with get_session() as session:
        ocurrencias = BiodiversidadRepository(session).muestras_con_media_o_habitat(limite=limite)
        filas = []
        for occ in ocurrencias:
            bruto = occ.raw_json if isinstance(occ.raw_json, dict) else {}
            media = bruto.get("media") or []
            filas.append(
                {
                    "occurrence_key": occ.occurrence_key,
                    "country_code": occ.country_code,
                    "year": occ.year,
                    "scientific_name": occ.scientific_name,
                    "habitat_json": occ.habitat_json,
                    "comentarios_evento": bruto.get("eventRemarks"),
                    "num_archivos_media": len(media) if isinstance(media, list) else None,
                    "url_primera_foto": occ.url_primera_imagen,
                    "gbif_url": occ.gbif_url,
                }
            )

    return pd.DataFrame(filas)
