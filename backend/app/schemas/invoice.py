from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import InvoiceKind, PaymentRecordStatus


class InvoiceCreateRequest(BaseModel):
    contract_id: int
    kind: InvoiceKind
    invoice_date: date | None = None


class InvoiceUpdateRequest(BaseModel):
    status: PaymentRecordStatus | None = None
    invoice_date: date | None = Field(None, description="Дата в шапке счёта")


class InvoiceResponse(BaseModel):
    id: int
    contract_id: int
    kind: InvoiceKind
    amount: Decimal
    invoice_date: date
    status: PaymentRecordStatus
    created_at: datetime
    created_by: int | None = None
    contract_number: str | None = None
    client_name: str | None = None
    addendum_number: int | None = None
    can_download: bool = True
    can_edit: bool = False

    model_config = {"from_attributes": True}
