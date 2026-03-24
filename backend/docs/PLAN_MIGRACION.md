# PLAN DETALLADO DE MIGRACIÓN: PIPATZO JAVA → STACK MODERNO

## 🎯 OBJETIVO FINAL
Transformar un sistema monolítico de visualización de mapas en Java a una architectura moderna con:
- **Backend**: Python + FastAPI (APIs REST)
- **Base de Datos**: PostgreSQL o MySQL (SQL)
- **Frontend**: Next.js + React + React Leaflet
- **DevOps & Analytics**: BigQuery + Looker Studio
- **Testing & Qualidad**: Pytest, Jest, componentes aislados

---

## 📊 FASES DE MIGRACIÓN

### **FASE 0: PREPARACIÓN (Pre-desarrollo)**
**OBJETIVO**: Entender completamente la estructura actual

#### 0.1 Análisis de Datos Existentes
- [x] Documentar estructura Java actual (ver ANALISIS_PROYECTO.md)
- [ ] **HACER**: Localizar archivos XML de ejemplo (nodes.xml, edges.xml)
  ```bash
  # Buscar en el proyecto
  find . -name "*.xml" -type f
  find . -name "*.json" -type f
  find . -type d -name "Resources" -o -name "data" -o -name "datos"
  ```
- [ ] **HACER**: Extraer 1-2 muestras de XML para analizar la estructura exacta
- [ ] **HACER**: Documentar formato de datos (¿cuántos nodos? ¿cuántos edges? ¿están con pesos/distancias?)

#### 0.2 Definir el Nuevo Repositorio
```bash
# Crear nuevo repo en GitHub
# Nombre sugerido: PIPATZO-NextGen o similar
# Estructura:
PIPATZO-NextGen/
├── backend/          # FastAPI + Python
├── frontend/         # Next.js + React
├── database/         # Scripts SQL, esquemas
├── data-migration/   # Scripts para migrar XML → SQL
└── docs/            # Documentación
```

---

### **FASE 1: DISEÑO DE BASE DE DATOS SQL**
**DURACIÓN**: ~2-3 horas de diseño y setup
**OBJETIVO**: Crear estructura SQL que replique los datos del XML

#### 1.1 Diseñar el Esquema Relacional

```sql
-- TABLA: ciudades
-- Propósito: Almacenar información de cada ciudad
CREATE TABLE ciudades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    latitud_min FLOAT,
    latitud_max FLOAT,
    longitud_min FLOAT,
    longitud_max FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA: nodos
-- Propósito: Puntos en el mapa (intersecciones)
CREATE TABLE nodos (
    id SERIAL PRIMARY KEY,
    ciudad_id INTEGER NOT NULL REFERENCES ciudades(id) ON DELETE CASCADE,
    osmid VARCHAR(50) UNIQUE,      -- ID de OpenStreetMap
    latitud FLOAT NOT NULL,
    longitud FLOAT NOT NULL,
    nombre VARCHAR(255),  -- Opcional: nombre de la intersección
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ciudad_id, osmid)
);

-- TABLA: edges (aristas/calles)
-- Propósito: Conexiones entre nodos
CREATE TABLE edges (
    id SERIAL PRIMARY KEY,
    ciudad_id INTEGER NOT NULL REFERENCES ciudades(id) ON DELETE CASCADE,
    nodo_origen_id INTEGER NOT NULL REFERENCES nodos(id),
    nodo_destino_id INTEGER NOT NULL REFERENCES nodos(id),
    osmid VARCHAR(50),        -- ID de la calle en OSM
    nombre VARCHAR(255),      -- Nombre de la calle
    distancia FLOAT,          -- Distancia en metros
    tipo_calle VARCHAR(50),   -- "residential", "tertiary", "secondary", etc.
    bidireccional BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABLA: consultas_rutas (TELEMETRÍA)
-- Propósito: Registrar cada búsqueda de ruta para análisis
CREATE TABLE consultas_rutas (
    id SERIAL PRIMARY KEY,
    ciudad_id INTEGER NOT NULL REFERENCES ciudades(id),
    nodo_origen_id INTEGER NOT NULL REFERENCES nodos(id),
    nodo_destino_id INTEGER NOT NULL REFERENCES nodos(id),
    algoritmo VARCHAR(20),    -- "dijkstra", "a_star", etc.
    distancia_total FLOAT,
    tiempo_ejecucion_ms INTEGER,  -- ms que tardó el algoritmo
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ÍNDICES para optimizar búsquedas
CREATE INDEX idx_nodos_ciudad ON nodos(ciudad_id);
CREATE INDEX idx_nodos_coords ON nodos(latitud, longitud);
CREATE INDEX idx_edges_ciudad ON edges(ciudad_id);
CREATE INDEX idx_edges_origen ON edges(nodo_origen_id);
CREATE INDEX idx_edges_destino ON edges(nodo_destino_id);
```

