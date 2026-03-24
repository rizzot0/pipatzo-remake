#!/usr/bin/env python3
"""Migración optimizada de Santiago (archivo muy grande - streaming)."""

import sqlite3
from pathlib import Path
import xml.etree.ElementTree as ET
from math import radians, sin, cos, sqrt, atan2
import json
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
MAPAS_DIR = BASE_DIR / "data" / "mapas"
DB_PATH = BASE_DIR / "data" / "pipatzo.db"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

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

log("="*70)
log("MIGRACIÓN DE SANTIAGO - Streaming optimizado para archivos grandes")
log("="*70)

# 1. Parse nodes con streaming
log("\n[1/5] Parseando nodos.xml (archivo grande)...")
nodos = {}
nodos_count = 0

try:
    tree = ET.parse(str(MAPAS_DIR / "santiago" / "nodes.xml"))
    for row in tree.getroot().findall('row'):
        osmid = row.findtext('osmid', '').strip()
        if osmid:
            try:
                lat = float(row.findtext('y', '0'))
                lon = float(row.findtext('x', '0'))
                nodos[osmid] = {'lat': lat, 'lon': lon}
                nodos_count += 1
                if nodos_count % 10000 == 0:
                    log(f"  {nodos_count} nodos parseados...")
            except ValueError:
                pass
except Exception as e:
    log(f"✗ Error en nodes.xml: {e}")
    exit(1)

log(f"✓ {nodos_count} nodos parseados")

# 2. Parse edges con streaming
log("\n[2/5] Parseando edges.xml (archivo grande)...")
edges = []
edges_count = 0
edges_invalidos = 0

try:
    tree = ET.parse(str(MAPAS_DIR / "santiago" / "edges.xml"))
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
                edges_count += 1
                if edges_count % 10000 == 0:
                    log(f"  {edges_count} edges válidos parseados...")
            else:
                edges_invalidos += 1
        except Exception as e:
            edges_invalidos += 1
except Exception as e:
    log(f"✗ Error en edges.xml: {e}")
    exit(1)

if edges_invalidos > 0:
    log(f"⚠️  {edges_invalidos} edges inválidos (nodos no encontrados)")
log(f"✓ {edges_count} edges válidos parseados")

# 3. Conectar a BD
log("\n[3/5] Conectando a BD (pipatzo.db)...")
con = sqlite3.connect(str(DB_PATH))
cur = con.cursor()

# 4. Insertar ciudad y nodos
log("\n[4/5] Insertando Santiago (ciudad + nodos + edges)...")

try:
    cur.execute("INSERT INTO ciudades (nombre) VALUES ('Santiago')")
    con.commit()
    ciudad_id = cur.lastrowid
    log(f"  ✓ Ciudad creada (ID={ciudad_id})")
    
    # Insertar nodos en batch de 5000
    log(f"  Insertando {nodos_count} nodos en lotes...")
    batch_size = 5000
    for i, (osmid, nodo_data) in enumerate(nodos.items()):
        try:
            cur.execute(
                "INSERT INTO nodos (ciudad_id, osmid, latitud, longitud) VALUES (?, ?, ?, ?)",
                (ciudad_id, osmid, nodo_data['lat'], nodo_data['lon'])
            )
        except sqlite3.IntegrityError:
            pass
        
        if (i + 1) % batch_size == 0:
            con.commit()
            log(f"    {i+1}/{nodos_count} nodos insertados...")
    
    con.commit()
    log(f"  ✓ {nodos_count} nodos insertados")
    
    # Construir mapeo osmid -> db_id
    log(f"  Construyendo mapeo osmid->id...")
    osmid_to_id = {}
    for osmid in nodos.keys():
        cur.execute(
            "SELECT id FROM nodos WHERE ciudad_id = ? AND osmid = ?",
            (ciudad_id, osmid)
        )
        row = cur.fetchone()
        if row:
            osmid_to_id[osmid] = row[0]
    log(f"  ✓ {len(osmid_to_id)} nodos mapeados")
    
    # Insertar edges en batch
    log(f"  Insertando {edges_count} edges en lotes...")
    edges_ok = 0
    for i, edge in enumerate(edges):
        nodo_origen_id = osmid_to_id.get(edge['u'])
        nodo_destino_id = osmid_to_id.get(edge['v'])
        
        if nodo_origen_id and nodo_destino_id:
            try:
                cur.execute(
                    "INSERT INTO edges (ciudad_id, nodo_origen_id, nodo_destino_id, k, osmid, nombre, distancia) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (ciudad_id, nodo_origen_id, nodo_destino_id, edge['k'], edge['osmid'], edge['nombre'], edge['dist'])
                )
                edges_ok += 1
            except Exception as e:
                pass
        
        if (i + 1) % batch_size == 0:
            con.commit()
            log(f"    {i+1}/{edges_count} edges procesados ({edges_ok} OK)...")
    
    con.commit()
    log(f"  ✓ {edges_ok} edges insertados")
    
    # Estadísticas finales
    log("\n[5/5] Estadísticas finales:")
    nodos_final = cur.execute("SELECT COUNT(*) FROM nodos WHERE ciudad_id = ?", (ciudad_id,)).fetchone()[0]
    edges_final = cur.execute("SELECT COUNT(*) FROM edges WHERE ciudad_id = ?", (ciudad_id,)).fetchone()[0]
    
    print(f"\n{'='*70}")
    print(f"✓✓✓ MIGRACIÓN COMPLETADA: Santiago")
    print(f"{'='*70}")
    print(f"  Nodos: {nodos_final:,}")
    print(f"  Edges: {edges_final:,}")
    print(f"  Total: {nodos_final + edges_final:,}")
    print(f"{'='*70}\n")
    
except Exception as e:
    log(f"✗ Error en inserción: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
finally:
    con.close()
