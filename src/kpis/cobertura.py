"""Qué parte de las ocurrencias trae cada campo que alimenta un indicador."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Ocurrencia
from kpis.filtros import FiltroKpi, aplicar, porcentaje


@dataclass(frozen=True)
class CoberturaCampo:
    campo: str
    con_valor: int
    total: int

    @property
    def porcentaje(self) -> float:
        return porcentaje(self.con_valor, self.total)


def _cuenta(session: Session, filtro: FiltroKpi | None, donde=None) -> int:
    consulta = select(func.count()).select_from(Ocurrencia)
    consulta = aplicar(consulta, session, filtro)
    if donde is not None:
        consulta = consulta.where(donde)
    return session.scalar(consulta) or 0


def cobertura_campos(session: Session, filtro: FiltroKpi | None = None) -> list[CoberturaCampo]:
    """Cobertura de los campos usados por el resto de indicadores."""
    total = _cuenta(session, filtro)
    tiene_foto = func.json_length(func.json_extract(Ocurrencia.raw_json, "$.media")) > 0
    tiene_habitat = func.json_extract(Ocurrencia.raw_json, "$.habitat").is_not(None)
    campos = (
        ("Año", Ocurrencia.year.is_not(None)),
        ("Mes", Ocurrencia.month.is_not(None)),
        ("Día", Ocurrencia.day.is_not(None)),
        ("Coordenadas", Ocurrencia.decimal_latitude.is_not(None)),
        ("Incertidumbre de la coordenada", Ocurrencia.coordinate_uncertainty_m.is_not(None)),
        ("Comunidad", Ocurrencia.comunidad_gadm.is_not(None)),
        ("Provincia", Ocurrencia.provincia_gadm.is_not(None)),
        ("Municipio", Ocurrencia.municipio_gadm.is_not(None)),
        ("Tipo de evidencia", Ocurrencia.basis_of_record.is_not(None)),
        ("Vitalidad", Ocurrencia.vitality.is_not(None)),
        ("Sexo", Ocurrencia.sex.is_not(None)),
        ("Fase vital", Ocurrencia.life_stage.is_not(None)),
        ("Número de individuos", Ocurrencia.individual_count.is_not(None)),
        ("Quién registró", Ocurrencia.recorded_by.is_not(None)),
        ("Licencia", Ocurrencia.license.is_not(None)),
        ("Taxón enlazado", Ocurrencia.taxon_key.is_not(None)),
        ("Fotografía", tiene_foto),
        ("Hábitat", tiene_habitat),
    )
    return [
        CoberturaCampo(nombre, _cuenta(session, filtro, condicion), total) for nombre, condicion in campos
    ]
