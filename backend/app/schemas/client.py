from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ClientBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=500)
    full_company_name: str | None = Field(None, max_length=1000)
    inn: str | None = Field(None, max_length=12)
    kpp: str | None = Field(None, max_length=9)
    ogrn: str | None = Field(None, max_length=15)
    legal_address: str | None = None
    actual_address: str | None = None
    bank_name: str | None = Field(None, max_length=500)
    bik: str | None = Field(None, max_length=9)
    correspondent_account: str | None = Field(None, max_length=20)
    settlement_account: str | None = Field(None, max_length=20)
    director_name: str | None = Field(None, max_length=255)
    director_name_genitive: str | None = Field(None, max_length=255)
    signer_position: str | None = Field(None, max_length=255)
    signer_basis: str | None = Field(None, max_length=255)
    contact_person: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    company_name: str | None = Field(None, min_length=1, max_length=500)
    full_company_name: str | None = Field(None, max_length=1000)
    inn: str | None = Field(None, max_length=12)
    kpp: str | None = Field(None, max_length=9)
    ogrn: str | None = Field(None, max_length=15)
    legal_address: str | None = None
    actual_address: str | None = None
    bank_name: str | None = Field(None, max_length=500)
    bik: str | None = Field(None, max_length=9)
    correspondent_account: str | None = Field(None, max_length=20)
    settlement_account: str | None = Field(None, max_length=20)
    director_name: str | None = Field(None, max_length=255)
    director_name_genitive: str | None = Field(None, max_length=255)
    signer_position: str | None = Field(None, max_length=255)
    signer_basis: str | None = Field(None, max_length=255)
    contact_person: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None


class ClientResponse(ClientBase):
    id: int
    owner_id: int
    is_archived: bool = False
    archive_comment: str | None = None
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    can_edit: bool = True

    model_config = {"from_attributes": True}


class ClientArchiveRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=2000, description="Причина архивации")


class ClientParseFields(BaseModel):
    company_name: str | None = None
    full_company_name: str | None = None
    inn: str | None = None
    kpp: str | None = None
    ogrn: str | None = None
    legal_address: str | None = None
    actual_address: str | None = None
    bank_name: str | None = None
    bik: str | None = None
    correspondent_account: str | None = None
    settlement_account: str | None = None
    director_name: str | None = None
    director_name_genitive: str | None = None
    signer_position: str | None = None
    signer_basis: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class ClientParseResponse(BaseModel):
    fields: ClientParseFields
    filled: list[str]
    warnings: list[str] = []


class BankLookupResponse(BaseModel):
    bik: str
    bank_name: str | None = None
    correspondent_account: str | None = None
    found: bool = False
    message: str | None = None


class PartyLookupResponse(BaseModel):
    query: str = ""
    inn: str = ""
    company_name: str | None = None
    full_company_name: str | None = None
    kpp: str | None = None
    ogrn: str | None = None
    legal_address: str | None = None
    director_name: str | None = None
    director_name_genitive: str | None = None
    signer_position: str | None = None
    signer_basis: str | None = None
    phone: str | None = None
    email: str | None = None
    found: bool = False
    message: str | None = None


class ClientHistoryResponse(BaseModel):
    id: int
    client_id: int
    changed_by: int
    field_name: str
    old_value: str | None
    new_value: str | None
    changed_at: datetime

    model_config = {"from_attributes": True}
