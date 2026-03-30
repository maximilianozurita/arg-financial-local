#!/bin/bash
set -euo pipefail

TYPE=${1:-}
if [ -z "$TYPE" ]; then
    echo "Uso: $0 <daily|monthly> [fuente1 fuente2 ...]"
    exit 1
fi
shift
SOURCES="$*"

REPO=/home/maxi/src/arg-financial-local
DATA=/home/maxi/src/arg-financial-data
PYTHON=$REPO/.venv/bin/python
FLAG_DIR=$REPO/db
LOG_DIR=$REPO/logs

mkdir -p "$LOG_DIR"
LOG_FILE=$LOG_DIR/fetch.log
exec > >(tee -a "$LOG_FILE") 2>&1

if [ "$TYPE" = "daily" ]; then
    FLAG_FILE="$FLAG_DIR/.last_daily_run"
    CURRENT=$(date +%Y-%m-%d)
elif [ "$TYPE" = "monthly" ]; then
    FLAG_FILE="$FLAG_DIR/.last_monthly_run"
    CURRENT=$(date +%Y-%m)
else
    echo "Tipo desconocido: $TYPE (usar 'daily' o 'monthly')"
    exit 1
fi

if [ -f "$FLAG_FILE" ] && [ "$(cat "$FLAG_FILE")" = "$CURRENT" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$TYPE] Ya ejecutado ($CURRENT), saltando."
    exit 0
fi

cd "$REPO"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$TYPE] Iniciando fetch: ${SOURCES:-todos}"
$PYTHON fetch.py $SOURCES

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$TYPE] Exportando a $DATA..."
$PYTHON export.py "$DATA" --push

echo "$CURRENT" > "$FLAG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$TYPE] Listo."
