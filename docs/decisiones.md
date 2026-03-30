# Decisiones de diseño

## Dos repositorios separados

**Decisión:** El pipeline de fetching (`arg-financial-local`) y los datos exportados
(`arg-financial-data`) viven en repos separados.

**Por qué:** `arg-financial-data` es un repo público de solo datos — permite que
otros lo consuman via git clone, GitHub raw, o pandas sin necesidad de correr
el pipeline. Mezclar código y datos haría el repo de datos más pesado y confuso.

---

## SQLite como base de datos intermedia

**Decisión:** Los datos se almacenan en SQLite antes de exportarse a CSV/Parquet.

**Por qué:** SQLite actúa como buffer histórico local. Si una API externa cambia
retroactivamente un dato, el upsert `ON CONFLICT DO UPDATE` lo corrige en la DB
sin duplicar filas. También permite correr `export.py` independientemente de
`fetch.py` (útil para re-exportar con un formato distinto sin re-descargar).

---

## Upsert en lugar de insert-only

**Decisión:** `upsert_data_points()` usa `INSERT ... ON CONFLICT DO UPDATE SET valor=excluded.valor`.

**Por qué:** Las APIs argentinas (especialmente BCRA e INDEC) a veces publican
revisiones retroactivas de datos. El upsert garantiza que la DB siempre tenga
el valor más reciente para cada `(serie_id, fecha)`.

---

## git pull --rebase antes de exportar

**Decisión:** `export.py --push` hace `git pull --rebase` antes de escribir los
archivos y commitear.

**Por qué:** Si el repo de datos tiene cambios remotos (ej. edits manuales en
GitHub), un push directo fallaría. El rebase mantiene el historial limpio sin
merges innecesarios.

---

## CSV + Parquet (ambos formatos)

**Decisión:** Cada serie se exporta tanto en `.csv` como en `.parquet`.

**Por qué:** CSV para consumo general (frontend, Excel, contexto LLM, scripts
simples). Parquet para análisis de datos en Python/pandas/polars — tipado
correcto, compresión eficiente, lectura más rápida con columnas grandes.

---

## Scrapers async con httpx

**Decisión:** Todos los scrapers usan `httpx.AsyncClient` y heredan `BaseScraper`.

**Por qué:** `httpx` soporta HTTP/2 y tiene una API async limpia. La herencia
de `BaseScraper` centraliza los helpers de DB para que cada scraper solo se
preocupe por parsear la respuesta de su API. Los scrapers corren secuencialmente
(no en paralelo) para simplificar el manejo de errores y evitar rate limiting.

---

## Flag files para deduplicación en crontab

**Decisión:** `run_fetch.sh` escribe la fecha/mes en archivos de texto en `db/`
para evitar ejecutar dos veces el mismo período.

**Por qué:** El crontab dispara el script dos veces por día (8h y 21h) como
mecanismo de resiliencia ante la PC apagada. Sin el flag, si la PC está encendida
en ambos horarios, el script correría dos veces descargando los mismos datos.
El flag es simple, legible (`cat db/.last_daily_run`) y fácil de resetear (`rm`).

---

## Slugify para nombres de archivo

**Decisión:** `export.py` convierte el nombre de cada serie a un slug ASCII
para usarlo como nombre de archivo (`Dólar Blue (Venta)` → `dolar_blue_venta`).

**Por qué:** Los nombres de serie vienen con acentos, espacios y paréntesis.
Un slug normalizado es compatible con todos los sistemas de archivos, URLs
y herramientas de línea de comandos sin necesidad de escapar caracteres.

---

## Agregar una nueva fuente

1. Crear `scrapers/nueva.py` con una clase que herede `BaseScraper`
2. Declarar `fuente = "NOMBRE"` en la clase
3. Implementar `async def run(self) -> int`
4. Registrar en el dict `SCRAPERS` de `fetch.py`
5. Decidir si es fuente diaria o mensual y actualizar `crontab.real` y `run_fetch.sh` si corresponde
