import sqlite3
from datetime import date
from decimal import Decimal
from db import get_or_create_serie, upsert_data_points


class BaseScraper:
    fuente: str = ""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    async def run(self) -> int:
        raise NotImplementedError

    def get_or_create_serie(
        self,
        nombre: str,
        categoria: str,
        unidad: str = "",
        frecuencia: str = "diaria",
        descripcion: str = "",
    ) -> int:
        return get_or_create_serie(
            self.conn, nombre, self.fuente, categoria, unidad, frecuencia, descripcion
        )

    def upsert_data_points(self, serie_id: int, points: list[tuple[date, Decimal]]) -> int:
        return upsert_data_points(self.conn, serie_id, points)
