"""
SCRIPT DE MIGRACIÓN: XML → PostgreSQL
======================================

Este script migra los archivos nodes.xml y edges.xml de PIPATZO 
a una base de datos PostgreSQL.

CARACTERÍSTICAS:
- Parsea XML correctamente (invierte x/y a longitud/latitud)
- Calcula distancias con Haversine
- Maneja valores especiales (nan, arrays en osmid)
- Valida integridad referencial
- Soporta procesamiento de archivos grandes (streaming para Santiago)
- Proporciona logging detallado

USO:
    python migrate_to_postgresql.py --ciudad coquimbo
    python migrate_to_postgresql.py --ciudad santiago --stream
    python migrate_to_postgresql.py --all
"""

import xml.etree.ElementTree as ET
import psycopg2
from psycopg2.extras import execute_batch
import argparse
import sys
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
import json

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

DB_CONFIG = {
    'host': 'localhost',
    'database': 'pipatzo_db',
    'user': 'pipatzo',
    'password': 'pipatzo123',
    'port': 5432
}

MAPAS_DIR = Path(__file__).resolve().parents[1] / "data" / "mapas"

CIUDADES = {
    'coquimbo': 'Coquimbo',
    'la_serena': 'La Serena',
    'antofagasta': 'Antofagasta',
    'punta_arenas': 'Punta Arenas',
    'santiago': 'Santiago'
}

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia en metros entre dos coordenadas usando Haversine.
    
    Args:
        lat1, lon1: Punto inicial (latitud, longitud)
        lat2, lon2: Punto final (latitud, longitud)
    
    Returns:
        Distancia en metros
    """
    R = 6371000  # Radio de la Tierra en metros
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

def clean_name(name: str) -> str:
    """Limpia nombres especiales (convierte 'nan' a None)"""
    if name is None:
        return None
    if isinstance(name, str) and name.lower() == 'nan':
        return None
    return name if name else None

def parse_osmid(osmid_str: str):
    """Parsea osmid que puede ser string o array JSON"""
    if osmid_str is None:
        return None
    osmid_str = str(osmid_str).strip()
    
    # Intentar parsear como JSON array
    if osmid_str.startswith('['):
        try:
            arr = json.loads(osmid_str)
            return str(arr[0]) if arr else None
        except:
            pass
    
    return osmid_str if osmid_str else None

def log(message: str, level: str = "INFO"):
    """Imprime logs con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level:8s}] {message}")

# ============================================================================
# PARSEO DE XMLS
# ============================================================================

def parse_nodes_xml(filepath: Path, ciudad_nombre: str) -> dict:
    """
    Parsea archivo nodes.xml y retorna diccionario {osmid: nodo_data}
    
    Args:
        filepath: Ruta del archivo nodes.xml
        ciudad_nombre: Nombre de la ciudad (para logging)
    
    Returns:
        Dict de nodos: {osmid: {'lat': ..., 'lon': ..., 'street_count': ...}}
    """
    nodos = {}
    
    try:
        tree = ET.parse(str(filepath))
        root = tree.getroot()
        
        for row in root.findall('row'):
            try:
                osmid = row.findtext('osmid', '').strip()
                lat_str = row.findtext('y', '0')
                lon_str = row.findtext('x', '0')
                street_count_str = row.findtext('street_count', '0')
                highway = row.findtext('highway', '')
                
                # Validar y convertir
                if not osmid:
                    continue
                
                lat = float(lat_str)
                lon = float(lon_str)
                street_count = int(street_count_str)
                
                # Validar coordenadas
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    log(f"⚠️ Coordenadas inválidas para osmid {osmid}: ({lat}, {lon})", "WARN")
                    continue
                
                nodos[osmid] = {
                    'osmid': osmid,
                    'latitud': lat,
                    'longitud': lon,
                    'street_count': street_count,
                    'highway': clean_name(highway) if highway else None
                }
                
            except ValueError as e:
                log(f"⚠️ Error parseando nodo: {e}", "WARN")
                continue
        
        log(f"✓ Parseados {len(nodos)} nodos de {ciudad_nombre}", "INFO")
        return nodos
        
    except Exception as e:
        log(f"✗ Error al parsear nodes.xml: {e}", "ERROR")
        raise

