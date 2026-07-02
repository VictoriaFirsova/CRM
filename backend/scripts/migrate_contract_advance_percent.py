"""Процент аванса для приложений: python -m scripts.migrate_contract_advance_percent"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.database import engine


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS advance_percent INTEGER")
        )
        await conn.execute(
            text(
                "UPDATE contracts SET advance_percent = 100 "
                "WHERE kind = 'ADDENDUM' AND advance_percent IS NULL"
            )
        )
        print("OK: contracts.advance_percent")
    print("Migration done.")


if __name__ == "__main__":
    asyncio.run(main())
