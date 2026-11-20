"""Выгрузка выбранных строк расчёта ЗП в Excel (как на странице)."""
from __future__ import annotations

from io import BytesIO

from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from app.schemas.payroll import PayrollLineResponse

HEADERS = (
    "Договор",
    "Документ",
    "Продукция",
    "Цена",
    "Себ-ть",
    "В ЗП",
    "÷2",
)

PAYMENT_LABELS = {
    "PAID": "Оплачен",
    "PARTIALLY_PAID": "Частично оплачен",
    "NOT_PAID": "Не оплачен",
}


def _contract_cell(row: PayrollLineResponse) -> str:
    parts = [row.contract_label]
    if row.client_name:
        parts.append(row.client_name)
    status = PAYMENT_LABELS.get(
        row.payment_status.value if hasattr(row.payment_status, "value") else str(row.payment_status),
        str(row.payment_status),
    )
    date_part = row.start_date.strftime("%d.%m.%Y") if row.start_date else None
    meta = status if not date_part else f"{status} · {date_part}"
    parts.append(meta)
    return "\n".join(parts)


def build_payroll_xlsx(rows: list[PayrollLineResponse]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Расчёт ЗП"

    header_font = Font(bold=True)
    for col, title in enumerate(HEADERS, start=1):
        cell = ws.cell(1, col, title)
        cell.font = header_font

    for r_idx, row in enumerate(rows, start=2):
        ws.cell(r_idx, 1, _contract_cell(row)).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(r_idx, 2, row.document_name).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(r_idx, 3, row.product_name).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(r_idx, 4, float(row.price))
        ws.cell(r_idx, 5, float(row.cost_price) if row.cost_price is not None else None)
        ws.cell(r_idx, 6, float(row.reward_mine))
        ws.cell(r_idx, 7, "да" if row.share_half else "нет")

    widths = (28, 22, 36, 12, 12, 12, 8)
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + i)].width = w

    # Итого по «В ЗП» выбранных
    total_row = len(rows) + 2
    total = sum((r.reward_mine for r in rows), Decimal("0"))
    ws.cell(total_row, 5, "Итого В ЗП").font = header_font
    ws.cell(total_row, 6, float(total))

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
