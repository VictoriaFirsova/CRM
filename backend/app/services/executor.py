"""Реквизиты исполнителя (НСК) — единые для всех договоров, из .env."""
from datetime import date

from app.core.config import settings
from app.models.client import Client
from app.models.contract import Contract
from app.services.money_words import format_rub_kopecks, format_rub_kopecks_with_words, rubles_in_words


def get_executor_variables() -> dict[str, str]:
    inn = settings.EXECUTOR_INN.strip()
    kpp = settings.EXECUTOR_KPP.strip()
    inn_kpp = f"{inn}/{kpp}" if inn and kpp else inn or kpp

    director = settings.EXECUTOR_DIRECTOR.strip()
    director_sign = settings.EXECUTOR_DIRECTOR_SIGN.strip() or director

    return {
        "executor_short_name": settings.EXECUTOR_SHORT_NAME.strip(),
        "executor_full_name": settings.EXECUTOR_FULL_NAME.strip(),
        "executor_director": director,
        "executor_director_sign": director_sign,
        "executor_legal_address": settings.EXECUTOR_LEGAL_ADDRESS.strip(),
        "executor_ogrn": settings.EXECUTOR_OGRN.strip(),
        "executor_inn": inn,
        "executor_kpp": kpp,
        "executor_inn_kpp": inn_kpp,
        "executor_bank_name": settings.EXECUTOR_BANK_NAME.strip(),
        "executor_settlement_account": settings.EXECUTOR_SETTLEMENT_ACCOUNT.strip(),
        "executor_correspondent_account": settings.EXECUTOR_CORRESPONDENT_ACCOUNT.strip(),
        "executor_bik": settings.EXECUTOR_BIK.strip(),
        "executor_acts_on_basis": settings.EXECUTOR_ACTS_ON_BASIS.strip(),
        "executor_preamble": _build_executor_preamble(),
    }


def _build_executor_preamble() -> str:
    full = settings.EXECUTOR_FULL_NAME.strip()
    director = settings.EXECUTOR_DIRECTOR.strip()
    basis = settings.EXECUTOR_ACTS_ON_BASIS.strip()
    if not full or not director:
        return ""
    return (
        f"{full} в лице Генерального директора {director}, "
        f"действующего на основании {basis}, именуемое в дальнейшем «Исполнитель»"
    )


_CUSTOMER_FIELD_KEYS = (
    "client_name",
    "customer_short_name",
    "full_company_name",
    "customer_full_name",
    "customer_director",
    "director_name",
    "director_name_genitive",
    "signer_position",
    "signer_basis",
    "customer_signer_position",
    "customer_signer_basis",
    "customer_signer_name_genitive",
    "inn",
    "kpp",
    "customer_inn_kpp",
    "ogrn",
    "legal_address",
    "actual_address",
    "bank_name",
    "bik",
    "correspondent_account",
    "settlement_account",
    "phone",
    "email",
    "customer_preamble",
)


def get_customer_variables(client: Client | None) -> dict[str, str]:
    if not client:
        return {k: "" for k in _CUSTOMER_FIELD_KEYS}

    full = (client.full_company_name or client.company_name or "").strip()
    short = (client.company_name or full).strip()
    director = (client.director_name or "").strip()
    director_genitive = (client.director_name_genitive or director).strip()
    signer_position = (client.signer_position or "Генерального директора").strip()
    signer_basis = (client.signer_basis or "Устава").strip()
    inn = (client.inn or "").strip()
    kpp = (client.kpp or "").strip()

    vars_map = {
        "client_name": short,
        "customer_short_name": short,
        "full_company_name": full,
        "customer_full_name": full,
        "customer_director": director,
        "director_name": director,
        "director_name_genitive": director_genitive,
        "signer_position": signer_position,
        "signer_basis": signer_basis,
        "customer_signer_position": signer_position,
        "customer_signer_basis": signer_basis,
        "customer_signer_name_genitive": director_genitive,
        "inn": inn,
        "kpp": kpp,
        "customer_inn_kpp": f"{inn}/{kpp}" if inn and kpp else inn or kpp,
        "ogrn": (client.ogrn or "").strip(),
        "legal_address": (client.legal_address or "").strip(),
        "actual_address": (client.actual_address or "").strip(),
        "bank_name": (client.bank_name or "").strip(),
        "bik": (client.bik or "").strip(),
        "correspondent_account": (client.correspondent_account or "").strip(),
        "settlement_account": (client.settlement_account or "").strip(),
        "phone": (client.phone or "").strip(),
        "email": (client.email or "").strip(),
        "customer_preamble": _build_customer_preamble(
            full,
            short,
            director_genitive,
            signer_position,
            signer_basis,
        ),
    }
    return vars_map


