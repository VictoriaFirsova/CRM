from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.core.deps import CurrentUser, DbSession
from app.repositories.contract import ContractRepository
from app.repositories.document import DocumentRepository
from app.schemas.act import ActCreateRequest, ActResponse, ActUpdateRequest
from app.services.act import ActService

router = APIRouter(prefix="/acts", tags=["acts"])


def _service(db: DbSession) -> ActService:
    return ActService(DocumentRepository(db), ContractRepository(db))


@router.get("", response_model=list[ActResponse])
async def list_acts(
    current_user: CurrentUser,
    db: DbSession,
    contract_id: int | None = Query(None),
):
    return await _service(db).list_acts(current_user, contract_id=contract_id)


@router.post("", response_model=ActResponse, status_code=201)
async def create_act(data: ActCreateRequest, current_user: CurrentUser, db: DbSession):
    return await _service(db).generate_act(current_user, data, db)


@router.delete("/{act_id}", status_code=204)
async def delete_act(act_id: int, current_user: CurrentUser, db: DbSession):
    await _service(db).delete_act(current_user, act_id, db)


@router.put("/{act_id}", response_model=ActResponse)
async def update_act(
    act_id: int, data: ActUpdateRequest, current_user: CurrentUser, db: DbSession
):
    return await _service(db).update_act(current_user, act_id, data, db)


@router.get("/{act_id}/download")
async def download_act(act_id: int, current_user: CurrentUser, db: DbSession):
    service = _service(db)
    doc = await service.get_act_document(act_id)
    path, filename = service.download_path(doc)
    return FileResponse(
        path=path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
