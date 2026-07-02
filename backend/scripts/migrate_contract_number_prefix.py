"""Колонка number_prefix и заполнение из номера договора: python -m scripts.migrate_contract_number_prefix"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text

from app.core.database import engine
from app.models.contract import Contract
from app.services.contract_numbering import parse_framework_number


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS number_prefix VARCHAR(2)")
        )
        print("OK: contracts.number_prefix")

    async with engine.begin() as conn:
        result = await conn.execute(select(Contract.id, Contract.contract_number, Contract.kind))
        rows = result.all()
        for row_id, number, kind in rows:
            if kind and str(kind) != "FRAMEWORK":
                continue
            parsed = parse_framework_number(number or "")
            if not parsed:
                continue
            prefix = parsed[0]
            await conn.execute(
                text("UPDATE contracts SET number_prefix = :p WHERE id = :id"),
                {"p": prefix, "id": row_id},
            )
        print(f"Обновлено префиксов: {len(rows)} записей проверено")

    print("Миграция завершена.")


if __name__ == "__main__":
    asyncio.run(main())
