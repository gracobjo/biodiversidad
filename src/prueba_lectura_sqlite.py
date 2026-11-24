import sys
from pathlib import Path
import pandas as pd

ruta_src = Path(__file__).resolve().parent / "src"
if str(ruta_src) not in sys.path:
    sys.path.append(str(ruta_src))

from consulta_gbif_sqlite import (
    cargar_ocurrencias,
    consultar_campos_raw_json,
    obtener_resumen_general,
    resumen_territorial_por_comunidad,
    top_datasets_publicadores,
)

pd.set_option("display.max_columns", 12)
pd.set_option("display.width", 140)
pd.set_option("display.max_colwidth", 45)


def ejecutar_bateria_pruebas() -> None:
    print("=" * 70)
    print("1. CONTEO GENERAL DE TABLAS EN SQLITE")
    print("=" * 70)
    print(obtener_resumen_general().to_string(index=False))

    print("\n" + "=" * 70)
    print("2. CARGA DE OCURRENCIAS (ES + PT) vs. LOBO SILVESTRE")
    print("=" * 70)
    df_todos = cargar_ocurrencias(paises=("ES", "PT"), solo_lobo_silvestre=False)
    df_lobos = cargar_ocurrencias(paises=("ES", "PT"), solo_lobo_silvestre=True, anio_min=2015)
    print(f"Total registros ES + PT: {len(df_todos)}")
    print(f"Registros lobo silvestre (>= 2015): {len(df_lobos)}")
    cols = ["key", "countryCode", "year", "scientificName", "comunidad_gadm", "publishing_org_title"]
    print(df_lobos[cols].head(5).to_string(index=False))

    print("\n" + "=" * 70)
    print("3. DISTRIBUCIÓN TERRITORIAL EN ESPAÑA")
    print("=" * 70)
    print(resumen_territorial_por_comunidad(pais="ES").head(10).to_string(index=False))

    print("\n" + "=" * 70)
    print("4. TOP 5 DATASETS PUBLICADORES")
    print("=" * 70)
    print(top_datasets_publicadores(limite=5).to_string(index=False))

    print("\n" + "=" * 70)
    print("5. CONSULTA SOBRE CAMPO JSON NATIVO (raw_json)")
    print("=" * 70)
    print(consultar_campos_raw_json(limite=5).to_string(index=False))


if __name__ == "__main__":
    ejecutar_bateria_pruebas()