"""Lobo, perro y catálogo. Desde la carpeta src:

    ..\\.venv\\Scripts\\python.exe kpi_taxonomia.py
"""

from database import get_session
from kpis.salida import titulo
from kpis.taxonomia import lobo_y_perro, por_taxon, sin_taxon_en_catalogo, taxones_sin_ocurrencias


def main() -> None:
    with get_session() as session:
        reparto = lobo_y_perro(session)
        titulo("Lobo, perro y resto")
        print(f"  Lobo silvestre:   {reparto.lobo_silvestre}")
        print(f"  Perro doméstico:  {reparto.perro_domestico} ({reparto.porcentaje_perro()} %)")
        print(f"  Otros:            {reparto.otros}")
        titulo("Registros por ficha")
        for ficha in por_taxon(session):
            print(f"  {ficha.total:>5}  {ficha.nombre}  ({ficha.taxon_key})")
        titulo("Sin taxón en el catálogo")
        print(f"  {sin_taxon_en_catalogo(session)} ocurrencias")
        titulo("Fichas sin ocurrencias")
        vacias = taxones_sin_ocurrencias(session)
        if vacias:
            for clave, nombre in vacias:
                print(f"  {clave}  {nombre}")
        else:
            print("  Ninguna")


if __name__ == "__main__":
    main()
