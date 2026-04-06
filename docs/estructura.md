# Estructura del proyecto

```
arg-financial-local/
│
├── fetch.py                  # CLI: descarga datos de las fuentes configuradas
├── export.py                 # CLI: exporta SQLite → CSV/Parquet/JSON
├── status.py                 # CLI: muestra resumen de la base de datos
├── db.py                     # Helpers de SQLite (conexión, schema, upserts)
│
├── scrapers/
│   ├── __init__.py
│   ├── base.py               # BaseScraper: clase base con helpers de DB
│   ├── bcra.py               # API del Banco Central (7 series, paginación)
│   ├── bluelytics.py         # API Bluelytics (4 series de TC)
│   ├── indec.py              # API datos.gob.ar — series INDEC (6 series)
│   ├── mecon.py              # API datos.gob.ar — Ministerio de Economía (4 series)
│   └── argentinadatos.py     # API ArgentinaDatos (riesgo país + MEP + CCL)
│
├── run_fetch.sh              # Wrapper bash para crontab: fetch + export --push + flag deduplicación
├── crontab.real              # Crontab listo para instalar (rutas reales)
├── crontab.example           # Crontab de ejemplo (rutas genéricas /opt/...)
│
├── requirements.txt          # httpx, pandas, pyarrow, python-dotenv
├── .env.example              # Plantilla de configuración
├── .env                      # Configuración local (no versionado)
├── .gitignore
│
├── db/                       # No versionado
│   ├── data.db               # Base de datos SQLite
│   ├── .last_daily_run       # Flag: última fecha de ejecución diaria
│   └── .last_monthly_run     # Flag: último mes de ejecución mensual
│
├── logs/                     # No versionado
│   └── fetch.log             # Log de ejecuciones del crontab
│
└── docs/                     # Documentación técnica
    ├── arquitectura.md
    ├── estructura.md
    ├── instalacion.md
    └── decisiones.md
```

## Archivos clave

### `db.py`
Toda la lógica de persistencia está centralizada acá. Los scrapers nunca
escriben SQL directamente — usan `get_or_create_serie()` y `upsert_data_points()`.

### `scrapers/base.py`
Define la interfaz común. Cada scraper concreto solo necesita:
1. Declarar `fuente = "NOMBRE"`
2. Implementar `async def run(self) -> int`

### `fetch.py` — registro de scrapers
```python
SCRAPERS = {
    "bcra":           BCRAScraper,
    "bluelytics":     BluelyticsScraper,
    "indec":          INDECScraper,
    "mecon":          MECONScraper,
    "argentinadatos": ArgentinaDatosScraper,
}
```
Para agregar una nueva fuente: crear `scrapers/nueva.py` y registrarla acá.

## Lo que no se versiona (`.gitignore`)

- `db/` — base de datos SQLite e historial local
- `.env` — credenciales y rutas locales
- `logs/` — logs de ejecución
- `crontab.real` — tiene rutas absolutas específicas de la máquina
- `.venv/` y `__pycache__/`
