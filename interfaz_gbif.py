"""Interfaz de escritorio para consultar GBIF, cargar la base y exportar resultados."""

from __future__ import annotations

import queue
import sys
import threading
import unicodedata
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pandas as pd

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import consulta_gbif
import consulta_gbif_sqlite
from exportacion_gbif import CARPETA_SALIDAS, exportar_csv, exportar_json, exportar_mapa_html
from servicio_bd import (
    consultar_taxon,
    crear_base,
    filtrar_ocurrencias,
    poblar_base,
    tabla_desde_registros_gbif,
    tabla_taxon,
)

MAX_FILAS_TABLA = 400
COLUMNAS_VISIBLES = 12
ESPECIE_DEFECTO = "Canis lupus"


class AplicacionGbif(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Biodiversidad GBIF")
        self.geometry("1180x760")
        self.minsize(960, 640)
        self.option_add("*Font", ("Segoe UI", 10))

        self._cola: queue.Queue = queue.Queue()
        self._ocupado = False
        self._botones: list[ttk.Button] = []
        self.df_actual: pd.DataFrame | None = None
        self.df_ocurrencias: pd.DataFrame | None = None
        self._tabla_es_catalogo = False
        self.especie_tabla: str | None = None
        self.aviso_api = tk.StringVar()
        self.aviso_base = tk.StringVar()
        self.aviso_consultas = tk.StringVar()
        self.aviso_exportar = tk.StringVar()

        self.especie = tk.StringVar(value=ESPECIE_DEFECTO)
        self.paises = tk.StringVar(value="ES, PT")
        self.anios = tk.StringVar(value="2000,2026")
        self.max_registros = tk.StringVar(value="1000")
        self.con_coordenadas = tk.BooleanVar(value=True)
        self.motor = tk.StringVar(value="sqlite")
        self.mysql_host = tk.StringVar(value="localhost")
        self.mysql_port = tk.StringVar(value="3306")
        self.mysql_user = tk.StringVar(value="root")
        self.mysql_password = tk.StringVar(value="")
        self.mysql_database = tk.StringVar(value="gbif_biodiversidad")
        self.solo_lobo = tk.BooleanVar(value=False)
        self.anio_min = tk.StringVar(value="")
        self.pais_territorio = tk.StringVar(value="ES")
        self.limite = tk.StringVar(value="10")
        self.filtro_pais = tk.StringVar(value="")
        self.filtro_anio = tk.StringVar(value="")
        self.filtro_provincia = tk.StringVar(value="")
        self.filtro_epiteto = tk.StringVar(value="")
        self.estado = tk.StringVar(value="Listo. La base SQLite ya puede consultarse sin llamar a la API.")

        self.especie.trace_add("write", self._refrescar_avisos_especie)
        self._construir()
        self._refrescar_avisos_especie()
        self._prellenar_mysql()
        self._al_cambiar_motor()
        self.after(120, self._bombear)

    def _construir(self) -> None:
        marco = ttk.Frame(self, padding=10)
        marco.pack(fill="both", expand=True)
        marco.rowconfigure(2, weight=1)
        marco.rowconfigure(3, weight=0)
        marco.columnconfigure(0, weight=1)

        self._filtros(marco)
        self._acciones(marco)
        self._tabla(marco)
        self._log(marco)
        ttk.Label(marco, textvariable=self.estado).grid(row=4, column=0, sticky="w", pady=(6, 0))

    def _filtros(self, padre: ttk.Frame) -> None:
        caja = ttk.LabelFrame(padre, text="Consulta a la API y carga", padding=8)
        caja.grid(row=0, column=0, sticky="ew")
        for columna in range(8):
            caja.columnconfigure(columna, weight=1)

        ttk.Label(
            caja,
            text="Especie\nGET /v1/occurrence/search\nfacet=speciesKey y hasCoordinate=true",
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        marco_especie = ttk.Frame(caja)
        marco_especie.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        marco_especie.columnconfigure(0, weight=1)
        self.combo_especie = ttk.Combobox(marco_especie, textvariable=self.especie, width=22)
        self.combo_especie.grid(row=0, column=0, sticky="ew")
        self.combo_especie.bind("<<ComboboxSelected>>", self._al_elegir_especie)
        self._boton(marco_especie, "Limpiar", self._limpiar_especie).grid(row=0, column=1, padx=(6, 0))
        self.grupo = tk.StringVar(value="Clase y familia: pulsa Especies con coordenadas.")
        ttk.Label(marco_especie, textvariable=self.grupo).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self._catalogo_especies: dict[str, dict] = {}
        ttk.Label(caja, text="Países").grid(row=0, column=1, sticky="w")
        ttk.Entry(caja, textvariable=self.paises, width=16).grid(row=1, column=1, sticky="ew", padx=(0, 8))
        ttk.Label(caja, text="Años").grid(row=0, column=2, sticky="w")
        ttk.Entry(caja, textvariable=self.anios, width=14).grid(row=1, column=2, sticky="ew", padx=(0, 8))
        ttk.Label(caja, text="Máx. por país").grid(row=0, column=3, sticky="w")
        ttk.Entry(caja, textvariable=self.max_registros, width=10).grid(row=1, column=3, sticky="ew", padx=(0, 8))
        ttk.Checkbutton(caja, text="Solo con coordenadas", variable=self.con_coordenadas).grid(
            row=1, column=4, sticky="w"
        )

        motores = ttk.Frame(caja)
        motores.grid(row=1, column=5, columnspan=3, sticky="e")
        ttk.Label(motores, text="Base").pack(side="left", padx=(0, 6))
        ttk.Radiobutton(motores, text="SQLite", variable=self.motor, value="sqlite", command=self._al_cambiar_motor).pack(
            side="left"
        )
        ttk.Radiobutton(motores, text="MySQL", variable=self.motor, value="mysql", command=self._al_cambiar_motor).pack(
            side="left", padx=(8, 0)
        )

        self.marco_mysql = ttk.Frame(caja)
        self.marco_mysql.grid(row=2, column=0, columnspan=8, sticky="ew", pady=(8, 0))
        campos = (
            ("Host", self.mysql_host, False),
            ("Puerto", self.mysql_port, False),
            ("Usuario", self.mysql_user, False),
            ("Contraseña", self.mysql_password, True),
            ("Base", self.mysql_database, False),
        )
        self._entradas_mysql: list[ttk.Entry] = []
        for indice, (etiqueta, variable, oculta) in enumerate(campos):
            ttk.Label(self.marco_mysql, text=etiqueta).grid(row=0, column=indice, sticky="w")
            entrada = ttk.Entry(self.marco_mysql, textvariable=variable, show="*" if oculta else "", width=18)
            entrada.grid(row=1, column=indice, sticky="ew", padx=(0, 8))
            self._entradas_mysql.append(entrada)
            self.marco_mysql.columnconfigure(indice, weight=1)

    def _acciones(self, padre: ttk.Frame) -> None:
        pestanas = ttk.Notebook(padre)
        pestanas.grid(row=1, column=0, sticky="ew", pady=(8, 8))

        api = ttk.Frame(pestanas, padding=8)
        base = ttk.Frame(pestanas, padding=8)
        consultas = ttk.Frame(pestanas, padding=8)
        exportar = ttk.Frame(pestanas, padding=8)
        pestanas.add(api, text="API GBIF")
        pestanas.add(base, text="Base de datos")
        pestanas.add(consultas, text="Consultas")
        pestanas.add(exportar, text="Exportar")

        ttk.Label(
            api,
            text=(
                "Especies del desplegable: 5 por clase (mamíferos, escamosos, anfibios,\n"
                "insectos, plantas y aves), aunque tengan menos registros que las aves.\n"
                "Clase: GET /v1/species/match?rank=CLASS.  Especies: GET /v1/occurrence/search?classKey=&facet=speciesKey&hasCoordinate=true.\n"
                "Nombre de cada especie:  GET /v1/species/{speciesKey}\n"
                "Taxón elegido:  GET /v1/species/match     Ocurrencias:  GET /v1/occurrence/search\n"
                "Al poblar la base también se leen  /v1/organization/{key}  y  /v1/dataset/{key}."
            ),
            justify="left",
        ).pack(anchor="w")
        ttk.Label(api, textvariable=self.aviso_api).pack(anchor="w", pady=(6, 0))
        fila_api = ttk.Frame(api)
        fila_api.pack(anchor="w", pady=(8, 0))
        self._boton(fila_api, "Especies con coordenadas", self._cargar_especies).pack(side="left")
        self._boton(fila_api, "Ver taxón", self._ver_taxon).pack(side="left", padx=(8, 0))
        self._boton(fila_api, "Ver ocurrencias", self._ver_ocurrencias).pack(side="left", padx=(8, 0))

        ttk.Label(base, textvariable=self.aviso_base).pack(anchor="w")
        fila_base = ttk.Frame(base)
        fila_base.pack(anchor="w", pady=(8, 0))
        self._boton(fila_base, "Crear base de datos", self._crear_base).pack(side="left")
        self._boton(fila_base, "Poblar base de datos", self._poblar_base).pack(side="left", padx=(8, 0))

        ttk.Label(consultas, textvariable=self.aviso_consultas).pack(anchor="w", pady=(0, 6))
        filtros = ttk.Frame(consultas)
        filtros.pack(anchor="w")
        ttk.Checkbutton(filtros, text="Solo lobo silvestre", variable=self.solo_lobo).pack(side="left")
        ttk.Label(filtros, text="Año mínimo").pack(side="left", padx=(12, 4))
        ttk.Entry(filtros, textvariable=self.anio_min, width=8).pack(side="left")
        ttk.Label(filtros, text="País del territorio").pack(side="left", padx=(12, 4))
        ttk.Entry(filtros, textvariable=self.pais_territorio, width=6).pack(side="left")
        ttk.Label(filtros, text="Límite").pack(side="left", padx=(12, 4))
        ttk.Entry(filtros, textvariable=self.limite, width=6).pack(side="left")

        fila_consultas = ttk.Frame(consultas)
        fila_consultas.pack(anchor="w", pady=(8, 0))
        self._boton(fila_consultas, "Resumen", self._consulta_resumen).pack(side="left")
        self._boton(fila_consultas, "Ocurrencias", self._consulta_ocurrencias).pack(side="left", padx=(8, 0))
        self._boton(fila_consultas, "Territorio", self._consulta_territorio).pack(side="left", padx=(8, 0))
        self._boton(fila_consultas, "Datasets", self._consulta_datasets).pack(side="left", padx=(8, 0))
        self._boton(fila_consultas, "Campos JSON", self._consulta_json).pack(side="left", padx=(8, 0))

        ttk.Label(exportar, textvariable=self.aviso_exportar).pack(anchor="w")
        fila_exportar = ttk.Frame(exportar)
        fila_exportar.pack(anchor="w", pady=(8, 0))
        self._boton(fila_exportar, "Exportar CSV", self._exportar_csv).pack(side="left")
        self._boton(fila_exportar, "Exportar JSON", self._exportar_json).pack(side="left", padx=(8, 0))
        self._boton(fila_exportar, "Mapa HTML", self._exportar_mapa).pack(side="left", padx=(8, 0))

    def _tabla(self, padre: ttk.Frame) -> None:
        caja = ttk.Frame(padre)
        caja.grid(row=2, column=0, sticky="nsew")
        caja.rowconfigure(1, weight=1)
        caja.columnconfigure(0, weight=1)

        filtro = ttk.LabelFrame(caja, text="Filtrar ocurrencias en pantalla", padding=6)
        filtro.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        campos = (
            ("country_code", self.filtro_pais, 10),
            ("year", self.filtro_anio, 8),
            ("state_province", self.filtro_provincia, 24),
            ("specific_epithet", self.filtro_epiteto, 16),
        )
        for indice, (etiqueta, variable, ancho) in enumerate(campos):
            ttk.Label(filtro, text=etiqueta).grid(row=0, column=indice, sticky="w")
            entrada = ttk.Entry(filtro, textvariable=variable, width=ancho)
            entrada.grid(row=1, column=indice, sticky="ew", padx=(0, 8))
            entrada.bind("<Return>", lambda _evento: self._aplicar_filtro_ocurrencias())
            filtro.columnconfigure(indice, weight=1)
        self._boton(filtro, "Filtrar", self._aplicar_filtro_ocurrencias).grid(row=1, column=4, padx=(4, 4))
        self._boton(filtro, "Quitar filtro", self._quitar_filtro_ocurrencias).grid(row=1, column=5)

        self.tree = ttk.Treeview(caja, show="headings")
        scroll_y = ttk.Scrollbar(caja, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(caja, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.bind("<<TreeviewSelect>>", self._al_pulsar_especie_catalogo)
        self.tree.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

    def _log(self, padre: ttk.Frame) -> None:
        self.log = tk.Text(padre, height=8, wrap="word", state="disabled", font=("Consolas", 9))
        self.log.grid(row=3, column=0, sticky="ew", pady=(8, 0))

    def _boton(self, padre: ttk.Frame, texto: str, comando) -> ttk.Button:
        boton = ttk.Button(padre, text=texto, command=comando)
        self._botones.append(boton)
        return boton

    def _prellenar_mysql(self) -> None:
        try:
            from db_config import DB_CONFIG
        except Exception:
            return
        self.mysql_host.set(str(DB_CONFIG.get("host", "localhost")))
        self.mysql_port.set(str(DB_CONFIG.get("port", 3306)))
        self.mysql_user.set(str(DB_CONFIG.get("user", "root")))
        self.mysql_password.set(str(DB_CONFIG.get("password", "")))
        self.mysql_database.set(str(DB_CONFIG.get("database", "gbif_biodiversidad")))

    def _al_cambiar_motor(self) -> None:
        activo = self.motor.get() == "mysql"
        estado = "normal" if activo else "disabled"
        for entrada in self._entradas_mysql:
            entrada.configure(state=estado)

    def _parametros(self, exigir_especie: bool = True) -> dict:
        especie = self.especie.get().strip()
        if exigir_especie and not especie:
            raise ValueError("Indica el nombre científico.")
        paises = [parte.strip().upper() for parte in self.paises.get().split(",") if parte.strip()]
        if not paises:
            raise ValueError("Indica al menos un país, por ejemplo ES, PT.")
        try:
            maximo = int(self.max_registros.get().strip() or "1000")
        except ValueError as exc:
            raise ValueError("El máximo por país tiene que ser un número entero.") from exc
        if maximo <= 0:
            raise ValueError("El máximo por país tiene que ser mayor que 0.")
        anio_txt = self.anio_min.get().strip()
        anio_min = None
        if anio_txt:
            try:
                anio_min = int(anio_txt)
            except ValueError as exc:
                raise ValueError("El año mínimo tiene que ser un número entero.") from exc
        try:
            limite = int(self.limite.get().strip() or "10")
        except ValueError as exc:
            raise ValueError("El límite tiene que ser un número entero.") from exc
        if limite <= 0:
            raise ValueError("El límite tiene que ser mayor que 0.")
        try:
            puerto = int(self.mysql_port.get().strip() or "3306")
        except ValueError as exc:
            raise ValueError("El puerto de MySQL tiene que ser un número.") from exc
        return {
            "especie": especie,
            "paises": paises,
            "year_range": self.anios.get().strip() or None,
            "max_registros": maximo,
            "has_coordinate": bool(self.con_coordenadas.get()),
            "solo_lobo": bool(self.solo_lobo.get()),
            "anio_min": anio_min,
            "pais_territorio": self.pais_territorio.get().strip().upper() or "ES",
            "limite": limite,
            "motor": self.motor.get(),
            "mysql": {
                "host": self.mysql_host.get().strip() or "localhost",
                "port": puerto,
                "user": self.mysql_user.get().strip(),
                "password": self.mysql_password.get(),
                "database": self.mysql_database.get().strip() or "gbif_biodiversidad",
            },
        }

    def _modulo_consulta(self, parametros: dict):
        if parametros["motor"] == "sqlite":
            return consulta_gbif_sqlite
        consulta_gbif.usar_config(parametros["mysql"])
        return consulta_gbif

    def _lanzar(self, trabajo, exigir_especie: bool = True) -> None:
        if self._ocupado:
            return
        try:
            parametros = self._parametros(exigir_especie=exigir_especie)
        except ValueError as exc:
            messagebox.showerror("Datos incompletos", str(exc))
            return
        self._ocupado = True
        self.estado.set("Trabajando…")
        for boton in self._botones:
            boton.configure(state="disabled")

        def ejecutar() -> None:
            try:
                mensaje = trabajo(parametros)
                self._cola.put(("log", mensaje))
            except Exception as exc:
                self._cola.put(("error", f"{type(exc).__name__}: {exc}"))
            finally:
                self._cola.put(("libre", None))

        threading.Thread(target=ejecutar, daemon=True).start()

    def _bombear(self) -> None:
        try:
            while True:
                tipo, carga = self._cola.get_nowait()
                if tipo == "log":
                    if not str(carga).strip():
                        continue
                    self._escribir_log(str(carga))
                    self.estado.set(str(carga).split("\n")[-1][:180])
                elif tipo == "df":
                    df, especie = carga
                    self.especie_tabla = especie
                    self._pintar_df(df)
                elif tipo == "especies":
                    self.especie_tabla = None
                    self._aplicar_catalogo(carga)
                elif tipo == "ocurrencias":
                    df, nota, especie = carga
                    self.especie_tabla = especie
                    self.df_ocurrencias = df
                    self._mostrar_ocurrencias_filtradas(nota)
                elif tipo == "error":
                    self._escribir_log(str(carga))
                    self.estado.set("La operación ha fallado.")
                    messagebox.showerror("Error", str(carga))
                elif tipo == "libre":
                    self._ocupado = False
                    for boton in self._botones:
                        boton.configure(state="normal")
                    if self.estado.get() == "Trabajando…":
                        self.estado.set("Listo.")
        except queue.Empty:
            pass
        self.after(120, self._bombear)

    def _escribir_log(self, mensaje: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", mensaje.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _avisar(self, mensaje: str) -> None:
        self._cola.put(("log", mensaje))

    def _publicar_df(self, df: pd.DataFrame, especie: str | None = None) -> None:
        self._cola.put(("df", (df, especie)))

    def _publicar_ocurrencias(self, df: pd.DataFrame, nota: str = "", especie: str | None = None) -> None:
        self._cola.put(("ocurrencias", (df, nota, especie)))

    def _refrescar_avisos_especie(self, *_args) -> None:
        nombre = self.especie.get().strip() or ESPECIE_DEFECTO
        slug = _slug_especie(nombre)
        self.aviso_api.set(f"Ver taxón, Ver ocurrencias y Poblar usan {nombre}.")
        self.aviso_base.set(f"Crear aplica el esquema. Poblar descarga {nombre} y lo guarda.")
        self.aviso_consultas.set(f"Las consultas de la base se limitan a {nombre}.")
        self.aviso_exportar.set(
            f"CSV, JSON y HTML de {nombre}. El fichero se propone como {slug} "
            "y la especie aparece dentro."
        )

    def _solo_lobo_aplicable(self, parametros: dict) -> bool:
        return parametros["solo_lobo"] and parametros["especie"].lower().startswith("canis lupus")

    def _criterios_filtro(self) -> dict:
        anio_txt = self.filtro_anio.get().strip()
        anio = None
        if anio_txt:
            try:
                anio = int(anio_txt)
            except ValueError as exc:
                raise ValueError("El filtro year tiene que ser un año entero, por ejemplo 2020.") from exc
        return {
            "country_code": self.filtro_pais.get().strip(),
            "year": anio,
            "state_province": self.filtro_provincia.get().strip(),
            "specific_epithet": self.filtro_epiteto.get().strip(),
        }

    def _filtro_activo(self, criterios: dict) -> bool:
        return any(criterios[clave] not in ("", None) for clave in criterios)

    def _aplicar_filtro_ocurrencias(self) -> None:
        if self.df_ocurrencias is None:
            messagebox.showinfo("Sin ocurrencias", "Primero pulsa Ver ocurrencias o Ocurrencias.")
            return
        try:
            self._mostrar_ocurrencias_filtradas()
        except ValueError as exc:
            messagebox.showerror("Filtro", str(exc))

    def _quitar_filtro_ocurrencias(self) -> None:
        self.filtro_pais.set("")
        self.filtro_anio.set("")
        self.filtro_provincia.set("")
        self.filtro_epiteto.set("")
        if self.df_ocurrencias is None:
            return
        self._mostrar_ocurrencias_filtradas()

    def _mostrar_ocurrencias_filtradas(self, nota: str = "") -> None:
        criterios = self._criterios_filtro()
        filtrado = filtrar_ocurrencias(self.df_ocurrencias, **criterios)
        self._pintar_df(filtrado, anunciar=False)
        total = 0 if self.df_ocurrencias is None else len(self.df_ocurrencias)
        if self._filtro_activo(criterios):
            texto = f"Filtro: {len(filtrado)} de {total} ocurrencias."
        else:
            texto = f"{total} ocurrencias."
        if nota:
            texto = f"{texto} {nota}"
        self._escribir_log(texto)
        self.estado.set(texto)

    def _pintar_df(self, df: pd.DataFrame, anunciar: bool = True, es_catalogo: bool = False) -> None:
        self.df_actual = df
        self._tabla_es_catalogo = bool(es_catalogo) and df is not None and not df.empty
        self.tree.delete(*self.tree.get_children())
        if df is None or df.empty:
            self.tree.configure(displaycolumns=())
            self.tree.configure(columns=())
            if anunciar:
                self._escribir_log("La consulta no ha devuelto filas.")
            return
        columnas = [str(columna) for columna in list(df.columns)[:COLUMNAS_VISIBLES]]
        # Vaciar displaycolumns antes de cambiar la lista: si no, Tk sigue
        # apuntando a los identificadores de la consulta anterior.
        self.tree.configure(displaycolumns=())
        self.tree.configure(columns=columnas)
        self.tree.configure(displaycolumns=columnas)
        for columna in columnas:
            self.tree.heading(columna, text=columna)
            self.tree.column(columna, width=130, anchor="w", stretch=True)
        vista = df.loc[:, columnas].head(MAX_FILAS_TABLA)
        for _, fila in vista.iterrows():
            valores = []
            for valor in fila.tolist():
                if pd.isna(valor):
                    valores.append("")
                else:
                    texto = str(valor)
                    valores.append(texto if len(texto) <= 80 else texto[:77] + "...")
            self.tree.insert("", "end", values=valores)
        if not anunciar:
            return
        aviso = f"{len(df)} filas."
        if len(df) > len(vista) or len(df.columns) > len(columnas):
            aviso += f" En pantalla: {len(vista)} filas y {len(columnas)} columnas. La exportación usa la tabla completa."
        self._escribir_log(aviso)

    def _limpiar_especie(self) -> None:
        self.especie.set(ESPECIE_DEFECTO)
        self.estado.set(f"Especie: {ESPECIE_DEFECTO}")
        self._al_elegir_especie()

    def _al_elegir_especie(self, _evento=None) -> None:
        nombre = self.especie.get().strip()
        ficha = self._catalogo_especies.get(nombre)
        if not ficha:
            self.grupo.set("Clase y familia: esta especie no está en el catálogo cargado.")
            return
        clase = ficha.get("clase") or "—"
        familia = ficha.get("familia") or "—"
        clave = ficha.get("taxon_key")
        self.grupo.set(f"Clase: {clase}    Familia: {familia}")
        self._escribir_log(f"{nombre}: clase {clase}, familia {familia}. GET https://api.gbif.org/v1/species/{clave}")
        self.estado.set(f"{nombre}  ·  {clase}  ·  {familia}")

    def _aplicar_catalogo(self, filas: list[dict]) -> None:
        self._catalogo_especies = {str(fila["nombre_cientifico"]): fila for fila in filas}
        nombres = list(self._catalogo_especies)
        self.combo_especie.configure(values=nombres)
        self._pintar_df(pd.DataFrame(filas), anunciar=False, es_catalogo=True)
        self._escribir_log(
            f"{len(filas)} especies con coordenadas. "
            "Pulsa una fila para copiarla arriba. El cuadro sigue en Canis lupus hasta entonces."
        )

    def _al_pulsar_especie_catalogo(self, _evento=None) -> None:
        if not self._tabla_es_catalogo:
            return
        seleccion = self.tree.selection()
        if not seleccion:
            return
        valores = self.tree.item(seleccion[0], "values")
        if not valores or not str(valores[0]).strip():
            return
        nombre = str(valores[0]).strip()
        self.especie.set(nombre)
        self._al_elegir_especie()

    def _cargar_especies(self) -> None:
        def trabajo(parametros: dict) -> str:
            from ingesta_gbif_sqlite import listar_especies_con_coordenadas

            filas = listar_especies_con_coordenadas(
                paises=parametros["paises"],
                year_range=parametros["year_range"],
                on_progreso=self._avisar,
            )
            self._cola.put(("especies", filas))
            clases = sorted({str(fila.get("clase") or "") for fila in filas if fila.get("clase")})
            return (
                f"Catálogo listo: {len(filas)} especies de {len(clases)} clases "
                f"({', '.join(clases)}). "
                "Clase: GET /v1/species/match?rank=CLASS. "
                "Especies de cada clase: GET /v1/occurrence/search?classKey=&facet=speciesKey&hasCoordinate=true. "
                "Nombre: GET /v1/species/{{speciesKey}}."
            )

        self._lanzar(trabajo, exigir_especie=False)

    def _ver_taxon(self) -> None:
        def trabajo(parametros: dict) -> str:
            self._avisar(f"GET https://api.gbif.org/v1/species/match  name={parametros['especie']}")
            taxon = consultar_taxon(parametros["especie"])
            self._publicar_df(tabla_taxon(taxon), especie=parametros["especie"])
            return (
                f"Taxón de {parametros['especie']}: {taxon.get('scientificName')} "
                f"(usageKey={taxon.get('usageKey')}, {taxon.get('status')})."
            )

        self._lanzar(trabajo)

    def _ver_ocurrencias(self) -> None:
        def trabajo(parametros: dict) -> str:
            from ingesta_gbif_sqlite import descargar_desde_gbif

            _taxon, registros, _sesion = descargar_desde_gbif(
                especie=parametros["especie"],
                paises=parametros["paises"],
                year_range=parametros["year_range"],
                max_registros_por_pais=parametros["max_registros"],
                has_coordinate=parametros["has_coordinate"],
                on_progreso=self._avisar,
            )
            self._publicar_ocurrencias(
                tabla_desde_registros_gbif(registros),
                "Aún no están guardadas en la base.",
                especie=parametros["especie"],
            )
            return ""

        self._lanzar(trabajo)

    def _crear_base(self) -> None:
        def trabajo(parametros: dict) -> str:
            config = parametros["mysql"] if parametros["motor"] == "mysql" else None
            return crear_base(parametros["motor"], config)

        self._lanzar(trabajo)

    def _poblar_base(self) -> None:
        def trabajo(parametros: dict) -> str:
            config = parametros["mysql"] if parametros["motor"] == "mysql" else None
            return poblar_base(
                motor=parametros["motor"],
                config_mysql=config,
                especie=parametros["especie"],
                paises=parametros["paises"],
                year_range=parametros["year_range"],
                max_registros_por_pais=parametros["max_registros"],
                has_coordinate=parametros["has_coordinate"],
                on_progreso=self._avisar,
            )

        self._lanzar(trabajo)

    def _consulta_resumen(self) -> None:
        def trabajo(parametros: dict) -> str:
            df = self._modulo_consulta(parametros).obtener_resumen_general(especie=parametros["especie"])
            self._publicar_df(df, especie=parametros["especie"])
            return f"Resumen de {parametros['especie']} en {parametros['motor']}."

        self._lanzar(trabajo)

    def _consulta_ocurrencias(self) -> None:
        def trabajo(parametros: dict) -> str:
            df = self._modulo_consulta(parametros).cargar_ocurrencias(
                paises=parametros["paises"],
                solo_lobo_silvestre=self._solo_lobo_aplicable(parametros),
                anio_min=parametros["anio_min"],
                especie=parametros["especie"],
            )
            self._publicar_ocurrencias(df, especie=parametros["especie"])
            return ""

        self._lanzar(trabajo)

    def _consulta_territorio(self) -> None:
        def trabajo(parametros: dict) -> str:
            df = self._modulo_consulta(parametros).resumen_territorial_por_comunidad(
                parametros["pais_territorio"],
                especie=parametros["especie"],
            )
            self._publicar_df(df, especie=parametros["especie"])
            return f"Territorio de {parametros['especie']} en {parametros['pais_territorio']}."

        self._lanzar(trabajo)

    def _consulta_datasets(self) -> None:
        def trabajo(parametros: dict) -> str:
            df = self._modulo_consulta(parametros).top_datasets_publicadores(
                parametros["limite"],
                especie=parametros["especie"],
            )
            self._publicar_df(df, especie=parametros["especie"])
            return f"Top {parametros['limite']} datasets de {parametros['especie']}."

        self._lanzar(trabajo)

    def _consulta_json(self) -> None:
        def trabajo(parametros: dict) -> str:
            df = self._modulo_consulta(parametros).consultar_campos_raw_json(
                parametros["limite"],
                especie=parametros["especie"],
            )
            self._publicar_df(df, especie=parametros["especie"])
            return f"Campos JSON de {parametros['especie']} (límite {parametros['limite']})."

        self._lanzar(trabajo)

    def _exigir_tabla(self) -> pd.DataFrame | None:
        if self.df_actual is None or self.df_actual.empty:
            messagebox.showinfo("Sin datos", "Primero consulta la API o la base de datos.")
            return None
        return self.df_actual

    def _elegir_ruta(self, titulo: str, nombre: str, tipos) -> Path | None:
        CARPETA_SALIDAS.mkdir(parents=True, exist_ok=True)
        ruta = filedialog.asksaveasfilename(
            title=titulo,
            initialdir=str(CARPETA_SALIDAS),
            initialfile=nombre,
            defaultextension=Path(nombre).suffix,
            filetypes=tipos,
        )
        if not ruta:
            return None
        return Path(ruta)

    def _datos_exportacion(self) -> tuple[pd.DataFrame, str] | None:
        df = self._exigir_tabla()
        if df is None:
            return None
        especie = self.especie.get().strip() or ESPECIE_DEFECTO
        recorte = _filas_de_especie(df, especie)
        if recorte is not None:
            if recorte.empty:
                messagebox.showinfo(
                    especie,
                    f"La tabla no tiene filas de {especie}. "
                    "Pulsa Ver ocurrencias u Ocurrencias para esa especie.",
                )
                return None
            return recorte, especie
        if self.especie_tabla and self.especie_tabla.lower() != especie.lower():
            messagebox.showinfo(
                especie,
                f"La tabla en pantalla es de {self.especie_tabla}. "
                f"Vuelve a lanzar la consulta para {especie}.",
            )
            return None
        return df, especie

    def _exportar_csv(self) -> None:
        datos = self._datos_exportacion()
        if datos is None:
            return
        df, especie = datos
        ruta = self._elegir_ruta(
            f"Exportar CSV de {especie}",
            f"{_slug_especie(especie)}.csv",
            [("CSV", "*.csv")],
        )
        if ruta is None:
            return
        destino = exportar_csv(df, ruta, especie=especie)
        self._escribir_log(f"CSV de {especie} guardado en {destino}")
        self.estado.set(f"CSV de {especie} guardado en {destino}")

    def _exportar_json(self) -> None:
        datos = self._datos_exportacion()
        if datos is None:
            return
        df, especie = datos
        ruta = self._elegir_ruta(
            f"Exportar JSON de {especie}",
            f"{_slug_especie(especie)}.json",
            [("JSON", "*.json")],
        )
        if ruta is None:
            return
        destino = exportar_json(df, ruta, especie=especie)
        self._escribir_log(f"JSON de {especie} guardado en {destino}")
        self.estado.set(f"JSON de {especie} guardado en {destino}")

    def _exportar_mapa(self) -> None:
        datos = self._datos_exportacion()
        if datos is None:
            return
        df, especie = datos
        ruta = self._elegir_ruta(
            f"Guardar mapa de {especie}",
            f"{_slug_especie(especie)}.html",
            [("HTML", "*.html")],
        )
        if ruta is None:
            return
        try:
            destino, puntos, recortado = exportar_mapa_html(df, ruta, especie=especie)
        except Exception as exc:
            messagebox.showerror(especie, str(exc))
            self._escribir_log(f"{type(exc).__name__}: {exc}")
            return
        aviso = f"Mapa de {especie} con {puntos} puntos guardado en {destino}"
        if recortado:
            aviso += " Se han dejado fuera los registros que superaban el tope del mapa."
        self._escribir_log(aviso)
        self.estado.set(f"Mapa de {especie} guardado en {destino}")
        webbrowser.open(destino.resolve().as_uri())


_COLUMNAS_ESPECIE = (
    "nombre_cientifico",
    "scientificName",
    "acceptedScientificName",
    "scientific_name",
    "canonicalName",
    "species",
    "especie",
)


def _slug_especie(nombre: str) -> str:
    base = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    limpio = "".join(caracter.lower() if caracter.isalnum() else "_" for caracter in base)
    while "__" in limpio:
        limpio = limpio.replace("__", "_")
    return limpio.strip("_") or "especie"


def _filas_de_especie(df: pd.DataFrame, especie: str) -> pd.DataFrame | None:
    nombre = especie.strip().lower()
    columnas = [columna for columna in _COLUMNAS_ESPECIE if columna in df.columns]
    if not columnas:
        return None
    mascara = pd.Series(False, index=df.index)
    for columna in columnas:
        texto = df[columna].astype(str).str.strip().str.lower()
        mascara = mascara | texto.eq(nombre) | texto.str.startswith(f"{nombre} ") | texto.str.startswith(f"{nombre},")
        mascara = mascara | texto.str.startswith(nombre)
    return df.loc[mascara]


def main() -> None:
    aplicacion = AplicacionGbif()
    aplicacion.mainloop()


if __name__ == "__main__":
    main()
