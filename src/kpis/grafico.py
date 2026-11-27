"""Gráficos de los indicadores. Un panel por figura, para que la ventana no los aplaste."""

from __future__ import annotations

from matplotlib.figure import Figure
from sqlalchemy.orm import Session

from kpis.calidad import bandas_incertidumbre, fotos_y_habitat
from kpis.cobertura import cobertura_campos
from kpis.evidencia import por_evidencia, por_fase_vital, por_sexo, por_vitalidad
from kpis.filtros import FiltroKpi
from kpis.publicadores import por_dataset, por_organizacion, top_registradores
from kpis.taxonomia import lobo_y_perro, por_taxon
from kpis.territorio import por_comunidad, por_municipio, por_provincia
from kpis.volumen import por_anio, por_mes, por_pais, por_pais_y_anio

_COLOR = "#2f6f4e"
_COLORES = ("#2f6f4e", "#c4a35a", "#4c6a8a", "#8c4a3a")
_MESES = (
    "",
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
)


def figuras_indicador(
    tema: str, session: Session, filtro: FiltroKpi | None = None
) -> list[tuple[str, Figure]]:
    """Un gráfico por panel. El recuento es el mismo que el de la tabla."""
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


def _figura(alto: float = 4.8) -> Figure:
    return Figure(figsize=(8.4, alto), layout="constrained")


def _vacia(figura: Figure, titulo: str) -> Figure:
    eje = figura.add_subplot(1, 1, 1)
    eje.set_title(titulo)
    eje.text(0.5, 0.5, "Sin registros", ha="center", va="center", transform=eje.transAxes)
    eje.set_axis_off()
    return figura


def _barras(
    titulo: str,
    etiquetas: list[str],
    valores: list[float],
    eje_nombre: str,
    horizontal: bool = False,
) -> Figure:
    alto = 4.8
    if horizontal:
        alto = max(3.6, 0.28 * len(etiquetas) + 1.15)
    figura = _figura(alto)
    if not valores or sum(valores) <= 0:
        return _vacia(figura, titulo)
    eje = figura.add_subplot(1, 1, 1)
    eje.set_title(titulo)
    if horizontal:
        eje.barh(etiquetas[::-1], valores[::-1], color=_COLOR, height=0.72)
        eje.set_xlabel(eje_nombre)
        eje.tick_params(axis="y", labelsize=9)
        eje.grid(axis="x", linestyle=":", alpha=0.6)
    else:
        eje.bar(etiquetas, valores, color=_COLOR)
        eje.set_ylabel(eje_nombre)
        eje.tick_params(axis="x", labelrotation=0 if len(etiquetas) <= 6 else 35, labelsize=9)
        eje.grid(axis="y", linestyle=":", alpha=0.6)
    return figura


def _volumen(session: Session, filtro: FiltroKpi) -> list[tuple[str, Figure]]:
    paises = por_pais(session, filtro)
    anios = por_anio(session, filtro)
    meses = {int(fila.clave): fila.total for fila in por_mes(session, filtro) if str(fila.clave).isdigit()}
    serie = por_pais_y_anio(session, filtro)

    figura_mes = _figura(4.4)
    eje_mes = figura_mes.add_subplot(1, 1, 1)
    eje_mes.set_title("Por mes")
    numeros = list(range(1, 13))
    eje_mes.plot(numeros, [meses.get(numero, 0) for numero in numeros], color=_COLOR, marker="o")
    eje_mes.set_xticks(numeros, _MESES[1:])
    eje_mes.set_ylabel("Registros")
    eje_mes.grid(axis="y", linestyle=":", alpha=0.6)

    figura_serie = _figura(4.6)
    paises_serie: list[str] = []
    for pais, _, _ in serie:
        if pais not in paises_serie:
            paises_serie.append(pais)
    anios_serie = sorted({anio for _, anio, _ in serie if anio is not None})
    if not anios_serie:
        _vacia(figura_serie, "País y año")
    else:
        eje_serie = figura_serie.add_subplot(1, 1, 1)
        eje_serie.set_title("País y año")
        ancho = 0.8 / max(len(paises_serie), 1)
        visibles = paises_serie[:4]
        for indice, pais in enumerate(visibles):
            totales = {anio: total for pais_fila, anio, total in serie if pais_fila == pais and anio is not None}
            posiciones = [pos + indice * ancho for pos in range(len(anios_serie))]
            eje_serie.bar(
                posiciones,
                [totales.get(anio, 0) for anio in anios_serie],
                width=ancho,
                label=pais,
                color=_COLORES[indice % len(_COLORES)],
            )
        centros = [pos + ancho * (len(visibles) - 1) / 2 for pos in range(len(anios_serie))]
        eje_serie.set_xticks(centros, [str(anio) for anio in anios_serie], rotation=0 if len(anios_serie) <= 8 else 35)
        eje_serie.set_ylabel("Registros")
        eje_serie.legend(fontsize=9)
        eje_serie.grid(axis="y", linestyle=":", alpha=0.6)

    return [
        ("Por país", _barras("Por país", [fila.clave for fila in paises], [fila.total for fila in paises], "Registros")),
        ("Por año", _barras("Por año", [fila.clave for fila in anios], [fila.total for fila in anios], "Registros")),
        ("Por mes", figura_mes),
        ("País y año", figura_serie),
    ]


