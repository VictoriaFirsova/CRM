from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ContractKind, ContractStatus, PaymentStatus, ProductionStatus


class ContractLineItemInput(BaseModel):
    document_name: str = Field(min_length=1, max_length=500)
    product_name: str = Field(min_length=1, max_length=5000)
    price: Decimal = Field(ge=0)
    vat_exempt: bool = True


class ContractLineItemResponse(ContractLineItemInput):
    id: int
    contract_id: int
    position: int

    model_config = {"from_attributes": True}


class ContractBase(BaseModel):
    client_id: int
    contract_number: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(ge=0, default=Decimal("0"))
    contract_status: ContractStatus = ContractStatus.OPEN
    payment_status: PaymentStatus = PaymentStatus.NOT_PAID
    production_status: ProductionStatus = ProductionStatus.REQUEST
    comment: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ContractCreate(BaseModel):
    kind: ContractKind = ContractKind.FRAMEWORK
    client_id: int
    parent_contract_id: int | None = None
    contract_number: str | None = Field(None, max_length=100)
    addendum_number: int | None = Field(None, ge=1)
    title: str | None = Field(None, max_length=500)
    amount: Decimal | None = Field(None, ge=0)
    contract_status: ContractStatus = ContractStatus.OPEN
    payment_status: PaymentStatus = PaymentStatus.NOT_PAID
    production_status: ProductionStatus = ProductionStatus.REQUEST
    comment: str | None = None
    work_days: int | None = Field(None, ge=1, le=999)
    advance_percent: int | None = Field(None, ge=1, le=100)
    line_items: list[ContractLineItemInput] | None = None
    start_date: date | None = None
    end_date: date | None = None
    responsible_manager_id: int | None = None
    allow_duplicate: bool = False

    @model_validator(mode="after")
    def validate_kind_fields(self) -> "ContractCreate":
        if self.kind == ContractKind.ADDENDUM:
            if self.advance_percent is None:
                self.advance_percent = 100
            if not self.parent_contract_id:
                raise ValueError("Для приложения укажите рамочный договор (parent_contract_id)")
            if not self.title or not str(self.title).strip():
                raise ValueError("Укажите название приложения")
            if not self.line_items:
                raise ValueError("Добавьте хотя бы одну строку в таблицу (документ, продукция, стоимость)")
        elif self.parent_contract_id:
            raise ValueError("parent_contract_id только для приложений")
        return self


class ContractUpdate(BaseModel):
    contract_number: str | None = None
    addendum_number: int | None = Field(None, ge=1)
    title: str | None = None
    amount: Decimal | None = None
    contract_status: ContractStatus | None = None
    payment_status: PaymentStatus | None = None
    production_status: ProductionStatus | None = None
    comment: str | None = None
    work_days: int | None = Field(None, ge=1, le=999)
    advance_percent: int | None = Field(None, ge=1, le=100)
    line_items: list[ContractLineItemInput] | None = None
    start_date: date | None = None
    end_date: date | None = None
    responsible_manager_id: int | None = None
    allow_duplicate: bool = False


class ContractResponse(ContractBase):
    id: int
    kind: ContractKind
    parent_contract_id: int | None = None
    addendum_number: int | None = None
    number_prefix: str | None = None
    responsible_manager_id: int
    created_at: datetime
    updated_at: datetime
    can_edit: bool = True
    client_name: str | None = None
    manager_name: str | None = None
    parent_contract_number: str | None = None
    display_label: str | None = None
    work_days: int | None = None
    advance_percent: int | None = None
    line_items: list[ContractLineItemResponse] = []

    model_config = {"from_attributes": True}


class ContractListResponse(BaseModel):
    items: list[ContractResponse]
    total: int


class ContractNumberSuggestResponse(BaseModel):
    suggested: str
    year: int
    prefix: str
    manager_name: str | None = None


class AddendumNumberSuggestResponse(BaseModel):
    suggested: int
    parent_contract_id: int
    parent_contract_number: str


class ContractDuplicateCheckResponse(BaseModel):
    exists: bool
    message: str | None = None
    existing_id: int | None = None
    existing_title: str | None = None
