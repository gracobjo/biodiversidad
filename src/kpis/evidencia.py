"""Tipo de evidencia, vitalidad, sexo, fase vital e individuos declarados."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Ocurrencia
from kpis.filtros import FiltroKpi, aplicar, porcentaje
from kpis.volumen import Conteo


def por_evidencia(session: Session, filtro: FiltroKpi | None = None) -> list[Conteo]:
    """Reparto de basis_of_record."""
    expresion = func.coalesce(Ocurrencia.basis_of_record, "Sin evidencia")
    consulta = aplicar(
        select(expresion.label("clave"), func.count(Ocurrencia.occurrence_key).label("total"))
        .group_by(expresion)
        .order_by(func.count(Ocurrencia.occurrence_key).desc()),
        session,
        filtro,
    )
    filas = session.execute(consulta).all()
    suma = sum(int(fila.total) for fila in filas)
    return [Conteo(str(fila.clave), int(fila.total), porcentaje(int(fila.total), suma)) for fila in filas]


def _reparto_campo(session: Session, filtro: FiltroKpi | None, columna, vacio: str) -> list[Conteo]:
    expresion = func.coalesce(columna, vacio)
    consulta = aplicar(
        select(expresion.label("clave"), func.count(Ocurrencia.occurrence_key).label("total"))
        .group_by(expresion)
        .order_by(func.count(Ocurrencia.occurrence_key).desc()),
        session,
        filtro,
    )
    filas = session.execute(consulta).all()
    suma = sum(int(fila.total) for fila in filas)
    return [Conteo(str(fila.clave), int(fila.total), porcentaje(int(fila.total), suma)) for fila in filas]


def por_vitalidad(session: Session, filtro: FiltroKpi | None = None) -> list[Conteo]:
    """Vivo, muerto o sin dato. El porcentaje de muertos solo se interpreta entre quienes informan el campo."""
    return _reparto_campo(session, filtro, Ocurrencia.vitality, "Sin dato")


def por_sexo(session: Session, filtro: FiltroKpi | None = None) -> list[Conteo]:
    """Sexo declarado. La mayoría de las filas no trae este campo."""
    return _reparto_campo(session, filtro, Ocurrencia.sex, "Sin dato")


def por_fase_vital(session: Session, filtro: FiltroKpi | None = None) -> list[Conteo]:
    """Fase vital declarada (life_stage)."""
    return _reparto_campo(session, filtro, Ocurrencia.life_stage, "Sin dato")


@dataclass(frozen=True)
class IndividuosDeclarados:
    registros_con_dato: int
    registros_totales: int
    suma_de_individuos: int
    media_cuando_hay_dato: float | None

    @property
    def porcentaje_con_dato(self) -> float:
        return porcentaje(self.registros_con_dato, self.registros_totales)


def individuos_declarados(session: Session, filtro: FiltroKpi | None = None) -> IndividuosDeclarados:
    """Suma y media de individual_count. No es un censo: solo suma lo que el registro declara."""
    total = session.scalar(aplicar(select(func.count()).select_from(Ocurrencia), session, filtro)) or 0
    con_dato = (
        session.scalar(
            aplicar(
                select(func.count()).select_from(Ocurrencia).where(Ocurrencia.individual_count.is_not(None)),
                session,
                filtro,
            )
        )
        or 0
    )
    suma = (
        session.scalar(
            aplicar(select(func.coalesce(func.sum(Ocurrencia.individual_count), 0)), session, filtro)
        )
        or 0
    )
    media = round(float(suma) / con_dato, 2) if con_dato else None
    return IndividuosDeclarados(con_dato, total, int(suma), media)
