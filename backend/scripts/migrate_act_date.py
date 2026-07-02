"""Дата акта в documents: python -m scripts.migrate_act_date"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.database import engine


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS document_date DATE")
        )
    print("OK: documents.document_date")


if __name__ == "__main__":
    asyncio.run(main())
