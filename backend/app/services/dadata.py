"""DaData: find-party (ИНН/ОГРН), find-bank (БИК) — https://dadata.ru/api/"""
import re

import httpx

from app.core.config import settings

DADATA_BANK_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/bank"
DADATA_PARTY_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {settings.DADATA_API_KEY}",
    }


async def _dadata_post(url: str, body: dict) -> list:
    if not settings.DADATA_API_KEY:
        return []
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=body, headers=_headers())
        response.raise_for_status()
        return response.json().get("suggestions") or []


# --- Банк ---


def normalize_bik(bik: str | None) -> str | None:
    if not bik:
        return None
    digits = re.sub(r"\D", "", bik)
    return digits if len(digits) == 9 else None


async def fetch_bank_by_bik(bik: str) -> dict | None:
    normalized = normalize_bik(bik)
    if not normalized:
        return None
    suggestions = await _dadata_post(DADATA_BANK_URL, {"query": normalized})
    if not suggestions:
        return None
    return suggestions[0].get("data")


def map_bank_data_to_client_fields(data: dict) -> dict[str, str]:
    name_block = data.get("name") or {}
    bank_name = name_block.get("short") or name_block.get("payment") or ""
    result: dict[str, str] = {}
    if bank_name:
        result["bank_name"] = bank_name.strip()
    if data.get("bic"):
        result["bik"] = str(data["bic"])
    if data.get("correspondent_account"):
        result["correspondent_account"] = str(data["correspondent_account"])
    return result


async def enrich_client_bank_fields(
    fields: dict[str, str | None],
    filled: list[str],
) -> tuple[dict[str, str | None], list[str], list[str]]:
    warnings: list[str] = []
    new_filled: list[str] = []

    if not settings.DADATA_API_KEY:
        if fields.get("bik"):
            warnings.append(
                "DaData не настроен (DADATA_API_KEY в .env) — реквизиты банка не подгружены"
            )
        return fields, filled, warnings

    bik = fields.get("bik")
    if not bik:
        return fields, filled, warnings

    try:
        bank_data = await fetch_bank_by_bik(bik)
    except httpx.HTTPError as e:
        warnings.append(f"Ошибка DaData (банк): {e}")
        return fields, filled, warnings

    if not bank_data:
        warnings.append(f"Банк с БИК {bik} не найден в DaData")
        return fields, filled, warnings

    mapped = map_bank_data_to_client_fields(bank_data)
    for key, value in mapped.items():
        if value:
            fields[key] = value
            if key not in filled:
                new_filled.append(key)

    status = (bank_data.get("state") or {}).get("status")
    if status and status != "ACTIVE":
        warnings.append(f"Внимание: банк в статусе {status}")

    warnings.append("Банк загружен из DaData (find-bank)")
    return fields, filled + new_filled, warnings


# --- Организация (find-party) ---


def normalize_inn(inn: str | None) -> str | None:
    if not inn:
        return None
    digits = re.sub(r"\D", "", inn)
    return digits if len(digits) in (10, 12) else None


def normalize_ogrn(ogrn: str | None) -> str | None:
    if not ogrn:
        return None
    digits = re.sub(r"\D", "", ogrn)
    return digits if len(digits) in (13, 15) else None


def build_party_request_body(
    query: str,
    kpp: str | None = None,
    branch_type: str = "MAIN",
) -> dict | None:
    """
    query: ИНН, ОГРН или ИНН/КПП (7707083893/540602001) — как в документации find-party.
    """
    raw = query.strip()
    if not raw:
        return None

    body: dict = {"query": raw, "branch_type": branch_type}

    if "/" in raw:
        inn_part, kpp_part = raw.split("/", 1)
        inn_digits = re.sub(r"\D", "", inn_part)
        if len(inn_digits) not in (10, 12):
            return None
        body["query"] = inn_digits
        kpp_digits = re.sub(r"\D", "", kpp_part)
        if kpp_digits:
            body["kpp"] = kpp_digits
    else:
        digits = re.sub(r"\D", "", raw)
        if len(digits) in (10, 12):
            body["query"] = digits
            body["type"] = "INDIVIDUAL" if len(digits) == 12 else "LEGAL"
        elif len(digits) in (13, 15):
            body["query"] = digits
        else:
            return None
        if kpp:
            body["kpp"] = re.sub(r"\D", "", kpp)

    return body


