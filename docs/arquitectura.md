# Arquitectura

## Visión general

El sistema se divide en dos repositorios con responsabilidades separadas:

```
arg-financial-local          arg-financial-data
(este repo — privado)        (repo público)
┌─────────────────┐          ┌──────────────────────┐
│  fetch.py       │          │  data/cambiario/      │
│  scrapers/      │ ──────→  │  data/monetario/      │
│  db/data.db     │export.py │  data/precios/        │
│  run_fetch.sh   │          │  all_series.csv        │
│  crontab.real   │          │  metadata.json         │
└─────────────────┘          │  latest.json           │
                             └──────────────────────┘
```

`arg-financial-local` maneja la lógica de descarga y almacenamiento.
`arg-financial-data` es el destino público con los archivos exportados.

## Flujo de datos

```
APIs externas
    │
    ▼
scrapers/*.py          Descargan vía httpx (async)
    │                  Parsean y validan
    ▼
db/data.db             SQLite con WAL mode
(series + data_points) UNIQUE(serie_id, fecha) → upsert seguro
    │
    ▼
export.py              Lee todas las series
    │                  Genera CSV + Parquet por serie
    │                  Genera all_series.csv / .parquet
    │                  Genera metadata.json + latest.json
    ▼
arg-financial-data/    git pull --rebase → commit → push
```

## Componentes

### fetch.py
Punto de entrada CLI. Inicializa la DB, instancia los scrapers pedidos y los
corre en secuencia con `asyncio.run()`. Devuelve 0 implícitamente en éxito;
imprime `ERROR: ...` en excepción pero no corta la ejecución de los siguientes scrapers.

### scrapers/
Cada scraper hereda `BaseScraper` e implementa `async def run() -> int`.
El entero devuelto es la cantidad de registros **nuevos** insertados (los duplicados
se actualizan via upsert pero no se cuentan).

Dos fuentes de datos:
- **Diarias** (BCRA, Bluelytics, ArgentinaDatos): actualizan con cada ejecución.
- **Mensuales** (INDEC, MECON): publican 1 dato por mes; re-fetching es idempotente.

### db.py
Encapsula toda la lógica de SQLite:
- `get_conn()` — abre conexión con WAL mode y foreign keys activados.
- `init_db()` — crea tablas si no existen.
- `get_or_create_serie()` — upsert en `series`, devuelve `id`.
- `upsert_data_points()` — inserta o actualiza puntos, devuelve conteo de nuevos.

### export.py
Lee de SQLite y escribe en el directorio de `arg-financial-data`.
Con `--push` hace primero `git pull --rebase` (para absorber cambios remotos)
y luego `git add -A && git commit && git push`.
Si no hay cambios (`nothing to commit`), saltea el push silenciosamente.

### run_fetch.sh
Wrapper bash para el crontab. En cada ejecución:
1. Verifica el flag de deduplicación (`db/.last_daily_run` o `db/.last_monthly_run`).
   Si coincide con el período actual, sale sin hacer nada.
2. Llama a `python fetch.py <fuentes>` para descargar datos.
3. Llama a `python export.py <DATA> --push` para exportar y pushear al repo de datos.
4. Actualiza el flag con la fecha/mes actual.

Redirige stdout y stderr a `logs/fetch.log` via `tee` (también muestra en terminal
al correr manual). El script tiene rutas absolutas hardcodeadas (`/home/maxi/src/...`)
y por eso se mantiene fuera del repo (gitignoreado).

## Esquema de la base de datos

```sql
series (
    id                   INTEGER PRIMARY KEY,
    nombre               TEXT NOT NULL,
    fuente               TEXT NOT NULL,
    categoria            TEXT NOT NULL,    -- cambiario, monetario, precios, etc.
    unidad               TEXT,
    frecuencia           TEXT,             -- diaria, mensual
    descripcion          TEXT,
    ultima_actualizacion TEXT,
    UNIQUE(nombre, fuente)
)

data_points (
    id       INTEGER PRIMARY KEY,
    serie_id INTEGER REFERENCES series(id) ON DELETE CASCADE,
    fecha    TEXT NOT NULL,               -- ISO 8601: YYYY-MM-DD
    valor    REAL NOT NULL,
    UNIQUE(serie_id, fecha)               -- upsert: INSERT OR REPLACE
)

INDEX idx_dp_serie_fecha ON data_points(serie_id, fecha)
```

## Categorías de series

| Categoria | Contenido |
|-----------|-----------|
| `cambiario` | Tipos de cambio (oficial, blue, MEP, CCL) |
| `monetario` | Reservas, base monetaria, tasas de interés |
| `precios` | IPC, inflación esperada |
| `actividad` | EMAE, IPI manufacturero |
| `laboral` | Índice de salarios |
| `financiero` | Riesgo país |
| `fiscal` | Recaudación tributaria |