#### 1.2 Setup Técnico

**OPCIÓN A: PostgreSQL (Recomendado)**
```bash
# Instalación en Windows
# Descargar: https://www.postgresql.org/download/windows/

# O usar Docker si lo tienes
docker run --name pipatzo-db \
  -e POSTGRES_USER=pipatzo_user \
  -e POSTGRES_PASSWORD=tu_password \
  -e POSTGRES_DB=pipatzo_db \
  -p 5432:5432 \
  -d postgres:15
```

**OPCIÓN B: MySQL**
```bash
# Similar a PostgreSQL, instalación local o Docker
docker run --name pipatzo-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=pipatzo_db \
  -p 3306:3306 \
  -d mysql:8.0
```

#### 1.3 Crear el Esquema en la BD
```bash
# Conectar a la BD y ejecutar el script SQL de arriba
psql -U pipatzo_user -d pipatzo_db -f schema.sql
```

---

### **FASE 2: MIGRACIÓN DE DATOS (XML → SQL)**
**DURACIÓN**: ~1-2 horas de scripting
**OBJETIVO**: Convertir archivos XML a registros SQL

#### 2.1 Script de Migración en Python

```python
# migrate_xml_to_sql.py
import xml.etree.ElementTree as ET
import psycopg2
from psycopg2.extras import execute_batch
import os

def parse_nodes_xml(filepath):
    """Leer archivo nodes.xml y extraer datos"""
    tree = ET.parse(filepath)
    root = tree.getroot()
    nodos = []
    
    for node in root.findall('node'):
        osmid = node.find('osmid').text
        lat = float(node.find('lat').text)
        lon = float(node.find('lon').text)
        nodos.append({
            'osmid': osmid,
            'latitud': lat,
            'longitud': lon
        })
    
    return nodos

def parse_edges_xml(filepath):
    """Leer archivo edges.xml y extraer datos"""
    tree = ET.parse(filepath)
    root = tree.getroot()
    edges = []
    
    for edge in root.findall('edge'):
        u = edge.find('u').text
        v = edge.find('v').text
        osmid = edge.find('osmid').text
        name = edge.find('name').text
        length = float(edge.find('length').text) if edge.find('length') is not None else None
        
        edges.append({
            'u': u,  # osmid del nodo origen
            'v': v,  # osmid del nodo destino
            'osmid': osmid,
            'nombre': name,
            'distancia': length
        })
    
    return edges

def insert_into_database(nodos, edges, ciudad_nombre):
    """Insertar datos en PostgreSQL"""
    conn = psycopg2.connect(
        host="localhost",
        database="pipatzo_db",
        user="pipatzo_user",
        password="tu_password"
    )
    cursor = conn.cursor()
    
    # 1. Insertar ciudad
    cursor.execute(
        "INSERT INTO ciudades (nombre) VALUES (%s) RETURNING id",
        (ciudad_nombre,)
    )
    ciudad_id = cursor.fetchone()[0]
    
    # 2. Insertar nodos
    nodo_osmid_to_db_id = {}
    for nodo in nodos:
        cursor.execute(
            """INSERT INTO nodos (ciudad_id, osmid, latitud, longitud) 
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (ciudad_id, nodo['osmid'], nodo['latitud'], nodo['longitud'])
        )
        nodo_id = cursor.fetchone()[0]
        nodo_osmid_to_db_id[nodo['osmid']] = nodo_id
    
    # 3. Insertar edges
    for edge in edges:
        nodo_origen_id = nodo_osmid_to_db_id.get(edge['u'])
        nodo_destino_id = nodo_osmid_to_db_id.get(edge['v'])
        
        if nodo_origen_id and nodo_destino_id:
            cursor.execute(
                """INSERT INTO edges 
                   (ciudad_id, nodo_origen_id, nodo_destino_id, osmid, nombre, distancia)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (ciudad_id, nodo_origen_id, nodo_destino_id, edge['osmid'], 
                 edge['nombre'], edge['distancia'])
            )
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✓ Migración completada para {ciudad_nombre}")
    print(f"  - Nodos insertados: {len(nodos)}")
    print(f"  - Edges insertados: {len(edges)}")

# USO
if __name__ == "__main__":
    nodos = parse_nodes_xml("datos/coquimbo_nodes.xml")
    edges = parse_edges_xml("datos/coquimbo_edges.xml")
    insert_into_database(nodos, edges, "Coquimbo")
```