def _build_customer_preamble(
    full: str,
    short: str,
    signer_name_genitive: str,
    signer_position: str,
    signer_basis: str,
) -> str:
    name = full or short
    if not name:
        return ""
    if signer_name_genitive:
        return (
            f"{name} в лице {signer_position} {signer_name_genitive}, "
            f"действующего на основании {signer_basis}, именуемое в дальнейшем «Заказчик»"
        )
    return f"{name}, именуемое в дальнейшем «Заказчик»"


def _format_rub(amount) -> str:
    value = float(amount)
    formatted = f"{value:,.0f}".replace(",", " ")
    return f"{formatted} руб."


def _format_line_price(amount, vat_exempt: bool = True) -> str:
    text = _format_rub(amount)
    if vat_exempt:
        return f"{text} (НДС не облагается)"
    return text


def build_document_variables(contract: Contract, client: Client | None) -> dict[str, str]:
    variables = {}
    variables.update(get_executor_variables())
    variables.update(get_customer_variables(client))
    variables["contract_number"] = contract.contract_number
    variables["amount"] = _format_rub(contract.amount)
    variables["total_amount"] = variables["amount"]
    variables["date"] = date.today().strftime("%d.%m.%Y")
    variables["work_days"] = str(contract.work_days or "")
    advance = contract.advance_percent if contract.advance_percent is not None else 100
    balance = 100 - advance
    total = float(contract.amount or 0)
    advance_sum = total * advance / 100
    balance_sum = total * balance / 100

    variables["advance_percent"] = str(advance)
    variables["balance_percent"] = str(balance)
    variables["advance_amount"] = _format_rub(advance_sum)
    variables["balance_amount"] = _format_rub(balance_sum)
    variables["total_amount_kopecks"] = format_rub_kopecks(total)
    variables["total_amount_words"] = rubles_in_words(total)
    variables["total_amount_full"] = format_rub_kopecks_with_words(total)
    variables["advance_amount_kopecks"] = format_rub_kopecks(advance_sum)
    variables["advance_amount_words"] = rubles_in_words(advance_sum)
    variables["advance_amount_full"] = format_rub_kopecks_with_words(advance_sum)
    variables["balance_amount_kopecks"] = format_rub_kopecks(balance_sum)
    variables["balance_amount_words"] = rubles_in_words(balance_sum)
    variables["balance_amount_full"] = format_rub_kopecks_with_words(balance_sum)
    variables["is_full_payment"] = advance >= 100
    variables["payment_terms"] = (
        f"{advance}% — при заключении договора, {balance}% — после выполнения работ"
        if balance > 0
        else "100% — при заключении договора"
    )
    variables["payment_clause_5_partial"] = (
        f"Исполнитель приступает к исполнению своих обязательств после внесения Заказчиком "
        f"{advance}% суммы Договора, что составляет {variables['advance_amount_full']}, без НДС, "
        f"в соответствии с положениями статей 346.12 и 346.13 главы 26.2 Налогового кодекса "
        f"Российской Федерации (Уведомление №26.2-1). Оставшиеся {balance}% суммы, "
        f"что составляет {variables['balance_amount_full']}, без НДС, перечисляются Заказчиком "
        f"на расчетный счет Исполнителя в течении 5 (пяти) банковских дней после предоставления "
        f"Исполнителем скан-копии Сертификата соответствия на адрес электронной почты Заказчика"
    )
    variables["table1_preamble"] = (
        "Исполнитель оказывает услуги Заказчику по подготовке необходимой "
        "документации для оформления."
    )

    if contract.parent:
        variables["framework_number"] = contract.parent.contract_number
        parent_date = contract.parent.start_date
        variables["framework_date"] = parent_date.strftime("%d.%m.%Y") if parent_date else ""
    else:
        variables["framework_number"] = contract.contract_number
        variables["framework_date"] = (
            contract.start_date.strftime("%d.%m.%Y") if contract.start_date else variables["date"]
        )

    if contract.addendum_number is not None:
        variables["addendum_number"] = str(contract.addendum_number)
    else:
        variables["addendum_number"] = ""

    lines = sorted(contract.line_items or [], key=lambda x: x.position)
    for idx, line in enumerate(lines, start=1):
        variables[f"line_{idx}_document"] = line.document_name
        variables[f"line_{idx}_product"] = line.product_name
        variables[f"line_{idx}_price"] = _format_line_price(line.price, line.vat_exempt)
    variables["lines_count"] = str(len(lines))

    return variables
