"""Один раз: вставить {{ плейсхолдеры }} в act_template.xlsx, сохранив форматирование ячеек."""
from pathlib import Path

import openpyxl

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "act_template.xlsx"

# 1-based координаты (row, col) -> плейсхолдер
PLACEHOLDERS: dict[tuple[int, int], str] = {
    (1, 1): "{{ act_header }}",
    (2, 1): "{{ act_preamble }}",
    (6, 1): "{{ line_text }}",
    (6, 6): "{{ line_unit }}",
    (6, 9): "{{ line_qty }}",
    (6, 11): "{{ line_price }}",
    (6, 13): "{{ line_sum }}",
    (7, 13): "{{ total_sum }}",
    (8, 1): "{{ amount_words }}",
    (10, 1): "{{ done_text }}",
    (12, 2): "{{ executor_block }}",
    (12, 7): "{{ customer_block }}",
    (13, 2): "{{ sign_executor_label }}",
    (13, 4): "{{ sign_executor_name }}",
    (13, 8): "{{ sign_customer_label }}",
    (13, 12): "{{ sign_customer_name }}",
}


def main() -> None:
    if not TEMPLATE.is_file():
        raise SystemExit(f"Шаблон не найден: {TEMPLATE}")

    wb = openpyxl.load_workbook(str(TEMPLATE))
    ws = wb.active
    for (row, col), placeholder in PLACEHOLDERS.items():
        ws.cell(row, col).value = placeholder
    wb.save(str(TEMPLATE))
    print(f"OK: плейсхолдеры записаны в {TEMPLATE}")


if __name__ == "__main__":
    main()
