"""
FASTAPI BACKEND - CON SQLITE Y SQLALCHEMY
============================================

USO:
    pip install fastapi uvicorn sqlalchemy
    python main.py
    
    Acceder a: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, event, func
from sqlalchemy.orm import sessionmaker, Session, aliased
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from contextlib import asynccontextmanager
import time
import heapq
from math import radians, sin, cos, sqrt, atan2
import os
from pathlib import Path
import sys

# Importar modelos de la migración
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scripts.migrate_to_sqlite import Base, Ciudad, Nodo, Edge, ConsultaRuta
from api.saas import SAAS_BACKEND, init_saas_db, router as saas_router

# ============================================================================
# SETUP
# ============================================================================

# Base de datos SQLite (el path se puede sobreescribir en deploy)
DB_PATH = Path(os.getenv("PIPATZO_DB", str(BACKEND_DIR / "data" / "pipatzo.db")))
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 30},
)
SessionLocal = sessionmaker(bind=engine)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

# Grafo en memoria (tuplas, sin objetos ORM) para no recargar 300k edges por request.
_GRAPH_CACHE: dict[int, dict] = {}

FRONTEND_DIST = Path(
    os.getenv("FRONTEND_DIST", str(BACKEND_DIR.parent / "frontend" / "dist"))
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_saas_db()
    yield


app = FastAPI(
    title="Plan Vial API",
    description="Cálculo de rutas urbanas sobre grafo vial (SQLite + Dijkstra)",
    version="1.1.0",
    lifespan=lifespan,
)

# En el demo one-box el frontend y la API son el mismo origen.
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "*").split(",")
    if origin.strip()
]
ALLOW_CREDENTIALS = "*" not in FRONTEND_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELOS PYDANTIC (para requests/responses)
# ============================================================================

class CiudadResponse(BaseModel):
    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)

class NodoResponse(BaseModel):
    id: int
    osmid: str
    latitud: float
    longitud: float

    model_config = ConfigDict(from_attributes=True)

class NodoCercanoResponse(NodoResponse):
    distancia_m: float

class RutaResponse(BaseModel):
    distancia_total: float
    ruta: List[NodoResponse]
    num_pasos: int
    tiempo_ejecucion_ms: int

class RutaResumenResponse(BaseModel):
    ciudad_id: int
    nodo_origen_id: int
    nodo_destino_id: int
    distancia_total: float
    tiempo_estimado_min: float
    num_pasos: int
    tiempo_ejecucion_ms: int

# ============================================================================
# ALGORITMO DIJKSTRA
# ============================================================================

def load_grafo(session: Session, ciudad_id: int):
    cached = _GRAPH_CACHE.get(ciudad_id)
    if cached is not None:
        return cached

    grafo = {}
    rows = (
        session.query(Edge.nodo_origen_id, Edge.nodo_destino_id, Edge.distancia)
        .filter(Edge.ciudad_id == ciudad_id)
        .all()
    )
    for origen_id, destino_id, distancia in rows:
        grafo.setdefault(origen_id, []).append((destino_id, distancia))

    _GRAPH_CACHE[ciudad_id] = grafo
    return grafo


def dijkstra_shortest_path(session: Session, ciudad_id: int, nodo_origen_id: int, nodo_destino_id: int):
    """
    Implementa Dijkstra para encontrar la ruta más corta
    
    Returns:
        (distancia_total, lista_de_nodos_ids)
    """
    grafo = load_grafo(session, ciudad_id)
    
    # 3. Ejecutar Dijkstra
    # Incluir nodos que solo aparecen como destino para evitar KeyError.
    nodos_grafo = set(grafo.keys())
    for vecinos in grafo.values():
        for neighbor, _ in vecinos:
            nodos_grafo.add(neighbor)

    distances = {node: float('inf') for node in nodos_grafo}
    if nodo_origen_id not in distances:
        distances[nodo_origen_id] = float('inf')
    distances[nodo_origen_id] = 0
    previous = {node: None for node in nodos_grafo}
    pq = [(0, nodo_origen_id)]
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        if current_dist > distances[current]:
            continue
        
        if current == nodo_destino_id:
            # Reconstruir ruta
            path = []
            node = nodo_destino_id
            while node is not None:
                path.append(node)
                node = previous[node]
            return distances[nodo_destino_id], path[::-1]
        
        if current in grafo:
            for neighbor, weight in grafo[current]:
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
    
    return float('inf'), []

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia entre dos coordenadas en metros."""
    r = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c

