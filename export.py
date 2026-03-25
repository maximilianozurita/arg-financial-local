#!/usr/bin/env python3
"""
Export SQLite → CSV + Parquet + metadata.json + all_series files.

Usage:
    python export.py /path/to/arg-financial-data
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from db import get_conn


def slugify(nombre: str) -> str:
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n", "ü": "u", " ": "_", "(": "", ")": "",
        "/": "_", "-": "_", ".": "", ",": "",
    }
    result = nombre.lower()
    for k, v in replacements.items():
        result = result.replace(k, v)
    result = "".join(c for c in result if c.isalnum() or c == "_")
    while "__" in result:
        result = result.replace("__", "_")
    return result.strip("_")


def export(data_repo: Path) -> None:
    conn = get_conn()
    series = conn.execute("SELECT * FROM series ORDER BY categoria, nombre").fetchall()

    all_frames: list[pd.DataFrame] = []
    metadata: list[dict] = []
    latest: list[dict] = []

    for row in series:
        sid, nombre, fuente, categoria, unidad, frecuencia, descripcion, ultima_act = row

        points = conn.execute(
            "SELECT fecha, valor FROM data_points WHERE serie_id=? ORDER BY fecha",
            (sid,),
        ).fetchall()

        if not points:
            continue

        df = pd.DataFrame(points, columns=["fecha", "valor"])
        df["fecha"] = pd.to_datetime(df["fecha"])

        slug = slugify(nombre)
        out_dir = data_repo / "data" / categoria
        out_dir.mkdir(parents=True, exist_ok=True)

        # CSV siempre
        df_csv = df.copy()
        df_csv["fecha"] = df_csv["fecha"].dt.strftime("%Y-%m-%d")
        df_csv.to_csv(out_dir / f"{slug}.csv", index=False)

        # Parquet siempre (ideal para ML/AI)
        df.to_parquet(out_dir / f"{slug}.parquet", index=False)

        # Acumular para all_series
        df_all = df.copy()
        df_all["serie"] = nombre
        df_all["categoria"] = categoria
        df_all["fuente"] = fuente
        df_all["unidad"] = unidad or ""
        all_frames.append(df_all)

        last_fecha, last_valor = points[-1]
        metadata.append({
            "id": sid,
            "nombre": nombre,
            "fuente": fuente,
            "categoria": categoria,
            "unidad": unidad,
            "frecuencia": frecuencia,
            "descripcion": descripcion,
            "slug": slug,
            "ultima_actualizacion": ultima_act,
        })
        latest.append({
            "id": sid,
            "nombre": nombre,
            "fuente": fuente,
            "categoria": categoria,
            "unidad": unidad,
            "frecuencia": frecuencia,
            "slug": slug,
            "ultimo_valor": last_valor,
            "ultima_fecha": last_fecha,
        })

        print(f"  [{categoria}] {nombre}: {len(points)} puntos")

    conn.close()

    # all_series — columnas: fecha, valor, serie, categoria, fuente, unidad
    if all_frames:
        df_all_series = pd.concat(all_frames, ignore_index=True)
        col_order = ["fecha", "serie", "valor", "categoria", "fuente", "unidad"]
        df_all_series = df_all_series[col_order].sort_values(["fecha", "serie"])

        # Parquet (para ML/pandas/polars)
        df_all_series.to_parquet(data_repo / "all_series.parquet", index=False)

        # CSV (para frontend y contexto LLM)
        df_csv_all = df_all_series.copy()
        df_csv_all["fecha"] = df_csv_all["fecha"].dt.strftime("%Y-%m-%d")
        df_csv_all.to_csv(data_repo / "all_series.csv", index=False)

    # metadata.json — catálogo de series
    (data_repo / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2)
    )

    # latest.json — último valor de cada serie
    (data_repo / "latest.json").write_text(
        json.dumps(latest, ensure_ascii=False, indent=2)
    )

    now = datetime.now(timezone.utc).isoformat()
    print(f"\nExportadas {len(metadata)} series → {data_repo}")
    print(f"Archivos: metadata.json, latest.json, all_series.csv, all_series.parquet")
    print(f"Timestamp: {now}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python export.py /path/to/arg-financial-data")
        sys.exit(1)
    export(Path(sys.argv[1]))
