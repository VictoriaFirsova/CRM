"""Таблица №1 приложений: python -m scripts.migrate_contract_line_items"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.database import engine


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS work_days INTEGER")
        )
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS contract_line_items (
                    id SERIAL PRIMARY KEY,
                    contract_id INTEGER NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
                    position INTEGER NOT NULL DEFAULT 0,
                    document_name VARCHAR(500) NOT NULL,
                    product_name TEXT NOT NULL,
                    price NUMERIC(15, 2) NOT NULL
                )
                """
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_contract_line_items_contract_id "
                "ON contract_line_items (contract_id)"
            )
        )
        print("OK: contract_line_items, contracts.work_days")
    print("Migration done.")


if __name__ == "__main__":
    asyncio.run(main())
