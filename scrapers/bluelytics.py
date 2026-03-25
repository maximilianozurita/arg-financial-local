from datetime import date
from decimal import Decimal
import httpx
from scrapers.base import BaseScraper


class BluelyticsScraper(BaseScraper):
    fuente = "Bluelytics"
    BASE_URL = "https://api.bluelytics.com.ar/v2/evolution.json"

    async def run(self) -> int:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(self.BASE_URL)
            resp.raise_for_status()
            data = resp.json()

        buckets: dict[str, list[tuple[date, Decimal]]] = {
            "Blue_sell": [], "Blue_buy": [],
            "Oficial_sell": [], "Oficial_buy": [],
        }

        for entry in data:
            try:
                fecha = date.fromisoformat(entry["date"][:10])
                source = entry["source"]
            except (KeyError, ValueError):
                continue

            if entry.get("value_sell") is not None:
                buckets[f"{source}_sell"].append((fecha, Decimal(str(entry["value_sell"]))))
            if entry.get("value_buy") is not None:
                buckets[f"{source}_buy"].append((fecha, Decimal(str(entry["value_buy"]))))

        series_config = [
            ("Blue_sell",    "Dólar Blue (Venta)",    "cambiario", "ARS/USD", "Cotización venta del dólar blue (informal)"),
            ("Blue_buy",     "Dólar Blue (Compra)",   "cambiario", "ARS/USD", "Cotización compra del dólar blue (informal)"),
            ("Oficial_sell", "Dólar Oficial (Venta)", "cambiario", "ARS/USD", "Cotización venta del dólar oficial BNA"),
            ("Oficial_buy",  "Dólar Oficial (Compra)","cambiario", "ARS/USD", "Cotización compra del dólar oficial BNA"),
        ]

        total = 0
        for key, nombre, categoria, unidad, descripcion in series_config:
            points = buckets[key]
            if not points:
                continue
            serie_id = self.get_or_create_serie(nombre, categoria, unidad, "diaria", descripcion)
            total += self.upsert_data_points(serie_id, points)

        return total
