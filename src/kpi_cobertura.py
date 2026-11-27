"""Cobertura de campos. Desde la carpeta src:

    ..\\.venv\\Scripts\\python.exe kpi_cobertura.py
"""

from database import get_session
from kpis.cobertura import cobertura_campos
from kpis.salida import titulo


def main() -> None:
    with get_session() as session:
        titulo("Campos con valor")
        for campo in cobertura_campos(session):
            print(f"  {campo.campo:<32} {campo.con_valor:>5} / {campo.total:<5} {campo.porcentaje:>5} %")


if __name__ == "__main__":
    main()