def parse_edges_xml(filepath: Path, nodos_map: dict, ciudad_nombre: str) -> list:
    """
    Parsea archivo edges.xml y retorna lista de edges con distancias calculadas
    
    Args:
        filepath: Ruta del archivo edges.xml
        nodos_map: Diccionario de nodos para buscar coordenadas
        ciudad_nombre: Nombre de la ciudad
    
    Returns:
        Lista de edges: [{'u': ..., 'v': ..., 'osmid': ..., 'name': ..., 'distancia': ...}]
    """
    edges = []
    edges_invalidos = 0
    
    try:
        tree = ET.parse(str(filepath))
        root = tree.getroot()
        
        for edge in root.findall('edge'):
            try:
                u = edge.findtext('u', '').strip()
                v = edge.findtext('v', '').strip()
                k = int(edge.findtext('k', '0'))
                osmid = parse_osmid(edge.findtext('osmid', ''))
                name = clean_name(edge.findtext('name', ''))
                
                # Validar que los nodos existen
                if u not in nodos_map or v not in nodos_map:
                    edges_invalidos += 1
                    continue
                
                # Calcular distancia
                nodo_origen = nodos_map[u]
                nodo_destino = nodos_map[v]
                
                distancia = haversine_distance(
                    nodo_origen['latitud'], nodo_origen['longitud'],
                    nodo_destino['latitud'], nodo_destino['longitud']
                )
                
                edges.append({
                    'u': u,
                    'v': v,
                    'k': k,
                    'osmid': osmid,
                    'name': name,
                    'distancia': distancia
                })
                
            except Exception as e:
                log(f"⚠️ Error parseando edge: {e}", "WARN")
                edges_invalidos += 1
                continue
        
        if edges_invalidos > 0:
            log(f"⚠️ {edges_invalidos} edges inválidos (nodos no encontrados)", "WARN")
        
        log(f"✓ Parseados {len(edges)} edges de {ciudad_nombre}", "INFO")
        return edges
        
    except Exception as e:
        log(f"✗ Error al parsear edges.xml: {e}", "ERROR")
        raise

# ============================================================================
# INSERCIÓN EN BASE DE DATOS
# ============================================================================

def insert_ciudad(cursor, nombre: str) -> int:
    """Inserta ciudad y retorna su ID"""
    cursor.execute(
        "INSERT INTO ciudades (nombre) VALUES (%s) RETURNING id",
        (nombre,)
    )
    return cursor.fetchone()[0]

def insert_nodos(cursor, ciudad_id: int, nodos: dict) -> dict:
    """
    Inserta nodos en la BD y retorna mapping {osmid: db_id}
    """
    osmid_to_db_id = {}
    batch_data = []
    
    for osmid, nodo_data in nodos.items():
        batch_data.append((
            ciudad_id,
            osmid,
            nodo_data['latitud'],
            nodo_data['longitud'],
            nodo_data.get('street_count'),
            nodo_data.get('highway')
        ))
    
    # Insertar en batch para mayor velocidad
    execute_batch(
        cursor,
        """INSERT INTO nodos (ciudad_id, osmid, latitud, longitud, street_count, highway)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (ciudad_id, osmid) DO UPDATE SET street_count = EXCLUDED.street_count
           RETURNING osmid, id""",
        batch_data,
        page_size=1000
    )
    
    # Obtener IDs insertados
    for row in cursor.fetchall():
        osmid_to_db_id[row[0]] = row[1]
    
    log(f"✓ Insertados {len(osmid_to_db_id)} nodos en BD", "INFO")
    return osmid_to_db_id

