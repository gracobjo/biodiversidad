from typing import Any, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session, defer, joinedload

from models import Dataset, Ocurrencia, Organizacion, Taxon


class BiodiversidadRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # INGESTA IDEMPOTENTE (UPSERT NATIVO MYSQL 8)
    # ------------------------------------------------------------------
    def upsert_taxon(self, taxon_data: dict[str, Any]) -> None:
        stmt = mysql_insert(Taxon).values(
            taxon_key=taxon_data["usageKey"],
            scientific_name=taxon_data.get("scientificName", ""),
            canonical_name=taxon_data.get("canonicalName"),
            taxon_rank=taxon_data.get("rank"),
            taxonomic_status=taxon_data.get("status"),
            kingdom=taxon_data.get("kingdom"),
            phylum=taxon_data.get("phylum"),
            class_name=taxon_data.get("class"),
            order_name=taxon_data.get("order"),
            family=taxon_data.get("family"),
            genus=taxon_data.get("genus"),
            species=taxon_data.get("species"),
            raw_json=taxon_data,
        )
        stmt = stmt.on_duplicate_key_update(
            scientific_name=stmt.inserted.scientific_name,
            canonical_name=stmt.inserted.canonical_name,
            taxonomic_status=stmt.inserted.taxonomic_status,
            raw_json=stmt.inserted.raw_json,
        )
        self.session.execute(stmt)

    def upsert_organizaciones(self, lista_orgs: list[dict[str, Any]]) -> None:
        if not lista_orgs:
            return
        filas = [
            {
                "organization_key": o["key"],
                "title": o.get("title", "Sin título"),
                "country": o.get("country"),
                "city": o.get("city"),
                "latitude": o.get("latitude"),
                "longitude": o.get("longitude"),
                "homepage": (o.get("homepage") or [None])[0] if isinstance(o.get("homepage"), list) else o.get("homepage"),
                "raw_json": o,
            }
            for o in lista_orgs
            if o.get("key")
        ]
        stmt = mysql_insert(Organizacion).values(filas)
        stmt = stmt.on_duplicate_key_update(
            title=stmt.inserted.title,
            country=stmt.inserted.country,
            city=stmt.inserted.city,
            raw_json=stmt.inserted.raw_json,
        )
        self.session.execute(stmt)

    def upsert_datasets(self, lista_datasets: list[dict[str, Any]]) -> None:
        if not lista_datasets:
            return
        filas = [
            {
                "dataset_key": d["key"],
                "organization_key": d.get("publishingOrganizationKey"),
                "title": d.get("title", "Sin título"),
                "dataset_type": d.get("type"),
                "license": d.get("license"),
                "doi": d.get("doi"),
                "raw_json": d,
            }
            for d in lista_datasets
            if d.get("key")
        ]
        stmt = mysql_insert(Dataset).values(filas)
        stmt = stmt.on_duplicate_key_update(
            title=stmt.inserted.title,
            license=stmt.inserted.license,
            doi=stmt.inserted.doi,
            raw_json=stmt.inserted.raw_json,
        )
        self.session.execute(stmt)

    def upsert_ocurrencias(self, registros_crudos: list[dict[str, Any]], tamano_lote: int = 250) -> int:
        if not registros_crudos:
            return 0

        filas = []
        for r in registros_crudos:
            key = r.get("key")
            if not key:
                continue
            gadm = r.get("gadm") or {}
            filas.append(
                {
                    "occurrence_key": key,
                    "taxon_key": r.get("taxonKey") or r.get("acceptedTaxonKey"),
                    "dataset_key": r.get("datasetKey"),
                    "organization_key": r.get("publishingOrgKey"),
                    "scientific_name": r.get("scientificName"),
                    "accepted_scientific_name": r.get("acceptedScientificName"),
                    "taxon_rank": r.get("taxonRank"),
                    "specific_epithet": r.get("specificEpithet"),
                    "infraspecific_epithet": r.get("infraspecificEpithet"),
                    "country_code": r.get("countryCode"),
                    "state_province": r.get("stateProvince"),
                    "comunidad_gadm": (gadm.get("level1") or {}).get("name"),
                    "provincia_gadm": (gadm.get("level2") or {}).get("name"),
                    "municipio_gadm": (gadm.get("level3") or {}).get("name"),
                    "locality": r.get("locality"),
                    "decimal_latitude": r.get("decimalLatitude"),
                    "decimal_longitude": r.get("decimalLongitude"),
                    "coordinate_uncertainty_m": r.get("coordinateUncertaintyInMeters"),
                    "event_date": r.get("eventDate"),
                    "year": r.get("year"),
                    "month": r.get("month"),
                    "day": r.get("day"),
                    "basis_of_record": r.get("basisOfRecord"),
                    "occurrence_status": r.get("occurrenceStatus"),
                    "vitality": r.get("vitality"),
                    "individual_count": r.get("individualCount"),
                    "sex": r.get("sex"),
                    "life_stage": r.get("lifeStage"),
                    "recorded_by": r.get("recordedBy"),
                    "identified_by": r.get("identifiedBy"),
                    "catalog_number": r.get("catalogNumber"),
                    "institution_code": r.get("institutionCode"),
                    "license": r.get("license"),
                    "gbif_url": f"https://www.gbif.org/occurrence/{key}",
                    "raw_json": r,
                }
            )

        self._soltar_claves_foraneas_desconocidas(filas)

        for i in range(0, len(filas), tamano_lote):
            lote = filas[i : i + tamano_lote]
            stmt = mysql_insert(Ocurrencia).values(lote)
            stmt = stmt.on_duplicate_key_update(
                accepted_scientific_name=stmt.inserted.accepted_scientific_name,
                comunidad_gadm=stmt.inserted.comunidad_gadm,
                provincia_gadm=stmt.inserted.provincia_gadm,
                municipio_gadm=stmt.inserted.municipio_gadm,
                decimal_latitude=stmt.inserted.decimal_latitude,
                decimal_longitude=stmt.inserted.decimal_longitude,
                vitality=stmt.inserted.vitality,
                raw_json=stmt.inserted.raw_json,
            )
            self.session.execute(stmt)

        return len(filas)

    def _claves_presentes(self, columna, claves: set) -> set:
        if not claves:
            return set()
        presentes: set = set()
        lista = list(claves)
        for inicio in range(0, len(lista), 500):
            lote = lista[inicio : inicio + 500]
            presentes.update(self.session.scalars(select(columna).where(columna.in_(lote))).all())
        return presentes

    def _soltar_claves_foraneas_desconocidas(self, filas: list[dict[str, Any]]) -> None:
        """
        La base ya puede tener catálogo. Si una ocurrencia cita un taxón, dataset
        u organización que no está cargado, se guarda el registro con esa clave vacía.
        """
        taxones = self._claves_presentes(Taxon.taxon_key, {f["taxon_key"] for f in filas if f["taxon_key"] is not None})
        datasets = self._claves_presentes(
            Dataset.dataset_key, {f["dataset_key"] for f in filas if f["dataset_key"]}
        )
        organizaciones = self._claves_presentes(
            Organizacion.organization_key, {f["organization_key"] for f in filas if f["organization_key"]}
        )

        sin_taxon = sin_dataset = sin_org = 0
        for fila in filas:
            if fila["taxon_key"] is not None and fila["taxon_key"] not in taxones:
                fila["taxon_key"] = None
                sin_taxon += 1
            if fila["dataset_key"] and fila["dataset_key"] not in datasets:
                fila["dataset_key"] = None
                sin_dataset += 1
            if fila["organization_key"] and fila["organization_key"] not in organizaciones:
                fila["organization_key"] = None
                sin_org += 1

        if not (sin_taxon or sin_dataset or sin_org):
            return

        partes = []
        if sin_taxon:
            partes.append(f"{sin_taxon} con un taxon_key que no está en taxones")
        if sin_dataset:
            partes.append(f"{sin_dataset} con un dataset que no está en datasets")
        if sin_org:
            partes.append(f"{sin_org} con una organización que no está en organizaciones")
        print(
            "La base ya contiene datos de catálogo. "
            + ", ".join(partes)
            + ". Esas claves se dejan vacías y la ocurrencia se inserta, o se actualiza si ya existía."
        )

    # ------------------------------------------------------------------
    # CONSULTAS ANALÍTICAS ORM (FASE B OFFLINE)
    # ------------------------------------------------------------------
    def _filtros_ocurrencias(
        self,
        paises: Sequence[str],
        solo_lobo_silvestre: bool,
        anio_min: int | None,
        comunidad: str | None,
        taxon_key: int | None,
    ) -> list[Any]:
        filtros: list[Any] = [Ocurrencia.country_code.in_(list(paises))]
        if taxon_key is not None:
            filtros.append(Ocurrencia.taxon_key == taxon_key)
        if solo_lobo_silvestre:
            filtros.append(Ocurrencia.specific_epithet == "lupus")
            filtros.append(
                or_(
                    Ocurrencia.infraspecific_epithet.is_(None),
                    Ocurrencia.infraspecific_epithet != "familiaris",
                )
            )
        if anio_min is not None:
            filtros.append(Ocurrencia.year >= anio_min)
        if comunidad:
            filtros.append(Ocurrencia.comunidad_gadm == comunidad)
        return filtros

    def contar_ocurrencias(
        self,
        paises: Sequence[str] = ("ES", "PT"),
        solo_lobo_silvestre: bool = True,
        anio_min: int | None = None,
        comunidad: str | None = None,
        taxon_key: int | None = None,
    ) -> int:
        """Cuenta las filas del mismo filtro que buscar_ocurrencias, sin el límite de pantalla."""
        filtros = self._filtros_ocurrencias(paises, solo_lobo_silvestre, anio_min, comunidad, taxon_key)
        return self.session.scalar(select(func.count()).select_from(Ocurrencia).where(*filtros)) or 0

    def buscar_ocurrencias(
        self,
        paises: Sequence[str] = ("ES", "PT"),
        solo_lobo_silvestre: bool = True,
        anio_min: int | None = None,
        comunidad: str | None = None,
        taxon_key: int | None = None,
        limite: int | None = None,
    ) -> Sequence[Ocurrencia]:
        """
        Ordena solo las claves. MySQL falla con el error 1038 si el ORDER BY
        incluye raw_json, porque el buffer de ordenación no cabe con ese JSON.
        """
        filtros = self._filtros_ocurrencias(paises, solo_lobo_silvestre, anio_min, comunidad, taxon_key)
        if comunidad:
            orden = (
                Ocurrencia.provincia_gadm.is_(None),
                Ocurrencia.provincia_gadm.asc(),
                Ocurrencia.year.desc(),
                Ocurrencia.occurrence_key.desc(),
            )
        else:
            orden = (Ocurrencia.year.desc(), Ocurrencia.occurrence_key.desc())

        claves_stmt = select(Ocurrencia.occurrence_key).where(*filtros).order_by(*orden)
        if limite:
            claves_stmt = claves_stmt.limit(limite)

        claves = list(self.session.scalars(claves_stmt).all())
        return self._cargar_por_claves(claves)

    def _cargar_por_claves(self, claves: Sequence[int]) -> list[Ocurrencia]:
        """Carga las entidades ya ordenadas, sin repetir el ORDER BY sobre el JSON."""
        if not claves:
            return []

        ocurrencias: list[Ocurrencia] = []
        for inicio in range(0, len(claves), 500):
            lote = list(claves[inicio : inicio + 500])
            stmt = (
                select(Ocurrencia)
                .options(
                    joinedload(Ocurrencia.taxon).defer(Taxon.raw_json),
                    joinedload(Ocurrencia.dataset).defer(Dataset.raw_json),
                    joinedload(Ocurrencia.organizacion).defer(Organizacion.raw_json),
                )
                .where(Ocurrencia.occurrence_key.in_(lote))
            )
            ocurrencias.extend(self.session.scalars(stmt).unique().all())

        posicion = {clave: indice for indice, clave in enumerate(claves)}
        ocurrencias.sort(key=lambda occ: posicion[occ.occurrence_key])
        return ocurrencias

    def resumen_conteo_tablas(self) -> dict[str, int]:
        return {
            "taxones": self.session.scalar(select(func.count()).select_from(Taxon)) or 0,
            "organizaciones": self.session.scalar(select(func.count()).select_from(Organizacion)) or 0,
            "datasets": self.session.scalar(select(func.count()).select_from(Dataset)) or 0,
            "ocurrencias": self.session.scalar(select(func.count()).select_from(Ocurrencia)) or 0,
        }

    def conteo_por_comunidad(self, pais: str = "ES") -> list[tuple[str, str, int]]:
        stmt = (
            select(
                func.coalesce(Ocurrencia.comunidad_gadm, "Sin especificar").label("region"),
                func.coalesce(Ocurrencia.basis_of_record, "N/D").label("evidencia"),
                func.count(Ocurrencia.occurrence_key).label("total"),
            )
            .where(Ocurrencia.country_code == pais)
            .group_by("region", "evidencia")
            .order_by(func.count(Ocurrencia.occurrence_key).desc())
        )
        return [(r.region, r.evidencia, r.total) for r in self.session.execute(stmt).all()]

    def listar_taxones(self) -> list[tuple[int, str]]:
        stmt = select(Taxon.taxon_key, Taxon.scientific_name).order_by(Taxon.scientific_name)
        return [(r.taxon_key, r.scientific_name) for r in self.session.execute(stmt).all()]

    def listar_comunidades(self, paises: Sequence[str] = ("ES", "PT")) -> list[str]:
        stmt = (
            select(Ocurrencia.comunidad_gadm)
            .where(
                Ocurrencia.country_code.in_(paises),
                Ocurrencia.comunidad_gadm.is_not(None),
                Ocurrencia.comunidad_gadm != "",
            )
            .distinct()
            .order_by(Ocurrencia.comunidad_gadm)
        )
        return list(self.session.scalars(stmt).all())

    def resumen_territorial(self, pais: str = "ES") -> list[tuple[Any, ...]]:
        """Agrupa por región GADM y tipo de evidencia, con el rango de años."""
        region_expr = func.coalesce(
            Ocurrencia.comunidad_gadm, Ocurrencia.state_province, "Sin asignar"
        ).label("region")
        stmt = (
            select(
                region_expr,
                func.coalesce(Ocurrencia.basis_of_record, "N/D").label("tipo_evidencia"),
                func.count(Ocurrencia.occurrence_key).label("total_registros"),
                func.min(Ocurrencia.year).label("desde_anio"),
                func.max(Ocurrencia.year).label("hasta_anio"),
            )
            .where(Ocurrencia.country_code == pais)
            .group_by(region_expr, Ocurrencia.basis_of_record)
            .order_by(func.count(Ocurrencia.occurrence_key).desc())
        )
        return [
            (r.region, r.tipo_evidencia, int(r.total_registros), r.desde_anio, r.hasta_anio)
            for r in self.session.execute(stmt).all()
        ]

    def top_datasets_publicadores(self, limite: int = 10) -> list[tuple[Any, ...]]:
        """Datasets con más ocurrencias y la organización que los publica."""
        stmt = (
            select(
                Dataset.title.label("dataset"),
                Organizacion.title.label("organizacion"),
                Organizacion.country.label("pais_org"),
                Dataset.license.label("licencia"),
                func.count(Ocurrencia.occurrence_key).label("registros_en_bd"),
            )
            .join(Dataset, Ocurrencia.dataset_key == Dataset.dataset_key)
            .outerjoin(Organizacion, Dataset.organization_key == Organizacion.organization_key)
            .group_by(
                Dataset.dataset_key,
                Dataset.title,
                Organizacion.title,
                Organizacion.country,
                Dataset.license,
            )
            .order_by(func.count(Ocurrencia.occurrence_key).desc())
            .limit(limite)
        )
        return [
            (r.dataset, r.organizacion, r.pais_org, r.licencia, int(r.registros_en_bd))
            for r in self.session.execute(stmt).all()
        ]

    def muestras_con_media_o_habitat(self, limite: int = 15) -> Sequence[Ocurrencia]:
        """Ocurrencias cuyo JSON guarda multimedia o hábitat."""
        media_len = func.json_length(func.json_extract(Ocurrencia.raw_json, "$.media"))
        habitat = func.json_extract(Ocurrencia.raw_json, "$.habitat")
        claves_stmt = (
            select(Ocurrencia.occurrence_key)
            .where(or_(media_len > 0, habitat.is_not(None)))
            .order_by(Ocurrencia.year.desc(), Ocurrencia.occurrence_key.desc())
            .limit(limite)
        )
        claves = list(self.session.scalars(claves_stmt).all())
        return self._cargar_por_claves(claves)