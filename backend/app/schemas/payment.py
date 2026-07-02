from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import PaymentRecordStatus


class PaymentBase(BaseModel):
    contract_id: int
    amount: Decimal = Field(gt=0)
    payment_date: date | None = None
    status: PaymentRecordStatus = PaymentRecordStatus.PENDING
    comment: str | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    amount: Decimal | None = None
    payment_date: date | None = None
    status: PaymentRecordStatus | None = None
    comment: str | None = None


class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime
    can_edit: bool = True
    contract_number: str | None = None

    model_config = {"from_attributes": True}
