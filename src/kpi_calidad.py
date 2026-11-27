"""Foto, hábitat e incertidumbre. Desde la carpeta src:

    ..\\.venv\\Scripts\\python.exe kpi_calidad.py
"""

from database import get_session
from kpis.calidad import bandas_incertidumbre, fotos_y_habitat
from kpis.salida import titulo


def main() -> None:
    with get_session() as session:
        presencia = fotos_y_habitat(session)
        titulo("Fotografía y hábitat")
        print(f"  Con fotografía: {presencia.con_fotografia} de {presencia.total} ({presencia.porcentaje_fotografia} %)")
        print(f"  Con hábitat:    {presencia.con_habitat} de {presencia.total} ({presencia.porcentaje_habitat} %)")
        incertidumbre = bandas_incertidumbre(session)
        titulo("Incertidumbre de la coordenada")
        print(f"  Mediana: {incertidumbre.mediana_metros} m  ({incertidumbre.porcentaje_con_dato} % con dato)")
        for banda in incertidumbre.bandas:
            print(f"  {banda.banda:<22} {banda.total:>6}   {banda.porcentaje:>5} %")


if __name__ == "__main__":
    main()
