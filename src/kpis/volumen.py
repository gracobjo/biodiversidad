"""Volumen de registros por país y por tiempo. Mide publicación, no abundancia."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Ocurrencia
from kpis.filtros import FiltroKpi, aplicar, porcentaje


@dataclass(frozen=True)
class Conteo:
    clave: str
    total: int
    porcentaje: float


def _reparto(session: Session, filtro: FiltroKpi | None, expresion, etiqueta: str) -> list[Conteo]:
    consulta = (
        select(expresion.label("clave"), func.count(Ocurrencia.occurrence_key).label("total"))
        .group_by(expresion)
        .order_by(func.count(Ocurrencia.occurrence_key).desc())
    )
    consulta = aplicar(consulta, session, filtro)
    filas = session.execute(consulta).all()
    suma = sum(int(fila.total) for fila in filas)
    return [
        Conteo(str(fila.clave if fila.clave not in (None, "") else etiqueta), int(fila.total), porcentaje(int(fila.total), suma))
        for fila in filas
    ]


def por_pais(session: Session, filtro: FiltroKpi | None = None) -> list[Conteo]:
    """Registros por código de país."""
    return _reparto(session, filtro, Ocurrencia.country_code, "Sin país")


def por_anio(session: Session, filtro: FiltroKpi | None = None) -> list[Conteo]:
    """Registros por año. El año en curso está incompleto."""
    consulta = (
        select(Ocurrencia.year.label("clave"), func.count(Ocurrencia.occurrence_key).label("total"))
        .group_by(Ocurrencia.year)
        .order_by(Ocurrencia.year)
    )
    consulta = aplicar(consulta, session, filtro)
    filas = session.execute(consulta).all()
    suma = sum(int(fila.total) for fila in filas)
    return [
        Conteo("Sin año" if fila.clave is None else str(fila.clave), int(fila.total), porcentaje(int(fila.total), suma))
        for fila in filas
    ]


def por_mes(session: Session, filtro: FiltroKpi | None = None) -> list[Conteo]:
    """Registros por mes, de enero a diciembre. Solo cuenta filas que traen mes."""
    consulta = (
        select(Ocurrencia.month.label("clave"), func.count(Ocurrencia.occurrence_key).label("total"))
        .where(Ocurrencia.month.is_not(None))
        .group_by(Ocurrencia.month)
        .order_by(Ocurrencia.month)
    )
    consulta = aplicar(consulta, session, filtro)
    filas = session.execute(consulta).all()
    suma = sum(int(fila.total) for fila in filas)
    return [Conteo(str(fila.clave), int(fila.total), porcentaje(int(fila.total), suma)) for fila in filas]


def por_pais_y_anio(session: Session, filtro: FiltroKpi | None = None) -> list[tuple[str, int | None, int]]:
    """Serie país-año. Cada fila es (país, año, registros)."""
    consulta = (
        select(
            func.coalesce(Ocurrencia.country_code, "Sin país").label("pais"),
            Ocurrencia.year.label("anio"),
            func.count(Ocurrencia.occurrence_key).label("total"),
        )
        .group_by(Ocurrencia.country_code, Ocurrencia.year)
        .order_by(Ocurrencia.country_code, Ocurrencia.year)
    )
    consulta = aplicar(consulta, session, filtro)
    return [(fila.pais, fila.anio, int(fila.total)) for fila in session.execute(consulta).all()]


def _imprimir(titulo: str, filas: list[Conteo]) -> None:
    print(f"\n{titulo}")
    for fila in filas:
        print(f"  {fila.clave:<12} {fila.total:>6}   {fila.porcentaje:>5} %")


if __name__ == "__main__":
    from database import get_session

    with get_session() as session:
        _imprimir("Registros por país", por_pais(session))
        _imprimir("Registros por año", por_anio(session))
        _imprimir("Registros por mes", por_mes(session))
