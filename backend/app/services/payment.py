from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import can_edit_contract, is_admin
from app.models.enums import PaymentRecordStatus, PaymentStatus
from app.models.payment import Payment
from app.models.user import User
from app.repositories.contract import ContractRepository
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentUpdate
from app.services.audit import log_audit


class PaymentService:
    def __init__(self, repo: PaymentRepository, contract_repo: ContractRepository):
        self.repo = repo
        self.contract_repo = contract_repo

    def _can_edit_payment(self, user: User, contract) -> bool:
        if not contract or not contract.client:
            return False
        return can_edit_contract(user, contract.client.owner_id, contract.responsible_manager_id)

    def _to_response(self, payment: Payment, user: User) -> PaymentResponse:
        data = PaymentResponse.model_validate(payment)
        data.can_edit = self._can_edit_payment(user, payment.contract)
        if payment.contract:
            data.contract_number = payment.contract.contract_number
        return data

    async def _sync_contract_payment_status(self, db: AsyncSession, contract_id: int) -> None:
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            return
        paid_sum = Decimal(str(await self.repo.get_paid_sum(contract_id)))
        amount = contract.amount or Decimal("0")
        if paid_sum <= 0:
            contract.payment_status = PaymentStatus.NOT_PAID
        elif paid_sum >= amount:
            contract.payment_status = PaymentStatus.PAID
        else:
            contract.payment_status = PaymentStatus.PARTIALLY_PAID

    async def list_payments(
        self,
        user: User,
        contract_id: int | None = None,
        status: PaymentRecordStatus | None = None,
    ) -> list[PaymentResponse]:
        payments = await self.repo.list_all(contract_id=contract_id, status=status)
        return [self._to_response(p, user) for p in payments]

    async def create_payment(self, user: User, data: PaymentCreate, db: AsyncSession) -> PaymentResponse:
        contract = await self.contract_repo.get_by_id(data.contract_id)
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        if not self._can_edit_payment(user, contract):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
        payment = Payment(**data.model_dump())
        payment = await self.repo.create(payment)
        if payment.status == PaymentRecordStatus.PAID:
            await self._sync_contract_payment_status(db, contract.id)
        await log_audit(db, user.id, "CREATE", "payment", payment.id, new_data=data.model_dump(mode="json"))
        payment = await self.repo.get_by_id(payment.id)
        return self._to_response(payment, user)

    async def update_payment(
        self, user: User, payment_id: int, data: PaymentUpdate, db: AsyncSession
    ) -> PaymentResponse:
        payment = await self.repo.get_by_id(payment_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        if not self._can_edit_payment(user, payment.contract):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(payment, field, value)
        await self._sync_contract_payment_status(db, payment.contract_id)
        await log_audit(db, user.id, "UPDATE", "payment", payment.id, new_data=updates)
        payment = await self.repo.get_by_id(payment.id)
        return self._to_response(payment, user)
