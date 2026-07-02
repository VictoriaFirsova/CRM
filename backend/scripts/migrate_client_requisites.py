"""Добавить колонки реквизитов в существующую БД: python -m scripts.migrate_client_requisites"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.database import engine

COLUMNS = [
    ("full_company_name", "VARCHAR(1000)"),
    ("bank_name", "VARCHAR(500)"),
    ("bik", "VARCHAR(9)"),
    ("correspondent_account", "VARCHAR(20)"),
    ("settlement_account", "VARCHAR(20)"),
    ("director_name", "VARCHAR(255)"),
]


async def main():
    async with engine.begin() as conn:
        for name, col_type in COLUMNS:
            await conn.execute(
                text(f"ALTER TABLE clients ADD COLUMN IF NOT EXISTS {name} {col_type}")
            )
            print(f"OK: clients.{name}")
    print("Миграция завершена.")


if __name__ == "__main__":
    asyncio.run(main())
