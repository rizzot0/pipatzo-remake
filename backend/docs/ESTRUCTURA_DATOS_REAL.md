# ESTRUCTURA REAL DE DATOS - PIPATZO

## 📁 Ubicación de Datos

```
PIPATZO/mapas/
├── antofagasta/
│   ├── nodes.xml
│   └── edges.xml
├── coquimbo/
│   ├── nodes.xml
│   └── edges.xml
├── la_serena/
│   ├── nodes.xml
│   └── edges.xml
├── punta_arenas/
│   ├── nodes.xml
│   └── edges.xml
└── santiago/
    ├── nodes.xml
    └── edges.xml  (>50MB)
```

## 📊 Volumen de Datos

Basado en conteos estimados:

| Ciudad | Nodos | Edges | Tamaño Approx |
|--------|-------|-------|---------------|
| Coquimbo | ~10,800 | ~15,000 | ~5MB |
| La Serena | ~8,000 | ~11,000 | ~3MB |
| Antofagasta | ~6,500 | ~9,000 | ~2.5MB |
| Punta Arenas | ~3,500 | ~5,000 | ~1.5MB |
| Santiago | ~50,000+ | ~70,000+ | >50MB |
| **TOTAL** | **~80,000** | **~110,000** | **~60MB** |

---

## 🔍 Estructura Exacta de NODOS

### Archivo: `nodes.xml`

```xml
<?xml version='1.0' encoding='utf-8'?>
<data>
  <row>
    <osmid>311683695</osmid>          <!-- ID único de OpenStreetMap -->
    <y>-30.1967332</y>                <!-- LATITUD (coordenada Y) -->
    <x>-71.3897958</x>                <!-- LONGITUD (coordenada X) -->
    <street_count>2</street_count>    <!-- Número de calles conectadas -->
    <highway/>                         <!-- Tipo de carretera (puede estar vacío) -->
    <geometry>POINT (-71.3897958 -30.1967332)</geometry>  <!-- WKT format -->
  </row>
  <!-- Más filas... -->
</data>
```

### Campos de NODOS

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `osmid` | STRING(50) | ID único de OpenStreetMap | `311683695` |
| `y` | FLOAT | Latitud (coordenada Y) | `-30.1967332` |
| `x` | FLOAT | Longitud (coordenada X) | `-71.3897958` |
| `street_count` | INTEGER | Número de calles/conexiones | `2`, `3`, `4` |
| `highway` | STRING | Tipo de carretera | `residential`, `tertiary`, vacío |
| `geometry` | TEXT | Formato WKT (Well Known Text) | `POINT (lon lat)` |

**IMPORTANTE**: 
- Las coordenadas están en formato **GEO (lon, lat)** no (lat, lon)
- En la BD: almacenar como `latitud = y`, `longitud = x`
- El campo `geometry` es redundante pero útil para validación

---

## 🔗 Estructura Exacta de EDGES

### Archivo: `edges.xml`

```xml
<?xml version='1.0' encoding='utf-8'?>
<edges>
    <edge>
        <u>311683695</u>              <!-- osmid del nodo ORIGEN -->
        <v>3461418104</v>             <!-- osmid del nodo DESTINO -->
        <k>0</k>                      <!-- Índice/multiplicidad (para grafos multigrafos) -->
        <osmid>703233214</osmid>      <!-- ID de la calle/ruta en OSM -->
        <name>Ruta D-410</name>       <!-- Nombre de la calle/ruta -->
    </edge>
    <!-- Más edges... -->
</edges>
```

### Campos de EDGES

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `u` | STRING(50) | osmid del nodo origen | `311683695` |
| `v` | STRING(50) | osmid del nodo destino | `3461418104` |
| `k` | INTEGER | Multiplicidad (cuando hay múltiples edges entre 2 nodos) | `0`, `1`, `2` |
| `osmid` | STRING(50) o ARRAY | ID de la calle en OSM | `703233214` o `[28381033, 1111156749]` |
| `name` | STRING | Nombre de la calle | `Ruta D-410`, `Tongoy - Guanaqueros`, `nan` |

**NOTAS IMPORTANTES**:
- Los valores `<name>` pueden ser `nan` (strings) - se tratan como NULL
- El campo `osmid` en algunos casos puede ser un array JSON: `[28381033, 1111156749]`
- **NO hay distancia explícita** en los edges
  - Solución: Calcular distancia usando **Haversine formula** entre las coordenadas de los nodos origen y destino

