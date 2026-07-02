"""Таблица счетов: python -m scripts.migrate_invoices"""
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
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    id SERIAL PRIMARY KEY,
                    contract_id INTEGER NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
                    kind VARCHAR(20) NOT NULL,
                    amount NUMERIC(15, 2) NOT NULL,
                    invoice_date DATE NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_contract_id ON invoices(contract_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_kind ON invoices(kind)"))
    print("OK: invoices table ready.")


if __name__ == "__main__":
    asyncio.run(main())