def get_nodo_or_404(session: Session, ciudad_id: int, nodo_id: int, label: str) -> Nodo:
    nodo = session.query(Nodo).filter(
        Nodo.id == nodo_id,
        Nodo.ciudad_id == ciudad_id
    ).first()
    if not nodo:
        raise HTTPException(status_code=404, detail=f"Nodo {label} no encontrado")
    return nodo

def calcular_ruta_core(session: Session, ciudad_id: int, nodo_origen_id: int, nodo_destino_id: int):
    """Valida nodos, ejecuta Dijkstra y registra telemetría."""
    get_nodo_or_404(session, ciudad_id, nodo_origen_id, "origen")
    get_nodo_or_404(session, ciudad_id, nodo_destino_id, "destino")

    tiempo_inicio = time.time()
    distancia_total, ruta_ids = dijkstra_shortest_path(
        session, ciudad_id, nodo_origen_id, nodo_destino_id
    )
    tiempo_ejecucion_ms = int((time.time() - tiempo_inicio) * 1000)

    if not ruta_ids:
        raise HTTPException(status_code=404, detail="No hay ruta disponible entre estos nodos")

    return distancia_total, ruta_ids, tiempo_ejecucion_ms

def build_ruta_nodos(session: Session, ruta_ids: List[int]) -> List[NodoResponse]:
    ruta_nodos: List[NodoResponse] = []
    for nodo_id in ruta_ids:
        nodo = session.query(Nodo).filter(Nodo.id == nodo_id).first()
        if nodo:
            ruta_nodos.append(NodoResponse(
                id=nodo.id,
                osmid=nodo.osmid,
                latitud=nodo.latitud,
                longitud=nodo.longitud
            ))
    return ruta_nodos

def estimar_tiempo_min(distancia_m: float, velocidad_kmh: float = 35.0) -> float:
    """Tiempo estimado en minutos para UI (velocidad urbana por defecto)."""
    if velocidad_kmh <= 0:
        return 0.0
    return round((distancia_m / 1000.0) / velocidad_kmh * 60.0, 2)

app.include_router(saas_router, prefix="/api")

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/api/ciudades", response_model=List[CiudadResponse])
def listar_ciudades():
    """Lista todas las ciudades disponibles"""
    session = SessionLocal()
    try:
        ciudades = session.query(Ciudad).all()
        return ciudades
    finally:
        session.close()

@app.get("/api/ciudades/{ciudad_id}/estadisticas")
def estadisticas_ciudad(ciudad_id: int):
    """Obtiene estadísticas de una ciudad"""
    session = SessionLocal()
    try:
        ciudad = session.query(Ciudad).filter(Ciudad.id == ciudad_id).first()
        if not ciudad:
            raise HTTPException(status_code=404, detail="Ciudad no encontrada")
        
        num_nodos = session.query(Nodo).filter(Nodo.ciudad_id == ciudad_id).count()
        num_edges = session.query(Edge).filter(Edge.ciudad_id == ciudad_id).count()
        
        return {
            "ciudad": ciudad.nombre,
            "id": ciudad.id,
            "num_nodos": num_nodos,
            "num_edges": num_edges,
            "distancia_promedio_m": session.query(func.avg(Edge.distancia)).filter(
                Edge.ciudad_id == ciudad_id
            ).scalar() or 0
        }
    finally:
        session.close()

