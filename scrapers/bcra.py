from datetime import date, timedelta
from decimal import Decimal
import httpx
from scrapers.base import BaseScraper

BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"

VARIABLES = [
    (1,   "Reservas Internacionales BCRA",      "monetario", "millones USD", "diaria",
     "Reservas internacionales del BCRA en millones de dólares"),
    (15,  "Base Monetaria",                     "monetario", "millones ARS", "diaria",
     "Base monetaria en millones de pesos"),
    (4,   "Tipo de Cambio Minorista BCRA",      "cambiario", "ARS/USD",      "diaria",
     "Tipo de cambio minorista promedio vendedor (BCRA)"),
    (7,   "BADLAR Bancos Privados",             "monetario", "% n.a.",       "diaria",
     "Tasa de interés BADLAR bancos privados (nominal anual)"),
    (29,  "Inflación Esperada 12m (REM)",       "precios",   "%",            "diaria",
     "Mediana de variación interanual esperada del IPC próximos 12 meses (REM-BCRA)"),
    (150, "Tasa Pases Pasivos BCRA 1 día",      "monetario", "% n.a.",       "diaria",
     "Tasa de pases pasivos entre terceros a 1 día (BCRA)"),
    (160, "Tasa de Política Monetaria",         "monetario", "% n.a.",       "diaria",
     "Tasa de interés de política monetaria (BCRA)"),
]

PAGE_SIZE = 3000


class BCRAScraper(BaseScraper):
    fuente = "BCRA"

    async def run(self) -> int:
        total = 0
        date_from = (date.today() - timedelta(days=365 * 30)).isoformat()
        date_to = date.today().isoformat()

        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            for var_id, nombre, categoria, unidad, frecuencia, descripcion in VARIABLES:
                points = await self._fetch(client, var_id, date_from, date_to)
                if not points:
                    continue
                serie_id = self.get_or_create_serie(nombre, categoria, unidad, frecuencia, descripcion)
                total += self.upsert_data_points(serie_id, points)

        return total

    async def _fetch(
        self, client: httpx.AsyncClient, var_id: int, date_from: str, date_to: str
    ) -> list[tuple[date, Decimal]]:
        points: list[tuple[date, Decimal]] = []
        offset = 0

        while True:
            try:
                resp = await client.get(
                    f"{BASE_URL}/{var_id}",
                    params={"desde": date_from, "hasta": date_to, "limit": PAGE_SIZE, "offset": offset},
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                break

            detalle = data.get("results", [{}])[0].get("detalle", [])
            for entry in detalle:
                try:
                    fecha = date.fromisoformat(entry["fecha"][:10])
                    points.append((fecha, Decimal(str(entry["valor"]))))
                except (KeyError, ValueError, TypeError):
                    continue

            total_count = data.get("metadata", {}).get("resultset", {}).get("count", 0)
            offset += PAGE_SIZE
            if offset >= total_count:
                break

        return points
