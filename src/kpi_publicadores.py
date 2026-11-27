"""Datasets, organizaciones y quien registra. Desde la carpeta src:

    ..\\.venv\\Scripts\\python.exe kpi_publicadores.py
"""

from database import get_session
from kpis.publicadores import (
    catalogo_datasets,
    pais_publicador_y_pais_avistamiento,
    por_dataset,
    por_organizacion,
    top_registradores,
)
from kpis.salida import titulo


def main() -> None:
    with get_session() as session:
        total, con_licencia, con_doi, con_tipo = catalogo_datasets(session)
        titulo("Catálogo de datasets")
        print(f"  {total} datasets, {con_licencia} con licencia, {con_doi} con DOI, {con_tipo} con tipo")
        titulo("Registros por dataset")
        for fila in por_dataset(session):
            print(f"  {fila.registros:>5}  {fila.porcentaje:>5} %  {fila.titulo}")
        titulo("Registros por organización")
        for fila in por_organizacion(session):
            pais = fila.pais_institucion or "sin país"
            print(f"  {fila.registros:>5}  {fila.porcentaje:>5} %  {pais:<4}  {fila.titulo}")
        titulo("País de la institución y país del registro")
        for fila in pais_publicador_y_pais_avistamiento(session):
            print(f"  {fila.registros:>5}  institución {fila.pais_institucion:<16} registro {fila.pais_avistamiento}")
        titulo("Quien más registra (20 primeros)")
        for fila in top_registradores(session):
            print(f"  {fila.registros:>5}  {fila.porcentaje:>5} %  {fila.nombre}")


if __name__ == "__main__":
    main()
