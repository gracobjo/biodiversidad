# Casos de uso

Cada caso indica el requisito que cubre y el artefacto con el que se ejecuta. El detalle de requisitos está en [ESPECIFICACION_REQUISITOS.md](./ESPECIFICACION_REQUISITOS.md). Los diagramas están en [UML.md](./UML.md).

Actores: persona investigadora, persona analista, persona ingeniera de datos. La API de GBIF y MySQL son sistemas externos.

## Catálogo

| ID | Nombre | Actor | Requisito | Dónde |
|---|---|---|---|---|
| CU-01 | Explorar una especie en España | Investigadora | RF-01, RF-02, RF-06, RF-08 | cuaderno v7 |
| CU-02 | Revisar mortalidad y evidencia | Analista | RF-08 | cuaderno v7, secciones de vitalidad y `dynamicProperties` |
| CU-03 | Separar lobo y perro | Investigadora | RF-06 | cuaderno v7, consultas de `src/`, filtro de la interfaz |
| CU-04 | Explorar el catálogo ibérico | Investigadora | RF-01, RF-04 | cuadernos v4 y v6 |
| CU-05 | Acotar por altitud | Investigadora | RF-04 | cuaderno v5 |
| CU-06 | Comparar varias especies | Investigadora | RF-11 | `gbif_multiespecie_es_pt.ipynb` |
| CU-07 | Guardar el lote multi-especie | Ingeniera | RF-16 | `gbif_multiespecie_es_pt_sqlite_mysql.ipynb` |
| CU-08 | Crear y poblar SQLite del pipeline | Ingeniera | RF-12, RF-14 | `src/` o interfaz |
| CU-09 | Crear y poblar MySQL del pipeline | Ingeniera | RF-13, RF-14 | cuaderno de ingesta o interfaz |
| CU-10 | Analizar sin red | Analista | RF-15 | `analisis_offline_gbif.ipynb`, `prueba_lectura_sqlite.py` o interfaz |
| CU-11 | Filtrar ocurrencias ya vistas | Analista | RF-20 | interfaz, barra sobre la tabla |
| CU-12 | Exportar tabla y mapa | Investigadora | RF-09, RF-10, RF-19 | interfaz o celda de exportación del cuaderno |
| CU-13 | Validar calidad de la muestra | Analista | RF-05, RF-07 | cuadernos de exploración y diccionario de datos |

## CU-01 Explorar una especie en España

**Disparador.** Hay que describir los registros recientes de una especie en España.

**Precondición.** Hay red y el entorno Python está activo.

**Flujo.**

1. Abre `notebooks/exploracion_biodiversidad_gbif_v7_mortalidad.ipynb`.
2. Revisa `ESPECIE_OBJETIVO`, el país y el rango de años.
3. Ejecuta las celdas. El cuaderno llama a `/v1/species/match` y pagina `/v1/occurrence/search`.
4. Lee el diagnóstico de filtros, la tabla normalizada y el mapa.

**Postcondición.** Existen `datos/registros_gbif_brutos.json`, el CSV y `salidas_gbif_multiespecie/mapa_avistamientos_gbif.html`.

**Alternativa.** Si GBIF no devuelve `usageKey`, se corrige el nombre científico y se repite el match.

## CU-03 Separar lobo y perro

**Disparador.** El taxón resuelto es *Canis lupus* y el análisis no puede mezclar perro doméstico.

**Flujo.**

1. Se parte del listado de CU-01, de CU-10 o de la interfaz.
2. Se filtra `specificEpithet = lupus` y se excluye `infraspecificEpithet = familiaris`.
3. En la interfaz, con las ocurrencias ya cargadas, se escribe `lupus` en `specific_epithet` y se pulsa Filtrar.
4. Los conteos y el mapa se leen sobre ese subconjunto.

**Postcondición.** El listado completo sigue disponible. Quitar filtro lo restaura.

## CU-06 Comparar varias especies

**Disparador.** Hay que ver en el mismo ámbito lince, lobo, oso y quebrantahuesos.

**Flujo.**

1. Abre `notebooks/gbif_multiespecie_es_pt.ipynb`.
2. Ajusta `ESPECIES_OBJETIVO`, `PAISES` y `MAX_REGISTROS_POR_ESPECIE_PAIS` si hace falta.
3. Ejecuta todas las celdas.
4. Abre el CSV maestro y `mapa_comparativo_multiespecie_es_pt.html`. Activa o desactiva la capa de cada especie.

**Postcondición.** En `salidas_gbif_multiespecie/` hay un CSV y un mapa por especie, el CSV maestro y el mapa comparativo. No hay base de datos nueva.

