"""Exporta el resultado visible de la interfaz a CSV, JSON o un mapa HTML."""

import json
import math
from html import escape
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_SALIDAS = RAIZ / "salidas_gbif_multiespecie"
MAX_PUNTOS_MAPA = 2500


def con_especie(df: pd.DataFrame, especie: str) -> pd.DataFrame:
    """Deja la especie en la primera columna para que se vea al abrir el fichero."""
    nombre = especie.strip()
    salida = df.copy()
    if "especie" in salida.columns:
        salida = salida.drop(columns=["especie"])
    salida.insert(0, "especie", nombre)
    return salida


def exportar_csv(df: pd.DataFrame, ruta: Path, especie: str | None = None) -> Path:
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tabla = con_especie(df, especie) if especie else df
    tabla.to_csv(destino, index=False, encoding="utf-8-sig")
    return destino


def exportar_json(df: pd.DataFrame, ruta: Path, especie: str | None = None) -> Path:
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tabla = con_especie(df, especie) if especie else df
    registros = json.loads(tabla.to_json(orient="records", force_ascii=False))
    if especie:
        payload = {"especie": especie.strip(), "registros": registros}
    else:
        payload = registros
    destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def exportar_mapa_html(df: pd.DataFrame, ruta: Path, especie: str | None = None) -> tuple[Path, int, bool]:
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

    nombre_especie = (especie or "").strip()
    cluster = MarkerCluster(name=nombre_especie or "Ocurrencias").add_to(mapa)
    if nombre_especie:
        from branca.element import Element

        mapa.get_root().html.add_child(
            Element(
                "<div style='position:fixed;top:12px;left:54px;z-index:9999;"
                "background:#ffffff;padding:8px 14px;border-radius:8px;"
                "font-family:Segoe UI,Arial,sans-serif;"
                "box-shadow:0 1px 4px rgba(0,0,0,.28);'>"
                f"<div style='font-size:16px;font-weight:600'>{escape(nombre_especie)}</div>"
                "<div style='font-size:12px;color:#333'>Ocurrencias GBIF con coordenadas</div>"
                "</div>"
            )
        )
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
