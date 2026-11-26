"""
Práctica bimestral 1B - Caracterización de las fuentes de datos.

Lee los archivos de la carpeta datos/ y reporta: número de registros,
campos, valores faltantes, duplicados, inconsistencias y los vínculos
entre fuentes (código de estación, cercanía geográfica y distrito).

Uso:  python scripts/analisis_fuentes.py
Requiere solo la biblioteca estándar de Python 3.
"""
import csv
import json
import re
import statistics
from collections import Counter, defaultdict
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

DATOS = Path(__file__).resolve().parent.parent / "datos"


def leer_csv(nombre):
    with open(DATOS / nombre, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def haversine_m(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * asin(sqrt(a))


def faltantes(filas):
    cols = filas[0].keys()
    return {c: sum(1 for f in filas if (f.get(c) or "").strip() == "") for c in cols}


# ---------------------------------------------------------------- distritos (F3)
def cargar_poligonos():
    texto = (DATOS / "distritos.kml").read_text(encoding="utf-8")
    poligonos = {}
    for pm in re.findall(r"<Placemark.*?</Placemark>", texto, re.S):
        cod = re.search(r"<name>(\d+)</name>", pm).group(1)
        anillos = []
        for c in re.findall(r"<coordinates>(.*?)</coordinates>", pm, re.S):
            anillos.append([tuple(map(float, p.split(",")[:2])) for p in c.split()])
        poligonos[cod] = anillos
    return poligonos


def dentro(lon, lat, anillo):
    res = False
    for (x1, y1), (x2, y2) in zip(anillo, anillo[1:] + anillo[:1]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            res = not res
    return res


def distrito_de(lon, lat, poligonos):
    for cod, anillos in poligonos.items():
        if sum(dentro(lon, lat, a) for a in anillos) % 2:
            return cod
    return None


def main():
    R = {}

    # F1a ------------------------------------------------------------------
    est = leer_csv("estaciones_calidad_aire.csv")
    R["F1a_registros"] = len(est)
    R["F1a_campos"] = len(est[0])
    R["F1a_faltantes"] = {k: v for k, v in faltantes(est).items() if v}
    R["F1a_codigos_duplicados"] = len(est) - len({e["CODIGO"] for e in est})
    R["F1a_tipos"] = Counter(e["NOM_TIPO"] for e in est)
    contaminantes = ["NO2", "SO2", "CO", "PM10", "PM2_5", "O3", "BTX"]
    R["F1a_estaciones_por_contaminante"] = {c: sum(1 for e in est if e[c].strip()) for c in contaminantes}
    # formato de las coordenadas sexagesimales (inconsistencia de formato)
    R["F1a_formatos_dms_distintos"] = sorted({
        "º" if "º" in e["LONGITUD_ETRS89"] else ("''" if "''" in e["LONGITUD_ETRS89"] else '"')
        for e in est})
    aire = {e["CODIGO"]: e for e in est}

    # F1b ------------------------------------------------------------------
    med = leer_csv("calidad_aire_tiempo_real_2026-10-29.csv")
    R["F1b_registros_filas"] = len(med)
    R["F1b_campos"] = len(med[0])
    R["F1b_estaciones"] = len({m["ESTACION"] for m in med})
    R["F1b_magnitudes"] = Counter(m["MAGNITUD"] for m in med)
    horas = [f"{i:02d}" for i in range(1, 25)]
    validos = sum(1 for m in med for h in horas if m["V" + h] == "V")
    nulos = sum(1 for m in med for h in horas if m["V" + h] == "N")
    R["F1b_valores_horarios_total"] = len(med) * 24
    R["F1b_valores_validos_V"] = validos
    R["F1b_valores_sin_dato_N"] = nulos
    R["F1b_N_con_valor_0"] = sum(1 for m in med for h in horas if m["V" + h] == "N" and m["H" + h] == "0")
    R["F1b_horas_con_dato"] = sorted({h for m in med for h in horas if m["V" + h] == "V"})
    R["F1b_fecha"] = sorted({f'{m["ANO"]}-{int(m["MES"]):02d}-{int(m["DIA"]):02d}' for m in med})
    R["F1b_duplicados_punto_muestreo"] = len(med) - len({m["PUNTO_MUESTREO"] for m in med})
    # tecnica 'A' en vez de numero en PUNTO_MUESTREO
    R["F1b_tecnica_no_numerica"] = sorted({m["PUNTO_MUESTREO"] for m in med
                                           if not m["PUNTO_MUESTREO"].split("_")[-1].isdigit()})
    # vinculo F1b -> F1a
    cod_f1b = {m["PUNTO_MUESTREO"].split("_")[0] for m in med}
    R["F1b_codigos_que_existen_en_F1a"] = len(cod_f1b & set(aire))
    R["F1a_sin_mediciones_en_F1b"] = [aire[c]["ESTACION"] for c in sorted(set(aire) - cod_f1b)]
    # consistencia: contaminantes declarados en F1a vs medidos en F1b
    mag_a_col = {"8": "NO2", "1": "SO2", "6": "CO", "10": "PM10", "9": "PM2_5", "14": "O3"}
    medido = defaultdict(set)
    for m in med:
        cod = m["PUNTO_MUESTREO"].split("_")[0]
        if m["MAGNITUD"] in mag_a_col:
            medido[cod].add(mag_a_col[m["MAGNITUD"]])
    incons = []
    for cod, e in aire.items():
        if cod not in cod_f1b:
            continue
        declarado = {c for c in mag_a_col.values() if e[c].strip()}
        if declarado != medido[cod]:
            incons.append((e["ESTACION"], sorted(declarado - medido[cod]), sorted(medido[cod] - declarado)))
    R["F1a_vs_F1b_inconsistencias"] = incons

    # F2 -------------------------------------------------------------------
    bici = json.loads((DATOS / "bicimad_station_information_2026-10-29.json").read_text(encoding="utf-8"))
    st = bici["data"]["stations"]
    R["F2_last_updated_unix"] = bici["last_updated"]
    R["F2_registros"] = len(st)
    claves = Counter(k for s in st for k in s)
    R["F2_campos_distintos"] = len(claves)
    R["F2_campos_no_presentes_en_todas"] = {k: v for k, v in claves.items() if v != len(st)}
    R["F2_ids_duplicados"] = len(st) - len({s["station_id"] for s in st})
    R["F2_nombres_duplicados"] = [n for n, c in Counter(s["name"].strip() for s in st).items() if c > 1]
    R["F2_coords_duplicadas"] = sum(c - 1 for c in Counter((s["lat"], s["lon"]) for s in st).values() if c > 1)
    R["F2_altitud_0"] = sum(1 for s in st if s["altitude"] == 0)
    R["F2_virtuales"] = sum(1 for s in st if s["is_virtual_station"])
    R["F2_capacidad_min_max_total"] = (min(s["capacity"] for s in st), max(s["capacity"] for s in st),
                                      sum(s["capacity"] for s in st))
    R["F2_nombres_con_espacios_dobles"] = sum(1 for s in st if "  " in s["name"])
    R["F2_direcciones_con_espacio_final"] = sum(1 for s in st if s["address"] != s["address"].strip())
    R["F2_config_fisica"] = Counter(s["physical_configuration"] for s in st)

    # F3 -------------------------------------------------------------------
    dis = leer_csv("distritos.csv")
    R["F3_registros_csv"] = len(dis)
    R["F3_campos"] = list(dis[0].keys())
    pol = cargar_poligonos()
    R["F3_poligonos_kml"] = len(pol)
    R["F3_codigos_csv_igual_kml"] = {d["COD_DIS"] for d in dis} == set(pol)
    nombre_dis = {d["COD_DIS"]: d["NOMBRE"] for d in dis}

    # Integración ------------------------------------------------------------
    bici_dis = Counter()
    fuera = []
    dist_min = []
    dentro_500_trafico = 0
    for s in st:
        d = distrito_de(s["lon"], s["lat"], pol)
        if d is None:
            fuera.append(s["name"])
            continue
        bici_dis[d] += 1
        cerca = min(aire.values(), key=lambda e: haversine_m(s["lat"], s["lon"], float(e["LATITUD"]), float(e["LONGITUD"])))
        dmin = haversine_m(s["lat"], s["lon"], float(cerca["LATITUD"]), float(cerca["LONGITUD"]))
        dist_min.append(dmin)
        if any(e["COD_TIPO"] == "UT" and haversine_m(s["lat"], s["lon"], float(e["LATITUD"]), float(e["LONGITUD"])) < 500
               for e in aire.values()):
            dentro_500_trafico += 1
    R["INT_bici_fuera_de_madrid"] = len(fuera)
    R["INT_bici_en_madrid"] = sum(bici_dis.values())
    R["INT_distancia_aire_mas_cercana_m"] = {
        "mediana": round(statistics.median(dist_min)),
        "min": round(min(dist_min)),
        "max": round(max(dist_min)),
        "<500m": sum(1 for x in dist_min if x < 500),
        "<1000m": sum(1 for x in dist_min if x < 1000),
    }
    R["INT_bici_a_menos_500m_de_estacion_trafico"] = dentro_500_trafico
    aire_dis = {c: distrito_de(float(e["LONGITUD"]), float(e["LATITUD"]), pol) for c, e in aire.items()}
    R["INT_distritos_sin_estacion_aire"] = [nombre_dis[c] for c in sorted(nombre_dis, key=int)
                                            if c not in aire_dis.values()]

    for k, v in R.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
