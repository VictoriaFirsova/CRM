from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.models.enums import PaymentRecordStatus
from app.repositories.contract import ContractRepository
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentUpdate
from app.services.payment import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentResponse])
async def list_payments(
    current_user: CurrentUser,
    db: DbSession,
    contract_id: int | None = Query(None),
    status: PaymentRecordStatus | None = Query(None),
):
    service = PaymentService(PaymentRepository(db), ContractRepository(db))
    return await service.list_payments(current_user, contract_id=contract_id, status=status)


@router.post("", response_model=PaymentResponse, status_code=201)
async def create_payment(data: PaymentCreate, current_user: CurrentUser, db: DbSession):
    service = PaymentService(PaymentRepository(db), ContractRepository(db))
    return await service.create_payment(current_user, data, db)


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int, data: PaymentUpdate, current_user: CurrentUser, db: DbSession
):
    service = PaymentService(PaymentRepository(db), ContractRepository(db))
    return await service.update_payment(current_user, payment_id, data, db)
