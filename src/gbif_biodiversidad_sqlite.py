import sqlite3
from pathlib import Path

# Rutas resueltas dinámicamente desde src/ hacia la raíz del proyecto y docs/
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_SCHEMA_SQL = RAIZ_PROYECTO / "docs" / "schema_gbif_sqlite.sql"
RUTA_DB_SQLITE = RAIZ_PROYECTO / "gbif_biodiversidad.sqlite"


def inicializar_sqlite(
    ruta_db: Path = RUTA_DB_SQLITE,
    ruta_sql: Path = RUTA_SCHEMA_SQL,
) -> Path:
    """Crea las tablas e índices en SQLite ejecutando docs/schema_gbif_sqlite.sql."""
    if not ruta_sql.exists():
        raise FileNotFoundError(f"No se encuentra el esquema SQL en: {ruta_sql}")

    with sqlite3.connect(str(ruta_db)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(ruta_sql.read_text(encoding="utf-8"))

    print(f"[SQLite] Esquema aplicado correctamente en: {ruta_db}")
    return ruta_db


if __name__ == "__main__":
    inicializar_sqlite()