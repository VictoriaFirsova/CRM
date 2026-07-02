from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DocumentType


class DocumentGenerateRequest(BaseModel):
    contract_id: int
    document_type: DocumentType


class DocumentResponse(BaseModel):
    id: int
    contract_id: int
    client_id: int
    type: DocumentType
    file_path: str
    generated_at: datetime
    generated_by: int | None

    model_config = {"from_attributes": True}
