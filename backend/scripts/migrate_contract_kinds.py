"""Рамка / приложение: python -m scripts.migrate_contract_kinds"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.database import engine


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS kind VARCHAR(20) NOT NULL DEFAULT 'FRAMEWORK'"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS parent_contract_id "
                "INTEGER REFERENCES contracts(id)"
            )
        )
        await conn.execute(
            text("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS addendum_number INTEGER")
        )
        await conn.execute(text("UPDATE contracts SET kind = 'FRAMEWORK' WHERE kind IS NULL"))
        print("OK: contracts.kind, parent_contract_id, addendum_number")
    print("Миграция завершена.")


if __name__ == "__main__":
    asyncio.run(main())
