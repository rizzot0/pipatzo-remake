# QUICK START - MIGRACIÓN PIPATZO PASO A PASO

## 📌 RESUMEN EJECUTIVO

Tu proyecto Java actual tiene:
- ✅ Visualización de mapas (Swing)
- ✅ Carga de datos XML
- ❌ Sin base de datos
- ❌ Sin APIs
- ❌ Sin análisis de datos

**Meta**: Convertir esto a arquitectura empresarial moderna.

---

## 🎯 PASO 1: DATOS YA ENCONTRADOS ✓

✅ **¡YA ENCONTRAMOS LOS DATOS!**

Están en la carpeta:
```
c:\Users\Basti\Documents\GitHub\PIPATZO\mapas\
├── antofagasta/
├── coquimbo/
├── la_serena/
├── punta_arenas/
└── santiago/
```

### 1.1 Estructura Real de Datos

**NODOS** (nodes.xml):
```xml
<row>
  <osmid>311683695</osmid>        <!-- ID de OpenStreetMap -->
  <y>-30.1967332</y>              <!-- LATITUD -->
  <x>-71.3897958</x>              <!-- LONGITUD (nota: x=lon, y=lat) -->
  <street_count>2</street_count>  <!-- Número de calles conectadas -->
  <highway/>                       <!-- Tipo de carretera (puede estar vacío) -->
  <geometry>...</geometry>         <!-- WKT format (redundante) -->
</row>
```

**EDGES** (edges.xml):
```xml
<edge>
  <u>311683695</u>                <!-- osmid del nodo ORIGEN -->
  <v>3461418104</v>               <!-- osmid del nodo DESTINO -->
  <k>0</k>                        <!-- Multiplicidad -->
  <osmid>703233214</osmid>        <!-- ID de la calle -->
  <name>Ruta D-410</name>         <!-- Nombre de la calle -->
  <!-- ⚠️ NO HAY <length>! Calcular con Haversine -->
</edge>
```

### 1.2 Volumen de Datos

| Ciudad | Nodos | Edges | Tamaño |
|--------|-------|-------|--------|
| **Coquimbo** | ~10,800 | ~15,000 | ~5MB |
| **La Serena** | ~8,000 | ~11,000 | ~3MB |
| **Antofagasta** | ~6,500 | ~9,000 | ~2.5MB |
| **Punta Arenas** | ~3,500 | ~5,000 | ~1.5MB |
| **Santiago** | ~50,000+ | ~70,000+ | >50MB |
| **TOTAL** | **~80,000** | **~110,000** | **~60MB** |

**Ver documentación detallada**: [ESTRUCTURA_DATOS_REAL.md](ESTRUCTURA_DATOS_REAL.md)

---

## 🗄️ PASO 2: CREAR BASE DE DATOS SQL (2-3 HORAS)

### 2.1 Instalar PostgreSQL

**Opción A: Descarga directa**
```
https://www.postgresql.org/download/windows/
- Instalar con componentes por defecto
- Anotar: usuario = postgres, contraseña = (la que definas)
- Puerto = 5432
```

**Opción B: Docker (más rápido)**
```bash
# Si tienes Docker instalado:
docker run --name pipatzo-db \
  -e POSTGRES_USER=pipatzo \
  -e POSTGRES_PASSWORD=pipatzo123 \
  -e POSTGRES_DB=pipatzo_db \
  -p 5432:5432 \
  -d postgres:15
```

### 2.2 Conectar a la BD

**Con pgAdmin (GUI)**:
- Abre pgAdmin (viene con PostgreSQL)
- Conexión rápida: localhost, puerto 5432, usuario postgres
- Crear nueva BD: "pipatzo_db"

**O con comando**:
```bash
psql -U postgres -h localhost
# Adentro de psql:
CREATE DATABASE pipatzo_db;
\c pipatzo_db
```

### 2.3 Crear el esquema

Copia este SQL y ejecútalo en tu BD:

```sql
-- CIUDADES
CREATE TABLE ciudades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NODOS (puntos del mapa)
CREATE TABLE nodos (
    id SERIAL PRIMARY KEY,
    ciudad_id INTEGER REFERENCES ciudades(id),
    osmid VARCHAR(50),
    latitud FLOAT NOT NULL,
    longitud FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- EDGES (calles/conexiones)
CREATE TABLE edges (
    id SERIAL PRIMARY KEY,
    ciudad_id INTEGER REFERENCES ciudades(id),
    nodo_origen_id INTEGER REFERENCES nodos(id),
    nodo_destino_id INTEGER REFERENCES nodos(id),
    osmid VARCHAR(50),
    nombre VARCHAR(255),
    distancia FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TELEMETRÍA (para análisis después)
CREATE TABLE consultas_rutas (
    id SERIAL PRIMARY KEY,
    ciudad_id INTEGER REFERENCES ciudades(id),
    nodo_origen_id INTEGER REFERENCES nodos(id),
    nodo_destino_id INTEGER REFERENCES nodos(id),
    distancia_total FLOAT,
    tiempo_ejecucion_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ÍNDICES para velocidad
CREATE INDEX idx_nodos_ciudad ON nodos(ciudad_id);
CREATE INDEX idx_edges_ciudad ON edges(ciudad_id);
CREATE INDEX idx_edges_origen ON edges(nodo_origen_id);
CREATE INDEX idx_edges_destino ON edges(nodo_destino_id);
```