def _territorio(session: Session, filtro: FiltroKpi) -> list[tuple[str, Figure]]:
    bloques = (
        ("Comunidad", por_comunidad(session, filtro)[:12]),
        ("Provincia", por_provincia(session, filtro)[:12]),
        ("Municipio", por_municipio(session, filtro)[:12]),
    )
    return [
        (titulo, _barras(titulo, [fila.clave for fila in filas], [fila.total for fila in filas], "Registros", horizontal=True))
        for titulo, filas in bloques
    ]


def _cobertura(session: Session, filtro: FiltroKpi) -> list[tuple[str, Figure]]:
    campos = cobertura_campos(session, filtro)
    return [
        (
            "Campos con valor",
            _barras(
                "Campos con valor",
                [campo.campo for campo in campos],
                [campo.porcentaje for campo in campos],
                "% de registros",
                horizontal=True,
            ),
        )
    ]


def _evidencia(session: Session, filtro: FiltroKpi) -> list[tuple[str, Figure]]:
    bloques = (
        ("Tipo de evidencia", por_evidencia(session, filtro)),
        ("Vitalidad", por_vitalidad(session, filtro)),
        ("Sexo", por_sexo(session, filtro)),
        ("Fase vital", por_fase_vital(session, filtro)),
    )
    return [
        (titulo, _barras(titulo, [fila.clave for fila in filas], [fila.porcentaje for fila in filas], "%", horizontal=True))
        for titulo, filas in bloques
    ]


def _taxonomia(session: Session, filtro: FiltroKpi) -> list[tuple[str, Figure]]:
    reparto = lobo_y_perro(session, filtro)
    fichas = por_taxon(session, filtro)
    return [
        (
            "Lobo, perro y resto",
            _barras(
                "Lobo, perro y resto",
                ["Lobo", "Perro", "Otros"],
                [reparto.lobo_silvestre, reparto.perro_domestico, reparto.otros],
                "Registros",
            ),
        ),
        (
            "Por ficha",
            _barras(
                "Registros por ficha",
                [ficha.nombre for ficha in fichas],
                [ficha.total for ficha in fichas],
                "Registros",
                horizontal=True,
            ),
        ),
    ]


def _calidad(session: Session, filtro: FiltroKpi) -> list[tuple[str, Figure]]:
    presencia = fotos_y_habitat(session, filtro)
    incertidumbre = bandas_incertidumbre(session, filtro)
    return [
        (
            "Fotografía y hábitat",
            _barras(
                "Fotografía y hábitat",
                ["Fotografía", "Hábitat"],
                [presencia.porcentaje_fotografia, presencia.porcentaje_habitat],
                "% de registros",
            ),
        ),
        (
            "Incertidumbre",
            _barras(
                "Incertidumbre de la coordenada",
                [banda.banda for banda in incertidumbre.bandas],
                [banda.porcentaje for banda in incertidumbre.bandas],
                "% de registros",
                horizontal=True,
            ),
        ),
    ]


def _publicadores(session: Session, filtro: FiltroKpi) -> list[tuple[str, Figure]]:
    bloques = (
        ("Datasets", [(fila.titulo, fila.registros) for fila in por_dataset(session, filtro)[:8]]),
        ("Organizaciones", [(fila.titulo, fila.registros) for fila in por_organizacion(session, filtro)[:8]]),
        ("Quién registra", [(fila.nombre, fila.registros) for fila in top_registradores(session, filtro, limite=8)]),
    )
    return [
        (titulo, _barras(titulo, [nombre for nombre, _ in filas], [total for _, total in filas], "Registros", horizontal=True))
        for titulo, filas in bloques
    ]
