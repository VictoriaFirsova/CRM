from datetime import date

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.core.deps import CurrentUser, DbSession
from app.models.enums import ContractStatus, PaymentStatus, ProductionStatus
from app.repositories.client import ClientRepository
from app.repositories.contract import ContractRepository
from app.repositories.document import DocumentRepository
from app.schemas.act import ActCreateRequest, ActGenerateBody, ActResponse
from app.schemas.contract import (
    AddendumNumberSuggestResponse,
    ContractCreate,
    ContractDuplicateCheckResponse,
    ContractListResponse,
    ContractNumberSuggestResponse,
    ContractResponse,
    ContractUpdate,
)
from app.services.act import ActService
from app.services.contract import ContractService
from app.services.document import DocumentService
from app.repositories.document import DocumentRepository

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _service(db) -> ContractService:
    return ContractService(ContractRepository(db), ClientRepository(db), DocumentRepository(db))


def _document_service(db) -> DocumentService:
    return DocumentService(DocumentRepository(db), ContractRepository(db))


def _act_service(db) -> ActService:
    return ActService(DocumentRepository(db), ContractRepository(db))


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    current_user: CurrentUser,
    db: DbSession,
    contract_status: ContractStatus | None = Query(None),
    payment_status: PaymentStatus | None = Query(None),
    production_status: ProductionStatus | None = Query(None),
    responsible_manager_id: int | None = Query(None),
    client_id: int | None = Query(None),
    contract_number: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    items, total = await _service(db).list_contracts(
        current_user,
        contract_status=contract_status,
        payment_status=payment_status,
        production_status=production_status,
        responsible_manager_id=responsible_manager_id,
        client_id=client_id,
        contract_number=contract_number,
        date_from=date_from,
        date_to=date_to,
        search=search,
        skip=skip,
        limit=limit,
    )
    return ContractListResponse(items=items, total=total)


@router.get("/suggest-number", response_model=ContractNumberSuggestResponse)
async def suggest_framework_number(
    current_user: CurrentUser,
    db: DbSession,
    year: int | None = Query(None, ge=2000, le=2100),
):
    return await _service(db).suggest_framework_number(current_user, year=year)


@router.get("/suggest-addendum", response_model=AddendumNumberSuggestResponse)
async def suggest_addendum_number(
    current_user: CurrentUser,
    db: DbSession,
    parent_contract_id: int = Query(...),
):
    return await _service(db).suggest_addendum_number(parent_contract_id)


@router.get("/check-number", response_model=ContractDuplicateCheckResponse)
async def check_contract_number(
    current_user: CurrentUser,
    db: DbSession,
    contract_number: str = Query(...),
    exclude_id: int | None = Query(None),
):
    return await _service(db).check_framework_number(contract_number, exclude_id=exclude_id)


@router.get("/check-addendum", response_model=ContractDuplicateCheckResponse)
async def check_addendum_number(
    current_user: CurrentUser,
    db: DbSession,
    parent_contract_id: int = Query(...),
    addendum_number: int = Query(..., ge=1),
    exclude_id: int | None = Query(None),
):
    return await _service(db).check_addendum_number(
        parent_contract_id, addendum_number, exclude_id=exclude_id
    )


@router.get("/frameworks", response_model=list[ContractResponse])
async def list_framework_contracts(
    current_user: CurrentUser,
    db: DbSession,
    client_id: int | None = Query(None),
):
    return await _service(db).list_frameworks(current_user, client_id=client_id)


@router.post("", response_model=ContractResponse, status_code=201)
async def create_contract(data: ContractCreate, current_user: CurrentUser, db: DbSession):
    return await _service(db).create_contract(current_user, data, db)


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: int, current_user: CurrentUser, db: DbSession):
    return await _service(db).get_contract(current_user, contract_id)


@router.get("/{contract_id}/download-docx")
async def download_contract_docx(
    contract_id: int, current_user: CurrentUser, db: DbSession
):
    """Сформировать и скачать договор / приложение в Word."""
    path, filename = await _document_service(db).build_contract_docx_file(
        current_user, contract_id, db
    )
    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/{contract_id}/generate-act", response_model=ActResponse, status_code=201)
async def generate_act(
    contract_id: int,
    current_user: CurrentUser,
    db: DbSession,
    body: ActGenerateBody | None = None,
):
    """Акт выполненных работ (xlsx) — когда этап «Готов»."""
    return await _act_service(db).generate_act(
        current_user,
        ActCreateRequest(contract_id=contract_id, act_date=body.act_date if body else None),
        db,
    )


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int, data: ContractUpdate, current_user: CurrentUser, db: DbSession
):
    return await _service(db).update_contract(current_user, contract_id, data, db)


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(contract_id: int, current_user: CurrentUser, db: DbSession):
    await _service(db).delete_contract(current_user, contract_id, db)
