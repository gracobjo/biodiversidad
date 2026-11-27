from __future__ import annotations

import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from database import get_session
from exportacion_gbif import CARPETA_SALIDAS, exportar_csv, exportar_mapa_html
from models import Ocurrencia
from repository import BiodiversidadRepository

GBIF_API = "https://api.gbif.org/v1"
TAXON_LOBO = 5219173

EVIDENCIA = {
    "HUMAN_OBSERVATION": "Observación humana",
    "OBSERVATION": "Observación",
    "MACHINE_OBSERVATION": "Observación automática",
    "PRESERVED_SPECIMEN": "Ejemplar conservado",
    "LIVING_SPECIMEN": "Ejemplar vivo",
    "FOSSIL_SPECIMEN": "Fósil",
    "MATERIAL_SAMPLE": "Muestra de material",
    "MATERIAL_CITATION": "Cita de material",
}

VITALIDAD = {
    "ALIVE": "Vivo",
    "DEAD": "Muerto",
}


class BiodiversidadApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Biodiversidad GBIF")
        self.geometry("1180x740")
        self.minsize(980, 640)

        self._cola_logs: list[str] = []
        self._cola_lock = threading.Lock()
        self._cancelar = threading.Event()
        self._bd_ok = False
        self._ocurrencias: list[Ocurrencia] = []
        self._total_filtro = 0
        self._mapa_taxones: dict[str, int] = {}
        self._orden_col = "anio"
        self._orden_desc = True

        self._construir_ui()
        self._procesar_cola_logs()
        self.after(200, self._arranque)

    def _construir_ui(self) -> None:
        estilo = ttk.Style(self)
        if "vista" in estilo.theme_names():
            estilo.theme_use("vista")

        barra_top = ttk.Frame(self, padding=(12, 8))
        barra_top.pack(fill="x")
        self.lbl_estado_bd = ttk.Label(barra_top, text="Conectando con MySQL...", font=("Segoe UI", 10, "bold"))
        self.lbl_estado_bd.pack(side="left")
        ttk.Button(barra_top, text="Actualizar conteos", command=self.refrescar_resumen_bd).pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.tab_consultar = ttk.Frame(notebook, padding=10)
        self.tab_descarga = ttk.Frame(notebook, padding=10)
        notebook.add(self.tab_consultar, text="Consultar")
        notebook.add(self.tab_descarga, text="Traer datos de GBIF")
        self._construir_tab_consultar()
        self._construir_tab_descarga()

    def _construir_tab_consultar(self) -> None:
        filtros = ttk.LabelFrame(self.tab_consultar, text="Filtros", padding=10)
        filtros.pack(fill="x", pady=(0, 8))

        ttk.Label(filtros, text="Especie:").grid(row=0, column=0, padx=(0, 4), pady=(0, 6), sticky="w")
        self.var_especie_filtro = tk.StringVar(value="Todas las especies")
        self.cb_especie_filtro = ttk.Combobox(
            filtros, textvariable=self.var_especie_filtro, values=("Todas las especies",), state="readonly", width=32
        )
        self.cb_especie_filtro.grid(row=0, column=1, padx=(0, 12), pady=(0, 6), sticky="w")
        self.cb_especie_filtro.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_filtro_lobo())

        ttk.Label(filtros, text="País:").grid(row=0, column=2, padx=(0, 4), pady=(0, 6), sticky="w")
        self.var_pais = tk.StringVar(value="ES + PT")
        self.cb_pais = ttk.Combobox(
            filtros, textvariable=self.var_pais, values=("ES + PT", "ES", "PT"), state="readonly", width=10
        )
        self.cb_pais.grid(row=0, column=3, padx=(0, 12), pady=(0, 6), sticky="w")
        self.cb_pais.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_lista_comunidades())

        ttk.Label(filtros, text="Desde el año:").grid(row=0, column=4, padx=(0, 4), pady=(0, 6), sticky="w")
        self.var_anio_min = tk.StringVar(value="2020")
        entrada_anio = ttk.Entry(filtros, textvariable=self.var_anio_min, width=8)
        entrada_anio.grid(row=0, column=5, padx=(0, 12), pady=(0, 6), sticky="w")
        entrada_anio.bind("<Return>", lambda _e: self.ejecutar_consulta())

        ttk.Button(filtros, text="Consultar", command=self.ejecutar_consulta).grid(
            row=0, column=6, padx=(0, 6), pady=(0, 6), sticky="ew"
        )

        ttk.Label(filtros, text="Comunidad:").grid(row=1, column=0, padx=(0, 4), sticky="w")
        self.var_comunidad = tk.StringVar(value="Todas las comunidades")
        self.cb_comunidad = ttk.Combobox(
            filtros,
            textvariable=self.var_comunidad,
            values=("Todas las comunidades",),
            state="readonly",
            width=32,
        )
        self.cb_comunidad.grid(row=1, column=1, padx=(0, 12), sticky="w")

        ttk.Label(filtros, text="Máximo en tabla:").grid(row=1, column=2, padx=(0, 4), sticky="w")
        self.var_limite = tk.StringVar(value="200")
        entrada_limite = ttk.Entry(filtros, textvariable=self.var_limite, width=8)
        entrada_limite.grid(row=1, column=3, padx=(0, 12), sticky="w")
        entrada_limite.bind("<Return>", lambda _e: self.ejecutar_consulta())

        ttk.Label(filtros, text="Buscar en la tabla:").grid(row=1, column=4, padx=(0, 4), sticky="w")
        self.var_texto = tk.StringVar()
        self.var_texto.trace_add("write", lambda *_: self._pintar_filas())
        ttk.Entry(filtros, textvariable=self.var_texto, width=18).grid(row=1, column=5, padx=(0, 12), sticky="w")

        ttk.Button(filtros, text="Resumen por comunidad", command=self.mostrar_resumen_territorial).grid(
            row=1, column=6, padx=(0, 6), sticky="ew"
        )

        self.var_solo_lobo = tk.BooleanVar(value=False)
        self.chk_lobo = ttk.Checkbutton(
            filtros,
            text="Excluir perro doméstico (dejar solo lobo)",
            variable=self.var_solo_lobo,
        )
        self.chk_lobo.grid(row=2, column=0, columnspan=5, sticky="w", pady=(8, 0))

        panel = ttk.Panedwindow(self.tab_consultar, orient="horizontal")
        panel.pack(fill="both", expand=True)

        marco_tabla = ttk.Frame(panel)
        columnas = (
            "key",
            "pais",
            "anio",
            "especie",
            "comunidad",
            "provincia",
            "evidencia",
            "foto",
            "dataset",
            "organizacion",
        )
        self.tree = ttk.Treeview(marco_tabla, columns=columnas, show="headings", selectmode="browse")
        encabezados = {
            "key": ("GBIF ID", 90),
            "pais": ("País", 46),
            "anio": ("Año", 52),
            "especie": ("Nombre científico", 170),
            "comunidad": ("Comunidad", 140),
            "provincia": ("Provincia", 120),
            "evidencia": ("Evidencia", 140),
            "foto": ("Foto", 46),
            "dataset": ("Dataset", 180),
            "organizacion": ("Organización", 160),
        }
        for col, (texto, ancho) in encabezados.items():
            self.tree.heading(col, text=texto, command=lambda c=col: self._ordenar_por(c))
            self.tree.column(col, width=ancho, anchor="w")
        scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(marco_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        marco_tabla.rowconfigure(0, weight=1)
        marco_tabla.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar)
        self.tree.bind("<Double-1>", self._al_doble_clic)

        ficha = ttk.LabelFrame(panel, text="Registro seleccionado", padding=10)
        self.lbl_ficha_titulo = ttk.Label(ficha, text="Selecciona una fila.", font=("Segoe UI", 11, "bold"), wraplength=250)
        self.lbl_ficha_titulo.pack(anchor="w")
        self.lbl_ficha_aviso = ttk.Label(ficha, text="", wraplength=250, foreground="#9b2226")
        self.lbl_ficha_aviso.pack(anchor="w", pady=(6, 0))
        self.lbl_ficha_cuerpo = ttk.Label(
            ficha,
            text="Doble clic en una fila abre la ficha en GBIF.",
            wraplength=250,
            justify="left",
        )
        self.lbl_ficha_cuerpo.pack(anchor="w", pady=(8, 0))
        panel.add(marco_tabla, weight=4)
        panel.add(ficha, weight=1)

        barra = ttk.Frame(self.tab_consultar, padding=(0, 8, 0, 0))
        barra.pack(fill="x")
        self.lbl_resultados = ttk.Label(barra, text="Todavía no hay una consulta.")
        self.lbl_resultados.pack(side="left")
        self.btn_foto = ttk.Button(barra, text="Abrir fotografía", command=self.abrir_imagen_seleccionada, state="disabled")
        self.btn_foto.pack(side="right", padx=(6, 0))
        ttk.Button(barra, text="Abrir ficha en GBIF", command=self.abrir_ficha_gbif_seleccionada).pack(side="right", padx=(6, 0))
        ttk.Button(barra, text="Ver mapa", command=self.ver_mapa).pack(side="right", padx=(6, 0))
        ttk.Button(barra, text="Exportar CSV", command=self.exportar_csv_visible).pack(side="right")

    def _construir_tab_descarga(self) -> None:
        params = ttk.LabelFrame(self.tab_descarga, text="Qué descargar de GBIF", padding=10)
        params.pack(fill="x", pady=(0, 8))

        ttk.Label(params, text="Especie:").grid(row=0, column=0, padx=(0, 4), sticky="w")
        self.var_especie_ing = tk.StringVar(value="Canis lupus")
        ttk.Entry(params, textvariable=self.var_especie_ing, width=22).grid(row=0, column=1, padx=(0, 12))

        ttk.Label(params, text="Países:").grid(row=0, column=2, padx=(0, 4), sticky="w")
        self.var_paises_ing = tk.StringVar(value="ES,PT")
        ttk.Entry(params, textvariable=self.var_paises_ing, width=12).grid(row=0, column=3, padx=(0, 12))

        ttk.Label(params, text="Años:").grid(row=0, column=4, padx=(0, 4), sticky="w")
        self.var_anios_ing = tk.StringVar(value="2020,2026")
        ttk.Entry(params, textvariable=self.var_anios_ing, width=12).grid(row=0, column=5, padx=(0, 12))

        ttk.Label(params, text="Máximo por país:").grid(row=0, column=6, padx=(0, 4), sticky="w")
        self.var_max_ing = tk.StringVar(value="300")
        ttk.Entry(params, textvariable=self.var_max_ing, width=8).grid(row=0, column=7, padx=(0, 12))

        self.btn_descargar = ttk.Button(params, text="Descargar de GBIF", command=self.iniciar_descarga)
        self.btn_descargar.grid(row=0, column=8, padx=(0, 6))
        self.btn_cancelar = ttk.Button(params, text="Cancelar", command=self._cancelar.set, state="disabled")
        self.btn_cancelar.grid(row=0, column=9)

        progreso = ttk.Frame(self.tab_descarga)
        progreso.pack(fill="x", pady=(0, 8))
        self.lbl_progreso = ttk.Label(progreso, text="Sin descarga en curso.")
        self.lbl_progreso.pack(anchor="w")
        self.barra_progreso = ttk.Progressbar(progreso, mode="determinate")
        self.barra_progreso.pack(fill="x", pady=(4, 0))

        marco_log = ttk.LabelFrame(self.tab_descarga, text="Detalle de la descarga", padding=8)
        marco_log.pack(fill="both", expand=True)
        self.txt_log = tk.Text(marco_log, wrap="word", font=("Consolas", 9), state="disabled")
        scroll_log = ttk.Scrollbar(marco_log, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scroll_log.set)
        self.txt_log.pack(side="left", fill="both", expand=True)
        scroll_log.pack(side="right", fill="y")

    def _arranque(self) -> None:
        self.refrescar_resumen_bd()
        if self._bd_ok:
            self.ejecutar_consulta()

    def _paises_seleccionados(self) -> tuple[str, ...]:
        seleccion = self.var_pais.get()
        return ("ES", "PT") if seleccion == "ES + PT" else (seleccion,)

    def _especie_permite_filtro_lobo(self) -> bool:
        nombre = self.var_especie_filtro.get()
        if nombre == "Todas las especies":
            return True
        if self._mapa_taxones.get(nombre) == TAXON_LOBO:
            return True
        return nombre.lower().startswith("canis lupus")

    def _actualizar_filtro_lobo(self) -> None:
        if self._especie_permite_filtro_lobo():
            self.chk_lobo.grid()
        else:
            self.chk_lobo.grid_remove()

    def _leer_anio(self) -> int | None:
        texto = self.var_anio_min.get().strip()
        if not texto:
            return None
        if not texto.isdigit() or not (1500 <= int(texto) <= 2100):
            raise ValueError("El año tiene que ser un número entre 1500 y 2100, o quedar vacío para no filtrar.")
        return int(texto)

    def _leer_limite(self) -> int:
        texto = self.var_limite.get().strip()
        if not texto.isdigit() or int(texto) < 1:
            raise ValueError("El máximo de la tabla tiene que ser un número entero mayor que cero.")
        return int(texto)

    def _parametros_consulta(self) -> dict[str, Any]:
        especie = self.var_especie_filtro.get()
        taxon_key = self._mapa_taxones.get(especie)
        solo_lobo = self.var_solo_lobo.get() and self._especie_permite_filtro_lobo()
        if solo_lobo and taxon_key not in (None, TAXON_LOBO):
            solo_lobo = False
        comunidad = self.var_comunidad.get().strip()
        if not comunidad or comunidad == "Todas las comunidades":
            comunidad = None
        return {
            "paises": self._paises_seleccionados(),
            "solo_lobo_silvestre": solo_lobo,
            "anio_min": self._leer_anio(),
            "comunidad": comunidad,
            "taxon_key": taxon_key,
            "limite": self._leer_limite(),
        }

    def _actualizar_lista_comunidades(self, repo_existente: BiodiversidadRepository | None = None) -> None:
        paises = self._paises_seleccionados()
        if repo_existente is not None:
            comunidades = repo_existente.listar_comunidades(paises=paises)
        else:
            with get_session() as session:
                comunidades = BiodiversidadRepository(session).listar_comunidades(paises=paises)
        opciones = ["Todas las comunidades", *comunidades]
        self.cb_comunidad["values"] = opciones
        if self.var_comunidad.get() not in opciones:
            self.var_comunidad.set("Todas las comunidades")

    def refrescar_resumen_bd(self) -> None:
        try:
            with get_session() as session:
                repo = BiodiversidadRepository(session)
                conteos = repo.resumen_conteo_tablas()
                taxones = repo.listar_taxones()
                self._actualizar_lista_comunidades(repo_existente=repo)
            self._mapa_taxones = {nombre: clave for clave, nombre in taxones}
            opciones = ["Todas las especies", *self._mapa_taxones.keys()]
            self.cb_especie_filtro["values"] = opciones
            if self.var_especie_filtro.get() not in opciones:
                self.var_especie_filtro.set("Todas las especies")
            self._actualizar_filtro_lobo()
            self._bd_ok = True
            self.lbl_estado_bd.config(
                text=(
                    f"MySQL conectada · {conteos['ocurrencias']:,} ocurrencias"
                    f" · {conteos['datasets']:,} datasets"
                )
            )
        except Exception:
            self._bd_ok = False
            self.lbl_estado_bd.config(text="Sin conexión con MySQL. Comprueba el servidor y el archivo .env.")

    def ejecutar_consulta(self) -> None:
        try:
            parametros = self._parametros_consulta()
        except ValueError as exc:
            messagebox.showwarning("Revisa el filtro", str(exc))
            return
        if not self._bd_ok:
            self.refrescar_resumen_bd()
            if not self._bd_ok:
                return
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            with get_session() as session:
                repo = BiodiversidadRepository(session)
                self._total_filtro = repo.contar_ocurrencias(
                    paises=parametros["paises"],
                    solo_lobo_silvestre=parametros["solo_lobo_silvestre"],
                    anio_min=parametros["anio_min"],
                    comunidad=parametros["comunidad"],
                    taxon_key=parametros["taxon_key"],
                )
                self._ocurrencias = list(
                    repo.buscar_ocurrencias(
                        paises=parametros["paises"],
                        solo_lobo_silvestre=parametros["solo_lobo_silvestre"],
                        anio_min=parametros["anio_min"],
                        comunidad=parametros["comunidad"],
                        taxon_key=parametros["taxon_key"],
                        limite=parametros["limite"],
                    )
                )
            self._pintar_filas()
        except Exception as exc:
            messagebox.showerror("No se pudo consultar", str(exc))
        finally:
            self.configure(cursor="")

    def _texto_fila(self, occ: Ocurrencia) -> str:
        dataset = occ.dataset.title if occ.dataset else ""
        organizacion = occ.organizacion.title if occ.organizacion else ""
        return " ".join(
            parte
            for parte in (
                occ.scientific_name,
                occ.comunidad_gadm,
                occ.provincia_gadm,
                dataset,
                organizacion,
                str(occ.occurrence_key),
            )
            if parte
        ).casefold()

    def _filas_visibles(self) -> list[Ocurrencia]:
        texto = self.var_texto.get().strip().casefold()
        filas = [occ for occ in self._ocurrencias if not texto or texto in self._texto_fila(occ)]

        def clave(occ: Ocurrencia):
            valores = {
                "key": occ.occurrence_key or 0,
                "pais": occ.country_code or "",
                "anio": occ.year or 0,
                "especie": occ.scientific_name or "",
                "comunidad": occ.comunidad_gadm or "",
                "provincia": occ.provincia_gadm or "",
                "evidencia": occ.basis_of_record or "",
                "foto": 1 if occ.url_primera_imagen else 0,
                "dataset": occ.dataset.title if occ.dataset else "",
                "organizacion": occ.organizacion.title if occ.organizacion else "",
            }
            return valores[self._orden_col]

        filas.sort(key=clave, reverse=self._orden_desc)
        return filas

    def _ordenar_por(self, columna: str) -> None:
        if self._orden_col == columna:
            self._orden_desc = not self._orden_desc
        else:
            self._orden_col = columna
            self._orden_desc = columna in {"key", "anio", "foto"}
        self._pintar_filas()

    def _pintar_filas(self) -> None:
        visibles = self._filas_visibles()
        seleccion = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for occ in visibles:
            self.tree.insert(
                "",
                "end",
                iid=str(occ.occurrence_key),
                values=(
                    occ.occurrence_key,
                    occ.country_code or "",
                    occ.year or "",
                    occ.scientific_name or "",
                    occ.comunidad_gadm or "",
                    occ.provincia_gadm or "",
                    EVIDENCIA.get(occ.basis_of_record or "", occ.basis_of_record or ""),
                    "Sí" if occ.url_primera_imagen else "No",
                    occ.dataset.title if occ.dataset else "",
                    occ.organizacion.title if occ.organizacion else "",
                ),
            )
        if seleccion and self.tree.exists(seleccion[0]):
            self.tree.selection_set(seleccion[0])
            self.tree.see(seleccion[0])
        else:
            self._mostrar_ficha(None)
        self._actualizar_contador(len(visibles))

    def _actualizar_contador(self, visibles: int) -> None:
        cargados = len(self._ocurrencias)
        total = self._total_filtro
        if cargados == 0:
            self.lbl_resultados.config(text=f"0 de {total:,} con estos filtros.")
            return
        if self.var_texto.get().strip() and visibles != cargados:
            texto = f"{visibles:,} en pantalla · {cargados:,} cargados de {total:,} con estos filtros."
        elif cargados < total:
            texto = f"{cargados:,} de {total:,} con estos filtros. Sube el máximo de la tabla para ver más."
        else:
            texto = f"{total:,} registros con estos filtros."
        self.lbl_resultados.config(text=texto)

    def _ocurrencia_seleccionada(self) -> Ocurrencia | None:
        seleccion = self.tree.selection()
        if not seleccion:
            return None
        clave = int(seleccion[0])
        return next((occ for occ in self._ocurrencias if occ.occurrence_key == clave), None)

    def _al_seleccionar(self, _evento=None) -> None:
        occ = self._ocurrencia_seleccionada()
        self._mostrar_ficha(occ)
        if occ and occ.url_primera_imagen:
            self.btn_foto.state(["!disabled"])
        else:
            self.btn_foto.state(["disabled"])

    def _al_doble_clic(self, evento) -> None:
        if self.tree.identify_region(evento.x, evento.y) != "cell":
            return
        self.abrir_ficha_gbif_seleccionada()

    def _mostrar_ficha(self, occ: Ocurrencia | None) -> None:
        if occ is None:
            self.lbl_ficha_titulo.config(text="Selecciona una fila.")
            self.lbl_ficha_aviso.config(text="")
            self.lbl_ficha_cuerpo.config(text="Doble clic en una fila abre la ficha en GBIF.")
            self.btn_foto.state(["disabled"])
            return
        self.lbl_ficha_titulo.config(text=occ.scientific_name or "Sin nombre")
        aviso = ""
        epiteto = (occ.specific_epithet or "").lower()
        infra = (occ.infraspecific_epithet or "").lower()
        if epiteto == "familiaris" or infra == "familiaris":
            aviso = "Perro doméstico (Canis familiaris), no lobo silvestre."
        self.lbl_ficha_aviso.config(text=aviso)
        evidencia = EVIDENCIA.get(occ.basis_of_record or "", occ.basis_of_record or "Sin evidencia")
        vitalidad = VITALIDAD.get(occ.vitality or "", occ.vitality or "")
        lineas = [
            f"{occ.country_code or '—'} · {occ.year or 'año desconocido'}",
            " · ".join(parte for parte in (occ.comunidad_gadm, occ.provincia_gadm) if parte) or "Sin comunidad",
            evidencia + (f" · {vitalidad}" if vitalidad else ""),
            occ.locality or "",
            f"Dataset: {occ.dataset.title}" if occ.dataset else "Dataset no cargado",
            f"Organización: {occ.organizacion.title}" if occ.organizacion else "",
            "Con fotografía" if occ.url_primera_imagen else "Sin fotografía",
        ]
        if occ.habitat_json:
            lineas.append(f"Hábitat: {occ.habitat_json}")
        self.lbl_ficha_cuerpo.config(text="\n".join(linea for linea in lineas if linea))

    def _avisar_sin_seleccion(self) -> Ocurrencia | None:
        occ = self._ocurrencia_seleccionada()
        if occ is None:
            messagebox.showinfo("Selecciona un registro", "Elige una fila de la tabla.")
        return occ

    def abrir_ficha_gbif_seleccionada(self) -> None:
        occ = self._avisar_sin_seleccion()
        if occ is None:
            return
        webbrowser.open(occ.gbif_url or f"https://www.gbif.org/occurrence/{occ.occurrence_key}")

    def abrir_imagen_seleccionada(self) -> None:
        occ = self._avisar_sin_seleccion()
        if occ is None:
            return
        if occ.url_primera_imagen:
            webbrowser.open(occ.url_primera_imagen)
        else:
            messagebox.showinfo("Sin fotografía", "Este registro no tiene fotografía.")

    def _tabla_visible(self) -> pd.DataFrame:
        filas = []
        for occ in self._filas_visibles():
            filas.append(
                {
                    "occurrence_key": occ.occurrence_key,
                    "scientificName": occ.scientific_name,
                    "countryCode": occ.country_code,
                    "year": occ.year,
                    "comunidad_gadm": occ.comunidad_gadm,
                    "provincia_gadm": occ.provincia_gadm,
                    "basisOfRecord": occ.basis_of_record,
                    "vitality": occ.vitality,
                    "decimalLatitude": occ.decimal_latitude,
                    "decimalLongitude": occ.decimal_longitude,
                    "url_imagen": occ.url_primera_imagen,
                    "gbif_url": occ.gbif_url or f"https://www.gbif.org/occurrence/{occ.occurrence_key}",
                    "dataset": occ.dataset.title if occ.dataset else None,
                    "organizacion": occ.organizacion.title if occ.organizacion else None,
                }
            )
        return pd.DataFrame(filas)

    def _especie_exportacion(self) -> str | None:
        nombre = self.var_especie_filtro.get()
        return None if nombre == "Todas las especies" else nombre

    def exportar_csv_visible(self) -> None:
        tabla = self._tabla_visible()
        if tabla.empty:
            messagebox.showinfo("Nada que exportar", "La consulta no tiene filas en pantalla.")
            return
        destino = CARPETA_SALIDAS / "consulta_gbif.csv"
        exportar_csv(tabla, destino, especie=self._especie_exportacion())
        messagebox.showinfo("CSV guardado", f"Se ha guardado {len(tabla):,} filas en\n{destino}")

    def ver_mapa(self) -> None:
        tabla = self._tabla_visible()
        if tabla.empty:
            messagebox.showinfo("Nada que mapear", "La consulta no tiene filas en pantalla.")
            return
        destino = CARPETA_SALIDAS / "mapa_consulta_gbif.html"
        try:
            ruta, puntos, recortado = exportar_mapa_html(tabla, destino, especie=self._especie_exportacion())
        except ValueError as exc:
            messagebox.showinfo("Sin coordenadas", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("No se pudo crear el mapa", str(exc))
            return
        webbrowser.open(Path(ruta).resolve().as_uri())
        if recortado:
            messagebox.showinfo(
                "Mapa abierto",
                f"El mapa muestra los primeros {puntos:,} puntos de la tabla. El HTML está en\n{ruta}",
            )

    def mostrar_resumen_territorial(self) -> None:
        paises = self._paises_seleccionados()
        try:
            with get_session() as session:
                repo = BiodiversidadRepository(session)
                filas = []
                for pais in paises:
                    filas.extend((pais, *fila) for fila in repo.conteo_por_comunidad(pais=pais))
        except Exception as exc:
            messagebox.showerror("No se pudo resumir", str(exc))
            return
        if not filas:
            messagebox.showinfo("Sin datos", "No hay ocurrencias para ese país.")
            return
        ventana = tk.Toplevel(self)
        ventana.title("Resumen por comunidad")
        ventana.geometry("720x440")
        ventana.transient(self)
        tabla = ttk.Treeview(ventana, columns=("pais", "comunidad", "evidencia", "total"), show="headings")
        for col, texto, ancho in (
            ("pais", "País", 50),
            ("comunidad", "Comunidad", 240),
            ("evidencia", "Evidencia", 220),
            ("total", "Registros", 90),
        ):
            tabla.heading(col, text=texto)
            tabla.column(col, width=ancho, anchor="w")
        for pais, comunidad, evidencia, total in filas:
            tabla.insert("", "end", values=(pais, comunidad, EVIDENCIA.get(evidencia, evidencia), total))
        scroll = ttk.Scrollbar(ventana, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll.set)
        tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _log(self, mensaje: str) -> None:
        with self._cola_lock:
            self._cola_logs.append(mensaje)

    def _procesar_cola_logs(self) -> None:
        with self._cola_lock:
            pendientes = self._cola_logs[:]
            self._cola_logs.clear()
        if pendientes:
            self.txt_log.configure(state="normal")
            for msg in pendientes:
                self.txt_log.insert("end", msg + "\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        self.after(150, self._procesar_cola_logs)

    def _poner_progreso(self, valor: int, maximo: int, texto: str) -> None:
        def aplicar() -> None:
            self.barra_progreso.configure(maximum=max(maximo, 1), value=min(valor, max(maximo, 1)))
            self.lbl_progreso.configure(text=texto)

        self.after(0, aplicar)

    def iniciar_descarga(self) -> None:
        especie = self.var_especie_ing.get().strip()
        paises = [p.strip().upper() for p in self.var_paises_ing.get().split(",") if p.strip()]
        anios = self.var_anios_ing.get().strip() or None
        max_txt = self.var_max_ing.get().strip()
        if max_txt and (not max_txt.isdigit() or int(max_txt) < 1):
            messagebox.showwarning("Revisa el máximo", "El máximo por país tiene que ser un número entero, o quedar vacío para traer todo.")
            return
        max_por_pais = int(max_txt) if max_txt else None
        if not especie or not paises:
            messagebox.showwarning("Faltan datos", "Indica la especie y al menos un código de país, por ejemplo ES,PT.")
            return
        self._cancelar.clear()
        self.btn_descargar.configure(state="disabled")
        self.btn_cancelar.configure(state="normal")
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")
        self._poner_progreso(0, 1, "Resolviendo el nombre en GBIF...")
        hilo = threading.Thread(
            target=self._worker_descarga,
            args=(especie, paises, anios, max_por_pais),
            daemon=True,
        )
        hilo.start()

    def _descarga_cancelada(self) -> bool:
        if not self._cancelar.is_set():
            return False
        self._log("Descarga cancelada. No se ha escrito nada en MySQL.")
        self._poner_progreso(0, 1, "Descarga cancelada.")
        return True

    def _worker_descarga(
        self,
        especie: str,
        paises: list[str],
        anios: str | None,
        max_por_pais: int | None,
    ) -> None:
        try:
            sesion_http = requests.Session()
            sesion_http.headers.update({"User-Agent": "BiodiversidadGBIF-Tk/1.0"})
            retry = Retry(total=4, backoff_factor=0.6, status_forcelist=[429, 500, 502, 503, 504])
            sesion_http.mount("https://", HTTPAdapter(max_retries=retry))

            self._log(f"Resolviendo «{especie}» en GBIF...")
            r_sp = sesion_http.get(f"{GBIF_API}/species/match", params={"name": especie}, timeout=20)
            r_sp.raise_for_status()
            taxon_data = r_sp.json()
            usage_key = taxon_data.get("usageKey")
            if not usage_key:
                raise ValueError(f"GBIF no reconoce el nombre «{especie}».")
            self._log(f"Taxón: {taxon_data.get('scientificName')} (clave {usage_key}).")
            if self._descarga_cancelada():
                return

            registros: list[dict[str, Any]] = []
            for pais in paises:
                offset = 0
                descargados_pais = 0
                while True:
                    if self._descarga_cancelada():
                        return
                    limite = 300 if max_por_pais is None else min(300, max_por_pais - descargados_pais)
                    if limite <= 0:
                        break
                    params: dict[str, Any] = {
                        "taxonKey": usage_key,
                        "country": pais,
                        "hasCoordinate": "true",
                        "limit": limite,
                        "offset": offset,
                    }
                    if anios:
                        params["year"] = anios
                    resp = sesion_http.get(f"{GBIF_API}/occurrence/search", params=params, timeout=30)
                    resp.raise_for_status()
                    payload = resp.json()
                    lote = payload.get("results", [])
                    if not lote:
                        self._poner_progreso(descargados_pais, max(descargados_pais, 1), f"{pais}: no hay más registros.")
                        break
                    registros.extend(lote)
                    descargados_pais += len(lote)
                    offset += len(lote)
                    disponible = int(payload.get("count") or descargados_pais)
                    objetivo = disponible if max_por_pais is None else min(disponible, max_por_pais)
                    self._poner_progreso(descargados_pais, objetivo, f"{pais}: {descargados_pais:,} de {objetivo:,}")
                    self._log(f"{pais}: {descargados_pais:,} de {objetivo:,}")
                    if payload.get("endOfRecords", False):
                        break
                    time.sleep(0.2)

            if not registros:
                self._log("GBIF no ha devuelto registros con esos filtros.")
                self._poner_progreso(0, 1, "Sin registros.")
                return
            if self._descarga_cancelada():
                return

            self._log("Descargando organizaciones y datasets...")
            self._poner_progreso(0, 1, "Guardando catálogos...")
            org_keys = {r["publishingOrgKey"] for r in registros if r.get("publishingOrgKey")}
            ds_keys = {r["datasetKey"] for r in registros if r.get("datasetKey")}
            orgs_crudas = []
            for ok in org_keys:
                if self._descarga_cancelada():
                    return
                ro = sesion_http.get(f"{GBIF_API}/organization/{ok}", timeout=20)
                if ro.ok:
                    orgs_crudas.append(ro.json())
            ds_crudos = []
            for dk in ds_keys:
                if self._descarga_cancelada():
                    return
                rd = sesion_http.get(f"{GBIF_API}/dataset/{dk}", timeout=20)
                if rd.ok:
                    ds_crudos.append(rd.json())
            self._log(f"{len(orgs_crudas)} organizaciones y {len(ds_crudos)} datasets.")

            self._poner_progreso(1, 1, "Guardando en MySQL...")
            with get_session() as session:
                repo = BiodiversidadRepository(session)
                repo.upsert_taxon(taxon_data)
                repo.upsert_organizaciones(orgs_crudas)
                repo.upsert_datasets(ds_crudos)
                total = repo.upsert_ocurrencias(registros)
            self._log(
                f"Listo: {total:,} ocurrencias guardadas o actualizadas. "
                "Si alguna citaba un taxón que no está en el catálogo, esa clave quedó vacía y el registro se guardó."
            )
            self._poner_progreso(1, 1, f"Listo: {total:,} ocurrencias guardadas o actualizadas.")
            self.after(0, self.refrescar_resumen_bd)
            self.after(0, self.ejecutar_consulta)
        except Exception as exc:
            self._log(f"No se pudo completar la descarga: {exc}")
            self._poner_progreso(0, 1, "La descarga no se ha completado.")
        finally:
            self.after(0, lambda: self.btn_descargar.configure(state="normal"))
            self.after(0, lambda: self.btn_cancelar.configure(state="disabled"))


def lanzar_gui() -> None:
    app = BiodiversidadApp()
    app.mainloop()