@app.get("/api/ciudades/{ciudad_id}/grafo")
def grafo_ciudad(
    ciudad_id: int,
    max_edges: int = Query(25000, ge=1000, le=80000)
):
    """Entrega segmentos del grafo para dibujar el mapa propio de una ciudad."""
    session = SessionLocal()
    try:
        ciudad = session.query(Ciudad).filter(Ciudad.id == ciudad_id).first()
        if not ciudad:
            raise HTTPException(status_code=404, detail="Ciudad no encontrada")

        total_edges = session.query(Edge).filter(Edge.ciudad_id == ciudad_id).count()

        nodo_origen = aliased(Nodo)
        nodo_destino = aliased(Nodo)

        rows = session.query(
            nodo_origen.latitud,
            nodo_origen.longitud,
            nodo_destino.latitud,
            nodo_destino.longitud
        ).select_from(Edge).join(
            nodo_origen, Edge.nodo_origen_id == nodo_origen.id
        ).join(
            nodo_destino, Edge.nodo_destino_id == nodo_destino.id
        ).filter(
            Edge.ciudad_id == ciudad_id
        ).limit(max_edges).all()

        segmentos = [
            [[o_lat, o_lon], [d_lat, d_lon]]
            for o_lat, o_lon, d_lat, d_lon in rows
        ]

        if not segmentos:
            return {
                "ciudad_id": ciudad_id,
                "ciudad": ciudad.nombre,
                "total_edges": total_edges,
                "loaded_edges": 0,
                "truncated": False,
                "bounds": None,
                "segmentos": []
            }

        lats = [p[0] for seg in segmentos for p in seg]
        lons = [p[1] for seg in segmentos for p in seg]

        return {
            "ciudad_id": ciudad_id,
            "ciudad": ciudad.nombre,
            "total_edges": total_edges,
            "loaded_edges": len(segmentos),
            "truncated": total_edges > len(segmentos),
            "bounds": {
                "min_lat": min(lats),
                "max_lat": max(lats),
                "min_lon": min(lons),
                "max_lon": max(lons)
            },
            "segmentos": segmentos
        }
    finally:
        session.close()

@app.get("/api/ciudades/{ciudad_id}/nodos/buscar", response_model=List[NodoResponse])
def buscar_nodos(ciudad_id: int, q: str = Query(..., min_length=1), limite: int = Query(20, ge=1, le=100)):
    """Busca nodos por osmid para autocompletado en frontend."""
    session = SessionLocal()
    try:
        _ = session.query(Ciudad).filter(Ciudad.id == ciudad_id).first()
        patron = f"%{q.strip()}%"
        nodos = session.query(Nodo).filter(
            Nodo.ciudad_id == ciudad_id,
            Nodo.osmid.like(patron)
        ).limit(limite).all()
        return nodos
    finally:
        session.close()

@app.get("/api/ciudades/{ciudad_id}/nodos/cercanos", response_model=List[NodoCercanoResponse])
def nodos_cercanos(
    ciudad_id: int,
    latitud: float,
    longitud: float,
    radio_m: float = Query(500, gt=0, le=5000),
    limite: int = Query(20, ge=1, le=100)
):
    """Entrega nodos cercanos a una coordenada para selección por mapa/click."""
    session = SessionLocal()
    try:
        lat_rad = radians(latitud)
        delta_lat = radio_m / 111320.0
        cos_lat = cos(lat_rad)
        delta_lon = radio_m / (111320.0 * cos_lat) if abs(cos_lat) > 1e-6 else 0.01

        candidatos = session.query(Nodo).filter(
            Nodo.ciudad_id == ciudad_id,
            Nodo.latitud >= latitud - delta_lat,
            Nodo.latitud <= latitud + delta_lat,
            Nodo.longitud >= longitud - delta_lon,
            Nodo.longitud <= longitud + delta_lon
        ).all()

        resultados: List[NodoCercanoResponse] = []
        for nodo in candidatos:
            dist = haversine_distance(latitud, longitud, nodo.latitud, nodo.longitud)
            if dist <= radio_m:
                resultados.append(NodoCercanoResponse(
                    id=nodo.id,
                    osmid=nodo.osmid,
                    latitud=nodo.latitud,
                    longitud=nodo.longitud,
                    distancia_m=round(dist, 2)
                ))

        resultados.sort(key=lambda n: n.distancia_m)
        return resultados[:limite]
    finally:
        session.close()

