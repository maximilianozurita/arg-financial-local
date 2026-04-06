from datetime import date
from decimal import Decimal
import httpx
from scrapers.base import BaseScraper

BASE_URL = "https://apis.datos.gob.ar/series/api/series/"

# (api_id, nombre, categoria, unidad, frecuencia, descripcion)
SERIES = [
    (
        "172.3_TL_RECAION_M_0_0_17",
        "Recaudación Tributaria", "fiscal", "millones ARS", "mensual",
        "Recaudación tributaria total mensual (Ministerio de Economía)",
    ),
    (
        "451.1_GPCGPC_0_0_3_66",
        "Gasto Público Consolidado", "fiscal", "millones ARS", "anual",
        "Gasto público consolidado (Nación + Provincias + Municipios, en millones de ARS corrientes)",
    ),
    (
        "451.3_GPNGPN_0_0_3_30",
        "Gasto Público Nacional", "fiscal", "millones ARS", "anual",
        "Gasto del sector público nacional (en millones de ARS corrientes)",
    ),
    (
        "379.6_GTOS_CORR_017__14_17",
        "Gasto Corriente del Estado", "fiscal", "millones ARS", "trimestral",
        "Gasto corriente del sector público nacional, metodología 2017 (trimestral)",
    ),
]


class MECONScraper(BaseScraper):
    fuente = "Ministerio de Economía"

    async def run(self) -> int:
        total = 0
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            for api_id, nombre, categoria, unidad, frecuencia, descripcion in SERIES:
                points = await self._fetch(client, api_id)
                if not points:
                    continue
                serie_id = self.get_or_create_serie(nombre, categoria, unidad, frecuencia, descripcion)
                total += self.upsert_data_points(serie_id, points)
        return total

    async def _fetch(self, client: httpx.AsyncClient, api_id: str) -> list[tuple[date, Decimal]]:
        try:
            resp = await client.get(BASE_URL, params={"ids": api_id, "limit": 5000, "format": "json"})
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

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
        return points
