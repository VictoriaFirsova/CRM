from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.core.deps import CurrentUser, DbSession
from app.repositories.contract import ContractRepository
from app.repositories.invoice import InvoiceRepository
from app.schemas.invoice import InvoiceCreateRequest, InvoiceResponse, InvoiceUpdateRequest
from app.services.invoice import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _service(db: DbSession) -> InvoiceService:
    return InvoiceService(InvoiceRepository(db), ContractRepository(db))


@router.get("", response_model=list[InvoiceResponse])
async def list_invoices(
    current_user: CurrentUser,
    db: DbSession,
    contract_id: int | None = Query(None),
):
    return await _service(db).list_invoices(current_user, contract_id=contract_id)


@router.post("", response_model=InvoiceResponse, status_code=201)
async def create_invoice(data: InvoiceCreateRequest, current_user: CurrentUser, db: DbSession):
    return await _service(db).create_invoice(current_user, data, db)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    return await _service(db).update_invoice(current_user, invoice_id, data, db)


@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(invoice_id: int, current_user: CurrentUser, db: DbSession):
    await _service(db).delete_invoice(current_user, invoice_id, db)


@router.get("/{invoice_id}/download")
async def download_invoice(invoice_id: int, current_user: CurrentUser, db: DbSession):
    service = _service(db)
    inv = await service.get_invoice(invoice_id)
    path, filename = service.download_path(inv)
    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/vnd.ms-excel",
    )
