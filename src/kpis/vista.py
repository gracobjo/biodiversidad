"""Filas listas para la pestaña Indicadores. No abre sesión ni pinta la ventana."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from kpis.calidad import bandas_incertidumbre, fotos_y_habitat
from kpis.cobertura import cobertura_campos
from kpis.evidencia import individuos_declarados, por_evidencia, por_fase_vital, por_sexo, por_vitalidad
from kpis.filtros import FiltroKpi, porcentaje
from kpis.publicadores import (
    catalogo_datasets,
    pais_publicador_y_pais_avistamiento,
    por_dataset,
    por_organizacion,
    top_registradores,
)
from kpis.taxonomia import lobo_y_perro, por_taxon, sin_taxon_en_catalogo, taxones_sin_ocurrencias
from kpis.territorio import por_comunidad, por_municipio, por_provincia
from kpis.volumen import Conteo, por_anio, por_mes, por_pais, por_pais_y_anio

TEMAS: tuple[tuple[str, str], ...] = (
    ("volumen", "Volumen"),
    ("territorio", "Territorio"),
    ("cobertura", "Cobertura de campos"),
    ("evidencia", "Evidencia y estado"),
    ("taxonomia", "Taxonomía"),
    ("calidad", "Calidad del registro"),
    ("publicadores", "Quién publica"),
)

_MESES = (
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)
_EVIDENCIA = {
    "HUMAN_OBSERVATION": "Observación humana",
    "OBSERVATION": "Observación",
    "MACHINE_OBSERVATION": "Observación automática",
    "PRESERVED_SPECIMEN": "Ejemplar conservado",
    "LIVING_SPECIMEN": "Ejemplar vivo",
    "FOSSIL_SPECIMEN": "Fósil",
    "MATERIAL_SAMPLE": "Muestra de material",
    "MATERIAL_CITATION": "Cita de material",
}
_VITALIDAD = {"ALIVE": "Vivo", "DEAD": "Muerto", "UNDETERMINED": "Sin determinar"}
_SEXO = {"MALE": "Macho", "FEMALE": "Hembra", "HERMAPHRODITE": "Hermafrodita"}
_FASE = {
    "ADULT": "Adulto",
    "JUVENILE": "Juvenil",
    "LARVA": "Larva",
    "PUPA": "Pupa",
    "EGG": "Huevo",
    "INFANT": "Cría",
}


@dataclass(frozen=True)
class NodoIndicador:
    titulo: str
    detalle: str = ""
    registros: str = ""
    porcentaje: str = ""
    hijos: tuple[NodoIndicador, ...] = ()


def filas_indicador(tema: str, session: Session, filtro: FiltroKpi | None = None) -> tuple[list[NodoIndicador], str]:
    """Devuelve las secciones del tema y una línea de estado."""
    filtro = filtro or FiltroKpi()
    constructores = {
        "volumen": _volumen,
        "territorio": _territorio,
        "cobertura": _cobertura,
        "evidencia": _evidencia,
        "taxonomia": _taxonomia,
        "calidad": _calidad,
        "publicadores": _publicadores,
    }
    if tema not in constructores:
        raise ValueError(f"No existe el indicador «{tema}».")
    return constructores[tema](session, filtro)


def _n(valor: int) -> str:
    return f"{valor:,}"


def _p(valor: float) -> str:
    return f"{valor:.1f} %"


def _traducir(mapa: dict[str, str], clave: str) -> str:
    return mapa.get(clave, clave)


def _mes(clave: str) -> str:
    if clave.isdigit() and 1 <= int(clave) <= 12:
        return _MESES[int(clave)]
    return clave


def _conteos(filas: list[Conteo], traducir=None) -> tuple[NodoIndicador, ...]:
    if not filas:
        return (NodoIndicador("Sin registros"),)
    return tuple(
        NodoIndicador(
            traducir(fila.clave) if traducir else fila.clave,
            registros=_n(fila.total),
            porcentaje=_p(fila.porcentaje),
        )
        for fila in filas
    )


def _seccion(titulo: str, hijos: tuple[NodoIndicador, ...]) -> NodoIndicador:
    return NodoIndicador(titulo, hijos=hijos or (NodoIndicador("Sin registros"),))


def _estado(total: int) -> str:
    if total <= 0:
        return "0 registros para este filtro. Un conteo mide publicación, no abundancia."
    return f"{_n(total)} registros en el filtro. Un conteo mide publicación, no abundancia."


def _volumen(session: Session, filtro: FiltroKpi) -> tuple[list[NodoIndicador], str]:
    paises = por_pais(session, filtro)
    serie = por_pais_y_anio(session, filtro)
    suma = sum(total for _, _, total in serie)
    hijos_serie = tuple(
        NodoIndicador(
            f"{pais} {anio if anio is not None else 'sin año'}",
            registros=_n(total),
            porcentaje=_p(porcentaje(total, suma)),
        )
        for pais, anio, total in serie
    )
    nodos = [
        _seccion("Por país", _conteos(paises)),
        _seccion("Por año", _conteos(por_anio(session, filtro))),
        _seccion("Por mes (solo registros con mes)", _conteos(por_mes(session, filtro), _mes)),
        _seccion("País y año", hijos_serie),
    ]
    return nodos, _estado(sum(fila.total for fila in paises))


def _territorio(session: Session, filtro: FiltroKpi) -> tuple[list[NodoIndicador], str]:
    comunidades = por_comunidad(session, filtro)
    nodos = [
        _seccion("Comunidad", _conteos(comunidades)),
        _seccion("Provincia", _conteos(por_provincia(session, filtro))),
        _seccion("Municipio (30 con más registros)", _conteos(por_municipio(session, filtro))),
    ]
    return nodos, _estado(sum(fila.total for fila in comunidades))


def _cobertura(session: Session, filtro: FiltroKpi) -> tuple[list[NodoIndicador], str]:
    campos = cobertura_campos(session, filtro)
    total = campos[0].total if campos else 0
    hijos = tuple(
        NodoIndicador(campo.campo, detalle=f"{_n(campo.con_valor)} de {_n(campo.total)}", porcentaje=_p(campo.porcentaje))
        for campo in campos
    )
    return [_seccion("Campos con valor", hijos)], _estado(total)


def _evidencia(session: Session, filtro: FiltroKpi) -> tuple[list[NodoIndicador], str]:
    evidencia = por_evidencia(session, filtro)
    individuos = individuos_declarados(session, filtro)
    media = "sin dato" if individuos.media_cuando_hay_dato is None else f"{individuos.media_cuando_hay_dato:.2f}"
    nodos = [
        _seccion("Tipo de evidencia", _conteos(evidencia, lambda clave: _traducir(_EVIDENCIA, clave))),
        _seccion("Vitalidad", _conteos(por_vitalidad(session, filtro), lambda clave: _traducir(_VITALIDAD, clave))),
        _seccion("Sexo", _conteos(por_sexo(session, filtro), lambda clave: _traducir(_SEXO, clave))),
        _seccion("Fase vital", _conteos(por_fase_vital(session, filtro), lambda clave: _traducir(_FASE, clave))),
        _seccion(
            "Individuos declarados",
            (
                NodoIndicador(
                    "Con dato",
                    detalle=f"{_n(individuos.registros_con_dato)} de {_n(individuos.registros_totales)}",
                    porcentaje=_p(individuos.porcentaje_con_dato),
                ),
                NodoIndicador("Suma de individuos declarados", registros=_n(individuos.suma_de_individuos)),
                NodoIndicador("Media cuando hay dato", registros=media),
            ),
        ),
    ]
    return nodos, _estado(sum(fila.total for fila in evidencia))


def _taxonomia(session: Session, filtro: FiltroKpi) -> tuple[list[NodoIndicador], str]:
    reparto = lobo_y_perro(session, filtro)
    fichas = por_taxon(session, filtro)
    suma = sum(ficha.total for ficha in fichas)
    vacias = taxones_sin_ocurrencias(session)
    hijos_fichas = tuple(
        NodoIndicador(
            ficha.nombre,
            detalle="" if ficha.taxon_key is None else str(ficha.taxon_key),
            registros=_n(ficha.total),
            porcentaje=_p(porcentaje(ficha.total, suma)),
        )
        for ficha in fichas
    )
    hijos_vacias = (
        tuple(NodoIndicador(nombre, detalle=str(clave)) for clave, nombre in vacias)
        if vacias
        else (NodoIndicador("Ninguna"),)
    )
    nodos = [
        _seccion(
            "Lobo, perro y resto",
            (
                NodoIndicador(
                    "Lobo silvestre",
                    registros=_n(reparto.lobo_silvestre),
                    porcentaje=_p(porcentaje(reparto.lobo_silvestre, reparto.total)),
                ),
                NodoIndicador(
                    "Perro doméstico",
                    registros=_n(reparto.perro_domestico),
                    porcentaje=_p(reparto.porcentaje_perro()),
                ),
                NodoIndicador(
                    "Otros",
                    registros=_n(reparto.otros),
                    porcentaje=_p(porcentaje(reparto.otros, reparto.total)),
                ),
            ),
        ),
        _seccion("Registros por ficha", hijos_fichas),
        _seccion(
            "Sin taxón en el catálogo",
            (NodoIndicador("Ocurrencias sin ficha", registros=_n(sin_taxon_en_catalogo(session, filtro))),),
        ),
        _seccion("Fichas sin ocurrencias (todo el catálogo)", hijos_vacias),
    ]
    return nodos, _estado(reparto.total)


def _calidad(session: Session, filtro: FiltroKpi) -> tuple[list[NodoIndicador], str]:
    presencia = fotos_y_habitat(session, filtro)
    incertidumbre = bandas_incertidumbre(session, filtro)
    mediana = "sin dato" if incertidumbre.mediana_metros is None else f"{incertidumbre.mediana_metros:g} m"
    bandas = tuple(
        NodoIndicador(banda.banda, registros=_n(banda.total), porcentaje=_p(banda.porcentaje))
        for banda in incertidumbre.bandas
    )
    nodos = [
        _seccion(
            "Fotografía y hábitat",
            (
                NodoIndicador(
                    "Con fotografía",
                    registros=_n(presencia.con_fotografia),
                    porcentaje=_p(presencia.porcentaje_fotografia),
                ),
                NodoIndicador(
                    "Con hábitat",
                    registros=_n(presencia.con_habitat),
                    porcentaje=_p(presencia.porcentaje_habitat),
                ),
            ),
        ),
        _seccion(
            "Incertidumbre de la coordenada",
            (
                NodoIndicador(
                    "Mediana",
                    detalle=mediana,
                    registros=_n(incertidumbre.con_dato),
                    porcentaje=_p(incertidumbre.porcentaje_con_dato),
                ),
                *bandas,
            ),
        ),
    ]
    return nodos, _estado(presencia.total)


def _publicadores(session: Session, filtro: FiltroKpi) -> tuple[list[NodoIndicador], str]:
    total, con_licencia, con_doi, con_tipo = catalogo_datasets(session)
    datasets = por_dataset(session, filtro)
    organizaciones = por_organizacion(session, filtro)
    nodos = [
        _seccion(
            "Catálogo de datasets (toda la base)",
            (
                NodoIndicador("Datasets", registros=_n(total)),
                NodoIndicador("Con licencia", registros=_n(con_licencia)),
                NodoIndicador("Con DOI", registros=_n(con_doi)),
                NodoIndicador("Con tipo", registros=_n(con_tipo)),
            ),
        ),
        _seccion(
            "Registros por dataset",
            tuple(
                NodoIndicador(
                    fila.titulo,
                    detalle=fila.organizacion or "",
                    registros=_n(fila.registros),
                    porcentaje=_p(fila.porcentaje),
                )
                for fila in datasets
            ),
        ),
        _seccion(
            "Registros por organización",
            tuple(
                NodoIndicador(
                    fila.titulo,
                    detalle=fila.pais_institucion or "sin país",
                    registros=_n(fila.registros),
                    porcentaje=_p(fila.porcentaje),
                )
                for fila in organizaciones
            ),
        ),
        _seccion(
            "País de la institución y país del registro",
            tuple(
                NodoIndicador(
                    f"institución {fila.pais_institucion}, registro {fila.pais_avistamiento}",
                    registros=_n(fila.registros),
                )
                for fila in pais_publicador_y_pais_avistamiento(session, filtro)
            ),
        ),
        _seccion(
            "Quien más registra (20 primeros)",
            tuple(
                NodoIndicador(
                    fila.nombre.replace("\n", " "),
                    registros=_n(fila.registros),
                    porcentaje=_p(fila.porcentaje),
                )
                for fila in top_registradores(session, filtro)
            ),
        ),
    ]
    return nodos, _estado(sum(fila.registros for fila in organizaciones))
