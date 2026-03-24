import xml.etree.ElementTree as ET
import os
from pathlib import Path

mapas_dir = Path(__file__).resolve().parents[1] / "data" / "mapas"

print("\n" + "="*60)
print("ANÁLISIS DE DATOS - PIPATZO (Ciudades Chilenas)")
print("="*60 + "\n")

total_nodos = 0
total_edges = 0
ciudades_data = []

for ciudad_dir in sorted(mapas_dir.iterdir()):
    if not ciudad_dir.is_dir():
        continue
    
    ciudad = ciudad_dir.name.replace('_', ' ').title()
    nodes_file = ciudad_dir / "nodes.xml"
    edges_file = ciudad_dir / "edges.xml"
    
    nodos = 0
    edges = 0
    
    if nodes_file.exists():
        try:
            tree = ET.parse(str(nodes_file))
            root = tree.getroot()
            nodos = len(root.findall('row'))
            total_nodos += nodos
        except Exception as e:
            print(f"Error leyendo {nodes_file}: {e}")
    
    if edges_file.exists():
        try:
            tree = ET.parse(str(edges_file))
            root = tree.getroot()
            edges = len(root.findall('edge'))
            total_edges += edges
        except Exception as e:
            print(f"Error leyendo {edges_file}: {e}")
    
    ciudades_data.append((ciudad, nodos, edges))
    print(f"📍 {ciudad:20} | Nodos: {nodos:>7,} | Edges: {edges:>8,}")

print("\n" + "-"*60)
print(f"TOTAL:                | Nodos: {total_nodos:>7,} | Edges: {total_edges:>8,}")
print("="*60 + "\n")

print("💡 FORMATO DE DATOS:")
print("   - Nodos: x (lon), y (lat), osmid, street_count, geometry")
print("   - Edges: u, v, k, osmid, name")
print("="*60 + "\n")
