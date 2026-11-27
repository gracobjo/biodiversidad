"""Fotografía, hábitat e incertidumbre de la coordenada."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Ocurrencia
from kpis.filtros import FiltroKpi, aplicar, porcentaje


@dataclass(frozen=True)
class PresenciaJson:
    con_fotografia: int
    con_habitat: int
    total: int

    @property
    def porcentaje_fotografia(self) -> float:
        return porcentaje(self.con_fotografia, self.total)

    @property
    def porcentaje_habitat(self) -> float:
        return porcentaje(self.con_habitat, self.total)


def fotos_y_habitat(session: Session, filtro: FiltroKpi | None = None) -> PresenciaJson:
    """Cuántos registros traen al menos una imagen o un hábitat dentro de raw_json."""
    total = session.scalar(aplicar(select(func.count()).select_from(Ocurrencia), session, filtro)) or 0
    con_foto = (
        session.scalar(
            aplicar(
                select(func.count())
                .select_from(Ocurrencia)
                .where(func.json_length(func.json_extract(Ocurrencia.raw_json, "$.media")) > 0),
                session,
                filtro,
            )
        )
        or 0
    )
    con_habitat = (
        session.scalar(
            aplicar(
                select(func.count())
                .select_from(Ocurrencia)
                .where(func.json_extract(Ocurrencia.raw_json, "$.habitat").is_not(None)),
                session,
                filtro,
            )
        )
        or 0
    )
    return PresenciaJson(con_foto, con_habitat, total)


@dataclass(frozen=True)
class BandaIncertidumbre:
    banda: str
    total: int
    porcentaje: float


@dataclass(frozen=True)
class IncertidumbreCoordenada:
    con_dato: int
    total: int
    mediana_metros: float | None
    bandas: list[BandaIncertidumbre]

    @property
    def porcentaje_con_dato(self) -> float:
        return porcentaje(self.con_dato, self.total)


def _mediana(valores: list[float]) -> float | None:
    if not valores:
        return None
    ordenados = sorted(valores)
    medio = len(ordenados) // 2
    if len(ordenados) % 2:
        return float(ordenados[medio])
    return (float(ordenados[medio - 1]) + float(ordenados[medio])) / 2


def bandas_incertidumbre(session: Session, filtro: FiltroKpi | None = None) -> IncertidumbreCoordenada:
    """Reparte la incertidumbre en metros. La mediana solo usa las filas que traen el dato."""
    total = session.scalar(aplicar(select(func.count()).select_from(Ocurrencia), session, filtro)) or 0
    valores = [
        float(valor)
        for valor in session.scalars(
            aplicar(
                select(Ocurrencia.coordinate_uncertainty_m).where(Ocurrencia.coordinate_uncertainty_m.is_not(None)),
                session,
                filtro,
            )
        ).all()
    ]
    cortes = (
        ("Sin dato", None, None),
        ("Hasta 100 m", 0, 100),
        ("De 100 m a 1 km", 100, 1_000),
        ("De 1 km a 10 km", 1_000, 10_000),
        ("Más de 10 km", 10_000, None),
    )
    conteos = []
    for nombre, minimo, maximo in cortes:
        if minimo is None:
            cantidad = total - len(valores)
        elif maximo is None:
            cantidad = sum(1 for valor in valores if valor > minimo)
        elif minimo == 0:
            cantidad = sum(1 for valor in valores if valor <= maximo)
        else:
            cantidad = sum(1 for valor in valores if minimo < valor <= maximo)
        conteos.append(BandaIncertidumbre(nombre, cantidad, porcentaje(cantidad, total)))
    return IncertidumbreCoordenada(len(valores), total, _mediana(valores), conteos)