@app.post("/api/rutas/calcular", response_model=RutaResponse)
def calcular_ruta(ciudad_id: int, nodo_origen_id: int, nodo_destino_id: int):
    """
    Calcula la ruta más corta entre dos nodos usando Dijkstra
    
    Query Parameters:
        - ciudad_id: ID de la ciudad
        - nodo_origen_id: ID del nodo origen
        - nodo_destino_id: ID del nodo destino
    
    Returns:
        {
            "distancia_total": metros,
            "ruta": [{"id": ..., "osmid": ..., "latitud": ..., "longitud": ...}],
            "num_pasos": número de nodos en la ruta,
            "tiempo_ejecucion_ms": tiempo en milisegundos
        }
    """
    session = SessionLocal()
    try:
        distancia_total, ruta_ids, tiempo_ejecucion_ms = calcular_ruta_core(
            session, ciudad_id, nodo_origen_id, nodo_destino_id
        )
        ruta_nodos = build_ruta_nodos(session, ruta_ids)
        
        return RutaResponse(
            distancia_total=distancia_total,
            ruta=ruta_nodos,
            num_pasos=len(ruta_nodos),
            tiempo_ejecucion_ms=tiempo_ejecucion_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.post("/api/rutas/calcular-resumen", response_model=RutaResumenResponse)
def calcular_ruta_resumen(ciudad_id: int, nodo_origen_id: int, nodo_destino_id: int):
    """Calcula ruta sin devolver geometría completa (ideal para cards/listados UI)."""
    session = SessionLocal()
    try:
        distancia_total, ruta_ids, tiempo_ejecucion_ms = calcular_ruta_core(
            session, ciudad_id, nodo_origen_id, nodo_destino_id
        )
        return RutaResumenResponse(
            ciudad_id=ciudad_id,
            nodo_origen_id=nodo_origen_id,
            nodo_destino_id=nodo_destino_id,
            distancia_total=distancia_total,
            tiempo_estimado_min=estimar_tiempo_min(distancia_total),
            num_pasos=len(ruta_ids),
            tiempo_ejecucion_ms=tiempo_ejecucion_ms
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/api/rutas/historial")
def historial_rutas(ciudad_id: int = None, limite: int = 100):
    """Obtiene historial de rutas consultadas (telemetría)"""
    session = SessionLocal()
    try:
        query = session.query(ConsultaRuta)
        
        if ciudad_id:
            query = query.filter(ConsultaRuta.ciudad_id == ciudad_id)
        
        consultas = query.order_by(ConsultaRuta.id.desc()).limit(limite).all()
        
        return {
            "total": len(consultas),
            "consultas": [
                {
                    "id": c.id,
                    "ciudad_id": c.ciudad_id,
                    "distancia_total": c.distancia_total,
                    "tiempo_ejecucion_ms": c.tiempo_ejecucion_ms,
                    "timestamp": c.timestamp
                }
                for c in consultas
            ]
        }
    finally:
        session.close()

@app.get("/health")
def health_check():
    """Health check para deployments"""
    return {
        "status": "OK",
        "database": "SQLite",
        "file": str(DB_PATH),
        "saas": SAAS_BACKEND,
        "frontend": (FRONTEND_DIST / "index.html").exists(),
        "cors_origins": FRONTEND_ORIGINS,
    }


def _mount_frontend():
    index = FRONTEND_DIST / "index.html"
    if not index.exists():
        @app.get("/")
        def root():
            return {
                "nombre": "Plan Vial API",
                "versión": "1.0.0",
                "docs": "/docs",
                "base_datos": "SQLite (pipatzo.db)",
            }
        return

    assets = FRONTEND_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="frontend-assets")

    @app.get("/")
    def spa_root():
        return FileResponse(index)

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health")):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


_mount_frontend()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    print("\n" + "=" * 60)
    print("Plan Vial API")
    print("=" * 60)
    print(f"\nDocs: http://localhost:{port}/docs")
    print(f"DB: {DB_PATH}")
    print("Iniciando servidor...\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
