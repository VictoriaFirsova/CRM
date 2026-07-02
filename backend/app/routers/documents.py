from pathlib import Path

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.deps import CurrentUser, DbSession
from app.models.enums import DocumentType
from app.repositories.contract import ContractRepository
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentGenerateRequest, DocumentResponse
from app.services.act import ActService
from app.services.act_xlsx import build_act_filename
from app.services.document import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def _service(db) -> DocumentService:
    return DocumentService(DocumentRepository(db), ContractRepository(db))


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    current_user: CurrentUser,
    db: DbSession,
    contract_id: int | None = Query(None),
):
    return await _service(db).list_documents(contract_id=contract_id)


@router.post("/generate", response_model=DocumentResponse, status_code=201)
async def generate_document(data: DocumentGenerateRequest, current_user: CurrentUser, db: DbSession):
    return await _service(db).generate(current_user, data, db)


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    current_user: CurrentUser,
    db: DbSession,
    contract_id: int = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
):
    return await _service(db).upload(current_user, contract_id, document_type, file, db)


@router.get("/{doc_id}")
async def download_document(doc_id: int, current_user: CurrentUser, db: DbSession):
    svc = _service(db)
    doc = await svc.get_document(doc_id)
    path = Path(doc.file_path)
    if not path.is_file():
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if doc.type == DocumentType.ACT:
        contract = await svc.contract_repo.get_by_id(doc.contract_id)
        client = contract.client if contract else None
        act_date = doc.document_date or (doc.generated_at.date() if doc.generated_at else None)
        filename = (
            build_act_filename(contract, client, act_date)
            if contract
            else f"act_{doc.id}.xlsx"
        )
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        filename = path.name
        media = "application/octet-stream"
    return FileResponse(path=path, filename=filename, media_type=media)
