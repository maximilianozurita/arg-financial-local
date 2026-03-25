#!/usr/bin/env python3
"""
Fetch data from public Argentine APIs and store in SQLite.

Usage:
    python fetch.py                          # fetch all sources
    python fetch.py bcra bluelytics          # fetch specific sources
    python fetch.py indec mecon argentinadatos
"""
import asyncio
import sys
from db import get_conn, init_db
from scrapers.bcra import BCRAScraper
from scrapers.bluelytics import BluelyticsScraper
from scrapers.indec import INDECScraper
from scrapers.mecon import MECONScraper
from scrapers.argentinadatos import ArgentinaDatosScraper

SCRAPERS = {
    "bcra":            BCRAScraper,
    "bluelytics":      BluelyticsScraper,
    "indec":           INDECScraper,
    "mecon":           MECONScraper,
    "argentinadatos":  ArgentinaDatosScraper,
}


async def main(sources: list[str]) -> None:
    conn = get_conn()
    init_db(conn)

    for name in sources:
        cls = SCRAPERS.get(name)
        if not cls:
            print(f"[WARN] fuente desconocida: {name}")
            continue
        print(f"[{name}] fetching...", end=" ", flush=True)
        try:
            scraper = cls(conn)
            new_rows = await scraper.run()
            print(f"{new_rows} nuevos registros")
        except Exception as e:
            print(f"ERROR: {e}")

    conn.close()


if __name__ == "__main__":
    sources = sys.argv[1:] or list(SCRAPERS.keys())
    asyncio.run(main(sources))
