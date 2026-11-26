# Grafo de conocimiento: calidad del aire y BiciMAD en Madrid

Práctica bimestral 1 (entregas 1A, 1B y 1C) de la asignatura **Interoperabilidad y Explotación de Datos en Sistemas Heterogéneos**, UTPL.
Docente: Ing. Eduardo Encalada.

**Integrantes:** Gabriela Loyola, Daniel Ludeña, Suanny Mayón.

## Estructura del repositorio

| Carpeta | Contenido |
| --- | --- |
| `datos/` | Archivos reales descargados de las fuentes oficiales (28-29 de octubre de 2026) |
| `modelos/` | Diagrama del modelo entidad-relación y del esquema RDF (PNG, SVG y fuente Graphviz `.dot`) |
| `rdf/` | Esquema semántico (`esquema_madrid_aire_bici.ttl`) e instancias generadas en 1C (`instancias_madrid_aire_bici.ttl`) |
| `scripts/` | Caracterización de los datos (`analisis_fuentes.py`, 1B) y transformación a RDF (`transformacion_rdf.py`, 1C) |
| `evidencias/` | Capturas de la implementación y exploración del grafo en GraphDB (1C) |

## Archivos de datos

| Archivo | Fuente | Entidad responsable | Obtención |
| --- | --- | --- | --- |
| `datos/estaciones_calidad_aire.csv` | [Calidad del aire. Estaciones de control](https://datos.madrid.es/dataset/212629-0-estaciones-control-aire) | Ayuntamiento de Madrid | Descarga directa (CSV) |
| `datos/calidad_aire_tiempo_real_2026-10-29.csv` | [Calidad del aire. Datos en tiempo real](https://datos.madrid.es/dataset/212531-0-calidad-aire-tiempo-real) | Ayuntamiento de Madrid | Descarga directa (CSV) |
| `datos/interprete_calidad_aire.pdf` | Intérprete de ficheros de calidad del aire (documentación) | Ayuntamiento de Madrid | Descarga directa (PDF) |
| `datos/bicimad_station_information_2026-10-29.json` | [BiciMAD GBFS – station_information](https://madrid.publicbikesystem.net/customer/gbfs/v2/es/station_information) | EMT de Madrid | API JSON (GBFS 2.3) |
| `datos/distritos.csv` | [Distritos municipales de Madrid](https://datos.madrid.es/dataset/300497-0-distritos-municipales-madrid) | Ayuntamiento de Madrid | Descarga directa (CSV) |
| `datos/distritos.kml` | [Geoportal – Distritos (KML)](https://geoportal.madrid.es/fsdescargas/IDEAM_WBGEOPORTAL/LIMITES_ADMINISTRATIVOS/Distritos/Distritos_.kml) | Ayuntamiento de Madrid | Descarga directa (KML) |

## Cómo reproducir el análisis

```bash
python scripts/analisis_fuentes.py
```

Solo necesita Python 3 (biblioteca estándar). Imprime el número de registros, campos, valores faltantes,
duplicados, inconsistencias y los vínculos entre fuentes.

Para regenerar los diagramas: `dot -Tpng modelos/mer.dot -o modelos/mer.png` (requiere Graphviz).

## Cómo generar el grafo RDF (1C)

```bash
pip install rdflib tzdata
python scripts/transformacion_rdf.py
```

Lee los archivos de `datos/`, limpia los valores (espacios, decimales con coma, horas sin dato «N») y genera
`rdf/instancias_madrid_aire_bici.ttl` con 13 426 tripletas: 21 distritos, 24 estaciones de calidad del aire,
126 puntos de muestreo, 378 mediciones horarias y 678 estaciones de BiciMAD. Junto con el esquema (218 tripletas)
el grafo completo tiene 13 644 tripletas.

Para cargarlo en GraphDB se importan los dos archivos de `rdf/` en un mismo repositorio.

## Vocabularios reutilizados en el esquema

SOSA (`sosa:`), GeoSPARQL (`geo:`), Schema.org (`schema:`), Dublin Core Terms (`dcterms:`), SKOS (`skos:`) y QUDT (`qudt:`, `unit:`).
Los términos propios usan el prefijo `mab:` (`http://example.org/madrid-aire-bici/ontologia#`).

## Licencias de los datos

Datos del Ayuntamiento de Madrid: CC BY 4.0. Datos de BiciMAD: condiciones de uso de datos abiertos de la EMT de Madrid.
