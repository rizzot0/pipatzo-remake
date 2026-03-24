#!/usr/bin/env python3
"""Script para resetear ciudades específicas de la BD antes de reimportar."""

import sqlite3
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Uso: python reset_ciudades.py <ciudad1> [<ciudad2> ...]")
    print("Ejemplo: python reset_ciudades.py la_serena antofagasta")
    sys.exit(1)

ciudades_to_reset = sys.argv[1:]
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "pipatzo.db"

try:
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    
    for ciudad_nombre in ciudades_to_reset:
        ciudad_nombre_title = ciudad_nombre.replace('_', ' ').title()
        
        # Obtener ID
        cur.execute("SELECT id FROM ciudades WHERE nombre = ?", (ciudad_nombre_title,))
        result = cur.fetchone()
        
        if not result:
            print(f"⚠️  {ciudad_nombre_title} no encontrada en BD")
            continue
        
        ciudad_id = result[0]
        
        # Eliminar edges y nodos
        cur.execute("DELETE FROM edges WHERE ciudad_id = ?", (ciudad_id,))
        edges_deleted = cur.rowcount
        
        cur.execute("DELETE FROM nodos WHERE ciudad_id = ?", (ciudad_id,))
        nodos_deleted = cur.rowcount
        
        cur.execute("DELETE FROM ciudades WHERE id = ?", (ciudad_id,))
        
        con.commit()
        
        print(f"✓ {ciudad_nombre_title} limpiada: {nodos_deleted} nodos, {edges_deleted} edges eliminados")
    
    con.close()
    print("\n✓ Reset completado")

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
