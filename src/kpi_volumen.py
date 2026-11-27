"""Volumen de registros. Desde la carpeta src:

    ..\\.venv\\Scripts\\python.exe kpi_volumen.py
"""

from database import get_session
from kpis.salida import conteos, titulo
from kpis.volumen import por_anio, por_mes, por_pais, por_pais_y_anio


def main() -> None:
    with get_session() as session:
        titulo("Registros por país")
        conteos(por_pais(session))
        titulo("Registros por año")
        conteos(por_anio(session))
        titulo("Registros por mes")
        conteos(por_mes(session))
        titulo("País y año")
        for pais, anio, total in por_pais_y_anio(session):
            print(f"  {pais:<6} {anio or 'sin año':<8} {total:>6}")


if __name__ == "__main__":
    main()