---

## 📐 Cálculo de Distancias

Como los edges **no tienen distancia explícita**, debes calcularla usando la **fórmula de Haversine**:

```python
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en metros entre dos puntos (lat/lon)
    Usa la fórmula de Haversine
    """
    R = 6371000  # Radio de la Tierra en metros
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance

# Ejemplo
dist = haversine_distance(-30.1967332, -71.3897958, -30.229273, -71.4229862)
print(f"Distancia: {dist:.2f} metros")
```

---

## 🗂️ Ciudades Disponibles

### Coquimbo 🏖️
- **Ubicación**: Región de Coquimbo, norte de Chile
- **Nodos**: ~10,800
- **Edges**: ~15,000
- **Centro aprox**: (-30.30, -71.34)

### La Serena 🌅
- **Ubicación**: Capital de la Región de Coquimbo
- **Nodos**: ~8,000
- **Edges**: ~11,000
- **Centro aprox**: (-29.90, -71.25)

### Antofagasta 🏜️
- **Ubicación**: Región de Antofagasta, norte desértico
- **Nodos**: ~6,500
- **Edges**: ~9,000
- **Centro aprox**: (-23.58, -70.40)

### Punta Arenas 🧊
- **Ubicación**: Región de Magallanes, extremo sur
- **Nodos**: ~3,500
- **Edges**: ~5,000
- **Centro aprox**: (-53.16, -70.91)

### Santiago 🏙️ (GRANDE)
- **Ubicación**: Capital de Chile, Región Metropolitana
- **Nodos**: ~50,000+
- **Edges**: ~70,000+ (Archivo >50MB)
- **Centro aprox**: (-33.45, -70.67)
- **Nota**: El archivo es tan grande que VS Code no puede sincronizarlo (>50MB)

---

## ⚠️ Desafíos Técnicos

### 1. **Coordenadas invertidas (GEO vs Matemática)**
- XML usa: `<x>` = longitud, `<y>` = latitud
- Maps usan: latitud primero, longitud segundo
- Solución: En BD, renombrar: `y` → `latitud`, `x` → `longitud`

### 2. **Distancias faltantes**
- Los edges no contienen longitud/distancia
- Solución: Calcular con Haversine en el script de migración o en la aplicación

### 3. **Nombres especiales en edges**
- Algunos `<name>` contienen el string literal `"nan"`
- Algunos `<osmid>` son arrays JSON: `[123, 456]`
- Solución: Validar durante parseo, convertir "nan" a NULL

### 4. **Archivo Santiago es muy grande (>50MB)**
- No se puede procesar en memoria fácilmente
- Solución: Usar procesamiento por streaming (leer línea a línea en lugar de cargar todo)

### 5. **Grafos multigrafos**
- El campo `k` permite múltiples edges entre 2 nodos
- La mayoría tienen `k=0`, pero algunos pueden tener valores más altos
- Solución: Almacenar como `(ciudad_id, nodo_origen_id, nodo_destino_id, k)` con índice compuesto único

---

## ✅ Validaciones Recomendadas

Al migrar, verifica:

```python
# 1. Todos los osmid en edges existen en nodes
for edge in edges:
    assert edge['u'] in node_map, f"Nodo origen {edge['u']} no existe"
    assert edge['v'] in node_map, f"Nodo destino {edge['v']} no existe"

# 2. No hay valores NaN en campos críticos
for node in nodes:
    assert node['osmid'] is not None
    assert node['y'] is not None
    assert node['x'] is not None

# 3. Coordenadas están dentro de rango válido
for node in nodes:
    assert -90 <= node['y'] <= 90, f"Latitud fuera de rango: {node['y']}"
    assert -180 <= node['x'] <= 180, f"Longitud fuera de rango: {node['x']}"
```

---

## 📋 Checklist para Migración

- [ ] Parsear nodos correctamente (invertir x/y)
- [ ] Parsear edges (manejar arrays en osmid)
- [ ] Calcular distancias con Haversine
- [ ] Manejar valores "nan" en names
- [ ] Validar integridad referencial (edges → nodes)
- [ ] Insertar en orden: ciudades → nodos → edges
- [ ] Crear índices para búsqueda rápida
- [ ] Procesar Santiago con streaming (no en memoria)

---

**Documento actualizado**: Estructura real de datos PIPATZO
**Estado**: Listo para escritura del script de migración actualizado
