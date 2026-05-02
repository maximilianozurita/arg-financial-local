import logging
from datetime import date
from decimal import Decimal

import pandas as pd
import yfinance as yf

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class MervalScraper(BaseScraper):
    fuente = "Yahoo Finance"

    async def run(self) -> int:
        return self._run_sync()

    def _run_sync(self) -> int:
        try:
            df = yf.download("^MERV", start="2000-01-01", progress=False, auto_adjust=True)
        except Exception as e:
            logger.warning("[merval] Error descargando ^MERV: %s", e)
            return 0

        if df.empty:
            logger.warning("[merval] DataFrame vacío para ^MERV")
            return 0

        close = df["Close"].squeeze()
        points: list[tuple[date, Decimal]] = []
        for ts, val in close.items():
            try:
                if pd.isna(val):
                    continue
                points.append((ts.date(), Decimal(str(float(val)))))
            except (ValueError, TypeError):
                continue

        sid = self.get_or_create_serie("Índice Merval", "acciones", "puntos", "diaria")
        return self.upsert_data_points(sid, points)
