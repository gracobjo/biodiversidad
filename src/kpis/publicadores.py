"""Datasets, organizaciones y quién concentra los registros."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Dataset, Ocurrencia, Organizacion
from kpis.filtros import FiltroKpi, aplicar, porcentaje


@dataclass(frozen=True)
class DatasetIndicador:
    titulo: str
    organizacion: str | None
    pais_organizacion: str | None
    licencia: str | None
    doi: str | None
    tipo: str | None
    registros: int
    porcentaje: float


def por_dataset(session: Session, filtro: FiltroKpi | None = None, limite: int | None = None) -> list[DatasetIndicador]:
    """Ocurrencias por dataset, con licencia, DOI y tipo. limite recorta el ranking."""
    consulta = (
        select(
            Dataset.title,
            Organizacion.title,
            Organizacion.country,
            Dataset.license,
            Dataset.doi,
            Dataset.dataset_type,
            func.count(Ocurrencia.occurrence_key).label("total"),
        )
        .join(Dataset, Ocurrencia.dataset_key == Dataset.dataset_key)
        .outerjoin(Organizacion, Dataset.organization_key == Organizacion.organization_key)
        .group_by(
            Dataset.dataset_key,
            Dataset.title,
            Organizacion.title,
            Organizacion.country,
            Dataset.license,
            Dataset.doi,
            Dataset.dataset_type,
        )
        .order_by(func.count(Ocurrencia.occurrence_key).desc())
    )
    if limite:
        consulta = consulta.limit(limite)
    consulta = aplicar(consulta, session, filtro)
    filas = session.execute(consulta).all()
    total = session.scalar(aplicar(select(func.count()).select_from(Ocurrencia), session, filtro)) or 0
    return [
        DatasetIndicador(
            fila[0],
            fila[1],
            fila[2],
            fila[3],
            fila[4],
            fila[5],
            int(fila.total),
            porcentaje(int(fila.total), total),
        )
        for fila in filas
    ]


def catalogo_datasets(session: Session) -> tuple[int, int, int, int]:
    """(datasets, con licencia, con DOI, con tipo). No depende del filtro de ocurrencias."""
    total = session.scalar(select(func.count()).select_from(Dataset)) or 0
    con_licencia = session.scalar(select(func.count()).select_from(Dataset).where(Dataset.license.is_not(None))) or 0
    con_doi = session.scalar(select(func.count()).select_from(Dataset).where(Dataset.doi.is_not(None))) or 0
    con_tipo = session.scalar(select(func.count()).select_from(Dataset).where(Dataset.dataset_type.is_not(None))) or 0
    return total, con_licencia, con_doi, con_tipo


@dataclass(frozen=True)
class OrganizacionIndicador:
    titulo: str
    pais_institucion: str | None
    registros: int
    porcentaje: float


def por_organizacion(session: Session, filtro: FiltroKpi | None = None) -> list[OrganizacionIndicador]:
    """Ocurrencias por institución publicadora. El país es el de la institución, no el del avistamiento."""
    consulta = (
        select(
            func.coalesce(Organizacion.title, "Sin organización").label("titulo"),
            Organizacion.country,
            func.count(Ocurrencia.occurrence_key).label("total"),
        )
        .outerjoin(Organizacion, Ocurrencia.organization_key == Organizacion.organization_key)
        .group_by(Organizacion.organization_key, Organizacion.title, Organizacion.country)
        .order_by(func.count(Ocurrencia.occurrence_key).desc())
    )
    consulta = aplicar(consulta, session, filtro)
    filas = session.execute(consulta).all()
    suma = sum(int(fila.total) for fila in filas)
    return [
        OrganizacionIndicador(fila.titulo, fila.country, int(fila.total), porcentaje(int(fila.total), suma))
        for fila in filas
    ]


@dataclass(frozen=True)
class CrucePais:
    pais_institucion: str
    pais_avistamiento: str
    registros: int


def pais_publicador_y_pais_avistamiento(session: Session, filtro: FiltroKpi | None = None) -> list[CrucePais]:
    """Cruza el país de la organización con el país del registro."""
    consulta = (
        select(
            func.coalesce(Organizacion.country, "Sin país de institución").label("institucion"),
            func.coalesce(Ocurrencia.country_code, "Sin país de registro").label("avistamiento"),
            func.count(Ocurrencia.occurrence_key).label("total"),
        )
        .outerjoin(Organizacion, Ocurrencia.organization_key == Organizacion.organization_key)
        .group_by(Organizacion.country, Ocurrencia.country_code)
        .order_by(func.count(Ocurrencia.occurrence_key).desc())
    )
    consulta = aplicar(consulta, session, filtro)
    return [
        CrucePais(fila.institucion, fila.avistamiento, int(fila.total)) for fila in session.execute(consulta).all()
    ]


@dataclass(frozen=True)
class Registrador:
    nombre: str
    registros: int
    porcentaje: float


def top_registradores(session: Session, filtro: FiltroKpi | None = None, limite: int = 20) -> list[Registrador]:
    """Quien más registros firma. El texto de recorded_by no está normalizado."""
    expresion = func.coalesce(Ocurrencia.recorded_by, "Sin dato")
    consulta = aplicar(
        select(expresion.label("nombre"), func.count(Ocurrencia.occurrence_key).label("total"))
        .group_by(expresion)
        .order_by(func.count(Ocurrencia.occurrence_key).desc())
        .limit(limite),
        session,
        filtro,
    )
    filas = session.execute(consulta).all()
    total = session.scalar(aplicar(select(func.count()).select_from(Ocurrencia), session, filtro)) or 0
    return [Registrador(str(fila.nombre), int(fila.total), porcentaje(int(fila.total), total)) for fila in filas]
