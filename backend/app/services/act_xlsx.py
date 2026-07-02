"""Генерация акта выполненных работ (.xlsx) по шаблону NSK."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from app.core.config import get_templates_dir, settings
from app.models.client import Client
from app.models.contract import Contract
from app.services.excel_placeholders import fill_xlsx_template
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


def _act_date(d: date) -> str:
    return f"{d.day} {MONTHS_GENITIVE[d.month - 1]} {d.year}"


def _build_line_text(contract: Contract) -> str:
    fw = contract.parent.contract_number if contract.parent else contract.contract_number
    add_num = contract.addendum_number or ""
    d = contract.start_date or date.today()
    date_short = d.strftime("%d.%m.%Y")
    return (
        f"Услуги по договору {fw}, приложение №{add_num} от {date_short} "
        f"по подготовке необходимой документации для оформления."
    )


def _executor_block() -> str:
    return (
        f'Исполнитель: {settings.EXECUTOR_SHORT_NAME.strip()}\n'
        f"Адрес: {settings.EXECUTOR_LEGAL_ADDRESS.strip()}\n"
        f"ИНН: {settings.EXECUTOR_INN.strip()}\n"
        f"КПП: {settings.EXECUTOR_KPP.strip()}\n"
        f"Расчетный счет: {settings.EXECUTOR_SETTLEMENT_ACCOUNT.strip()}\n"
        f"Кор. счет: {settings.EXECUTOR_CORRESPONDENT_ACCOUNT.strip()}\n"
        f"Банк: {settings.EXECUTOR_BANK_NAME.strip()}\n"
        f"БИК: {settings.EXECUTOR_BIK.strip()}"
    )


def _customer_block(client: Client | None) -> str:
    if not client:
        return ""
    name = (client.company_name or client.full_company_name or "").strip()
    lines = [f"Заказчик: {name}"]
    if client.legal_address:
        lines.append(f"Адрес: {client.legal_address.strip()}")
    if client.inn:
        lines.append(f"ИНН: {client.inn.strip()}")
    if client.kpp:
        lines.append(f"КПП: {client.kpp.strip()}")
    if client.settlement_account:
        lines.append(f"Расчетный счет: {client.settlement_account.strip()}")
    if client.correspondent_account:
        lines.append(f"Кор. счет: {client.correspondent_account.strip()}")
    if client.bank_name:
        lines.append(f"Банк: {client.bank_name.strip()}")
    if client.bik:
        lines.append(f"БИК: {client.bik.strip()}")
    return "\n".join(lines)


def build_act_variables(
    contract: Contract, client: Client | None, act_date: date | None = None
) -> dict[str, str | float | int]:
    act_date = act_date or date.today()
    amount = float(Decimal(str(contract.amount or 0)).quantize(Decimal("0.01")))
    executor_sign = settings.EXECUTOR_DIRECTOR_SIGN.strip() or settings.EXECUTOR_DIRECTOR.strip()
    customer_rep = (client.director_name if client else "") or ""

    words = rubles_in_words(amount)
    if words:
        words = words[0].upper() + words[1:]

    return {
        "act_number": contract.id,
        "act_date": _act_date(act_date),
        "act_header": (
            f"АКТ №{contract.id}  от {_act_date(act_date)} г.\nна выполнение работ-услуг"
        ),
        "act_preamble": (
            f"        Мы, нижеподписавшиеся, {executor_sign} представитель ИСПОЛНИТЕЛЯ, "
            f"с одной стороны и {customer_rep} представитель ЗАКАЗЧИКА с другой стороны, "
            f"составили настоящий акт в том, что ИСПОЛНИТЕЛЬ выполнил, "
            f"а ЗАКАЗЧИК принял следующие работы:"
        ),
        "executor_sign": executor_sign,
        "customer_rep": customer_rep,
        "line_text": _build_line_text(contract),
        "line_unit": "шт",
        "line_qty": 1,
        "line_price": amount,
        "line_sum": amount,
        "total_sum": amount,
        "amount_words": f"Сумма прописью: {words}. Без НДС.",
        "done_text": (
            "Работы выполнены в полном объеме, в установленные сроки и с надлежащим качеством. "
            "Стороны претензий друг к другу не имеют."
        ),
        "executor_block": _executor_block(),
        "customer_block": _customer_block(client),
        "sign_executor_label": "Сдал",
        "sign_executor_name": executor_sign,
        "sign_customer_label": "Принял",
        "sign_customer_name": customer_rep,
    }


def build_act_filename(
    contract: Contract, client: Client | None, act_date: date | None = None
) -> str:
    client_part = (client.company_name if client else "акт").strip()
    add = f" доп{contract.addendum_number}" if contract.addendum_number else ""
    d = (act_date or date.today()).strftime("%d.%m.%Y")
    return f"Акт {client_part}{add} {d}.xlsx"


def save_act_xlsx(
    contract: Contract, client: Client | None, output_path: Path, act_date: date | None = None
) -> None:
    template = get_templates_dir() / "act_template.xlsx"
    if not template.is_file():
        raise FileNotFoundError(
            f"Шаблон акта не найден: {template}. Положите act_template.xlsx в backend/templates."
        )

    variables = build_act_variables(contract, client, act_date)
    fill_xlsx_template(template, output_path, variables)
