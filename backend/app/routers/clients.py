import re

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.repositories.client import ClientRepository
from app.schemas.client import (
    BankLookupResponse,
    ClientArchiveRequest,
    ClientCreate,
    ClientHistoryResponse,
    ClientParseFields,
    ClientParseResponse,
    ClientResponse,
    ClientUpdate,
    PartyLookupResponse,
)
from app.services.client import ClientService
from app.services.dadata import (
    enrich_client_bank_fields,
    enrich_client_party_fields,
    fetch_bank_by_bik,
    fetch_party,
    map_bank_data_to_client_fields,
    map_party_data_to_client_fields,
    normalize_bik,
    normalize_inn,
    normalize_ogrn,
)
from app.services.docx_parser import parse_client_requisites
from app.services.word_convert import WordConvertError, ensure_docx_bytes


def _validate_party_query(query: str) -> None:
    raw = query.strip()
    if "/" in raw:
        if not normalize_inn(raw.split("/", 1)[0]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Некорректный ИНН в формате ИНН/КПП",
            )
        return
    digits = re.sub(r"\D", "", raw)
    if not normalize_inn(digits) and not normalize_ogrn(digits):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ИНН (10/12 цифр), ОГРН (13/15) или ИНН/КПП (7707083893/540602001)",
        )


async def _do_party_lookup(query: str, kpp: str | None) -> PartyLookupResponse:
    raw = query.strip()
    if not settings.DADATA_API_KEY:
        return PartyLookupResponse(
            query=raw,
            found=False,
            message="Укажите DADATA_API_KEY в backend/.env (dadata.ru)",
        )
    data = await fetch_party(raw, kpp=kpp)
    if not data:
        return PartyLookupResponse(
            query=raw,
            inn=normalize_inn(raw) or normalize_ogrn(raw) or "",
            found=False,
            message="Организация не найдена в DaData",
        )
    mapped = map_party_data_to_client_fields(data)
    return PartyLookupResponse(
        query=raw,
        inn=mapped.get("inn", normalize_inn(raw) or ""),
        company_name=mapped.get("company_name"),
        full_company_name=mapped.get("full_company_name"),
        kpp=mapped.get("kpp"),
        ogrn=mapped.get("ogrn"),
        legal_address=mapped.get("legal_address"),
        director_name=mapped.get("director_name"),
        director_name_genitive=mapped.get("director_name_genitive"),
        signer_position=mapped.get("signer_position"),
        signer_basis=mapped.get("signer_basis"),
        phone=mapped.get("phone"),
        email=mapped.get("email"),
        found=True,
        message="Данные из DaData find-party",
    )

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/parse-docx", response_model=ClientParseResponse)
async def parse_client_docx(
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    if current_user.role.value == "VIEWER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewers cannot import")
    name = (file.filename or "").lower()
    if not (name.endswith(".docx") or name.endswith(".doc")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются файлы Word: .docx и .doc",
        )
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл слишком большой (макс. 10 МБ)")
    try:
        docx_bytes = ensure_docx_bytes(content, file.filename or "file.docx")
    except WordConvertError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    try:
        result = parse_client_requisites(docx_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка разбора файла: {e}",
        ) from e

    fields, filled, party_warnings = await enrich_client_party_fields(result["fields"], result["filled"])
    fields, filled, bank_warnings = await enrich_client_bank_fields(fields, filled)
    result["fields"] = fields
    result["filled"] = list(dict.fromkeys(filled))
    result["warnings"] = result["warnings"] + party_warnings + bank_warnings

    return ClientParseResponse(
        fields=ClientParseFields(**result["fields"]),
        filled=result["filled"],
        warnings=result["warnings"],
    )


@router.get("/lookup-bank/{bik}", response_model=BankLookupResponse)
async def lookup_bank_by_bik(current_user: CurrentUser, bik: str):
    if current_user.role.value == "VIEWER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    normalized = normalize_bik(bik)
    if not normalized:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="БИК должен содержать 9 цифр")

    if not settings.DADATA_API_KEY:
        return BankLookupResponse(
            bik=normalized,
            found=False,
            message="Укажите DADATA_API_KEY в backend/.env (ключ с dadata.ru)",
        )

    try:
        data = await fetch_bank_by_bik(normalized)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка DaData: {e}",
        ) from e

    if not data:
        return BankLookupResponse(
            bik=normalized,
            found=False,
            message="Банк не найден",
        )

    mapped = map_bank_data_to_client_fields(data)
    return BankLookupResponse(
        bik=mapped.get("bik", normalized),
        bank_name=mapped.get("bank_name"),
        correspondent_account=mapped.get("correspondent_account"),
        found=True,
        message="Данные банка из DaData",
    )


@router.get("/lookup-party/{query}", response_model=PartyLookupResponse)
async def lookup_party_by_query(
    current_user: CurrentUser,
    query: str,
    kpp: str | None = Query(None),
):
    """find-party: ИНН, ОГРН или ИНН/КПП — https://dadata.ru/api/find-party/"""
    if current_user.role.value == "VIEWER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    _validate_party_query(query)
    try:
        return await _do_party_lookup(query, kpp=kpp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Ошибка DaData: {e}") from e


@router.get("/lookup-inn/{inn}", response_model=PartyLookupResponse)
async def lookup_party_by_inn(
    current_user: CurrentUser,
    inn: str,
    kpp: str | None = Query(None),
):
    """Совместимость: то же, что lookup-party."""
    if current_user.role.value == "VIEWER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    _validate_party_query(inn)
    try:
        return await _do_party_lookup(inn, kpp=kpp)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Ошибка DaData: {e}") from e


@router.get("", response_model=list[ClientResponse])
async def list_clients(
    current_user: CurrentUser,
    db: DbSession,
    search: str | None = Query(None),
    archived: bool = Query(False),
):
    service = ClientService(ClientRepository(db))
    return await service.list_clients(current_user, search=search, archived=archived)


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(data: ClientCreate, current_user: CurrentUser, db: DbSession):
    service = ClientService(ClientRepository(db))
    return await service.create_client(current_user, data, db)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, current_user: CurrentUser, db: DbSession):
    service = ClientService(ClientRepository(db))
    return await service.get_client(current_user, client_id)


@router.get("/{client_id}/history", response_model=list[ClientHistoryResponse])
async def get_client_history(client_id: int, current_user: CurrentUser, db: DbSession):
    service = ClientService(ClientRepository(db))
    await service.get_client(current_user, client_id)
    repo = ClientRepository(db)
    return await repo.get_history(client_id)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: int, data: ClientUpdate, current_user: CurrentUser, db: DbSession):
    service = ClientService(ClientRepository(db))
    return await service.update_client(current_user, client_id, data, db)


@router.post("/{client_id}/archive", response_model=ClientResponse)
async def archive_client(
    client_id: int, data: ClientArchiveRequest, current_user: CurrentUser, db: DbSession
):
    service = ClientService(ClientRepository(db))
    return await service.archive_client(current_user, client_id, data, db)


@router.post("/{client_id}/unarchive", response_model=ClientResponse)
async def unarchive_client(client_id: int, current_user: CurrentUser, db: DbSession):
    service = ClientService(ClientRepository(db))
    return await service.unarchive_client(current_user, client_id, db)


@router.delete("/{client_id}", status_code=204)
async def delete_client(client_id: int, current_user: CurrentUser, db: DbSession):
    service = ClientService(ClientRepository(db))
    await service.delete_client(current_user, client_id, db)
