"""Добавить поля подписанта клиента: python -m scripts.migrate_client_signer_fields"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.database import engine

COLUMNS = [
    ("director_name_genitive", "VARCHAR(255)"),
    ("signer_position", "VARCHAR(255)"),
    ("signer_basis", "VARCHAR(255)"),
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
