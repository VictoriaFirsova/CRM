"""Порядковый номер и год (глобальная уникальность): python -m scripts.migrate_contract_sequence"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text

from app.core.database import engine
from app.models.contract import Contract
from app.models.enums import ContractKind
from app.services.contract_numbering import parse_framework_number


async def main():
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS number_sequence INTEGER")
        )
        await conn.execute(text("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS number_year INTEGER"))
        print("OK: number_sequence, number_year")

    async with engine.begin() as conn:
        result = await conn.execute(
            select(Contract.id, Contract.contract_number, Contract.kind)
        )
        updated = 0
        for row_id, number, kind in result.all():
            if kind != ContractKind.FRAMEWORK:
                continue
            parsed = parse_framework_number(number or "")
            if not parsed:
                continue
            _, seq, year = parsed
            await conn.execute(
                text(
                    "UPDATE contracts SET number_sequence = :s, number_year = :y WHERE id = :id"
                ),
                {"s": seq, "y": year, "id": row_id},
            )
            updated += 1
        print(f"Заполнено sequence/year: {updated} рамочных договоров")

    print("Миграция завершена.")


if __name__ == "__main__":
    asyncio.run(main())
