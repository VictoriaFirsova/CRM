"""Статус счёта: python -m scripts.migrate_invoice_status"""
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
                "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'PENDING'"
            )
        )
    print("OK: invoices.status")


if __name__ == "__main__":
    asyncio.run(main())
