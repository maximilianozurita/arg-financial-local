# arg-financial-local

Pipeline local para recolectar y exportar datos económicos argentinos.
Descarga desde APIs públicas → guarda en SQLite → exporta CSV/Parquet a [`arg-financial-data`](https://github.com/maximilianozurita/arg-financial-data).

## Documentación

| | |
|---|---|
| [Arquitectura](docs/arquitectura.md) | Diseño del sistema, componentes y flujo de datos |
| [Estructura](docs/estructura.md) | Organización del proyecto y responsabilidades |
| [Instalación](docs/instalacion.md) | Requisitos y pasos para correr el proyecto |
| [Decisiones técnicas](docs/decisiones.md) | Trade-offs y justificaciones de diseño |

---

## Stack

- Python 3.10+ con `httpx`, `pandas`, `pyarrow`
- SQLite como base de datos local
- Crontab para scheduling en Linux

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuración del repo de datos

Este pipeline escribe en un repo separado (`arg-financial-data`). Para usarlo con tu propia cuenta:

1. Forkeá [arg-financial-data](https://github.com/maximilianozurita/arg-financial-data) en tu cuenta de GitHub
2. Cloná tu fork localmente:
   ```bash
   git clone https://github.com/TU_USUARIO/arg-financial-data /ruta/local/arg-financial-data
   ```
3. Copiá el archivo de entorno y editalo:
   ```bash
   cp .env.example .env
   # editar DATA_REPO con la ruta del paso anterior
   ```

`.env` no se sube al repo (incluido en `.gitignore`).

## Uso

```bash
# Descargar todas las fuentes
python fetch.py

# Descargar fuentes específicas
python fetch.py bcra bluelytics argentinadatos
python fetch.py indec mecon

# Ver estado de la base de datos
python status.py

# Exportar a arg-financial-data (usa DATA_REPO del .env)
python export.py

# Exportar + git push automático
python export.py --push

# Sobreescribir path o remote puntualmente
python export.py /otra/ruta --push --remote origin --branch main
```

## Fuentes y series

| Fuente | Series | Frecuencia |
|--------|--------|------------|
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

## Scheduling (crontab)

```bash
# Instalar el crontab de producción (con deduplicación por flags)
crontab crontab.real

# Ejecutar manualmente
./run_fetch.sh daily bcra bluelytics argentinadatos
./run_fetch.sh monthly indec mecon

# Ver logs
tail -f logs/fetch.log
```

El script `run_fetch.sh` evita re-descargas usando flags en `db/`:
- `db/.last_daily_run` — fecha YYYY-MM-DD de la última ejecución diaria exitosa
- `db/.last_monthly_run` — mes YYYY-MM de la última ejecución mensual exitosa

Si el cron dispara dos veces el mismo día/mes, la segunda salida sin hacer nada.
Para forzar una re-ejecución: `rm db/.last_daily_run` o `rm db/.last_monthly_run`.

## Base de datos

SQLite en `db/data.db`. No se sube al repo (incluido en `.gitignore`).
Es el backup histórico local; la fuente pública son los archivos en `arg-financial-data`.

## Configuración (.env)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATA_REPO` | Path al clon local de `arg-financial-data` | — |
| `GIT_REMOTE` | Nombre del remote git | `origin` |
| `GIT_BRANCH` | Branch de destino | `main` |
