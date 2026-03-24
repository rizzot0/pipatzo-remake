# ANÁLISIS COMPLETO DEL PROYECTO PIPATZO

## 📋 RESUMEN DEL PROYECTO ACTUAL

Sistema de visualización y cálculo de rutas tipo Waze, basado en **Java + Swing** que carga datos de mapas urbanos desde archivos XML o desde servidores remotos (OpenStreetMap).

---

## 🏗️ ESTRUCTURA ACTUAL DEL CÓDIGO JAVA

### **Entidades Principales**

```
1. Nodo.java
   ├─ Atributos: x, y, osmid, color, marcado
   ├─ Propósito: Representa un punto en el mapa (intersección, esquina)
   └─ Métodos: getters/setters, gestión de visualización (color, tamaño)

2. Edge.java
   ├─ Atributos: u (nodo origen), v (nodo destino), k (índice), osmid, name
   ├─ Propósito: Representa una calle/conexión entre dos nodos
   └─ Métodos: getters/setters para los atributos

3. Ciudad.java
   ├─ Atributos: xmlNodes (ruta archivo XML nodos), xmlEdges (ruta archivo XML edges)
   ├─ Propósito: Define qué ciudad se va a cargar y dónde están sus datos
   └─ Métodos: getXmlNodes(), getXmlEdges()

4. Ventana.java (GUI)
   ├─ Hereda: JPanel
   ├─ Atributos: List<Nodo>, List<Edge>, zoom, panX, panY, nodosSeleccionados[]
   ├─ Propósito: Renderiza el mapa, maneja clicks del mouse, zoom, pan
   ├─ Métodos:
   │  ├─ mousePressed(): Seleccionar nodos
   │  ├─ mouseDragged(): Pan del mapa
   │  ├─ mouseWheelMoved(): Zoom
   │  └─ paintComponent(): Dibujar nodos y edges
   └─ Características:
      ├─ Soporte para zoom y pan
      ├─ Selección de nodos por proximidad
      ├─ Última búsqueda aparente (todavía sin algoritmo Dijkstra/A*)

5. Menu.java (Orquestador Principal)
   ├─ Hereda: JFrame
   ├─ Atributos: Map<String, Nodo> nodosMap, List<Nodo> Nodos, List<Edge> Edges
   ├─ Propósito: Menú principal con pestañas para cargar datos
   ├─ Funcionalidades:
   │  ├─ "Carga Local": Abrir archivos XML locales
   │  ├─ "Carga Remota": Descargar datos de OpenStreetMap
   │  └─ "Mostrar Mapa": Renderizar la visualización
   └─ Métodos:
      ├─ BotonNodos(): Abrir diálogo para seleccionar archivo de nodos
      ├─ BotonEdges(): Abrir diálogo para seleccionar archivo de edges
      ├─ BotonMostrarMapa(): Inicializar Ventana con datos cargados

6. CiudadesProvider.java (Proveedor Remoto)
   ├─ Patrón: Singleton
   ├─ Propósito: Descargar datos de ciudades desde OpenStreetMap
   ├─ Métodos:
   │  ├─ getURLContents(): Descargar JSON plano
   │  ├─ getURLContentsZIP(): Descargar JSON comprimido (GZIP)
   │  └─ ciudad(nombre): Obtener datos de una ciudad específica
   └─ Origen de datos: Servidor OSM remoto
```

---

## 📊 FORMATO DE DATOS ACTUAL

### **Archivos XML de Nodos** (nodes.xml)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<nodes>
    <node>
        <id>123456</id>
        <osmid>456789</osmid>
        <lat>-29.9015</lat>
        <lon>-71.2530</lon>
    </node>
    <node>
        <id>123457</id>
        <osmid>456790</osmid>
        <lat>-29.9020</lat>
        <lon>-71.2540</lon>
    </node>
</nodes>
```

### **Archivos XML de Edges** (edges.xml)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<edges>
    <edge>
        <u>456789</u>          <!-- nodo origen (osmid) -->
        <v>456790</v>          <!-- nodo destino (osmid) -->
        <k>0</k>               <!-- índice/multiplicidad de edges -->
        <osmid>789123</osmid>  <!-- identificador de la calle -->
        <name>Avenida Principal</name>  <!-- nombre de la calle -->
        <length>234.56</length> <!-- distancia (si existe) -->
    </edge>
</edges>
```

### **Datos Remotos** (OpenStreetMap)
Se descargan en formato JSON/GeoJSON comprimido (GZIP)

---

## 🔄 FLUJO ACTUAL DE LA APLICACIÓN

