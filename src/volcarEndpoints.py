from __future__ import annotations

from typing import Any

import requests

from database import get_session
from repository import BiodiversidadRepository


def guardar_en_mysql(
    db_config: dict[str, Any] | None,
    taxon_info: dict[str, Any],
    registros_crudos: list[dict[str, Any]],
    session: requests.Session | None = None,
    gbif_api: str = "https://api.gbif.org/v1",
) -> dict[str, int]:
    """
    Descarga catálogos asociados del Registry (organizaciones y datasets)
    y persiste taxón, organizaciones, datasets y ocurrencias en MySQL 8
    mediante SQLAlchemy ORM (BiodiversidadRepository).

    Se conserva el parámetro `db_config` por compatibilidad con llamadas previas
    desde cuadernos, aunque la conexión ORM utiliza la configuración de `.env`.
    """
    http = session or requests.Session()

    # 1. Extraer UUIDs únicos de organizaciones y datasets
    org_keys = {
        r["publishingOrgKey"]
        for r in registros_crudos
        if r.get("publishingOrgKey")
    }
    dataset_keys = {
        r["datasetKey"]
        for r in registros_crudos
        if r.get("datasetKey")
    }

    # 2. Consultar Registry una sola vez por UUID único
    orgs_crudas: list[dict[str, Any]] = []
    for ok in org_keys:
        resp = http.get(f"{gbif_api}/organization/{ok}", timeout=20)
        if resp.status_code == 200:
            orgs_crudas.append(resp.json())

    datasets_crudos: list[dict[str, Any]] = []
    for dk in dataset_keys:
        resp = http.get(f"{gbif_api}/dataset/{dk}", timeout=20)
        if resp.status_code == 200:
            ds = resp.json()
            # Evita violación de FK si la org publicadora del dataset no estaba en org_keys
            if ds.get("publishingOrganizationKey") not in org_keys:
                ds["publishingOrganizationKey"] = None
            datasets_crudos.append(ds)

    # 3. Persistencia transaccional idempotente mediante ORM
    with get_session() as db_session:
        repo = BiodiversidadRepository(db_session)
        repo.upsert_taxon(taxon_info)
        repo.upsert_organizaciones(orgs_crudas)
        repo.upsert_datasets(datasets_crudos)
        total_occ = repo.upsert_ocurrencias(registros_crudos)

    resumen = {
        "taxones": 1,
        "organizaciones": len(orgs_crudas),
        "datasets": len(datasets_crudos),
        "ocurrencias": total_occ,
    }
    print(
        f"Carga ORM completada: 1 taxón, {len(orgs_crudas)} organizaciones, "
        f"{len(datasets_crudos)} datasets y {total_occ} ocurrencias."
    )
    return resumen