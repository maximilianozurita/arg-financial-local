#!/usr/bin/env python3
"""Muestra el estado de la base de datos: series, última fecha y total de registros."""
from db import get_conn

conn = get_conn()
rows = conn.execute("""
    SELECT s.nombre, s.fuente, MAX(dp.fecha) AS ultima_fecha, COUNT(dp.id) AS total
    FROM series s
    JOIN data_points dp ON dp.serie_id = s.id
    GROUP BY s.id
    ORDER BY s.fuente, s.nombre
""").fetchall()
conn.close()

print(f"{'Nombre':<40} {'Fuente':<25} {'Última fecha':<14} {'Registros':>10}")
print("-" * 95)
for nombre, fuente, ultima, total in rows:
    print(f"{nombre:<40} {fuente:<25} {str(ultima):<14} {total:>10}")
print(f"\nTotal series: {len(rows)}")
