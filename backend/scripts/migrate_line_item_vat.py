"""vat_exempt для строк таблицы: python -m scripts.migrate_line_item_vat"""
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
                "ALTER TABLE contract_line_items "
                "ADD COLUMN IF NOT EXISTS vat_exempt BOOLEAN NOT NULL DEFAULT TRUE"
            )
        )
        print("OK: contract_line_items.vat_exempt")
    print("Migration done.")


if __name__ == "__main__":
    asyncio.run(main())
