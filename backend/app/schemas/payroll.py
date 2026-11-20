from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import PaymentStatus


class PayrollLineUpdate(BaseModel):
    cost_price: Decimal | None = Field(None, ge=0)
    share_half: bool | None = None
    salary_paid: bool | None = None


class PayrollLineResponse(BaseModel):
    id: int
    contract_id: int
    contract_label: str
    client_name: str | None = None
    document_name: str
    product_name: str
    price: Decimal
    cost_price: Decimal | None = None
    share_half: bool
    salary_paid: bool
    reward_full: Decimal
    reward_mine: Decimal
    payment_status: PaymentStatus
    start_date: date | None = None
    year: int | None = None


class PayrollListResponse(BaseModel):
    items: list[PayrollLineResponse]
    total_to_pay: Decimal
    total_paid: Decimal
    total_all: Decimal
