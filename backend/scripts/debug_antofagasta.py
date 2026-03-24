#!/usr/bin/env python3
"""Script de migración DEBUG para Antofagasta."""

import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET
from math import radians, sin, cos, sqrt, atan2
import json

BASE_DIR = Path(__file__).resolve().parents[1]
MAPAS_DIR = BASE_DIR / "data" / "mapas"
DB_PATH = BASE_DIR / "data" / "pipatzo.db"

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def parse_osmid(osmid_str):
    if osmid_str is None:
        return None
    osmid_str = str(osmid_str).strip()
    if osmid_str.startswith('['):
        try:
            arr = json.loads(osmid_str)
            return str(arr[0]) if arr else None
        except:
            pass
    return osmid_str if osmid_str else None

# Parse nodes
print("[1/4] Parseando nodos...")
nodos = {}
tree = ET.parse(str(MAPAS_DIR / "antofagasta" / "nodes.xml"))
for row in tree.getroot().findall('row'):
    osmid = row.findtext('osmid', '').strip()
    if osmid:
        try:
            lat = float(row.findtext('y', '0'))
            lon = float(row.findtext('x', '0'))
            nodos[osmid] = {'lat': lat, 'lon': lon}
        except:
            pass
print(f"✓ {len(nodos)} nodos parseados")

# Parse edges
print("[2/4] Parseando edges...")
edges = []
tree = ET.parse(str(MAPAS_DIR / "antofagasta" / "edges.xml"))
for edge in tree.getroot().findall('edge'):
    try:
        u = edge.findtext('u', '').strip()
        v = edge.findtext('v', '').strip()
        if u in nodos and v in nodos:
            dist = haversine_distance(
                nodos[u]['lat'], nodos[u]['lon'],
                nodos[v]['lat'], nodos[v]['lon']
            )
            edges.append({
                'u': u, 'v': v,
                'dist': dist,
                'k': int(edge.findtext('k', '0')),
                'osmid': parse_osmid(edge.findtext('osmid', '')),
                'nombre': edge.findtext('name', '')
            })
    except Exception as e:
        pass
print(f"✓ {len(edges)} edges parseados (válidos)")

# Connect to DB
print("[3/4] Conectando a BD...")
con = sqlite3.connect(str(DB_PATH))
cur = con.cursor()

# Insert ciudad
cur.execute("INSERT INTO ciudades (nombre) VALUES ('Antofagasta')")
con.commit()
ciudad_id = cur.lastrowid
print(f"✓ Ciudad creada con ID: {ciudad_id}")

# Insert nodos
print(f"[4/4] Insertando {len(nodos)} nodos...")
for i, (osmid, nodo_data) in enumerate(nodos.items()):
    try:
        cur.execute(
            "INSERT INTO nodos (ciudad_id, osmid, latitud, longitud) VALUES (?, ?, ?, ?)",
            (ciudad_id, osmid, nodo_data['lat'], nodo_data['lon'])
        )
    except sqlite3.IntegrityError:
        pass
    if (i+1) % 2000 == 0:
        print(f"  {i+1}/{len(nodos)} nodos insertados...")
con.commit()

# Get node mapping
print("Construyendo mapeo osmid -> db_id...")
osmid_to_id = {}
for osmid, nodo_data in nodos.items():
    cur.execute(
        "SELECT id FROM nodos WHERE ciudad_id = ? AND osmid = ?",
        (ciudad_id, osmid)
    )
    row = cur.fetchone()
    if row:
        osmid_to_id[osmid] = row[0]
print(f"✓ {len(osmid_to_id)} nodos mapeados a IDs de BD")

# Insert edges
print(f"Insertando {len(edges)} edges...")
edges_ok = 0
for i, edge in enumerate(edges):
    try:
        nodo_origen_id = osmid_to_id.get(edge['u'])
        nodo_destino_id = osmid_to_id.get(edge['v'])
        if nodo_origen_id and nodo_destino_id:
            cur.execute(
                "INSERT INTO edges (ciudad_id, nodo_origen_id, nodo_destino_id, k, osmid, nombre, distancia) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ciudad_id, nodo_origen_id, nodo_destino_id, edge['k'], edge['osmid'], edge['nombre'], edge['dist'])
            )
            edges_ok += 1
    except Exception as e:
        if i < 5:  # Log primeros errores
            print(f"  Error en edge {i}: {e}")
    if (i+1) % 5000 == 0:
        print(f"  {i+1}/{len(edges)} edges procesados ({edges_ok} OK)...")

con.commit()
print(f"✓ {edges_ok} edges insertados")

# Summary
nodos_count = cur.execute("SELECT COUNT(*) FROM nodos WHERE ciudad_id = ?", (ciudad_id,)).fetchone()[0]
edges_count = cur.execute("SELECT COUNT(*) FROM edges WHERE ciudad_id = ?", (ciudad_id,)).fetchone()[0]

print(f"\n{'='*60}")
print(f"RESULTADO FINAL:")
print(f"Antofagasta (ID={ciudad_id}): {nodos_count} nodos, {edges_count} edges")
print(f"{'='*60}")

con.close()
