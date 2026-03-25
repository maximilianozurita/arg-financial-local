# arg-financial-local

Pipeline local para recolectar y exportar datos económicos argentinos.
Descarga desde APIs públicas → guarda en SQLite → exporta CSV/Parquet a [`arg-financial-data`](https://github.com/maximilianozurita/arg-financial-data).

## Stack

- Python 3.11+ con `httpx`, `pandas`, `pyarrow`
- SQLite como base de datos local (backup histórico)
- Crontab para scheduling en Linux

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
# Descargar todas las fuentes
python fetch.py

# Descargar fuentes específicas
python fetch.py bcra bluelytics argentinadatos
python fetch.py indec mecon

# Ver estado de la base de datos
python status.py

# Exportar a arg-financial-data (CSV + Parquet + JSON)
python export.py /ruta/a/arg-financial-data
```

## Fuentes y series

| Fuente | Series | Frecuencia |
|--------|--------|-----------|
| **BCRA** | Reservas, Base Monetaria, TC Minorista, BADLAR, Tasa Política Monetaria, Pases Pasivos, Inflación Esperada (REM) | Diaria |
| **Bluelytics** | Dólar Blue compra/venta, Dólar Oficial compra/venta | Diaria |
| **ArgentinaDatos** | Dólar MEP compra/venta, Dólar CCL compra/venta, Riesgo País | Diaria |
| **INDEC** | IPC Nivel General, EMAE, Índice de Salarios, IPI Manufacturero | Mensual |
| **Ministerio de Economía** | Recaudación Tributaria | Mensual |

## Archivos generados en arg-financial-data

```
data/{categoria}/{slug}.csv       ← serie individual
data/{categoria}/{slug}.parquet   ← serie individual
all_series.csv                    ← todas las series unificadas
all_series.parquet                ← todas las series unificadas
metadata.json                     ← catálogo de series
latest.json                       ← último valor por serie
```

## Scheduling (Linux)

Ver [`crontab.example`](crontab.example) para la configuración completa.

```bash
crontab -e
```

```
# Lunes a viernes 8:00 — fuentes diarias
0 8 * * 1-5  cd /opt/arg-financial-local && .venv/bin/python fetch.py bcra bluelytics argentinadatos && .venv/bin/python export.py /opt/arg-financial-data && cd /opt/arg-financial-data && git add -A && git commit -m "data: update $(date +%Y-%m-%d)" && git push

# Día 6 de cada mes — fuentes mensuales
0 8 6 * *    cd /opt/arg-financial-local && .venv/bin/python fetch.py indec mecon && .venv/bin/python export.py /opt/arg-financial-data && cd /opt/arg-financial-data && git add -A && git commit -m "data: monthly update $(date +%Y-%m-%d)" && git push
```

## Base de datos

SQLite en `db/data.db`. No se sube al repo (incluido en `.gitignore`).
Es el backup histórico local; la fuente pública son los archivos en `arg-financial-data`.
