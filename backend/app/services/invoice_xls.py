"""Генерация счёта в .xls по шаблону (как в образцах NSK)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from app.core.config import get_templates_dir
from app.models.client import Client
from app.models.contract import Contract
from app.models.enums import InvoiceKind
from app.services.excel_placeholders import fill_xls_template
from app.services.money_words import rubles_in_words

MONTHS_GENITIVE = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def _invoice_date_header(d: date, invoice_number: int | None = None) -> str:
    num = f"{invoice_number} " if invoice_number else ""
    return f"Счет № {num} от {d.day} {MONTHS_GENITIVE[d.month - 1]} {d.year} г."


def _format_amount_display(amount: Decimal | float) -> str:
    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    rub = int(value)
    kop = int((value - rub) * 100)
    rub_str = f"{rub:,}".replace(",", " ")
    return f"{rub_str},{kop:02d}"


def _build_payment_line(contract: Contract, kind: InvoiceKind, advance_pct: int) -> str:
    fw = contract.parent.contract_number if contract.parent else contract.contract_number
    add_num = contract.addendum_number or ""
    inv_date = contract.start_date or date.today()
    date_short = inv_date.strftime("%d.%m.%Y")
    if kind == InvoiceKind.FULL:
        return f"Оплата услуг по договору {fw}, приложение №{add_num} от {date_short}"
    if kind == InvoiceKind.ADVANCE:
        return (
            f"Оплата (аванс {advance_pct}%) услуг по договору {fw}, "
            f"приложение №{add_num} от {date_short}"
        )
    balance_pct = 100 - advance_pct
    return (
        f"Оплата (остаток {balance_pct}%) услуг по договору {fw}, "
        f"приложение №{add_num} от {date_short}"
    )


def build_invoice_variables(
    contract: Contract,
    client: Client | None,
    kind: InvoiceKind,
    amount: float,
    invoice_number: int | None = None,
    invoice_date: date | None = None,
) -> dict[str, str | float]:
    inv_date = invoice_date or contract.start_date or date.today()
    advance_pct = contract.advance_percent if contract.advance_percent is not None else 100
    amount_dec = Decimal(str(amount)).quantize(Decimal("0.01"))
    amount_float = float(amount_dec)

    buyer = ""
    buyer_address = ""
    buyer_inn_kpp = ""
    if client:
        buyer = (client.company_name or client.full_company_name or "").strip()
        if client.legal_address:
            buyer_address = client.legal_address.strip()
        inn = (client.inn or "").strip()
        kpp = (client.kpp or "").strip()
        if inn or kpp:
            buyer_inn_kpp = f"{inn} /{kpp}" if inn and kpp else inn or kpp

    words = rubles_in_words(amount_dec)
    if words:
        words = words[0].upper() + words[1:]

    return {
        "invoice_number": invoice_number or "",
        "invoice_date_header": _invoice_date_header(inv_date, invoice_number),
        "buyer_name": buyer,
        "buyer_address": buyer_address,
        "buyer_inn_kpp": buyer_inn_kpp,
        "line_text": _build_payment_line(contract, kind, advance_pct),
        "line_qty": "1",
        "line_price": amount_float,
        "line_sum": amount_float,
        "line_vat": "0,00",
        "line_vat_pct": "-",
        "line_total": amount_float,
        "total_label": "Итого:",
        "total_qty": "1",
        "total_price_dash": "-",
        "total_sum": amount_float,
        "total_vat_pct": "-",
        "total_vat": "0,00",
        "total_amount": amount_float,
        "total_items_text": f"Всего наименований 1, на сумму {_format_amount_display(amount_dec)} рублей.",
        "amount_words": f"Сумма прописью: {words}. Без НДС." if words else "Сумма прописью: Без НДС.",
    }


def build_invoice_filename(
    contract: Contract,
    client: Client | None,
    kind: InvoiceKind,
    invoice_date: date | None = None,
) -> str:
    client_part = (client.company_name if client else "счет").strip()
    inv_date = (invoice_date or contract.start_date or date.today()).strftime("%d.%m.%Y")
    kind_label = {"ADVANCE": "аванс", "BALANCE": "остаток", "FULL": "100"}.get(kind.value, kind.value)
    add = f" доп{contract.addendum_number}" if contract.addendum_number else ""
    return f"Счет {client_part}{add} {kind_label} {inv_date}.xls"


def save_invoice_xls(
    contract: Contract,
    client: Client | None,
    kind: InvoiceKind,
    amount: float,
    output_path: Path,
    invoice_number: int | None = None,
    invoice_date: date | None = None,
) -> None:
    template = get_templates_dir() / "invoice_template.xls"
    if not template.is_file():
        raise FileNotFoundError(
            f"Шаблон счёта не найден: {template}. Положите invoice_template.xls в backend/templates."
        )

    variables = build_invoice_variables(
        contract, client, kind, amount, invoice_number, invoice_date=invoice_date
    )
    fill_xls_template(template, output_path, variables)
