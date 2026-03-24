"""
SCRIPT DE MIGRACIÓN: XML → SQLite (CON SQLALCHEMY)
====================================================

VENTAJAS:
✓ CERO instalación - usa archivo local .db
✓ Perfecto para desarrollo y práctica
✓ SQLAlchemy es más moderno que psycopg2 raw
✓ Tipo-safe con modelos
✓ Fácil migrar después a PostgreSQL

USO:
    python migrate_to_sqlite.py --ciudad coquimbo
    python migrate_to_sqlite.py --all

RESULTADO:
    archivo: pipatzo.db (se crea automáticamente)
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
import json

# Importar SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Base de datos SQLite (archivo local, sin servidor)
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "pipatzo.db"
DB_URL = f"sqlite:///{DB_PATH.as_posix()}"
engine = create_engine(DB_URL, echo=False)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

MAPAS_DIR = BASE_DIR / "data" / "mapas"

CIUDADES = {
    'coquimbo': 'Coquimbo',
    'la_serena': 'La Serena',
    'antofagasta': 'Antofagasta',
    'punta_arenas': 'Punta Arenas',
    'santiago': 'Santiago'
}

# ============================================================================
# MODELOS SQLALCHEMY
# ============================================================================

class Ciudad(Base):
    """Tabla de ciudades"""
    __tablename__ = 'ciudades'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    
    nodos = relationship("Nodo", back_populates="ciudad", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="ciudad", cascade="all, delete-orphan")
    consultas = relationship("ConsultaRuta", back_populates="ciudad", cascade="all, delete-orphan")

class Nodo(Base):
    """Tabla de nodos (puntos del mapa)"""
    __tablename__ = 'nodos'
    
    id = Column(Integer, primary_key=True)
    ciudad_id = Column(Integer, ForeignKey('ciudades.id'), nullable=False)
    osmid = Column(String(50), nullable=False)
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    street_count = Column(Integer)
    highway = Column(String(100))
    
    ciudad = relationship("Ciudad", back_populates="nodos")
    edges_origen = relationship("Edge", foreign_keys="Edge.nodo_origen_id", back_populates="nodo_origen")
    edges_destino = relationship("Edge", foreign_keys="Edge.nodo_destino_id", back_populates="nodo_destino")
    
    __table_args__ = (
        UniqueConstraint('ciudad_id', 'osmid', name='uq_ciudad_osmid'),
        Index('idx_nodos_ciudad', 'ciudad_id'),
        Index('idx_nodos_coords', 'latitud', 'longitud'),
    )

class Edge(Base):
    """Tabla de edges (calles/conexiones)"""
    __tablename__ = 'edges'
    
    id = Column(Integer, primary_key=True)
    ciudad_id = Column(Integer, ForeignKey('ciudades.id'), nullable=False)
    nodo_origen_id = Column(Integer, ForeignKey('nodos.id'), nullable=False)
    nodo_destino_id = Column(Integer, ForeignKey('nodos.id'), nullable=False)
    k = Column(Integer, default=0)
    osmid = Column(String(50))
    nombre = Column(String(255))
    distancia = Column(Float)  # En metros (calculada con Haversine)
    
    ciudad = relationship("Ciudad", back_populates="edges")
    nodo_origen = relationship("Nodo", foreign_keys=[nodo_origen_id], back_populates="edges_origen")
    nodo_destino = relationship("Nodo", foreign_keys=[nodo_destino_id], back_populates="edges_destino")
    
    __table_args__ = (
        Index('idx_edges_ciudad', 'ciudad_id'),
        Index('idx_edges_origen', 'nodo_origen_id'),
        Index('idx_edges_destino', 'nodo_destino_id'),
    )

class ConsultaRuta(Base):
    """Tabla de telemetría (para analytics después)"""
    __tablename__ = 'consultas_rutas'
    
    id = Column(Integer, primary_key=True)
    ciudad_id = Column(Integer, ForeignKey('ciudades.id'), nullable=False)
    nodo_origen_id = Column(Integer, ForeignKey('nodos.id'), nullable=False)
    nodo_destino_id = Column(Integer, ForeignKey('nodos.id'), nullable=False)
    distancia_total = Column(Float)
    tiempo_ejecucion_ms = Column(Integer)
    timestamp = Column(String(30))
    
    ciudad = relationship("Ciudad", back_populates="consultas")

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia en metros entre dos coordenadas"""
    R = 6371000  # Radio Tierra en metros
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

def clean_name(name: str) -> str:
    """Convierte 'nan' a None"""
    if name is None:
        return None
    if isinstance(name, str) and name.lower() == 'nan':
        return None
    return name if name else None

def parse_osmid(osmid_str: str):
    """Parsea osmid (puede ser string o array JSON)"""
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