## CU-07 Guardar el lote multi-especie

**Disparador.** El mismo lote de CU-06 tiene que poder consultarse después en SQL.

**Flujo.**

1. Abre `notebooks/gbif_multiespecie_es_pt_sqlite_mysql.ipynb`.
2. Ejecuta hasta la sección 5. SQLite se crea solo en `salidas_gbif_multiespecie/biodiversidad_gbif.db`.
3. Para MySQL, rellena `.env` y pon `ACTIVAR_MYSQL = True` antes de esa sección.

**Postcondición.** La vista `vw_ocurrencias_completas` devuelve el lote. Esta base no sustituye a `datos/gbif_biodiversidad.sqlite`.

**Excepción.** Si MySQL no responde, el cuaderno deja SQLite escrito y registra el fallo de MySQL.

## CU-08 Crear y poblar SQLite del pipeline

**Disparador.** Hace falta la base que usan las consultas de `src/` y la interfaz.

**Flujo.**

1. Desde `src/`, `python gbif_biodiversidad_sqlite.py` crea `datos/gbif_biodiversidad.sqlite`.
2. `python ingesta_gbif_sqlite.py` descarga *Canis lupus* (ES, PT, máximo 1.000 por país) y vuelca taxón, organizaciones, datasets y ocurrencias.
3. `python prueba_lectura_sqlite.py` comprueba conteos y consultas.

**Alternativa en la interfaz.** Pestaña Base de datos, motor SQLite, botones Crear y Poblar. Los parámetros editables están en la parte superior de la ventana.

**Excepción.** Certificado autofirmado: la ingesta ya activa `truststore`. Si el error vuelve, el intérprete no tiene ese paquete.

## CU-09 Crear y poblar MySQL del pipeline

**Precondición.** MySQL 8 en marcha y credenciales en `src/db_config.py` o en el formulario.

**Flujo.**

1. Aplica `docs/schema_gbif.sql`.
2. Ejecuta `notebooks/ingesta_gbif_mysql.ipynb` o, en la interfaz, elige MySQL y pulsa Crear y Poblar.
3. Ejecuta `notebooks/analisis_offline_gbif.ipynb` o las consultas de la interfaz.

**Excepción.** Si la conexión es rechazada, no se escribe nada. SQLite sigue siendo utilizable.

## CU-10 Analizar sin red

**Precondición.** CU-08 o CU-09 ya cargaron datos.

**Flujo.**

1. Abre la interfaz o `analisis_offline_gbif.ipynb` o `prueba_lectura_sqlite.py`.
2. Pide el resumen, las ocurrencias, el territorio, los datasets o los campos JSON.
3. No se abre ninguna conexión con `api.gbif.org`.

## CU-11 Filtrar ocurrencias ya vistas

**Precondición.** La tabla de la interfaz es un listado de ocurrencias (Ver ocurrencias o Ocurrencias).

**Flujo.**

1. Rellena solo los campos que importan: `country_code`, `year`, `state_province`, `specific_epithet`.
2. Pulsa Filtrar o Intro.
3. La tabla, el estado y la exportación pasan a mostrar el subconjunto.
4. Quitar filtro vacía los cuatro campos y devuelve el listado cargado, sin otra descarga.

**Ejemplo comprobado** sobre las 2.000 ocurrencias de referencia: `ES`, año `2025` y epíteto `lupus` dejan 257 filas; añadiendo provincia `Leon` quedan 19 (León y Castilla y León).

## CU-12 Exportar tabla y mapa

**Precondición.** Hay una tabla visible. Para el mapa, esa tabla tiene latitud y longitud.

**Flujo.**

1. Pestaña Exportar.
2. Elige CSV, JSON o Mapa HTML.
3. Confirma la ruta. Por defecto se ofrece `salidas_gbif_multiespecie/`.
4. El mapa se abre en el navegador.

**Excepción.** Si la tabla es un resumen territorial, el mapa avisa de que no hay coordenadas.

## CU-13 Validar calidad de la muestra

**Flujo.**

1. Compara filas descargadas con el `count` que anuncia GBIF.
2. Mide nulos de `stateProvince` frente a `comunidad_gadm`.
3. Cruza el epíteto con el nombre aceptado.
4. Revisa `coordinateUncertaintyInMeters` antes de interpretar un punto como localidad fina.
5. Consulta [diccionario_datos_gbif.md](./diccionario_datos_gbif.md) para el significado de cada campo.

**Postcondición.** El informe describe la muestra, no el censo de la especie.
