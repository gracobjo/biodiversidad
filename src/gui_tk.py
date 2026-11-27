from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from database import get_session
from models import Ocurrencia
from repository import BiodiversidadRepository

GBIF_API = "https://api.gbif.org/v1"


class BiodiversidadApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Biodiversidad GBIF — Pipeline ETL & Explorador ORM (MySQL 8)")
        self.geometry("1160x720")
        self.minsize(980, 640)

        self._cola_logs: queue.Queue[str] = queue.Queue()
        self._resultados_actuales: dict[str, Ocurrencia] = {}
        self._mapa_taxones: dict[str, int] = {}

        self._construir_ui()
        self._procesar_cola_logs()
        self.after(200, self.refrescar_resumen_bd)

    # ------------------------------------------------------------------
    # CONSTRUCCIÓN DE INTERFAZ (TTK NOTEBOOK: FASE A + FASE B)
    # ------------------------------------------------------------------
    def _construir_ui(self) -> None:
        estilo = ttk.Style(self)
        if "vista" in estilo.theme_names():
            estilo.theme_use("vista")

        # Barra superior de estado de BD
        barra_top = ttk.Frame(self, padding=(12, 8))
        barra_top.pack(fill="x")

        self.lbl_estado_bd = ttk.Label(
            barra_top,
            text="Estado MySQL (ORM): conectando...",
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_estado_bd.pack(side="left")

        ttk.Button(
            barra_top,
            text="Actualizar conteos BD",
            command=self.refrescar_resumen_bd,
        ).pack(side="right")

        # Pestañas principales
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.tab_offline = ttk.Frame(notebook, padding=10)
        self.tab_ingesta = ttk.Frame(notebook, padding=10)

        notebook.add(self.tab_offline, text="Fase B: Exploración Offline (ORM)")
        notebook.add(self.tab_ingesta, text="Fase A: Ingesta Online GBIF -> MySQL")

        self._construir_tab_offline()
        self._construir_tab_ingesta()

    # ------------------------------------------------------------------
    # PESTAÑA FASE B: EXPLORACIÓN OFFLINE CON REPOSITORIO ORM
    # ------------------------------------------------------------------
    def _construir_tab_offline(self) -> None:
        panel_filtros = ttk.LabelFrame(self.tab_offline, text="Filtros de consulta ORM", padding=10)
        panel_filtros.pack(fill="x", pady=(0, 8))

        # Fila 0: Especie, País, Año mínimo y botón Consultar ORM
        ttk.Label(panel_filtros, text="Especie:").grid(row=0, column=0, padx=(0, 4), pady=(0, 6), sticky="w")
        self.var_especie_filtro = tk.StringVar(value="Todas las especies")
        self.cb_especie_filtro = ttk.Combobox(
            panel_filtros,
            textvariable=self.var_especie_filtro,
            values=("Todas las especies",),
            state="readonly",
            width=30,
        )
        self.cb_especie_filtro.grid(row=0, column=1, padx=(0, 12), pady=(0, 6), sticky="w")

        ttk.Label(panel_filtros, text="País:").grid(row=0, column=2, padx=(0, 4), pady=(0, 6), sticky="w")
        self.var_pais = tk.StringVar(value="ES + PT")
        self.cb_pais = ttk.Combobox(
            panel_filtros,
            textvariable=self.var_pais,
            values=("ES + PT", "ES", "PT"),
            state="readonly",
            width=10,
        )
        self.cb_pais.grid(row=0, column=3, padx=(0, 12), pady=(0, 6), sticky="w")
        self.cb_pais.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_lista_comunidades())

        ttk.Label(panel_filtros, text="Año >= :").grid(row=0, column=4, padx=(0, 4), pady=(0, 6), sticky="w")
        self.var_anio_min = tk.StringVar(value="2020")
        ttk.Entry(panel_filtros, textvariable=self.var_anio_min, width=8).grid(
            row=0, column=5, padx=(0, 12), pady=(0, 6), sticky="w"
        )

        ttk.Button(
            panel_filtros,
            text="Consultar ORM",
            command=self.ejecutar_consulta_orm,
        ).grid(row=0, column=6, padx=(0, 6), pady=(0, 6), sticky="ew")

        # Fila 1: Comunidad GADM (desplegable), Límite, Check lobo y botón Top Comunidades
        ttk.Label(panel_filtros, text="Comunidad GADM:").grid(row=1, column=0, padx=(0, 4), sticky="w")
        self.var_comunidad = tk.StringVar(value="Todas las comunidades")
        self.cb_comunidad = ttk.Combobox(
            panel_filtros,
            textvariable=self.var_comunidad,
            values=("Todas las comunidades",),
            state="readonly",
            width=30,
        )
        self.cb_comunidad.grid(row=1, column=1, padx=(0, 12), sticky="w")

        ttk.Label(panel_filtros, text="Límite:").grid(row=1, column=2, padx=(0, 4), sticky="w")
        self.var_limite = tk.StringVar(value="200")
        ttk.Entry(panel_filtros, textvariable=self.var_limite, width=10).grid(
            row=1, column=3, padx=(0, 12), sticky="w"
        )

        self.var_solo_lobo = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            panel_filtros,
            text="Excluir perro doméstico (solo Canis lupus)",
            variable=self.var_solo_lobo,
        ).grid(row=1, column=4, columnspan=2, padx=(0, 12), sticky="w")

        ttk.Button(
            panel_filtros,
            text="Ver Top Comunidades (ES)",
            command=self.mostrar_resumen_territorial,
        ).grid(row=1, column=6, padx=(0, 6), sticky="ew")

        # Tabla Treeview de resultados
        marco_tabla = ttk.Frame(self.tab_offline)
        marco_tabla.pack(fill="both", expand=True)

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
            "key": ("GBIF ID", 95),
            "pais": ("País", 45),
            "anio": ("Año", 55),
            "especie": ("Nombre científico", 165),
            "comunidad": ("Comunidad GADM", 145),
            "provincia": ("Provincia GADM", 120),
            "evidencia": ("Basis of Record", 130),
            "foto": ("Foto", 45),
            "dataset": ("Dataset", 180),
            "organizacion": ("Organización", 160),
        }
        for col, (texto, ancho) in encabezados.items():
            self.tree.heading(col, text=texto)
            self.tree.column(col, width=ancho, anchor="w")

        scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(marco_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        marco_tabla.rowconfigure(0, weight=1)
        marco_tabla.columnconfigure(0, weight=1)

        # Barra inferior de acciones sobre fila seleccionada
        barra_inf = ttk.Frame(self.tab_offline, padding=(0, 8, 0, 0))
        barra_inf.pack(fill="x")

        self.lbl_resultados = ttk.Label(barra_inf, text="0 registros mostrados.")
        self.lbl_resultados.pack(side="left")

        ttk.Button(
            barra_inf,
            text="Abrir fotografía (raw_json)",
            command=self.abrir_imagen_seleccionada,
        ).pack(side="right", padx=(6, 0))

        ttk.Button(
            barra_inf,
            text="Abrir ficha en GBIF",
            command=self.abrir_ficha_gbif_seleccionada,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # PESTAÑA FASE A: INGESTA DESDE API GBIF -> UPSERT ORM
    # ------------------------------------------------------------------
    def _construir_tab_ingesta(self) -> None:
        panel_params = ttk.LabelFrame(self.tab_ingesta, text="Parámetros de extracción API GBIF", padding=10)
        panel_params.pack(fill="x", pady=(0, 8))

        ttk.Label(panel_params, text="Especie:").grid(row=0, column=0, padx=(0, 4), sticky="w")
        self.var_especie_ing = tk.StringVar(value="Canis lupus")
        ttk.Entry(panel_params, textvariable=self.var_especie_ing, width=22).grid(row=0, column=1, padx=(0, 12))

        ttk.Label(panel_params, text="Países (coma):").grid(row=0, column=2, padx=(0, 4), sticky="w")
        self.var_paises_ing = tk.StringVar(value="ES,PT")
        ttk.Entry(panel_params, textvariable=self.var_paises_ing, width=12).grid(row=0, column=3, padx=(0, 12))

        ttk.Label(panel_params, text="Años:").grid(row=0, column=4, padx=(0, 4), sticky="w")
        self.var_anios_ing = tk.StringVar(value="2020,2026")
        ttk.Entry(panel_params, textvariable=self.var_anios_ing, width=12).grid(row=0, column=5, padx=(0, 12))

        ttk.Label(panel_params, text="Máx./país:").grid(row=0, column=6, padx=(0, 4), sticky="w")
        self.var_max_ing = tk.StringVar(value="300")
        ttk.Entry(panel_params, textvariable=self.var_max_ing, width=8).grid(row=0, column=7, padx=(0, 12))

        self.btn_iniciar_ingesta = ttk.Button(
            panel_params,
            text="Ejecutar Ingesta ETL -> ORM",
            command=self.iniciar_hilo_ingesta,
        )
        self.btn_iniciar_ingesta.grid(row=0, column=8)

        # Consola de progreso
        marco_log = ttk.LabelFrame(self.tab_ingesta, text="Registro de ejecución ETL", padding=8)
        marco_log.pack(fill="both", expand=True)

        self.txt_log = tk.Text(marco_log, wrap="word", font=("Consolas", 9), state="disabled")
        scroll_log = ttk.Scrollbar(marco_log, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scroll_log.set)

        self.txt_log.pack(side="left", fill="both", expand=True)
        scroll_log.pack(side="right", fill="y")

    # ------------------------------------------------------------------
    # LÓGICA DE ACCESO A DATOS MEDIANTE ORM
    # ------------------------------------------------------------------
    def _paises_seleccionados(self) -> tuple[str, ...]:
        seleccion_pais = self.var_pais.get()
        return ("ES", "PT") if seleccion_pais == "ES + PT" else (seleccion_pais,)

    def _actualizar_lista_comunidades(self, repo_existente: BiodiversidadRepository | None = None) -> None:
        paises = self._paises_seleccionados()
        if repo_existente is not None:
            comunidades = repo_existente.listar_comunidades(paises=paises)
        else:
            with get_session() as session:
                repo = BiodiversidadRepository(session)
                comunidades = repo.listar_comunidades(paises=paises)

        opciones_com = ["Todas las comunidades", *comunidades]
        self.cb_comunidad["values"] = opciones_com
        if self.var_comunidad.get() not in opciones_com:
            self.var_comunidad.set("Todas las comunidades")

    def refrescar_resumen_bd(self) -> None:
        try:
            with get_session() as session:
                repo = BiodiversidadRepository(session)
                conteos = repo.resumen_conteo_tablas()
                taxones = repo.listar_taxones()
                self._actualizar_lista_comunidades(repo_existente=repo)

            self._mapa_taxones = {nombre: t_key for t_key, nombre in taxones}
            opciones = ["Todas las especies", *self._mapa_taxones.keys()]
            self.cb_especie_filtro["values"] = opciones
            if self.var_especie_filtro.get() not in opciones:
                self.var_especie_filtro.set("Todas las especies")

            self.lbl_estado_bd.config(
                text=(
                    f"MySQL 8 (ORM activo)  |  Taxones: {conteos['taxones']:,}  •  "
                    f"Organizaciones: {conteos['organizaciones']:,}  •  "
                    f"Datasets: {conteos['datasets']:,}  •  "
                    f"Ocurrencias: {conteos['ocurrencias']:,}"
                )
            )
        except Exception as exc:
            self.lbl_estado_bd.config(text=f"Error de conexión ORM: {exc}")

    def ejecutar_consulta_orm(self) -> None:
        especie_sel = self.var_especie_filtro.get()
        taxon_key_sel = self._mapa_taxones.get(especie_sel)
        paises = self._paises_seleccionados()

        anio_txt = self.var_anio_min.get().strip()
        anio_min = int(anio_txt) if anio_txt.isdigit() else None

        limite_txt = self.var_limite.get().strip()
        limite = int(limite_txt) if limite_txt.isdigit() else 200

        comunidad_sel = self.var_comunidad.get().strip()
        comunidad = None if (not comunidad_sel or comunidad_sel == "Todas las comunidades") else comunidad_sel

        solo_lobo = self.var_solo_lobo.get() and (taxon_key_sel in (None, 5219173))

        try:
            with get_session() as session:
                repo = BiodiversidadRepository(session)
                ocurrencias = repo.buscar_ocurrencias(
                    paises=paises,
                    solo_lobo_silvestre=solo_lobo,
                    anio_min=anio_min,
                    comunidad=comunidad,
                    taxon_key=taxon_key_sel,
                    limite=limite,
                )

            self.tree.delete(*self.tree.get_children())
            self._resultados_actuales.clear()

            for occ in ocurrencias:
                iid = str(occ.occurrence_key)
                self._resultados_actuales[iid] = occ
                self.tree.insert(
                    "",
                    "end",
                    iid=iid,
                    values=(
                        occ.occurrence_key,
                        occ.country_code or "",
                        occ.year or "",
                        occ.scientific_name or "",
                        occ.comunidad_gadm or "N/D",
                        occ.provincia_gadm or "N/D",
                        occ.basis_of_record or "",
                        "Sí" if occ.url_primera_imagen else "No",
                        occ.dataset.title if occ.dataset else "N/D",
                        occ.organizacion.title if occ.organizacion else "N/D",
                    ),
                )

            self.lbl_resultados.config(text=f"{len(ocurrencias):,} registros recuperados vía SQLAlchemy ORM.")
        except Exception as exc:
            messagebox.showerror("Error en consulta ORM", str(exc))

    def mostrar_resumen_territorial(self) -> None:
        try:
            with get_session() as session:
                repo = BiodiversidadRepository(session)
                filas = repo.conteo_por_comunidad(pais="ES")[:15]

            lineas = [f"{reg:<28} | {ev:<20} | {tot:>5}" for reg, ev, tot in filas]
            texto = "Top 15 agregación territorial ORM (España):\n\n" + "\n".join(lineas)
            messagebox.showinfo("Resumen Territorial ORM", texto)
        except Exception as exc:
            messagebox.showerror("Error en agregación ORM", str(exc))

    def _obtener_ocurrencia_seleccionada(self) -> Ocurrencia | None:
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Selección vacía", "Selecciona primero un registro de la tabla.")
            return None
        return self._resultados_actuales.get(seleccion[0])

    def abrir_ficha_gbif_seleccionada(self) -> None:
        occ = self._obtener_ocurrencia_seleccionada()
        if occ and occ.gbif_url:
            webbrowser.open(occ.gbif_url)

    def abrir_imagen_seleccionada(self) -> None:
        occ = self._obtener_ocurrencia_seleccionada()
        if not occ:
            return
        url_img = occ.url_primera_imagen
        if url_img:
            webbrowser.open(url_img)
        else:
            messagebox.showinfo("Sin fotografía", "Este registro no contiene enlaces multimedia en raw_json.")

    # ------------------------------------------------------------------
    # WORKER EN SEGUNDO PLANO PARA INGESTA ETL -> ORM
    # ------------------------------------------------------------------
    def _log(self, mensaje: str) -> None:
        self._cola_logs.put(mensaje)

    def _procesar_cola_logs(self) -> None:
        while not self._cola_logs.empty():
            msg = self._cola_logs.get_nowait()
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", msg + "\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        self.after(150, self._procesar_cola_logs)

    def iniciar_hilo_ingesta(self) -> None:
        especie = self.var_especie_ing.get().strip()
        paises = [p.strip().upper() for p in self.var_paises_ing.get().split(",") if p.strip()]
        anios = self.var_anios_ing.get().strip() or None
        max_txt = self.var_max_ing.get().strip()
        max_por_pais = int(max_txt) if max_txt.isdigit() else None

        if not especie or not paises:
            messagebox.showwarning("Parámetros incompletos", "Indica al menos una especie y un código de país.")
            return

        self.btn_iniciar_ingesta.configure(state="disabled")
        hilo = threading.Thread(
            target=self._worker_ingesta_orm,
            args=(especie, paises, anios, max_por_pais),
            daemon=True,
        )
        hilo.start()

    def _worker_ingesta_orm(
        self,
        especie: str,
        paises: list[str],
        anios: str | None,
        max_por_pais: int | None,
    ) -> None:
        try:
            sesion_http = requests.Session()
            sesion_http.headers.update({"User-Agent": "BiodiversidadGBIF-TkORM/1.0"})
            retry = Retry(total=4, backoff_factor=0.6, status_forcelist=[429, 500, 502, 503, 504])
            sesion_http.mount("https://", HTTPAdapter(max_retries=retry))

            self._log(f"[1/4] Resolviendo taxón '{especie}' en GBIF...")
            r_sp = sesion_http.get(f"{GBIF_API}/species/match", params={"name": especie}, timeout=20)
            r_sp.raise_for_status()
            taxon_data = r_sp.json()
            usage_key = taxon_data.get("usageKey")
            if not usage_key:
                raise ValueError(f"Taxón no encontrado: {taxon_data}")
            self._log(f"      -> {taxon_data.get('scientificName')} (taxonKey={usage_key})")

            self._log(f"[2/4] Descargando ocurrencias para países {paises}...")
            registros: list[dict[str, Any]] = []
            for pais in paises:
                offset = 0
                descargados_pais = 0
                while True:
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
                        break

                    registros.extend(lote)
                    descargados_pais += len(lote)
                    offset += len(lote)
                    self._log(f"      [{pais}] +{len(lote)} registros (acumulado país: {descargados_pais})")

                    if payload.get("endOfRecords", False):
                        break
                    time.sleep(0.2)

            self._log(f"[3/4] Descargando catálogos únicos del Registry...")
            org_keys = {r["publishingOrgKey"] for r in registros if r.get("publishingOrgKey")}
            ds_keys = {r["datasetKey"] for r in registros if r.get("datasetKey")}

            orgs_crudas = []
            for ok in org_keys:
                ro = sesion_http.get(f"{GBIF_API}/organization/{ok}", timeout=20)
                if ro.ok:
                    orgs_crudas.append(ro.json())

            ds_crudos = []
            for dk in ds_keys:
                rd = sesion_http.get(f"{GBIF_API}/dataset/{dk}", timeout=20)
                if rd.ok:
                    ds_crudos.append(rd.json())

            self._log(
                f"      -> {len(orgs_crudas)} organizaciones y {len(ds_crudos)} datasets recuperados."
            )

            self._log("[4/4] Ejecutando Upsert transaccional en MySQL 8 vía SQLAlchemy ORM...")
            with get_session() as session:
                repo = BiodiversidadRepository(session)
                repo.upsert_taxon(taxon_data)
                repo.upsert_organizaciones(orgs_crudas)
                repo.upsert_datasets(ds_crudos)
                total_volcados = repo.upsert_ocurrencias(registros)

            self._log(f"COMPLETADO: {total_volcados:,} ocurrencias persistidas/actualizadas mediante ORM.\n")
            self.after(0, self.refrescar_resumen_bd)
            self.after(0, self.ejecutar_consulta_orm)
        except Exception as exc:
            self._log(f"ERROR EN INGESTA ORM: {exc}\n")
        finally:
            self.after(0, lambda: self.btn_iniciar_ingesta.configure(state="normal"))


def lanzar_gui() -> None:
    app = BiodiversidadApp()
    app.mainloop()