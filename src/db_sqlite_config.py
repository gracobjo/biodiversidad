from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_DB_SQLITE = RAIZ_PROYECTO / "datos" / "gbif_biodiversidad.sqlite"
RUTA_SCHEMA_SQLITE = RAIZ_PROYECTO / "docs" / "schema_gbif_sqlite.sql"