### 2.4 Verificar que funcionó

```bash
psql -U pipatzo -d pipatzo_db -c "SELECT * FROM información_tables();"
# O abrir pgAdmin y ver las tablas creadas
```

---

## 📤 PASO 3: MIGRAR DATOS XML → SQL (2-3 HORAS)

### 3.1 El script ya está creado ✓

Ya creé un script robusto de migración en:
```
c:\Users\Basti\Documents\GitHub\PIPATZO\migrate_to_postgresql.py
```

**Características del script**:
- ✅ Parsea correctamente la estructura real (invierte x/y)
- ✅ Calcula distancias con Haversine (no están en los edges)
- ✅ Maneja valores especiales (nan, arrays en osmid)
- ✅ Validación de integridad referencial
- ✅ Inserción en batch para velocidad
- ✅ Logging detallado
- ✅ Soporta procesamiento streaming

### 3.2 Instalar dependencias Python

```bash
# Instalar psycopg2 (driver para PostgreSQL)
pip install psycopg2-binary

# O si das error, intenta:
pip install psycopg2-binary==2.9.9
```

### 3.3 Ejecutar migración

```bash
# Migrar una ciudad específica
python migrate_to_postgresql.py --ciudad coquimbo

# Migrar todas las ciudades
python migrate_to_postgresql.py --all

# Ejemplo de output esperado:
# [2024-03-23 14:30:15] [INFO    ] Parseados 10826 nodos de Coquimbo
# [2024-03-23 14:30:16] [INFO    ] Parseados 15234 edges de Coquimbo
# [2024-03-23 14:30:18] [INFO    ] ✓ Insertados 10826 nodos en BD
# [2024-03-23 14:30:22] [INFO    ] ✓ Insertados 15234 edges en BD
# [2024-03-23 14:30:22] [INFO    ] ✓✓✓ MIGRACIÓN COMPLETADA: Coquimbo
```

### 3.4 Verificar la migración

```bash
# En pgAdmin o por terminal:
psql -U pipatzo -d pipatzo_db -c "SELECT COUNT(*) as total_nodos FROM nodos;"
psql -U pipatzo -d pipatzo_db -c "SELECT COUNT(*) as total_edges FROM edges;"

# Debería mostrar:
# total_nodos
# -----------
#     10826  (para Coquimbo)

# Verificar distancias calculadas
psql -U pipatzo -d pipatzo_db -c "SELECT AVG(distancia) as distancia_promedio FROM edges WHERE ciudad_id=1;"
```

**⚠️ NOTA**: Santiago es muy grande (>50MB), puede tardar 10-15 minutos en migrar

---

## 🐍 PASO 4: CREAR BACKEND PYTHON + FASTAPI (4-5 HORAS)

### 4.1 Estructura de carpetas

```bash
mkdir backend
cd backend

# Crear estructura
mkdir models services routes utils
touch main.py requirements.txt config.py
touch models/__init__.py services/__init__.py routes/__init__.py utils/__init__.py
```

### 4.2 Instalar dependencias

**requirements.txt**:
```
fastapi==0.104.1
uvicorn==0.24.0
psycopg2-binary==2.9.9
pydantic==2.5.0
python-dotenv==1.0.0
networkx==3.2.1
```

```bash
pip install -r requirements.txt
```

### 4.3 Crear modelos Pydantic

**models/nodo.py**:
```python
from pydantic import BaseModel

class Nodo(BaseModel):
    id: int
    osmid: str
    latitud: float
    longitud: float
    
    class Config:
        from_attributes = True
```

**models/edge.py**:
```python
from pydantic import BaseModel

class Edge(BaseModel):
    id: int
    nodo_origen_id: int
    nodo_destino_id: int
    distancia: float
    
    class Config:
        from_attributes = True
```

### 4.4 Implementar Dijkstra

