# Casos de uso

Cada caso indica el requisito que cubre y el artefacto con el que se ejecuta. El detalle de requisitos está en [ESPECIFICACION_REQUISITOS.md](./ESPECIFICACION_REQUISITOS.md). Los diagramas están en [UML.md](./UML.md).

Actores: persona investigadora, persona analista, persona ingeniera de datos. La API de GBIF y MySQL son sistemas externos.

## Catálogo

| ID | Nombre | Actor | Requisito | Dónde |
|---|---|---|---|---|
| CU-01 | Explorar una especie en España | Investigadora | RF-01, RF-02, RF-06, RF-08 | cuaderno 01, mortalidad |
| CU-02 | Revisar mortalidad y evidencia | Analista | RF-08 | cuaderno 01, secciones de vitalidad y `dynamicProperties` |
| CU-03 | Separar lobo y perro | Investigadora | RF-06 | cuaderno 01, consultas de `src/`, filtro de la interfaz |
| CU-04 | Explorar el catálogo ibérico | Investigadora | RF-01, RF-04 | cuaderno 02; el 04 es el archivo |
| CU-05 | Acotar por altitud | Investigadora | RF-04 | cuaderno 03 |
| CU-06 | Comparar varias especies | Investigadora | RF-11 | `gbif_multiespecie_es_pt.ipynb` |
| CU-07 | Guardar el lote multi-especie | Ingeniera | RF-16 | `gbif_multiespecie_es_pt_sqlite_mysql.ipynb` |
| CU-08 | Crear y poblar SQLite del pipeline | Ingeniera | RF-12, RF-14 | `src/` o interfaz |
| CU-09 | Crear y poblar MySQL del pipeline | Ingeniera | RF-13, RF-14 | cuaderno de ingesta o interfaz |
| CU-10 | Analizar sin red | Analista | RF-15 | `analisis_offline_gbif.ipynb`, `prueba_lectura_sqlite.py` o interfaz |
| CU-11 | Filtrar ocurrencias ya vistas | Analista | RF-20 | interfaz, barra sobre la tabla |
| CU-12 | Exportar tabla y mapa | Investigadora | RF-09, RF-10, RF-19 | interfaz o celda de exportación del cuaderno |
| CU-13 | Validar calidad de la muestra | Analista | RF-05, RF-07 | cuadernos de exploración y diccionario de datos |
| CU-14 | Ver especies de varias clases | Investigadora | RF-21 | interfaz, Traer datos de `app_tkinter.py` o `gbif_especies_por_clase_es_pt.ipynb` |
| CU-15 | Medir indicadores de MySQL | Analista | RF-22 | pestaña Indicadores de `app_tkinter.py`, o `src/kpi_*.py` |

## CU-01 Explorar una especie en España

**Disparador.** Hay que describir los registros recientes de una especie en España.

**Precondición.** Hay red y el entorno Python está activo.

**Flujo.**

1. Abre `notebooks/exploracion_01_canis_lupus_espana_mortalidad.ipynb`.
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

**Precondición.** La base tiene que estar iniciada: existe `datos/gbif_biodiversidad.sqlite` con el esquema aplicado. El paso 1 de este caso la inicia. Las consultas del paso 3 no se lanzan sobre el `gbif_biodiversidad.sqlite` de la raíz.

**Flujo.**

1. Desde `src/`, `python gbif_biodiversidad_sqlite.py` crea `datos/gbif_biodiversidad.sqlite`.
2. `python ingesta_gbif_sqlite.py` descarga *Canis lupus* (ES, PT, máximo 1.000 por país) y vuelca taxón, organizaciones, datasets y ocurrencias.
3. `python prueba_lectura_sqlite.py` comprueba conteos y consultas.

**Alternativa en la interfaz.** Pestaña Base de datos, motor SQLite, botones Crear y Poblar. Los parámetros editables están en la parte superior de la ventana.

**Excepción.** Certificado autofirmado: la ingesta ya activa `truststore`. Si el error vuelve, el intérprete no tiene ese paquete.

## CU-09 Crear y poblar MySQL del pipeline

**Precondición.** La base tiene que estar iniciada: el servidor MySQL 8 está en marcha, la base `gbif_biodiversidad` existe y `.env` tiene `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` y `DB_NAME`. `src/db_config.py` solo lee ese archivo.

**Flujo.**

1. Aplica `docs/schema_gbif.sql`.
2. Ejecuta `notebooks/ingesta_gbif_mysql.ipynb`, la pestaña Traer datos de GBIF de `python app_tkinter.py`, o en `interfaz_gbif.py` elige MySQL y pulsa Crear y Poblar. Las tres vías terminan en el repositorio ORM. En Traer datos, el texto de la pestaña y el detalle de la descarga dicen el orden: `/v1/species/match`, `/v1/occurrence/search` por país con coordenadas y el periodo escrito, organización, dataset y escritura en MySQL. Cargar especies disponibles lista hasta cinco especies de cada clase para esos países y esas fechas; pulsar una fila rellena Especie. Cancelar antes de guardar no escribe.
3. Ejecuta `notebooks/analisis_offline_gbif.ipynb`, la pestaña Consultar de `app_tkinter.py` o las consultas de `interfaz_gbif.py`. En Consultar se puede elegir cualquier país ya guardado, un año concreto o un intervalo de fechas.

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

