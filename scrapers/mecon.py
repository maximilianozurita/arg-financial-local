from datetime import date
from decimal import Decimal
import httpx
from scrapers.base import BaseScraper

RECAUDACION_URL = (
    "https://apis.datos.gob.ar/series/api/series/"
    "?ids=172.3_TL_RECAION_M_0_0_17&limit=5000&format=json"
)


class MECONScraper(BaseScraper):
    fuente = "Ministerio de Economía"

    async def run(self) -> int:
        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                resp = await client.get(RECAUDACION_URL)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return 0

        points: list[tuple[date, Decimal]] = []
        for entry in data.get("data", []):
            try:
                fecha_str = entry[0]
                valor = entry[1]
                if valor is None:
                    continue
                year, month = int(fecha_str[:4]), int(fecha_str[5:7])
                points.append((date(year, month, 1), Decimal(str(valor))))
            except (IndexError, ValueError, TypeError):
                continue

        if not points:
            return 0

        serie_id = self.get_or_create_serie(
            "Recaudación Tributaria", "fiscal", "millones ARS", "mensual",
            "Recaudación tributaria total mensual (Ministerio de Economía)",
        )
        return self.upsert_data_points(serie_id, points)