#### 2.2 Ejecutar la Migración
```bash
# Asegúrate de tener los archivos XML
# python migrate_xml_to_sql.py

# Verificar en la base de datos
# psql -U pipatzo_user -d pipatzo_db
# SELECT COUNT(*) FROM nodos;
# SELECT COUNT(*) FROM edges;
```

---

### **FASE 3: BACKEND PYTHON + FASTAPI**
**DURACIÓN**: ~4-6 horas
**OBJETIVO**: Crear APIs REST que reemplacen la lógica de Java

#### 3.1 Estructura del Proyecto Backend

```
backend/
├── main.py                 # Entrada principal de FastAPI
├── requirements.txt        # Dependencias Python
├── config.py              # Configuración (DB, etc.)
├── models/
│   ├── __init__.py
│   ├── nodo.py           # Modelo Pydantic para Nodo
│   ├── edge.py           # Modelo Pydantic para Edge
│   └── ciudad.py         # Modelo Pydantic para Ciudad
├── services/
│   ├── __init__.py
│   ├── graph_service.py   # Lógica de grafos
│   ├── routing_service.py # Dijkstra, A*
│   └── ciudad_service.py  # Queries a ciudades
├── routes/
│   ├── __init__.py
│   ├── ciudades.py       # Endpoints de ciudades
│   └── rutas.py          # Endpoints de cálculo de rutas
└── utils/
    ├── __init__.py
    └── algorithms.py     # Dijkstra, A*, BFS, DFS
```

#### 3.2 Instalar Dependencias

```bash
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
psycopg2-binary==2.9.9
pydantic==2.5.0
python-dotenv==1.0.0
networkx==3.2.1  # Para gráfos
pytest==7.4.3
```

#### 3.3 Archivos Principales

**backend/models/nodo.py**
```python
from pydantic import BaseModel

class NodoBase(BaseModel):
    osmid: str
    latitud: float
    longitud: float

class NodoCreate(NodoBase):
    ciudad_id: int

class Nodo(NodoBase):
    id: int
    
    class Config:
        from_attributes = True
```

**backend/models/edge.py**
```python
from pydantic import BaseModel

class EdgeBase(BaseModel):
    nombre: str
    distancia: float
    tipo_calle: str = "unknown"

class EdgeCreate(EdgeBase):
    ciudad_id: int
    nodo_origen_id: int
    nodo_destino_id: int

class Edge(EdgeBase):
    id: int
    
    class Config:
        from_attributes = True
```

**backend/utils/algorithms.py** (DIJKSTRA)
```python
import heapq
from collections import defaultdict

def dijkstra(graph, start, end):
    """
    Algoritmo de Dijkstra para encontrar la ruta más corta
    
    Args:
        graph: dict con estructura {nodo_id: [(vecino_id, distancia), ...]}
        start: ID del nodo inicial
        end: ID del nodo final
    
    Returns:
        (distancia_total, ruta_como_lista_de_nodos)
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
            # Reconstruir ruta
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = previous[node]
            return distances[end], path[::-1]
        
        for neighbor, weight in graph[current]:
            distance = current_dist + weight
            
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current
                heapq.heappush(pq, (distance, neighbor))
    
    return float('inf'), []  # Sin ruta encontrada
```

