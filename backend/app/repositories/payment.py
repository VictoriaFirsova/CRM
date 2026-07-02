from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import PaymentRecordStatus
from app.models.payment import Payment


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, payment_id: int) -> Payment | None:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.id == payment_id)
            .options(selectinload(Payment.contract))
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        contract_id: int | None = None,
        status: PaymentRecordStatus | None = None,
    ) -> list[Payment]:
        query = select(Payment).options(selectinload(Payment.contract)).order_by(Payment.created_at.desc())
        if contract_id:
            query = query.where(Payment.contract_id == contract_id)
        if status:
            query = query.where(Payment.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def get_paid_sum(self, contract_id: int) -> float:
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.contract_id == contract_id,
                Payment.status == PaymentRecordStatus.PAID,
            )
        )
        return float(result.scalar() or 0)
