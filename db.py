"""
SQLite database setup and helpers.
Schema:
  series      — metadata de cada serie temporal
  data_points — (serie_id, fecha, valor) con UNIQUE(serie_id, fecha)
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "db" / "data.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS series (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre              TEXT NOT NULL,
            fuente              TEXT NOT NULL,
            categoria           TEXT NOT NULL,
            unidad              TEXT,
            frecuencia          TEXT,
            descripcion         TEXT,
            ultima_actualizacion TEXT,
            UNIQUE(nombre, fuente)
        );

        CREATE TABLE IF NOT EXISTS data_points (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            serie_id INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
            fecha    TEXT NOT NULL,
            valor    REAL NOT NULL,
            UNIQUE(serie_id, fecha)
        );

        CREATE INDEX IF NOT EXISTS idx_dp_serie_fecha
            ON data_points(serie_id, fecha);
    """)
    conn.commit()


def get_or_create_serie(
    conn: sqlite3.Connection,
    nombre: str,
    fuente: str,
    categoria: str,
    unidad: str = "",
    frecuencia: str = "diaria",
    descripcion: str = "",
) -> int:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    conn.execute("""
        INSERT INTO series(nombre, fuente, categoria, unidad, frecuencia, descripcion, ultima_actualizacion)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(nombre, fuente) DO UPDATE SET ultima_actualizacion=excluded.ultima_actualizacion
    """, (nombre, fuente, categoria, unidad, frecuencia, descripcion, now))
    conn.commit()

    row = conn.execute(
        "SELECT id FROM series WHERE nombre=? AND fuente=?", (nombre, fuente)
    ).fetchone()
    return row[0]


def upsert_data_points(
    conn: sqlite3.Connection,
    serie_id: int,
    points: list[tuple],  # list of (date, Decimal)
) -> int:
    """Insert new points, update valor if fecha already exists. Returns count of new rows."""
    existing = {
        row[0]
        for row in conn.execute(
            "SELECT fecha FROM data_points WHERE serie_id=?", (serie_id,)
        )
    }
    new_count = 0
    rows = []
    for fecha, valor in points:
        fecha_str = fecha.isoformat() if hasattr(fecha, "isoformat") else str(fecha)
        rows.append((serie_id, fecha_str, float(valor)))
        if fecha_str not in existing:
            new_count += 1

    conn.executemany("""
        INSERT INTO data_points(serie_id, fecha, valor)
        VALUES(?, ?, ?)
        ON CONFLICT(serie_id, fecha) DO UPDATE SET valor=excluded.valor
    """, rows)
    conn.commit()
    return new_count
