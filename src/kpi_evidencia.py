"""Evidencia, vitalidad, sexo, fase vital e individuos. Desde la carpeta src:

    ..\\.venv\\Scripts\\python.exe kpi_evidencia.py
"""

from database import get_session
from kpis.evidencia import individuos_declarados, por_evidencia, por_fase_vital, por_sexo, por_vitalidad
from kpis.salida import conteos, titulo


def main() -> None:
    with get_session() as session:
        titulo("Tipo de evidencia")
        conteos(por_evidencia(session))
        titulo("Vitalidad")
        conteos(por_vitalidad(session))
        titulo("Sexo")
        conteos(por_sexo(session))
        titulo("Fase vital")
        conteos(por_fase_vital(session))
        individuos = individuos_declarados(session)
        titulo("Individuos declarados")
        print(f"  Con dato: {individuos.registros_con_dato} de {individuos.registros_totales} ({individuos.porcentaje_con_dato} %)")
        print(f"  Suma de individual_count: {individuos.suma_de_individuos}")
        print(f"  Media cuando hay dato: {individuos.media_cuando_hay_dato}")


if __name__ == "__main__":
    main()
