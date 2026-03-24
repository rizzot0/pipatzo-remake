#!/usr/bin/env python3
"""Script para verificar estado de importaciones de ciudades."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "pipatzo.db"

con = sqlite3.connect(str(DB_PATH))
cur = con.cursor()

print("\n" + "="*80)
print("ESTADO DE IMPORTACIONES EN PIPATZO.DB")
print("="*80 + "\n")

ciudades = cur.execute("SELECT id, nombre FROM ciudades ORDER BY id").fetchall()

for ciudad_id, nombre in ciudades:
    nodos = cur.execute("SELECT COUNT(*) FROM nodos WHERE ciudad_id = ?", (ciudad_id,)).fetchone()[0]
    edges = cur.execute("SELECT COUNT(*) FROM edges WHERE ciudad_id = ?", (ciudad_id,)).fetchone()[0]
    
    if nodos == 0:
        estado = "VACIA"
    elif edges == 0:
        estado = "PARCIAL (solo nodos)"
    else:
        estado = "COMPLETA"
    
    print(f"ID {ciudad_id} | {nombre:20s} | {estado:30s} | Nodos: {nodos:7d} | Edges: {edges:7d}")

print("\n" + "="*80 + "\n")

total_nodos = cur.execute("SELECT COUNT(*) FROM nodos").fetchone()[0]
total_edges = cur.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

print(f"TOTAL GLOBAL: {total_nodos} nodos | {total_edges} edges\n")

con.close()