def log(message: str, level: str = "INFO"):
    """Imprime logs con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level:8s}] {message}")

# ============================================================================
# PARSEO DE XMLS
# ============================================================================

def parse_nodes_xml(filepath: Path, ciudad_nombre: str) -> dict:
    """Parsea nodes.xml"""
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
                
                if not osmid:
                    continue
                
                lat = float(lat_str)
                lon = float(lon_str)
                street_count = int(street_count_str)
                
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
    """Parsea edges.xml"""
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
                
                if u not in nodos_map or v not in nodos_map:
                    edges_invalidos += 1
                    continue
                
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

def migrate_ciudad(ciudad_key: str, ciudad_nombre: str):
    """Realiza la migración completa de una ciudad"""
    log(f"\n{'='*60}", "INFO")
    log(f"MIGRANDO: {ciudad_nombre} ({ciudad_key})", "INFO")
    log(f"{'='*60}", "INFO")
    
    nodes_file = MAPAS_DIR / ciudad_key / "nodes.xml"
    edges_file = MAPAS_DIR / ciudad_key / "edges.xml"
    
    if not nodes_file.exists() or not edges_file.exists():
        log(f"✗ Archivos no encontrados", "ERROR")
        return False
    
    try:
        # 1. Parsear XMLs
        log(f"Parseando nodes.xml...", "INFO")
        nodos = parse_nodes_xml(nodes_file, ciudad_nombre)
        
        log(f"Parseando edges.xml...", "INFO")
        edges = parse_edges_xml(edges_file, nodos, ciudad_nombre)
        
        # 2. Comenzar sesión con la BD
        session = SessionLocal()
        
        try:
            # 3. Insertar ciudad
            log(f"Insertando ciudad...", "INFO")
            ciudad = Ciudad(nombre=ciudad_nombre)
            session.add(ciudad)
            session.commit()
            log(f"✓ Ciudad insertada con ID: {ciudad.id}", "INFO")
            
            # 4. Insertar nodos
            log(f"Insertando nodos...", "INFO")
            osmid_to_db_id = {}
            
            for osmid, nodo_data in nodos.items():
                nodo = Nodo(
                    ciudad_id=ciudad.id,
                    osmid=osmid,
                    latitud=nodo_data['latitud'],
                    longitud=nodo_data['longitud'],
                    street_count=nodo_data['street_count'],
                    highway=nodo_data['highway']
                )
                session.add(nodo)
                osmid_to_db_id[osmid] = nodo
            
            # flush() asigna IDs sin commitear, permitiendo usarlos en edges
            session.flush()
            log(f"✓ Insertados {len(osmid_to_db_id)} nodos con IDs asignados", "INFO")
            
            # Commit final para guardar todo
            session.commit()
            log(f"✓ Nodos guardados en BD", "INFO")
            
            # 5. Insertar edges (usar SQL directo para mejor rendimiento)
            log(f"Insertando edges...", "INFO")
            
            # Primero: construir mapeo osmid -> db_nodo_id
            nodos_db = session.query(Nodo).filter(Nodo.ciudad_id == ciudad.id).all()
            osmid_to_node_id = {nodo.osmid: nodo.id for nodo in nodos_db}
            log(f"✓ Mapeo osmid->id construido para {len(osmid_to_node_id)} nodos", "INFO")
            
            # Segundo: preparar batch de edges con IDs válidos
            edges_batch = []
            for edge in edges:
                nodo_origen_id = osmid_to_node_id.get(edge['u'])
                nodo_destino_id = osmid_to_node_id.get(edge['v'])
                
                if nodo_origen_id and nodo_destino_id:
                    edges_batch.append((
                        ciudad.id,
                        nodo_origen_id,
                        nodo_destino_id,
                        edge['k'],
                        edge['osmid'],
                        edge['name'],
                        edge['distancia']
                    ))
            
            # Tercero: insertar en batch usando SQL directo
            if edges_batch:
                from sqlalchemy import text
                
                insert_sql = """
                INSERT INTO edges (ciudad_id, nodo_origen_id, nodo_destino_id, k, osmid, nombre, distancia)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                # Usar conexión raw para batch insert
                raw_con = engine.raw_connection()
                raw_cur = raw_con.cursor()
                raw_cur.executemany(insert_sql, edges_batch)
                raw_con.commit()
                raw_con.close()
                
                log(f"✓ Insertados {len(edges_batch)} edges en BD (batch SQL)", "INFO")
            else:
                log(f"⚠️ 0 edges válidos para insertar", "WARN")
            
            # 6. Estadísticas finales
            nodos_count = session.query(Nodo).filter(Nodo.ciudad_id == ciudad.id).count()
            edges_count = session.query(Edge).filter(Edge.ciudad_id == ciudad.id).count()
            
            log(f"\n✓✓✓ MIGRACIÓN COMPLETADA: {ciudad_nombre}", "INFO")
            log(f"    Nodos: {nodos_count}", "INFO")
            log(f"    Edges: {edges_count}", "INFO")
            if edges_count > 0:
                distancia_promedio = session.query(func.avg(Edge.distancia)).filter(
                    Edge.ciudad_id == ciudad.id
                ).scalar() or 0
                log(f"    Distancia promedio: {distancia_promedio:.2f}m", "INFO")
            
            return True
            
        finally:
            session.close()
        
    except Exception as e:
        log(f"✗ Error en migración: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    import sys
    
    # Crear todas las tablas
    log("Creando tablas en SQLite...", "INFO")
    Base.metadata.create_all(engine)
    log("✓ Tablas creadas/verificadas", "INFO")
    
    parser = argparse.ArgumentParser(
        description="Migra datos de XML a SQLite (sin necesidad de PostgreSQL)"
    )
    parser.add_argument("--ciudad", choices=CIUDADES.keys(), help="Ciudad específica a migrar")
    parser.add_argument("--all", action="store_true", help="Migrar todas las ciudades")
    
    args = parser.parse_args()
    
    if not args.ciudad and not args.all:
        print("Uso:")
        print("  python migrate_to_sqlite.py --ciudad coquimbo")
        print("  python migrate_to_sqlite.py --all")
        sys.exit(1)
    
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
    
    log(f"\nTotal: {exitosas}/{total} ciudades migradas exitosamente", "INFO")
    log(f"\n✓ Base de datos creada: pipatzo.db", "INFO")
    
    sys.exit(0 if exitosas == total else 1)
