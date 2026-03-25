from datetime import date
from decimal import Decimal
import httpx
from scrapers.base import BaseScraper

BASE_URL = "https://api.argentinadatos.com/v1"


class ArgentinaDatosScraper(BaseScraper):
    fuente = "ArgentinaDatos"

    async def run(self) -> int:
        total = 0
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            total += await self._fetch_riesgo_pais(client)
            total += await self._fetch_dolar(client, "bolsa",
                "Dólar MEP Compra", "Dólar MEP Venta")
            total += await self._fetch_dolar(client, "contadoconliqui",
                "Dólar CCL Compra", "Dólar CCL Venta")
        return total

    async def _fetch_riesgo_pais(self, client: httpx.AsyncClient) -> int:
        try:
            resp = await client.get(f"{BASE_URL}/finanzas/indices/riesgo-pais")
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return 0

        points: list[tuple[date, Decimal]] = []
        for entry in data:
            try:
                points.append((date.fromisoformat(entry["fecha"]), Decimal(str(entry["valor"]))))
            except (KeyError, ValueError, TypeError):
                continue

        if not points:
            return 0

        serie_id = self.get_or_create_serie(
            "Riesgo País (EMBI+)", "financiero", "bps", "diaria",
            "Riesgo país argentino (EMBI+ spread en puntos básicos)",
        )
        return self.upsert_data_points(serie_id, points)

    async def _fetch_dolar(
        self, client: httpx.AsyncClient, casa: str,
        nombre_compra: str, nombre_venta: str,
    ) -> int:
        try:
            resp = await client.get(f"{BASE_URL}/cotizaciones/dolares/{casa}")
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return 0

        compra_pts: list[tuple[date, Decimal]] = []
        venta_pts: list[tuple[date, Decimal]] = []

        for entry in data:
            try:
                fecha = date.fromisoformat(entry["fecha"])
                if entry.get("compra") is not None:
                    compra_pts.append((fecha, Decimal(str(entry["compra"]))))
                if entry.get("venta") is not None:
                    venta_pts.append((fecha, Decimal(str(entry["venta"]))))
            except (KeyError, ValueError, TypeError):
                continue

        total = 0
        if compra_pts:
            sid = self.get_or_create_serie(nombre_compra, "cambiario", "ARS/USD", "diaria",
                                           f"{nombre_compra} (ArgentinaDatos)")
            total += self.upsert_data_points(sid, compra_pts)
        if venta_pts:
            sid = self.get_or_create_serie(nombre_venta, "cambiario", "ARS/USD", "diaria",
                                           f"{nombre_venta} (ArgentinaDatos)")
            total += self.upsert_data_points(sid, venta_pts)
        return total
