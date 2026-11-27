"""Dónde se han publicado los registros, con la jerarquía GADM."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Ocurrencia
from kpis.filtros import FiltroKpi, aplicar, porcentaje
from kpis.volumen import Conteo


def _por_nivel(session: Session, filtro: FiltroKpi | None, columna, vacio: str, limite: int | None) -> list[Conteo]:
    total = session.scalar(aplicar(select(func.count()).select_from(Ocurrencia), session, filtro)) or 0
    expresion = func.coalesce(columna, vacio)
    consulta = (
        select(expresion.label("clave"), func.count(Ocurrencia.occurrence_key).label("total"))
        .group_by(expresion)
        .order_by(func.count(Ocurrencia.occurrence_key).desc())
    )
    if limite:
        consulta = consulta.limit(limite)
    consulta = aplicar(consulta, session, filtro)
    filas = session.execute(consulta).all()
    return [Conteo(str(fila.clave), int(fila.total), porcentaje(int(fila.total), total)) for fila in filas]


def por_comunidad(session: Session, filtro: FiltroKpi | None = None) -> list[Conteo]:
    """Registros por comunidad o región GADM de nivel 1."""
    return _por_nivel(session, filtro, Ocurrencia.comunidad_gadm, "Sin comunidad", None)


def por_provincia(session: Session, filtro: FiltroKpi | None = None, limite: int | None = None) -> list[Conteo]:
    """Registros por provincia GADM. limite recorta el ranking."""
    return _por_nivel(session, filtro, Ocurrencia.provincia_gadm, "Sin provincia", limite)


def por_municipio(session: Session, filtro: FiltroKpi | None = None, limite: int = 30) -> list[Conteo]:
    """Los municipios con más registros. Por defecto, los 30 primeros."""
    return _por_nivel(session, filtro, Ocurrencia.municipio_gadm, "Sin municipio", limite)
