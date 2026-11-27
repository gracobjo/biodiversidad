r"""Indicadores de la base, agrupados para encontrarlos por tema.

Para ver el resultado en consola, desde la carpeta src:

    ..\.venv\Scripts\python.exe kpi_volumen.py
    ..\.venv\Scripts\python.exe kpi_territorio.py
    ..\.venv\Scripts\python.exe kpi_cobertura.py
    ..\.venv\Scripts\python.exe kpi_evidencia.py
    ..\.venv\Scripts\python.exe kpi_taxonomia.py
    ..\.venv\Scripts\python.exe kpi_calidad.py
    ..\.venv\Scripts\python.exe kpi_publicadores.py

Para usar una consulta dentro de otro programa:
    from kpis import FiltroKpi
    from kpis.territorio import por_comunidad

    with get_session() as session:
        filas = por_comunidad(session, FiltroKpi(paises=("ES",), anio_min=2018, anio_max=2018))

Temas:

- cobertura: qué porcentaje de filas trae cada campo
- volumen: país, año, mes
- territorio: comunidad, provincia, municipio
- evidencia: tipo de registro, vitalidad, sexo, fase vital, individuos
- taxonomia: lobo y perro, fichas y registros sin taxón
- calidad: fotografía, hábitat e incertidumbre de la coordenada
- publicadores: datasets, organizaciones y quien registra
"""

from kpis.filtros import FiltroKpi

__all__ = ["FiltroKpi"]
