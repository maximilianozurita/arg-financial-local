from datetime import date
from decimal import Decimal
import httpx
from scrapers.base import BaseScraper

BASE_URL = "https://apis.datos.gob.ar/series/api/series/"

# (api_id, nombre, categoria, unidad, frecuencia, descripcion)
SERIES = [
    (
        "148.3_INIVELNAL_DICI_M_26",
        "IPC - Nivel General", "precios", "índice", "mensual",
        "Índice de Precios al Consumidor - Nivel General (INDEC, base Dic 2016=100)",
    ),
    (
        "143.3_NO_PR_2004_A_21",
        "EMAE - Actividad Económica", "actividad", "índice", "mensual",
        "Estimador Mensual de Actividad Económica - Nivel General (INDEC, base 2004=100)",
    ),
    (
        "149.1_TL_INDIIOS_OCTU_0_21",
        "Índice de Salarios", "laboral", "índice", "mensual",
        "Índice de Salarios total (INDEC, base Oct 2016=100)",
    ),
    (
        "453.1_SERIE_ORIGNAL_0_0_14_46",
        "IPI Manufacturero", "actividad", "índice", "mensual",
        "Índice de Producción Industrial Manufacturero - Serie original (INDEC, base 2004=100)",
    ),
]


class INDECScraper(BaseScraper):
    fuente = "INDEC"

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
