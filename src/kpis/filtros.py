"""Filtro común de las consultas de indicadores.

Por defecto no recorta país ni año: cada función mide la base entera.
Para acotar, se pasa un FiltroKpi con los mismos criterios que la ventana.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Sequence

from sqlalchemy.orm import Session

from repository import BiodiversidadRepository


@dataclass(frozen=True)
class FiltroKpi:
    """Recorte opcional. Los campos vacíos no filtran."""

    paises: Sequence[str] | None = None
    anio_min: int | None = None
    anio_max: int | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
    comunidad: str | None = None
    taxon_key: int | None = None
    solo_lobo_silvestre: bool = False


def condiciones(session: Session, filtro: FiltroKpi | None = None) -> list[Any]:
    """Traduce el filtro a cláusulas del ORM, las mismas que usa el repositorio."""
    filtro = filtro or FiltroKpi()
    return BiodiversidadRepository(session)._filtros_ocurrencias(
        paises=filtro.paises,
        solo_lobo_silvestre=filtro.solo_lobo_silvestre,
        anio_min=filtro.anio_min,
        comunidad=filtro.comunidad,
        taxon_key=filtro.taxon_key,
        anio_max=filtro.anio_max,
        fecha_desde=filtro.fecha_desde,
        fecha_hasta=filtro.fecha_hasta,
    )


def aplicar(consulta, session: Session, filtro: FiltroKpi | None = None):
    """Añade el filtro a una consulta de ocurrencias, si hay alguna condición."""
    clausulas = condiciones(session, filtro)
    if clausulas:
        return consulta.where(*clausulas)
    return consulta


def porcentaje(parte: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(100 * parte / total, 1)
