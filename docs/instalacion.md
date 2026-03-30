# Instalación y configuración

## Requisitos

- Python 3.10+
- Git
- Acceso a internet para las APIs públicas

## Instalación

```bash
# 1. Clonar el repo
git clone https://github.com/maximilianozurita/arg-financial-local
cd arg-financial-local

# 2. Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
```

Editar `.env`:
```
DATA_REPO=/home/tuusuario/src/arg-financial-data
GIT_REMOTE=origin
GIT_BRANCH=main
```

## Configurar arg-financial-data

Este pipeline necesita un clon local de `arg-financial-data` donde escribir los exports.

```bash
# Opción A: clonar el repo original (solo lectura si no sos el owner)
git clone https://github.com/maximilianozurita/arg-financial-data /ruta/deseada

# Opción B: forkear primero en GitHub y clonar tu fork
git clone https://github.com/TU_USUARIO/arg-financial-data /ruta/deseada
```

Actualizar `DATA_REPO` en `.env` con la ruta del clon.

## Verificar instalación

```bash
# Confirmar que la DB se inicializa correctamente
python status.py
# Salida esperada: "Total series: 0" (base vacía)

# Primer fetch (puede tardar ~30s por el volumen histórico del BCRA)
python fetch.py bcra
# Salida esperada: "[bcra] fetching... N nuevos registros"

# Ver el estado
python status.py
```

## Configurar el crontab

```bash
# Hacer ejecutable el script
chmod +x run_fetch.sh

# Instalar
crontab crontab.real

# Verificar
crontab -l

# Ver logs en tiempo real
tail -f logs/fetch.log
```

### Programación del crontab

| Tarea | Horarios | Días |
|-------|----------|------|
| Fuentes diarias (BCRA, Bluelytics, ArgentinaDatos) | 8:00 y 21:00 | Lun–Vie |
| Fuentes mensuales (INDEC, MECON) | 8:00 y 21:00 | Miércoles |

La doble ejecución diaria es para tolerar que la PC esté apagada en uno de los
dos horarios. El script `run_fetch.sh` usa flags para evitar re-descargar si
ambas ejecuciones corren el mismo día/mes.

### Forzar re-ejecución

```bash
# Forzar re-ejecución de fuentes diarias (ignorar flag)
rm db/.last_daily_run

# Forzar re-ejecución de fuentes mensuales (ignorar flag)
rm db/.last_monthly_run
```

## Ejecución manual

```bash
# Fuentes diarias
./run_fetch.sh daily bcra bluelytics argentinadatos

# Fuentes mensuales
./run_fetch.sh monthly indec mecon

# Solo fetch sin export (para debug)
python fetch.py bcra
python fetch.py indec mecon

# Solo export sin fetch
python export.py --push
```