**utils/algorithms.py**:
```python
import heapq
from typing import List, Tuple

def dijkstra(graph: dict, start: int, end: int) -> Tuple[float, List[int]]:
    """
    Algoritmo de Dijkstra
    
    Args:
        graph: {nodo_id: [(vecino_id, distancia), ...]}
        start: ID del nodo inicial
        end: ID del nodo final
    
    Returns:
        (distancia_total, lista_de_nodos_en_ruta)
    """
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous = {node: None for node in graph}
    pq = [(0, start)]
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        if current_dist > distances[current]:
            continue
        
        if current == end:
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = previous[node]
            return distances[end], path[::-1]
        
        if current in graph:
            for neighbor, weight in graph[current]:
                distance = current_dist + weight
                
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))
    
    return float('inf'), []
```

### 4.5 Endpoint principal

**main.py**:
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import time
from utils.algorithms import dijkstra

app = FastAPI(title="PIPATZO API")

# CORS para Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración BD
DB_CONFIG = {
    'host': 'localhost',
    'database': 'pipatzo_db',
    'user': 'pipatzo',
    'password': 'pipatzo123'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.get("/")
def root():
    return {"mensaje": "PIPATZO API lista"}

@app.get("/api/ciudades")
def listar_ciudades():
    """Lista todas las ciudades disponibles"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM ciudades")
    ciudades = [{'id': row[0], 'nombre': row[1]} for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"ciudades": ciudades}

@app.post("/api/rutas/calcular")
def calcular_ruta(ciudad_id: int, nodo_origen_id: int, nodo_destino_id: int):
    """Calcula la ruta más corta entre dos nodos"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Verificar que los nodos existen
        cursor.execute(
            "SELECT id FROM nodos WHERE id = %s AND ciudad_id = %s",
            (nodo_origen_id, ciudad_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Nodo origen no existe")
        
        cursor.execute(
            "SELECT id FROM nodos WHERE id = %s AND ciudad_id = %s",
            (nodo_destino_id, ciudad_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Nodo destino no existe")
        
        # 2. Cargar todos los edges de la ciudad para formar el grafo
        cursor.execute(
            """SELECT nodo_origen_id, nodo_destino_id, distancia 
               FROM edges WHERE ciudad_id = %s""",
            (ciudad_id,)
        )
        edges = cursor.fetchall()
        
        # 3. Construir grafo
        grafo = {}
        for origen_id, destino_id, distancia in edges:
            if origen_id not in grafo:
                grafo[origen_id] = []
            if destino_id not in grafo:
                grafo[destino_id] = []
            
            grafo[origen_id].append((destino_id, distancia))
        
        # 4. Ejecutar Dijkstra
        inicio = time.time()
        distancia_total, ruta_ids = dijkstra(grafo, nodo_origen_id, nodo_destino_id)
        tiempo_ms = int((time.time() - inicio) * 1000)
        
        if not ruta_ids:
            raise HTTPException(status_code=404, detail="No hay ruta disponible")
        
        # 5. Obtener coordenadas de los nodos en la ruta
        ruta_nodos = []
        for nodo_id in ruta_ids:
            cursor.execute(
                "SELECT id, latitud, longitud FROM nodos WHERE id = %s",
                (nodo_id,)
            )
            row = cursor.fetchone()
            if row:
                ruta_nodos.append({
                    'id': row[0],
                    'lat': row[1],
                    'lon': row[2]
                })
        
        # 6. Registrar en telemetría
        cursor.execute(
            """INSERT INTO consultas_rutas 
               (ciudad_id, nodo_origen_id, nodo_destino_id, distancia_total, tiempo_ejecucion_ms)
               VALUES (%s, %s, %s, %s, %s)""",
            (ciudad_id, nodo_origen_id, nodo_destino_id, distancia_total, tiempo_ms)
        )
        conn.commit()
        
        return {
            "distancia_total": distancia_total,
            "ruta": ruta_nodos,
            "num_pasos": len(ruta_nodos),
            "tiempo_ejecucion_ms": tiempo_ms
        }
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4.6 Ejecutar backend

```bash
python main.py
# Accede a: http://localhost:8000/docs
```

---

## ⚛️ PASO 5: CREAR FRONTEND NEXT.JS + REACT (4-6 HORAS)

### 5.1 Crear proyecto

```bash
npx create-next-app@latest frontend --typescript --eslint --tailwind

cd frontend
npm install leaflet react-leaflet axios
```

### 5.2 Simple página de búsqueda

**src/app/page.tsx**:
```typescript
'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import dynamic from 'next/dynamic';

const MapComponent = dynamic(() => import('@/components/Map'), { ssr: false });

interface Ruta {
  id: number;
  lat: number;
  lon: number;
}

export default function Home() {
  const [ciudades, setCiudades] = useState<any[]>([]);
  const [ciudadId, setCiudadId] = useState(1);
  const [nodoOrigen, setNodoOrigen] = useState('');
  const [nodoDestino, setNodoDestino] = useState('');
  const [ruta, setRuta] = useState<Ruta[]>([]);
  const [distancia, setDistancia] = useState(0);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    // Cargar ciudades al abrir
    axios.get(`${API_URL}/api/ciudades`)
      .then(res => setCiudades(res.data.ciudades))
      .catch(err => console.error(err));
  }, []);

  const handleBuscar = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await axios.post(`${API_URL}/api/rutas/calcular`, {
        ciudad_id: ciudadId,
        nodo_origen_id: parseInt(nodoOrigen),
        nodo_destino_id: parseInt(nodoDestino),
      });

      setRuta(res.data.ruta);
      setDistancia(res.data.distancia_total);
    } catch (error) {
      alert('Error al buscar ruta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="p-8">
      <h1 className="text-4xl font-bold mb-8">🗺️ PIPATZO</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Formulario */}
        <form onSubmit={handleBuscar} className="bg-white p-6 rounded shadow">
          <div className="mb-4">
            <label className="block font-bold mb-2">Ciudad</label>
            <select
              value={ciudadId}
              onChange={(e) => setCiudadId(parseInt(e.target.value))}
              className="w-full border p-2 rounded"
            >
              {ciudades.map(c => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="block font-bold mb-2">Nodo Origen</label>
            <input
              type="number"
              value={nodoOrigen}
              onChange={(e) => setNodoOrigen(e.target.value)}
              className="w-full border p-2 rounded"
              placeholder="ID del nodo"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block font-bold mb-2">Nodo Destino</label>
            <input
              type="number"
              value={nodoDestino}
              onChange={(e) => setNodoDestino(e.target.value)}
              className="w-full border p-2 rounded"
              placeholder="ID del nodo"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white p-2 rounded font-bold hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? 'Buscando...' : 'Buscar Ruta'}
          </button>

          {ruta.length > 0 && (
            <div className="mt-6 bg-green-100 p-4 rounded">
              <p>📍 Distancia: {distancia.toFixed(2)}m</p>
              <p>🚶 Pasos: {ruta.length}</p>
            </div>
          )}
        </form>

        {/* Mapa */}
        <MapComponent ruta={ruta} />
      </div>
    </main>
  );
}
```

**src/components/Map.tsx**:
```typescript
'use client';

import { MapContainer, TileLayer, Marker, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface RoutePoint {
  id: number;
  lat: number;
  lon: number;
}

export default function Map({ ruta }: { ruta: RoutePoint[] }) {
  const center = ruta.length > 0 
    ? [
        (Math.min(...ruta.map(p => p.lat)) + Math.max(...ruta.map(p => p.lat))) / 2,
        (Math.min(...ruta.map(p => p.lon)) + Math.max(...ruta.map(p => p.lon))) / 2
      ] as [number, number]
    : [-29.9015, -71.253] as [number, number];

  const polylinePoints = ruta.map(p => [p.lat, p.lon] as [number, number]);

  return (
    <MapContainer center={center} zoom={13} style={{ height: '500px', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap'
      />
      {ruta.map(p => (
        <Marker key={p.id} position={[p.lat, p.lon]} />
      ))}
      {polylinePoints.length > 1 && <Polyline positions={polylinePoints} color="red" />}
    </MapContainer>
  );
}
```

### 5.3 Ejecutar frontend

```bash
# Crear .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Ejecutar
npm run dev
# http://localhost:3000
```

---

## ✅ CHECKLIST FINAL

```
FASE 1: ANÁLISIS DE DATOS
  ☐ Encontrar archivos XML originales
  ☐ Analizar estructura (nodos y edges)
  ☐ Documentar volumen de datos

FASE 2: BASE DE DATOS
  ☐ Instalar PostgreSQL
  ☐ Crear esquema SQL
  ☐ Crear tablas

FASE 3: MIGRACIÓN
  ☐ Escribir script Python para migración
  ☐ Ejecutar migración
  ☐ Verificar datos en BD

FASE 4: BACKEND
  ☐ Crear proyecto FastAPI
  ☐ Implementar Dijkstra
  ☐ Crear endpoints REST
  ☐ Probar en http://localhost:8000/docs

FASE 5: FRONTEND
  ☐ Crear proyecto Next.js
  ☐ Implementar formulario
  ☐ Integrar mapa con Leaflet
  ☐ Conectar con API backend
  ☐ Probar en http://localhost:3000

FASE 6 (BONUS): ANÁLISIS
  ☐ Configurar BigQuery
  ☐ Crear dashboards Looker Studio
```

---

## 🚀 COMANDOS FINALES (PARA EJECUTAR TODO)

```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Monitoreo BD (opcional)
psql -U pipatzo -d pipatzo_db -c "SELECT * FROM consultas_rutas;"
```

---

**¡Listo para comenzar la migración!**