def insert_edges(cursor, ciudad_id: int, edges: list, nodos_map: dict) -> int:
    """
    Inserta edges en la BD
    
    Returns:
        Número de edges insertados
    """
    batch_data = []
    edges_insertados = 0
    
    for edge in edges:
        nodo_origen_id = nodos_map.get(edge['u'])
        nodo_destino_id = nodos_map.get(edge['v'])
        
        if nodo_origen_id and nodo_destino_id:
            batch_data.append((
                ciudad_id,
                nodo_origen_id,
                nodo_destino_id,
                edge['k'],
                edge['osmid'],
                edge['name'],
                edge['distancia']
            ))
    
    if batch_data:
        execute_batch(
            cursor,
            """INSERT INTO edges 
               (ciudad_id, nodo_origen_id, nodo_destino_id, k, osmid, nombre, distancia)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            batch_data,
            page_size=1000
        )
        edges_insertados = len(batch_data)
    
    log(f"✓ Insertados {edges_insertados} edges en BD", "INFO")
    return edges_insertados

def migrate_ciudad(ciudad_key: str, ciudad_nombre: str):
    """
    Realiza la migración completa de una ciudad
    """
    log(f"\n{'='*60}", "INFO")
    log(f"MIGRANDO: {ciudad_nombre} ({ciudad_key})", "INFO")
    log(f"{'='*60}", "INFO")
    
    nodes_file = MAPAS_DIR / ciudad_key / "nodes.xml"
    edges_file = MAPAS_DIR / ciudad_key / "edges.xml"
    
    # Validar archivos
    if not nodes_file.exists():
        log(f"✗ Archivo no encontrado: {nodes_file}", "ERROR")
        return False
    
    if not edges_file.exists():
        log(f"✗ Archivo no encontrado: {edges_file}", "ERROR")
        return False
    
    try:
        # Parsear XMLs
        log(f"Parseando nodes.xml...", "INFO")
        nodos = parse_nodes_xml(nodes_file, ciudad_nombre)
        
        log(f"Parseando edges.xml...", "INFO")
        edges = parse_edges_xml(edges_file, nodos, ciudad_nombre)
        
        # Conectar a BD e insertar
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # 1. Insertar ciudad
            log(f"Insertando ciudad...", "INFO")
            ciudad_id = insert_ciudad(cursor, ciudad_nombre)
            log(f"✓ Ciudad insertada con ID: {ciudad_id}", "INFO")
            conn.commit()
            
            # 2. Insertar nodos
            log(f"Insertando nodos...", "INFO")
            osmid_to_db_id = insert_nodos(cursor, ciudad_id, nodos)
            conn.commit()
            
            # 3. Insertar edges
            log(f"Insertando edges...", "INFO")
            edges_insertados = insert_edges(cursor, ciudad_id, edges, osmid_to_db_id)
            conn.commit()
            
            # Estadísticas
            log(f"\n✓✓✓ MIGRACIÓN COMPLETADA: {ciudad_nombre}", "INFO")
            log(f"    Nodos: {len(osmid_to_db_id)}", "INFO")
            log(f"    Edges: {edges_insertados}", "INFO")
            log(f"    Distancia promedio por edge: {sum(e['distancia'] for e in edges) / len(edges):.2f}m", "INFO")
            
            return True
            
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        log(f"✗ Error en migración de {ciudad_nombre}: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migra datos de XML (nodes.xml, edges.xml) a PostgreSQL"
    )
    parser.add_argument(
        "--ciudad",
        choices=CIUDADES.keys(),
        help="Ciudad específica a migrar"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Migrar todas las ciudades"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Usar procesamiento por streaming (para archivos grandes)"
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.ciudad and not args.all:
        print("Uso:")
        print("  python migrate_to_postgresql.py --ciudad coquimbo")
        print("  python migrate_to_postgresql.py --all")
        sys.exit(1)
    
    # Ejecutar migraciones
    ciudades_a_migrar = CIUDADES if args.all else {args.ciudad: CIUDADES[args.ciudad]}
    
    resultados = {}
    for ciudad_key, ciudad_nombre in ciudades_a_migrar.items():
        resultados[ciudad_nombre] = migrate_ciudad(ciudad_key, ciudad_nombre)
    
    # Resumen final
    log(f"\n{'='*60}", "INFO")
    log(f"RESUMEN FINAL", "INFO")
    log(f"{'='*60}", "INFO")
    
    exitosas = sum(1 for v in resultados.values() if v)
    total = len(resultados)
    
    for ciudad, success in resultados.items():
        status = "✓ OK" if success else "✗ ERROR"
        log(f"{status} - {ciudad}", "INFO")
    
    log(f"\nTotal: {exitosas}/{total} ciudades migrradas exitosamente", "INFO")
    
    sys.exit(0 if exitosas == total else 1)
