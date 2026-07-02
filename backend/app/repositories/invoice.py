from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contract import Contract
from app.models.enums import InvoiceKind
from app.models.invoice import Invoice


class InvoiceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self):
        return select(Invoice).options(
            selectinload(Invoice.contract).selectinload(Contract.client),
            selectinload(Invoice.contract).selectinload(Contract.parent),
        )

    async def get_by_id(self, invoice_id: int) -> Invoice | None:
        result = await self.db.execute(self._base_query().where(Invoice.id == invoice_id))
        return result.scalar_one_or_none()

    async def list_all(self, contract_id: int | None = None) -> list[Invoice]:
        q = self._base_query().order_by(Invoice.created_at.desc())
        if contract_id is not None:
            q = q.where(Invoice.contract_id == contract_id)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_for_contract(self, contract_id: int, kind: InvoiceKind | None = None) -> list[Invoice]:
        q = self._base_query().where(Invoice.contract_id == contract_id)
        if kind is not None:
            q = q.where(Invoice.kind == kind)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def create(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        await self.db.flush()
        await self.db.refresh(invoice)
        return invoice

    async def delete(self, invoice: Invoice) -> None:
        await self.db.delete(invoice)
        await self.db.flush()
