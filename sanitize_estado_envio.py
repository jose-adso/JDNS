#!/usr/bin/env python3
"""
Script seguro para sanear valores no permitidos en ventas_factura.estado_envio.
Crea una copia de seguridad de instance/flaskdb.sqlite y cambia valores mapeados.

Por defecto mapea: 'enviado' -> 'pagado'
Ejecutar desde la raíz del proyecto:
    python sanitize_estado_envio.py
"""
import os
import shutil
import sqlite3
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, 'instance', 'flaskdb.sqlite')

MAPPING = {
    'enviado': 'pagado',
}

if not os.path.exists(DB_PATH):
    print(f"Base de datos no encontrada en {DB_PATH}")
    sys.exit(1)

backup_path = DB_PATH + '.bak'
shutil.copy2(DB_PATH, backup_path)
print(f"Backup creado: {backup_path}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Valores actuales en ventas_factura.estado_envio:")
for row in cur.execute("SELECT estado_envio, COUNT(*) FROM ventas_factura GROUP BY estado_envio").fetchall():
    print(f"  {row[0]!r}: {row[1]}")

# Aplicar mapeos
total_changes = 0
for bad, good in MAPPING.items():
    cur.execute("SELECT COUNT(*) FROM ventas_factura WHERE estado_envio = ?", (bad,))
    count = cur.fetchone()[0]
    if count:
        print(f"Mapeando {count} filas: {bad} -> {good}")
        cur.execute("UPDATE ventas_factura SET estado_envio = ? WHERE estado_envio = ?", (good, bad))
        total_changes += count

conn.commit()

print(f"Total filas modificadas: {total_changes}")

print("Valores finales en ventas_factura.estado_envio:")
for row in cur.execute("SELECT estado_envio, COUNT(*) FROM ventas_factura GROUP BY estado_envio").fetchall():
    print(f"  {row[0]!r}: {row[1]}")

conn.close()
print("Saneamiento completado.")
