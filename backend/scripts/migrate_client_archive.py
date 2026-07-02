"""Архив клиентов: python -m scripts.migrate_client_archive"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.database import engine


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE clients ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT FALSE")
        )
        await conn.execute(text("ALTER TABLE clients ADD COLUMN IF NOT EXISTS archive_comment TEXT"))
        await conn.execute(
            text("ALTER TABLE clients ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ")
        )
        await conn.execute(
            text(
                "ALTER TABLE clients ADD COLUMN IF NOT EXISTS archived_by INTEGER REFERENCES users(id)"
            )
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_clients_is_archived ON clients(is_archived)")
        )
    print("OK: clients archive fields")


if __name__ == "__main__":
    asyncio.run(main())