```
Menu.java (Main)
    │
    ├─ Pestaña "Carga Local"
    │   ├─ BotonNodos() → JFileChooser → Seleccionar nodes.xml
    │   ├─ BotonEdges() → JFileChooser → Seleccionar edges.xml
    │   ├─ Parsear XML → Map<String, Nodo> nodosMap + List<Edge>
    │   └─ BotonMostrarMapa() → Ventana
    │
    ├─ Pestaña "Carga Remota"
    │   ├─ CiudadesProvider.instance()
    │   ├─ ciudad("Coquimbo") → Descargar JSON desde OSM
    │   ├─ Parsear JSON → Nodos + Edges
    │   └─ BotonMostrarMapa() → Ventana
    │
    └─ Ventana.java (JPanel)
        ├─ Renderizar nodos (círculos azules)
        ├─ Renderizar edges (líneas)
        ├─ MouseListener:
        │  ├─ Click izquierdo → Seleccionar nodo más cercano
        │  ├─ Drag → Pan del mapa (mover vista)
        │  └─ Wheel → Zoom in/out
        └─ paintComponent() → Redibujar constantemente

```

---

## ⚙️ CARACTERÍSTICAS IMPLEMENTADAS vs FALTANTES

### ✅ **IMPLEMENTADO**
- [x] Visualización gráfica del mapa (Swing)
- [x] Carga de datos desde XML local
- [x] Descarga de datos desde OpenStreetMap
- [x] Selección interactiva de nodos
- [x] Zoom y pan del mapa
- [x] Almacenamiento en memoria (List, Map, LinkedList)

### ❌ **FALTANTE**
- [ ] Algoritmo Dijkstra o A*
- [ ] Cálculo de distancia entre nodos (pesos de edges)
- [ ] Búsqueda de ruta entre dos puntos
- [ ] Persistencia en base de datos
- [ ] API REST
- [ ] Análisis de datos / telemetría
- [ ] Interfaz moderna (web)

---

## 🗂️ ARCHIVOS PRINCIPALES EN DETALLE

### **Menu.java**
- **Líneas aproximadas**: ~500+
- **Dependencias**: javax.swing.*, javax.xml.parsers.*
- **Responsabilidad**: Orquestador principal, selector de archivos, parseo XML
- **Métodos clave**:
  - `panelCargaDirectaJPanel()`: Crear UI con 3 botones
  - `BotonNodos()`: Cargar archivo nodes.xml
  - `BotonEdges()`: Cargar archivo edges.xml
  - `parseXmlNodes()`: Transformar XML → List<Nodo>
  - `parseXmlEdges()`: Transformar XML → List<Edge>

### **Ventana.java**
- **Líneas aproximadas**: ~400+
- **Dependencias**: java.awt.*, java.awt.event.*, java.util.*
- **Responsabilidad**: Renderizado gráfico y eventos del usuario
- **Métodos clave**:
  - `mousePressed()`: Manejar selección de nodos
  - `mouseDragged()`: Manejar pan
  - `mouseWheelMoved()`: Manejar zoom
  - `encontrarNodoMasCercano()`: Buscar nodo dentro de radio
  - `paintComponent()`: Redibujar mapa

### **CiudadesProvider.java**
- **Líneas aproximadas**: ~300+
- **Dependencias**: java.net.*, org.json.*, javax.xml.parsers.*
- **Responsabilidad**: Descargar datos de ciudades desde servidor
- **Métodos clave**:
  - `getURLContents()`: Descargar JSON plano
  - `getURLContentsZIP()`: Descargar JSON comprimido
  - `ciudad()`: Obtener datos completos de una ciudad

---

## 📌 CIUDADES SOPORTADAS (Presumido)

Basándome en los comentarios y estructura, el proyecto sopor ta ciudades chilenas como:
- Coquimbo
- Santiago
- (Posiblemente otras ciudades del país)

---

## 🎯 CONCLUSIONES DEL ANÁLISIS

1. **Arquitectura**: Monolítica en Swing, sin separación clara de capas
2. **Datos**: Almacenados en XML o descargados desde OpenStreetMap
3. **Lógica de negocio**: Ausente (solo visualización)
4. **Escalabilidad**: Limitada (todo en memoria, sin persistencia)
5. **Potencial**: Alto - Es una base sólida para una migración a arquitectura moderna

---

## 📋 PLAN DE MIGRACIÓN (próxima fase)

```
FASE 1: Base de Datos SQL
  ├─ Diseñar esquema (Ciudades, Nodos, Edges)
  ├─ Crear script de migración XML → SQL
  └─ Validar datos importados

FASE 2: Backend Python + FastAPI
  ├─ Crear modelos Pydantic (Nodo, Edge, Ciudad)
  ├─ Implementar endpoints REST
  ├─ Conectar a base de datos
  └─ Implementar algoritmos (Dijkstra, A*)

FASE 3: Frontend Next.js + React
  ├─ Crear componentes UI aislados (React Cosmos)
  ├─ Integrar librería de mapas (Leaflet o Mapbox)
  ├─ Consumir API del backend
  └─ Implementar búsqueda de rutas

FASE 4: Análisis de Datos (BigQuery + BI)
  ├─ Enviar telemetría a BigQuery
  ├─ Crear dashboards en Looker/Power BI
  └─ Análisis de patrones de uso

```

---

**Documento generado**: Análisis de la arquitectura actual de PIPATZO
**Estado**: Listo para migración