**backend/routes/rutas.py**
```python
from fastapi import APIRouter, HTTPException
from models.nodo import Nodo
from services.routing_service import calcular_ruta

router = APIRouter(prefix="/api/rutas", tags=["rutas"])

@router.post("/calcular")
def calcular_ruta_endpoint(ciudad_id: int, nodo_origen_id: int, nodo_destino_id: int):
    """
    Calcula la ruta más corta entre dos nodos usando Dijkstra
    
    Ejemplo:
    POST /api/rutas/calcular?ciudad_id=1&nodo_origen_id=10&nodo_destino_id=250
    """
    try:
        resultado = calcular_ruta(ciudad_id, nodo_origen_id, nodo_destino_id)
        return {
            "distancia_total": resultado['distancia'],
            "ruta": resultado['nodos'],
            "num_pasos": len(resultado['nodos']),
            "tiempo_ejecucion_ms": resultado['tiempo']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**backend/main.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import ciudades, rutas

app = FastAPI(
    title="PIPATZO API",
    description="Sistema de cálculo de rutas",
    version="1.0.0"
)

# CORS (para que el frontend Next.js pueda consumir la API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(ciudades.router)
app.include_router(rutas.router)

@app.get("/")
def read_root():
    return {
        "nombre": "PIPATZO API",
        "versión": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 3.4 Ejecutar el Backend
```bash
cd backend/
pip install -r requirements.txt
python main.py
# Acceder a: http://localhost:8000/docs
```

---

### **FASE 4: FRONTEND NEXT.JS + REACT**
**DURACIÓN**: ~5-8 horas
**OBJETIVO**: Crear interfaz web moderna con mapas interactivos

#### 4.1 Estructura del Proyecto Frontend

```
frontend/
├── package.json
├── next.config.js
├── tsconfig.json
├── .env.local
├── public/
├── src/
│   ├── pages/
│   │   ├── _app.tsx
│   │   ├── index.tsx        # Página principal
│   │   └── api/             # API routes si es necesario
│   ├── components/
│   │   ├── Map.tsx          # Componente del mapa (Leaflet)
│   │   ├── SearchForm.tsx   # Búsqueda de rutas
│   │   ├── RouteDisplay.tsx # Mostrar ruta calculada
│   │   └── ...
│   ├── styles/
│   ├── utils/
│   │   └── api.ts           # Cliente HTTP para llamar al backend
│   └── ...
└── cosmos.config.js         # Config para React Cosmos
```

#### 4.2 Instalación y Setup

```bash
npx create-next-app@latest frontend --typescript

cd frontend/
npm install leaflet react-leaflet
npm install axios  # Para llamadas HTTP
npm install react-cosmos --save-dev
```

#### 4.3 Componentes Principales

**src/components/Map.tsx** (usando react-leaflet)
```typescript
'use client';

import React, { useEffect, useState } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface RoutePoint {
  id: number;
  lat: number;
  lon: number;
}