1. La especie del cuadro superior es la que se exporta. Si la tabla es de otra especie, la interfaz pide repetir la consulta.
2. Pestaña Exportar.
3. Elige CSV, JSON o Mapa HTML. El nombre propuesto incluye la especie, por ejemplo `turdus_merula.csv`.
4. Confirma la ruta. Por defecto se ofrece `salidas_gbif_multiespecie/`.
5. El CSV lleva la columna `especie`, el JSON el campo `especie` y el mapa un recuadro con el nombre. El mapa se abre en el navegador.

**Excepción.** Si la tabla es un resumen territorial, el mapa avisa de que no hay coordenadas.

## CU-13 Validar calidad de la muestra

**Flujo.**

1. Compara filas descargadas con el `count` que anuncia GBIF.
2. Mide nulos de `stateProvince` frente a `comunidad_gadm`.
3. Cruza el epíteto con el nombre aceptado.
4. Revisa `coordinateUncertaintyInMeters` antes de interpretar un punto como localidad fina.
5. Consulta [diccionario_datos_gbif.md](./diccionario_datos_gbif.md) para el significado de cada campo.

## CU-14 Ver especies de varias clases

**Disparador.** El ranking global de GBIF solo muestra aves y hace falta ver también mamíferos, escamosos, anfibios, insectos y plantas.

**Precondición.** Hay red. El entorno virtual es la carpeta `.venv`. El cuaderno se ejecuta con el kernel **Python (biodiversidad)**, que usa ese intérprete. Si después se va a poblar o consultar la base, tiene que estar iniciada.

**Flujo.**

1. En `interfaz_gbif.py` pulsa Especies con coordenadas, en Traer datos de GBIF de `app_tkinter.py` pulsa Cargar especies disponibles, o abre `notebooks/gbif_especies_por_clase_es_pt.ipynb` y ejecuta las celdas. En Traer datos el listado usa los países y el periodo ya escritos.
2. La tabla muestra cinco especies por clase, con clase, familia y ocurrencias con coordenadas. Si una clase no responde, se omite y el listado sigue.
3. Al pulsar una fila de `interfaz_gbif.py`, el nombre pasa al cuadro superior. Limpiar devuelve *Canis lupus*. En Traer datos, pulsar una fila rellena el campo Especie de esa pestaña.
4. Ver taxón, Ver ocurrencias, Poblar, las consultas y la exportación usan esa especie.

**Postcondición.** El cuaderno, al terminar, guarda `salidas_gbif_multiespecie/especies_por_clase_es_pt.csv`. No descarga ocurrencias.

## CU-15 Medir indicadores de MySQL

**Disparador.** Hay que saber cómo está repartida la base ya cargada: por país y año, por territorio, por campo informado, por evidencia, por taxón, por calidad de la coordenada o por quien publica.

**Precondición.** CU-09 ya cargó datos. MySQL 8 está en marcha y `.env` apunta a `gbif_biodiversidad`.

**Flujo.**

1. Abre `python app_tkinter.py`. La primera pestaña es Traer datos de GBIF; después Consultar e Indicadores. Entra en Indicadores. La pestaña calcula el volumen de toda la base y dibuja el gráfico por país.
2. Elige otro tema en la lista, o acota con país, Desde, Hasta y especie, y pulsa Calcular. El mismo valor en Desde y Hasta deja solo ese año o ese día. Si el tema tiene varios gráficos, elige cuál ver. Contraer datos oculta la tabla; la división entre tabla y gráfico se puede arrastrar.
3. No se abre ninguna conexión con `api.gbif.org` y no se escribe en MySQL.

**Alternativa.** Con el entorno activado, desde la raíz, `python src\kpi_volumen.py` (y el mismo patrón para el resto de `kpi_*.py`) imprime el tema en la consola. El recorte se escribe con `FiltroKpi` dentro del script, como en la sección 4.9 de [documentacion_del_pipeline_gbif_y_mysql_8.md](./documentacion_del_pipeline_gbif_y_mysql_8.md).

**Postcondición.** El resultado queda en la tabla y en el gráfico de la pestaña, o en la consola si se usó el script. La consola no dibuja. El porcentaje de un ranking recortado (municipios, datasets con límite, registradores) se lee sobre el total filtrado. El gráfico de territorio muestra 12 filas por nivel y el de publicadores 8; la tabla no se recorta igual.

**Lectura.** Un conteo de ocurrencias es esfuerzo de publicación. La suma de `individual_count` no es un censo. «Sin dato» entra en los porcentajes de vitalidad, sexo y fase vital.
