"""Lobo y perro, fichas del catálogo y registros que se quedaron sin taxón."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from models import Ocurrencia, Taxon
from kpis.filtros import FiltroKpi, aplicar, porcentaje


@dataclass(frozen=True)
class LoboYPerro:
    lobo_silvestre: int
    perro_domestico: int
    otros: int

    @property
    def total(self) -> int:
        return self.lobo_silvestre + self.perro_domestico + self.otros

    def porcentaje_perro(self) -> float:
        return porcentaje(self.perro_domestico, self.total)


def lobo_y_perro(session: Session, filtro: FiltroKpi | None = None) -> LoboYPerro:
    """Separa epíteto lupus (sin familiaris) de perro doméstico y del resto."""
    es_perro = or_(
        Ocurrencia.specific_epithet == "familiaris",
        Ocurrencia.infraspecific_epithet == "familiaris",
    )
    es_lobo = and_(
        Ocurrencia.specific_epithet == "lupus",
        or_(
            Ocurrencia.infraspecific_epithet.is_(None),
            Ocurrencia.infraspecific_epithet != "familiaris",
        ),
    )
    perro = session.scalar(aplicar(select(func.count()).select_from(Ocurrencia).where(es_perro), session, filtro)) or 0
    lobo = session.scalar(aplicar(select(func.count()).select_from(Ocurrencia).where(es_lobo), session, filtro)) or 0
    total = session.scalar(aplicar(select(func.count()).select_from(Ocurrencia), session, filtro)) or 0
    return LoboYPerro(lobo, perro, total - lobo - perro)


@dataclass(frozen=True)
class OcurrenciasPorTaxon:
    taxon_key: int | None
    nombre: str
    rango: str | None
    total: int


def por_taxon(session: Session, filtro: FiltroKpi | None = None) -> list[OcurrenciasPorTaxon]:
    """Registros por ficha de taxones. Las filas sin enlace salen con taxon_key vacío."""
    consulta = (
        select(
            Ocurrencia.taxon_key,
            func.coalesce(func.max(Taxon.scientific_name), func.max(Ocurrencia.scientific_name), "Sin nombre").label(
                "nombre"
            ),
            func.max(Taxon.taxon_rank).label("taxon_rank"),
            func.count(Ocurrencia.occurrence_key).label("total"),
        )
        .outerjoin(Taxon, Ocurrencia.taxon_key == Taxon.taxon_key)
        .group_by(Ocurrencia.taxon_key)
        .order_by(func.count(Ocurrencia.occurrence_key).desc())
    )
    consulta = aplicar(consulta, session, filtro)
    return [
        OcurrenciasPorTaxon(fila.taxon_key, fila.nombre, fila.taxon_rank, int(fila.total))
        for fila in session.execute(consulta).all()
    ]


def sin_taxon_en_catalogo(session: Session, filtro: FiltroKpi | None = None) -> int:
    """Ocurrencias cuyo taxon_key no apunta a taxones."""
    return (
        session.scalar(
            aplicar(
                select(func.count()).select_from(Ocurrencia).where(Ocurrencia.taxon_key.is_(None)),
                session,
                filtro,
            )
        )
        or 0
    )


def taxones_sin_ocurrencias(session: Session) -> list[tuple[int, str]]:
    """Fichas del catálogo que no tienen ninguna ocurrencia enlazada."""
    consulta = (
        select(Taxon.taxon_key, Taxon.scientific_name)
        .outerjoin(Ocurrencia, Ocurrencia.taxon_key == Taxon.taxon_key)
        .group_by(Taxon.taxon_key, Taxon.scientific_name)
        .having(func.count(Ocurrencia.occurrence_key) == 0)
        .order_by(Taxon.scientific_name)
    )
    return [(fila.taxon_key, fila.scientific_name) for fila in session.execute(consulta).all()]
