# Grafo de conocimiento: calidad del aire y BiciMAD en Madrid

Práctica bimestral 1 (entregas 1A y 1B) de la asignatura **Interoperabilidad y Explotación de Datos en Sistemas Heterogéneos**, UTPL.
Docente: Ing. Eduardo Encalada.

**Integrantes:** Gabriela Loyola, Daniel Ludeña, Suanny Mayón.

## Estructura del repositorio

| Carpeta | Contenido |
| --- | --- |
| `datos/` | Archivos reales descargados de las fuentes oficiales (28-29 de octubre de 2026) |
| `modelos/` | Diagrama del modelo entidad-relación y del esquema RDF (PNG, SVG y fuente Graphviz `.dot`) |
| `rdf/` | Esquema semántico en Turtle (`esquema_madrid_aire_bici.ttl`) |
| `scripts/` | Script de caracterización de los datos (`analisis_fuentes.py`) |

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

## Vocabularios reutilizados en el esquema

SOSA (`sosa:`), GeoSPARQL (`geo:`), Schema.org (`schema:`), Dublin Core Terms (`dcterms:`), SKOS (`skos:`) y QUDT (`qudt:`, `unit:`).
Los términos propios usan el prefijo `mab:` (`http://example.org/madrid-aire-bici/ontologia#`).

## Licencias de los datos

Datos del Ayuntamiento de Madrid: CC BY 4.0. Datos de BiciMAD: condiciones de uso de datos abiertos de la EMT de Madrid.