export const Map = ({ ciudadId, ruta }: { ciudadId: number; ruta: RoutePoint[] }) => {
  const [center, setCenter] = useState<[number, number]>([-29.9015, -71.253]); // Coquimbo

  useEffect(() => {
    if (ruta.length > 0) {
      const latitudes = ruta.map((p) => p.lat);
      const longitudes = ruta.map((p) => p.lon);
      const centerLat = (Math.min(...latitudes) + Math.max(...latitudes)) / 2;
      const centerLon = (Math.min(...longitudes) + Math.max(...longitudes)) / 2;
      setCenter([centerLat, centerLon]);
    }
  }, [ruta]);

  const polylinePoints = ruta.map((p) => [p.lat, p.lon] as [number, number]);

  return (
    <MapContainer center={center} zoom={13} style={{ height: '500px', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />

      {/* Marcadores de los nodos en la ruta */}
      {ruta.map((punto, idx) => (
        <Marker key={punto.id} position={[punto.lat, punto.lon]}>
          <Popup>{`Paso ${idx + 1}`}</Popup>
        </Marker>
      ))}

      {/* Polilínea de la ruta */}
      {polylinePoints.length > 1 && <Polyline positions={polylinePoints} color="blue" />}
    </MapContainer>
  );
};
```

**src/components/SearchForm.tsx**
```typescript
'use client';

import React, { useState } from 'react';
import axios from 'axios';
import { Map } from './Map';

interface RoutePoint {
  id: number;
  lat: number;
  lon: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const SearchForm = ({ ciudadId }: { ciudadId: number }) => {
  const [nodoOrigen, setNodoOrigen] = useState('');
  const [nodoDestino, setNodoDestino] = useState('');
  const [ruta, setRuta] = useState<RoutePoint[]>([]);
  const [distancia, setDistancia] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleBuscarRuta = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_URL}/api/rutas/calcular`, {
        ciudad_id: ciudadId,
        nodo_origen_id: parseInt(nodoOrigen),
        nodo_destino_id: parseInt(nodoDestino),
      });

      setRuta(response.data.ruta);
      setDistancia(response.data.distancia_total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al buscar ruta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-container">
      <h2>Buscador de Rutas</h2>
      
      <div className="form-group">
        <label>Nodo Origen:</label>
        <input
          type="number"
          value={nodoOrigen}
          onChange={(e) => setNodoOrigen(e.target.value)}
          placeholder="ID del nodo origen"
        />
      </div>

      <div className="form-group">
        <label>Nodo Destino:</label>
        <input
          type="number"
          value={nodoDestino}
          onChange={(e) => setNodoDestino(e.target.value)}
          placeholder="ID del nodo destino"
        />
      </div>

      <button onClick={handleBuscarRuta} disabled={loading}>
        {loading ? 'Buscando...' : 'Buscar Ruta'}
      </button>

      {error && <div className="error">{error}</div>}

      {ruta.length > 0 && (
        <div className="results">
          <p>Distancia total: {distancia.toFixed(2)} metros</p>
          <p>Pasos: {ruta.length}</p>
        </div>
      )}

      <Map ciudadId={ciudadId} ruta={ruta} />
    </div>
  );
};
```

**src/pages/index.tsx**
```typescript
import React from 'react';
import { SearchForm } from '@/components/SearchForm';

export default function Home() {
  return (
    <main>
      <h1>🗺️ PIPATZO - Búsqueda de Rutas</h1>
      <SearchForm ciudadId={1} />
    </main>
  );
}
```

#### 4.4 Ejecutar el Frontend
```bash
npm run dev
# http://localhost:3000
```

---

### **FASE 5: ANÁLISIS DE DATOS (BigQuery + BI)**
**DURACIÓN**: ~4-6 horas
**OBJETIVO**: Implementar telemetría y dashboards

#### 5.1 Enviar Telemetría a BigQuery

```python
# backend/services/telemetry_service.py
from google.cloud import bigquery
from datetime import datetime

def registrar_consulta_ruta(
    ciudad_id: int,
    nodo_origen_id: int,
    nodo_destino_id: int,
    distancia: float,
    tiempo_ms: int,
    algoritmo: str = "dijkstra"
):
    """Registrar una búsqueda de ruta en BigQuery"""
    client = bigquery.Client()
    
    table_id = "proyecto-gcp.dataset.consultas_rutas"
    
    rows_to_insert = [
        {
            "ciudad_id": ciudad_id,
            "nodo_origen_id": nodo_origen_id,
            "nodo_destino_id": nodo_destino_id,
            "distancia_total": distancia,
            "tiempo_ejecucion_ms": tiempo_ms,
            "algoritmo": algoritmo,
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print(f"Error al insertar en BigQuery: {errors}")
```

#### 5.2 Crear Dashboards en Looker Studio

```
Gráficos sugeridos:
1. "Rutas más buscadas" - Top 10 pares origen-destino
2. "Horarios de pico" - Número de consultas por hora
3. "Rendimiento del algoritmo" - Tiempo promedio por distancia
4. "Ciudades más consultadas" - % de búsquedas por ciudad
```

---

## ✅ CHECKLIST POR FASE

### Fase 0 ✓
- [ ] Analizar archivos XML existentes
- [ ] Documentar estructura de datos
- [ ] Crear repositorio nuevo en GitHub

### Fase 1 ✓
- [ ] Diseñar esquema SQL
- [ ] Crear base de datos (PostgreSQL/MySQL)
- [ ] Crear índices para optimización

### Fase 2 ✓
- [ ] Escribir script de migración XML → SQL
- [ ] Ejecutar migraciones para cada ciudad
- [ ] Validar integridad de datos

### Fase 3 ✓
- [ ] Crear estructura de backend FastAPI
- [ ] Implementar modelosydantic
- [ ] Implementar Dijkstra/A*
- [ ] Crear endpoints REST
- [ ] Testear con Pytest

### Fase 4 ✓
- [ ] Crear proyecto Next.js
- [ ] Implementar componentes React
- [ ] Integrar react-leaflet
- [ ] Conectar con API del backend
- [ ] Testear con React Cosmos

### Fase 5 ✓
- [ ] Configurar BigQuery
- [ ] Implementar logging de telemetría
- [ ] Crear dashboards en Looker Studio

---

## 🚀 COMANDOS RÁPIDOS (RESUMEN)

```bash
# Backend
cd backend && pip install -r requirements.txt && python main.py

# Frontend
cd frontend && npm install && npm run dev

# Base de datos
psql -U pipatzo_user -d pipatzo_db -c "SELECT COUNT(*) FROM nodos;"

# Migración
python data_migration/migrate_xml_to_sql.py
```

---

**Documento de Referencia para la Migración**
**Estado**: Listo para comenzar Fase 1
