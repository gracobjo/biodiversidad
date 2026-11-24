import pandas as pd
from consulta_gbif import (
    cargar_ocurrencias,
    consultar_campos_raw_json,
    obtener_resumen_general,
    resumen_territorial_por_comunidad,
    top_datasets_publicadores,
)

# Configurar salida legible en consola
pd.set_option("display.max_columns", 12)
pd.set_option("display.width", 140)
pd.set_option("display.max_colwidth", 45)


def ejecutar_bateria_pruebas() -> None:
    print("=" * 70)
    print("1. CONTEO GENERAL DE TABLAS EN MYSQL 8")
    print("=" * 70)
    df_conteo = obtener_resumen_general()
    print(df_conteo.to_string(index=False))

    print("\n" + "=" * 70)
    print("2. CARGA DE OCURRENCIAS (ES + PT) vs. FILTRO LOBO SILVESTRE")
    print("=" * 70)
    df_todos = cargar_ocurrencias(paises=("ES", "PT"), solo_lobo_silvestre=False)
    df_lobos = cargar_ocurrencias(paises=("ES", "PT"), solo_lobo_silvestre=True, anio_min=2015)
    print(f"Total registros ES + PT: {len(df_todos)}")
    print(f"Registros lobo silvestre (>= 2015): {len(df_lobos)}")
    print("\nMuestra de 5 registros enriquecidos:")
    cols_muestra = [
        "key",
        "countryCode",
        "year",
        "scientificName",
        "comunidad_gadm",
        "publishing_org_title",
    ]
    print(df_lobos[cols_muestra].head(5).to_string(index=False))

    print("\n" + "=" * 70)
    print("3. DISTRIBUCIÓN TERRITORIAL EN ESPAÑA POR REGIÓN Y EVIDENCIA")
    print("=" * 70)
    df_territorial = resumen_territorial_por_comunidad(pais="ES")
    print(df_territorial.head(10).to_string(index=False))

    print("\n" + "=" * 70)
    print("4. TOP 5 DATASETS PUBLICADORES")
    print("=" * 70)
    df_datasets = top_datasets_publicadores(limite=5)
    print(df_datasets.to_string(index=False))

    print("\n" + "=" * 70)
    print("5. CONSULTA DINÁMICA SOBRE EL CAMPO JSON NATIVO (raw_json)")
    print("=" * 70)
    df_json = consultar_campos_raw_json(limite=5)
    if df_json.empty:
        print("Ningún registro del lote actual contiene multimedia o habitat en raw_json.")
    else:
        print(df_json.to_string(index=False))


if __name__ == "__main__":
    ejecutar_bateria_pruebas()