from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import ProductionStatus


class ActCreateRequest(BaseModel):
    contract_id: int
    act_date: date | None = None


class ActGenerateBody(BaseModel):
    act_date: date | None = None


class ActUpdateRequest(BaseModel):
    act_date: date = Field(..., description="Дата акта в документе")


class ActResponse(BaseModel):
    id: int
    contract_id: int
    amount: Decimal
    act_date: date
    generated_at: datetime
    contract_number: str | None = None
    client_name: str | None = None
    addendum_number: int | None = None
    production_status: ProductionStatus | None = None
    can_edit: bool = False
    can_download: bool = True

    model_config = {"from_attributes": True}
