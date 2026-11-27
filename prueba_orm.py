import sys
from pathlib import Path

ruta_src = Path(__file__).resolve().parent / "src"
if str(ruta_src) not in sys.path:
    sys.path.insert(0, str(ruta_src))

from database import get_session
from repository import BiodiversidadRepository


def probar_capa_orm() -> None:
    with get_session() as session:
        repo = BiodiversidadRepository(session)

        print("=== 1. CONTEO DE TABLAS VÍA ORM ===")
        for tabla, total in repo.resumen_conteo_tablas().items():
            print(f"  - {tabla:<15}: {total:,} registros")

        print("\n=== 2. CONSULTA RELACIONAL (LOBO SILVESTRE EN ESPAÑA) ===")
        ocurrencias = repo.buscar_ocurrencias(
            paises=("ES",),
            solo_lobo_silvestre=True,
            anio_min=2020,
            limite=5,
        )
        for occ in ocurrencias:
            ds = occ.dataset.title if occ.dataset else "N/D"
            org = occ.organizacion.title if occ.organizacion else "N/D"
            print(
                f"[{occ.occurrence_key}] {occ.scientific_name} ({occ.year}) | "
                f"{occ.comunidad_gadm or 'N/D'} ({occ.provincia_gadm or 'N/D'}) | "
                f"Foto: {bool(occ.url_primera_imagen)} | Dataset: {ds[:30]}... | Org: {org[:25]}..."
            )

        print("\n=== 3. AGREGACIÓN TERRITORIAL ORM (TOP 5 COMUNIDADES ES) ===")
        for region, evidencia, total in repo.conteo_por_comunidad("ES")[:5]:
            print(f"  - {region:<28} | {evidencia:<20} | {total:>4}")


if __name__ == "__main__":
    probar_capa_orm()