"""Texto de consola compartido por los lanzadores de src/kpi_*.py."""


def titulo(texto: str) -> None:
    print(f"\n{texto}")


def conteos(filas) -> None:
    ancho = 8
    for fila in filas:
        ancho = max(ancho, len(str(fila.clave)))
    ancho = min(ancho, 42)
    for fila in filas:
        clave = str(fila.clave).replace("\n", " ")
        if len(clave) > ancho:
            clave = clave[: ancho - 3] + "..."
        print(f"  {clave:<{ancho}} {fila.total:>6}   {fila.porcentaje:>5} %")
