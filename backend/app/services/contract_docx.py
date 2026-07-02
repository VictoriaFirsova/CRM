"""Сборка .docx: шаблоны docxtpl (как в образцах) или упрощённый fallback."""
import re
from pathlib import Path

from app.models.client import Client
from app.models.contract import Contract
from app.models.enums import ContractKind
from app.services.executor import _format_line_price, _format_rub, build_document_variables
from app.services.word_template import render_from_template, template_path

# ... keep fallback builders


def safe_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\r\n]+', "_", name).strip(" .")
    return cleaned[:180] or "document"


def download_filename(contract: Contract, client: Client | None) -> str:
    client_part = (client.company_name if client else "договор").strip()
    if contract.kind == ContractKind.ADDENDUM and contract.addendum_number is not None:
        parent_num = contract.parent.contract_number if contract.parent else contract.contract_number
        base = f"{client_part} {parent_num} доп {contract.addendum_number}"
    else:
        base = f"{client_part} {contract.contract_number}"
    return f"{safe_filename(base)}.docx"


def _add_requisites_table(doc, variables: dict[str, str]) -> None:
    doc.add_paragraph()
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    left, right = table.rows[0].cells

    def block(cell, title: str, lines: list[str]) -> None:
        parts = [title, *[line for line in lines if line]]
        cell.text = "\n".join(parts)

    block(
        left,
        "Исполнитель",
        [
            variables.get("executor_full_name", ""),
            variables.get("executor_legal_address", ""),
            f"ИНН/КПП {variables.get('executor_inn_kpp', '')}",
            f"р/с {variables.get('executor_settlement_account', '')}",
            variables.get("executor_bank_name", ""),
            f"БИК {variables.get('executor_bik', '')}",
            f"к/с {variables.get('executor_correspondent_account', '')}",
            variables.get("executor_director_sign", ""),
        ],
    )
    block(
        right,
        "Заказчик",
        [
            variables.get("customer_full_name", "") or variables.get("full_company_name", ""),
            variables.get("legal_address", ""),
            f"ИНН/КПП {variables.get('customer_inn_kpp', '')}",
            f"р/с {variables.get('settlement_account', '')}",
            variables.get("bank_name", ""),
            f"БИК {variables.get('bik', '')}",
            f"к/с {variables.get('correspondent_account', '')}",
            variables.get("director_name", ""),
        ],
    )


def build_addendum_docx(contract: Contract, client: Client | None):
    from docx import Document as DocxDocument

    variables = build_document_variables(contract, client)
    doc = DocxDocument()
    fw_num = variables.get("framework_number", contract.contract_number)
    fw_date = variables.get("framework_date", variables.get("date", ""))
    add_num = variables.get("addendum_number", "")

    doc.add_heading(
        f"Приложение №{add_num} к договору № {fw_num} от {fw_date}",
        level=0,
    )
    if variables.get("customer_preamble"):
        doc.add_paragraph(variables["customer_preamble"])
    if variables.get("executor_preamble"):
        doc.add_paragraph(variables["executor_preamble"])
    doc.add_paragraph(variables.get("table1_preamble", ""))

    lines = sorted(contract.line_items or [], key=lambda x: x.position)
    table = doc.add_table(rows=1 + max(len(lines), 1), cols=3)
    table.style = "Table Grid"
    headers = ("Наименование документа", "Продукция", "Стоимость работы")
    for idx, title in enumerate(headers):
        table.rows[0].cells[idx].text = title

    if lines:
        for row_idx, line in enumerate(lines, start=1):
            cells = table.rows[row_idx].cells
            cells[0].text = line.document_name
            cells[1].text = line.product_name
            cells[2].text = _format_line_price(line.price, line.vat_exempt)
    else:
        for idx in range(3):
            table.rows[1].cells[idx].text = ""

    if contract.work_days:
        doc.add_paragraph(f"Срок выполнения работ: {contract.work_days} рабочих дней.")
    doc.add_paragraph(f"Стоимость работ по настоящему приложению: {variables.get('total_amount', '')}.")
    if variables.get("payment_terms"):
        doc.add_paragraph(f"Порядок оплаты: {variables['payment_terms']}.")

    _add_requisites_table(doc, variables)
    return doc


def build_framework_docx(contract: Contract, client: Client | None):
    from docx import Document as DocxDocument

    variables = build_document_variables(contract, client)
    doc = DocxDocument()
    doc.add_heading(f"Рамочный договор № {contract.contract_number}", level=0)
    if contract.start_date:
        doc.add_paragraph(f"Дата: {contract.start_date.strftime('%d.%m.%Y')}")
    if variables.get("customer_preamble"):
        doc.add_paragraph(variables["customer_preamble"])
    if variables.get("executor_preamble"):
        doc.add_paragraph(variables["executor_preamble"])
    doc.add_paragraph(
        "Стороны заключили настоящий договор о возмездном оказании услуг по подготовке "
        "документации. Конкретный перечень работ, продукция и стоимость определяются "
        "в приложениях к настоящему договору."
    )
    if contract.comment:
        doc.add_paragraph(f"Комментарий: {contract.comment}")
    _add_requisites_table(doc, variables)
    return doc


def save_contract_docx(contract: Contract, client: Client | None, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if render_from_template(contract, client, output_path):
        return
    tpl = template_path(contract.kind)
    raise FileNotFoundError(
        f"Файл шаблона не найден: {tpl}. Положите addendum_template.docx и framework_template.docx "
        f"в папку backend/templates."
    )