async def fetch_party(
    query: str,
    kpp: str | None = None,
    branch_type: str = "MAIN",
) -> dict | None:
    """find-party: организация по ИНН, ОГРН или ИНН/КПП."""
    body = build_party_request_body(query, kpp=kpp, branch_type=branch_type)
    if not body or not settings.DADATA_API_KEY:
        return None
    suggestions = await _dadata_post(DADATA_PARTY_URL, body)
    if not suggestions:
        return None
    return suggestions[0].get("data")


async def fetch_party_by_inn(inn: str, kpp: str | None = None) -> dict | None:
    return await fetch_party(inn, kpp=kpp)


def _first_list_value(data: dict, key: str) -> str | None:
    items = data.get(key)
    if not items or not isinstance(items, list):
        return None
    item = items[0]
    if isinstance(item, dict):
        val = item.get("value")
        if not val and isinstance(item.get("data"), dict):
            val = item["data"].get("source")
        return str(val).strip() if val else None
    if isinstance(item, str):
        return item.strip() or None
    return None


def map_party_data_to_client_fields(data: dict) -> dict[str, str]:
    """Маппинг ответа find-party → поля клиента."""
    name = data.get("name") or {}
    mgmt = data.get("management") or {}
    address = (data.get("address") or {}).get("value") or ""

    short_name = name.get("short_with_opf") or name.get("short") or ""
    full_name = name.get("full_with_opf") or name.get("full") or short_name

    director = (mgmt.get("name") or "").strip()
    position = (mgmt.get("post") or "").strip()

    result: dict[str, str] = {}
    if short_name:
        result["company_name"] = short_name.strip()
    if full_name:
        result["full_company_name"] = full_name.strip()
    if data.get("inn"):
        result["inn"] = str(data["inn"])
    if data.get("kpp"):
        result["kpp"] = str(data["kpp"])
    if data.get("ogrn"):
        result["ogrn"] = str(data["ogrn"])
    if address:
        result["legal_address"] = address.strip()
    if director:
        result["director_name"] = director
        result["director_name_genitive"] = director
    if position:
        result["signer_position"] = position

    phone = _first_list_value(data, "phones")
    if phone:
        result["phone"] = phone
    email = _first_list_value(data, "emails")
    if email:
        result["email"] = email

    return result


async def enrich_client_party_fields(
    fields: dict[str, str | None],
    filled: list[str],
) -> tuple[dict[str, str | None], list[str], list[str]]:
    warnings: list[str] = []
    new_filled: list[str] = []

    if not settings.DADATA_API_KEY:
        if fields.get("inn") or fields.get("ogrn"):
            warnings.append("DaData не настроен — организация не подгружена (find-party)")
        return fields, filled, warnings

    query = fields.get("inn")
    kpp = fields.get("kpp")
    if not query:
        query = fields.get("ogrn")
        kpp = None
    if not query:
        return fields, filled, warnings

    try:
        party_data = await fetch_party(query, kpp=kpp)
    except httpx.HTTPError as e:
        warnings.append(f"Ошибка DaData (find-party): {e}")
        return fields, filled, warnings

    if not party_data:
        warnings.append(f"Организация не найдена в DaData по запросу {query}")
        return fields, filled, warnings

    mapped = map_party_data_to_client_fields(party_data)
    for key, value in mapped.items():
        if value:
            fields[key] = value
            if key not in filled:
                new_filled.append(key)

    status = (party_data.get("state") or {}).get("status")
    if status and status != "ACTIVE":
        warnings.append(f"Внимание: организация в статусе {status}")

    warnings.append("Организация загружена из DaData (find-party)")
    return fields, filled + new_filled, warnings
