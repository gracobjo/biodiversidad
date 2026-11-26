"""Exporta el resultado visible de la interfaz a CSV, JSON o un mapa HTML."""

import math
from html import escape
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_SALIDAS = RAIZ / "salidas_gbif_multiespecie"
MAX_PUNTOS_MAPA = 2500


def exportar_csv(df: pd.DataFrame, ruta: Path) -> Path:
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destino, index=False, encoding="utf-8-sig")
    return destino


def exportar_json(df: pd.DataFrame, ruta: Path) -> Path:
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(destino, orient="records", force_ascii=False, indent=2)
    return destino


def exportar_mapa_html(df: pd.DataFrame, ruta: Path) -> tuple[Path, int, bool]:
    """Guarda un mapa Folium. Devuelve la ruta y cuántos puntos ha pintado."""
    if "decimalLatitude" not in df.columns or "decimalLongitude" not in df.columns:
        raise ValueError("Esta tabla no tiene coordenadas. Consulta ocurrencias antes de generar el mapa.")

    import folium
    from folium.plugins import MarkerCluster

    trabajo = df.copy()
    trabajo["decimalLatitude"] = pd.to_numeric(trabajo["decimalLatitude"], errors="coerce")
    trabajo["decimalLongitude"] = pd.to_numeric(trabajo["decimalLongitude"], errors="coerce")
    trabajo = trabajo.dropna(subset=["decimalLatitude", "decimalLongitude"])
    if trabajo.empty:
        raise ValueError("Ninguna fila de la tabla tiene coordenadas válidas.")

    recortado = False
    if len(trabajo) > MAX_PUNTOS_MAPA:
        trabajo = trabajo.head(MAX_PUNTOS_MAPA)
        recortado = True

    centro_lat = float(trabajo["decimalLatitude"].mean())
    centro_lon = float(trabajo["decimalLongitude"].mean())
    mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=6, tiles="OpenStreetMap")
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satélite (Esri)",
        overlay=False,
        control=True,
    ).add_to(mapa)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Street Map",
        name="Callejero (Esri)",
        overlay=False,
        control=True,
    ).add_to(mapa)

    cluster = MarkerCluster(name="Ocurrencias").add_to(mapa)
    for _, fila in trabajo.iterrows():
        url_img = _texto(fila, "url_imagen", "")
        tiene_imagen = isinstance(url_img, str) and url_img.startswith("http")
        bloque_imagen = ""
        if tiene_imagen:
            href = escape(url_img, quote=True)
            bloque_imagen = (
                "<div style='margin:6px 0;'>"
                f"<a href='{href}' target='_blank' rel='noopener noreferrer'>"
                f"<img src='{href}' alt='Foto' "
                "style='width:220px; max-height:150px; object-fit:cover; border-radius:4px; display:block;'>"
                "Ver imagen original</a></div>"
            )
        ficha = _texto(fila, "gbif_url", "")
        enlace_gbif = ""
        if isinstance(ficha, str) and ficha.startswith("http"):
            enlace_gbif = (
                f"<a href='{escape(ficha, quote=True)}' target='_blank' rel='noopener noreferrer'>"
                "Ver ficha en GBIF</a>"
            )
        popup_html = (
            "<div style='font-family: Segoe UI, Arial, sans-serif; font-size: 12px;'>"
            f"<b>{escape(str(_texto(fila, 'scientificName')))}</b><br>"
            f"País: {escape(str(_texto(fila, 'countryCode')))} | Año: {escape(str(_texto(fila, 'year')))}<br>"
            f"Región: {escape(str(_texto(fila, 'comunidad_gadm')))}<br>"
            f"Evidencia: {escape(str(_texto(fila, 'basisOfRecord')))}<br>"
            f"{bloque_imagen}{enlace_gbif}</div>"
        )
        folium.CircleMarker(
            location=[float(fila["decimalLatitude"]), float(fila["decimalLongitude"])],
            radius=6 if tiene_imagen else 5,
            color="#9b2226" if tiene_imagen else "#1b4332",
            fill=True,
            fill_color="#e63946" if tiene_imagen else "#2d6a4f",
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(cluster)

    folium.LayerControl().add_to(mapa)
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    mapa.save(str(destino))
    return destino, len(trabajo), recortado


def _texto(fila: pd.Series, columna: str, defecto: str = "N/D"):
    if columna not in fila.index:
        return defecto
    valor = fila[columna]
    if valor is None:
        return defecto
    if isinstance(valor, float) and math.isnan(valor):
        return defecto
    try:
        if pd.isna(valor):
            return defecto
    except TypeError:
        pass
    texto = str(valor).strip()
    return texto or defecto
