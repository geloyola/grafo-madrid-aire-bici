"""
Práctica bimestral 1C - Transformación de los datos a RDF.

Lee los archivos de la carpeta datos/, los limpia y genera las instancias
del grafo de conocimiento siguiendo el esquema rdf/esquema_madrid_aire_bici.ttl.

Salida: rdf/instancias_madrid_aire_bici.ttl

Uso:   python scripts/transformacion_rdf.py
Requiere: Python 3.9+, rdflib y tzdata  (pip install rdflib tzdata)
"""
import csv
import json
import re
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from zoneinfo import ZoneInfo

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

# ---------------------------------------------------------------------------
# Rutas y espacios de nombres
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
SALIDA = RAIZ / "rdf" / "instancias_madrid_aire_bici.ttl"

MAB = Namespace("http://example.org/madrid-aire-bici/ontologia#")   # esquema propio
MABR = Namespace("http://example.org/madrid-aire-bici/recurso/")    # instancias
SOSA = Namespace("http://www.w3.org/ns/sosa/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
SCHEMA = Namespace("https://schema.org/")
DCTERMS = Namespace("http://purl.org/dc/terms/")

FUENTE_AIRE = URIRef("https://datos.madrid.es/dataset/212629-0-estaciones-control-aire")
FUENTE_MEDICIONES = URIRef("https://datos.madrid.es/dataset/212531-0-calidad-aire-tiempo-real")
FUENTE_BICI = URIRef("https://datos.madrid.es/dataset/900021-0-bicimad-gbfs")
FUENTE_DISTRITOS = URIRef("https://datos.madrid.es/dataset/300497-0-distritos-municipales-madrid")

ZONA_MADRID = ZoneInfo("Europe/Madrid")

# Códigos de magnitud (PDF intérprete, Anexo II) -> conceptos SKOS del esquema
CONTAMINANTES = {"1": MAB.SO2, "6": MAB.CO, "7": MAB.NO, "8": MAB.NO2, "9": MAB.PM25,
                 "10": MAB.PM10, "12": MAB.NOx, "14": MAB.O3, "20": MAB.TOL,
                 "30": MAB.BEN, "35": MAB.EBE}
TIPOS_ESTACION = {"UT": MAB.UrbanaTrafico, "UF": MAB.UrbanaFondo, "S": MAB.Suburbana}


# ---------------------------------------------------------------------------
# Funciones para construir las URI (patrón: mabr:<tipo>-<identificador>)
# ---------------------------------------------------------------------------
def uri_distrito(cod):        return MABR[f"distrito-{int(cod):02d}"]
def uri_aire(codigo):         return MABR[f"aire-{codigo}"]
def uri_bici(station_id):     return MABR[f"bici-{station_id}"]
def uri_punto(punto):         return MABR[f"pm-{punto}"]
def uri_medicion(punto, fh):  return MABR[f"med-{punto}-{fh:%Y-%m-%dT%H}"]
def uri_geometria(tipo, cod): return MABR[f"geom-{tipo}-{cod}"]


# ---------------------------------------------------------------------------
# Utilidades de limpieza y cálculo
# ---------------------------------------------------------------------------
def leer_csv(nombre):
    with open(DATOS / nombre, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def limpiar(texto):
    """Quita espacios al inicio/fin y espacios dobles."""
    return re.sub(r"\s+", " ", (texto or "")).strip()


def decimal(texto):
    """Convierte '5228245,51' o '16.4' en un literal xsd:decimal."""
    return Literal(texto.strip().replace(",", "."), datatype=XSD.decimal)


def haversine_m(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * asin(sqrt(a))


def cargar_poligonos():
    """Devuelve {codigo_distrito: [(lon, lat), ...]} a partir del KML del Geoportal."""
    texto = (DATOS / "distritos.kml").read_text(encoding="utf-8")
    poligonos = {}
    for pm in re.findall(r"<Placemark.*?</Placemark>", texto, re.S):
        cod = re.search(r"<name>(\d+)</name>", pm).group(1)
        coords = re.search(r"<coordinates>(.*?)</coordinates>", pm, re.S).group(1)
        poligonos[cod] = [tuple(map(float, p.split(",")[:2])) for p in coords.split()]
    return poligonos


def dentro(lon, lat, anillo):
    """Punto en polígono (algoritmo de ray casting)."""
    res = False
    for (x1, y1), (x2, y2) in zip(anillo, anillo[1:] + anillo[:1]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            res = not res
    return res


def distrito_de(lon, lat, poligonos):
    for cod, anillo in poligonos.items():
        if dentro(lon, lat, anillo):
            return cod
    return None


def punto_wkt(lon, lat):
    return Literal(f"POINT({lon} {lat})", datatype=GEO.wktLiteral)


def poligono_wkt(anillo):
    coords = ", ".join(f"{x} {y}" for x, y in anillo)
    return Literal(f"MULTIPOLYGON((({coords})))", datatype=GEO.wktLiteral)


# ---------------------------------------------------------------------------
# Transformación
# ---------------------------------------------------------------------------
def main():
    g = Graph()
    for prefijo, ns in [("mab", MAB), ("mabr", MABR), ("sosa", SOSA), ("geo", GEO),
                        ("schema", SCHEMA), ("dcterms", DCTERMS), ("xsd", XSD)]:
        g.bind(prefijo, ns)
    resumen = {}

    # 1. Distritos (F3: CSV + KML) -----------------------------------------
    poligonos = cargar_poligonos()
    distritos = leer_csv("distritos.csv")
    for d in distritos:
        cod = d["COD_DIS"].strip()
        s = uri_distrito(cod)
        geom = uri_geometria("distrito", f"{int(cod):02d}")
        g.add((s, RDF.type, MAB.Distrito))
        g.add((s, DCTERMS.identifier, Literal(f"{int(cod):02d}")))
        g.add((s, SCHEMA.name, Literal(limpiar(d["NOMBRE"]))))
        g.add((s, MAB.areaM2, decimal(d["AREA"])))
        g.add((s, GEO.hasGeometry, geom))
        g.add((s, DCTERMS.source, FUENTE_DISTRITOS))
        g.add((geom, RDF.type, GEO.Geometry))
        g.add((geom, GEO.asWKT, poligono_wkt(poligonos[cod])))
    resumen["Distritos"] = len(distritos)

    # 2. Estaciones de calidad del aire (F1a) -------------------------------
    estaciones = leer_csv("estaciones_calidad_aire.csv")
    coords_aire = {}
    for e in estaciones:
        codigo = e["CODIGO"].strip()
        lon, lat = float(e["LONGITUD"]), float(e["LATITUD"])
        coords_aire[codigo] = (lat, lon)
        s = uri_aire(codigo)
        geom = uri_geometria("aire", codigo)
        g.add((s, RDF.type, MAB.EstacionCalidadAire))
        g.add((s, DCTERMS.identifier, Literal(codigo)))
        g.add((s, MAB.codigoCorto, Literal(e["CODIGO_CORTO"].strip())))
        g.add((s, SCHEMA.name, Literal(limpiar(e["ESTACION"]))))
        g.add((s, SCHEMA.address, Literal(limpiar(e["DIRECCION"]))))
        g.add((s, MAB.altitudM, decimal(e["ALTITUD"])))
        fecha = datetime.strptime(e["Fecha alta"].strip(), "%d/%m/%Y").date()
        g.add((s, MAB.fechaAlta, Literal(fecha.isoformat(), datatype=XSD.date)))
        g.add((s, MAB.tipoEstacion, TIPOS_ESTACION[e["COD_TIPO"].strip()]))
        cod_dis = distrito_de(lon, lat, poligonos)
        if cod_dis:
            g.add((s, MAB.ubicadaEnDistrito, uri_distrito(cod_dis)))
        g.add((s, GEO.hasGeometry, geom))
        g.add((s, DCTERMS.source, FUENTE_AIRE))
        g.add((geom, RDF.type, GEO.Geometry))
        g.add((geom, GEO.asWKT, punto_wkt(lon, lat)))
    resumen["Estaciones de calidad del aire"] = len(estaciones)

    # 3. Puntos de muestreo y mediciones (F1b) -------------------------------
    #    Solo se crean mediciones para horas con validación "V";
    #    las horas "N" (sin dato, guardadas como 0) se descartan.
    filas = leer_csv("calidad_aire_tiempo_real_2026-10-29.csv")
    n_mediciones = n_descartadas = 0
    for f in filas:
        punto = f["PUNTO_MUESTREO"].strip()
        codigo, magnitud, tecnica = punto.split("_")
        pm = uri_punto(punto)
        contaminante = CONTAMINANTES[magnitud]
        g.add((pm, RDF.type, MAB.PuntoMuestreo))
        g.add((pm, DCTERMS.identifier, Literal(punto)))
        g.add((pm, MAB.codigoTecnica, Literal(tecnica)))
        g.add((pm, SOSA.observes, contaminante))
        g.add((pm, SOSA.isHostedBy, uri_aire(codigo)))
        g.add((uri_aire(codigo), SOSA.hosts, pm))
        dia = datetime(int(f["ANO"]), int(f["MES"]), int(f["DIA"]))
        for h in range(1, 25):
            if f[f"V{h:02d}"].strip() != "V":
                n_descartadas += 1
                continue
            fecha_hora = (dia + timedelta(hours=h)).replace(tzinfo=ZONA_MADRID)
            m = uri_medicion(punto, fecha_hora)
            g.add((m, RDF.type, MAB.Medicion))
            g.add((m, SOSA.madeBySensor, pm))
            g.add((m, SOSA.observedProperty, contaminante))
            g.add((m, SOSA.resultTime, Literal(fecha_hora.isoformat(), datatype=XSD.dateTime)))
            g.add((m, SOSA.hasSimpleResult, decimal(f[f"H{h:02d}"])))
            g.add((m, MAB.codigoValidacion, Literal("V")))
            g.add((m, DCTERMS.source, FUENTE_MEDICIONES))
            n_mediciones += 1
    resumen["Puntos de muestreo"] = len(filas)
    resumen["Mediciones (horas V)"] = n_mediciones
    resumen["Horas descartadas (N)"] = n_descartadas

    # 4. Estaciones de BiciMAD (F2) -----------------------------------------
    bici = json.loads((DATOS / "bicimad_station_information_2026-10-29.json").read_text(encoding="utf-8"))
    estaciones_bici = bici["data"]["stations"]
    fuera_madrid = 0
    for b in estaciones_bici:
        sid = str(b["station_id"]).strip()
        lat, lon = b["lat"], b["lon"]
        s = uri_bici(sid)
        geom = uri_geometria("bici", sid)
        g.add((s, RDF.type, MAB.EstacionBiciMAD))
        g.add((s, DCTERMS.identifier, Literal(sid)))
        g.add((s, MAB.numeroEstacion, Literal(str(b["obcn"]).strip())))
        g.add((s, SCHEMA.name, Literal(limpiar(b["name"]))))
        g.add((s, SCHEMA.address, Literal(limpiar(b["address"]))))
        if limpiar(b.get("post_code")):
            g.add((s, SCHEMA.postalCode, Literal(limpiar(b["post_code"]))))
        g.add((s, MAB.capacidadAnclajes, Literal(int(b["capacity"]), datatype=XSD.nonNegativeInteger)))
        g.add((s, MAB.configuracionFisica, Literal(limpiar(b["physical_configuration"]))))
        cod_dis = distrito_de(lon, lat, poligonos)
        if cod_dis:
            g.add((s, MAB.ubicadaEnDistrito, uri_distrito(cod_dis)))
        else:
            fuera_madrid += 1
        # estación de calidad del aire más cercana (distancia geodésica)
        codigo, dist = min(((c, haversine_m(lat, lon, la, lo)) for c, (la, lo) in coords_aire.items()),
                           key=lambda x: x[1])
        g.add((s, MAB.estacionAireMasCercana, uri_aire(codigo)))
        g.add((s, MAB.distanciaEstacionAireM, Literal(str(round(dist)), datatype=XSD.decimal)))
        g.add((s, GEO.hasGeometry, geom))
        g.add((s, DCTERMS.source, FUENTE_BICI))
        g.add((geom, RDF.type, GEO.Geometry))
        g.add((geom, GEO.asWKT, punto_wkt(lon, lat)))
    resumen["Estaciones BiciMAD"] = len(estaciones_bici)
    resumen["Estaciones BiciMAD fuera de Madrid (sin distrito)"] = fuera_madrid

    # 5. Serialización -------------------------------------------------------
    g.serialize(destination=SALIDA, format="turtle", encoding="utf-8")
    print("Instancias generadas:")
    for k, v in resumen.items():
        print(f"  {k}: {v}")
    print(f"Archivo: {SALIDA.relative_to(RAIZ)}")
    print(f"Total de tripletas: {len(g)}")


if __name__ == "__main__":
    main()
