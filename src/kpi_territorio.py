"""Territorio GADM. Desde la carpeta src:

    ..\\.venv\\Scripts\\python.exe kpi_territorio.py
"""

from database import get_session
from kpis.salida import conteos, titulo
from kpis.territorio import por_comunidad, por_municipio, por_provincia


def main() -> None:
    with get_session() as session:
        titulo("Comunidad")
        conteos(por_comunidad(session))
        titulo("Provincia")
        conteos(por_provincia(session))
        titulo("Municipio (30 con más registros)")
        conteos(por_municipio(session))


if __name__ == "__main__":
    main()
