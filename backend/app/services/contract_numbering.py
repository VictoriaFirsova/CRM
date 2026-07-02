"""Нумерация договоров: {ИНИЦИАЛЫ}-NNN-ГГГГ (рамка), приложение №N к рамке."""
import re
from datetime import date

# ФВ-038-2022, ИП-001-2026
FRAMEWORK_NUMBER_RE = re.compile(
    r"^([А-ЯЁA-Z]{2})-(\d+)-(\d{4})$",
    re.IGNORECASE,
)


def normalize_contract_number(value: str) -> str:
    return " ".join(value.strip().split())


def format_framework_number(prefix: str, seq: int, year: int) -> str:
    return f"{prefix.upper()}-{seq:03d}-{year}"


def parse_framework_number(contract_number: str) -> tuple[str, int, int] | None:
    """Возвращает (префикс, порядковый номер, год) или None."""
    m = FRAMEWORK_NUMBER_RE.match(normalize_contract_number(contract_number))
    if not m:
        return None
    return m.group(1).upper(), int(m.group(2)), int(m.group(3))


def suggest_next_framework_number(
    existing_numbers: list[str],
    prefix: str,
    year: int | None = None,
) -> str:
    """Следующий номер: max(XXX) за год по всей CRM + 1; префикс — инициалы менеджера."""
    year = year or date.today().year
    prefix = prefix.upper()
    max_seq = max_sequence_for_year(existing_numbers, year)
    return format_framework_number(prefix, max_seq + 1, year)


def max_sequence_for_year(existing_numbers: list[str], year: int) -> int:
    max_seq = 0
    for num in existing_numbers:
        parsed = parse_framework_number(num)
        if parsed and parsed[2] == year:
            max_seq = max(max_seq, parsed[1])
    return max_seq


def format_sequence_year(seq: int, year: int) -> str:
    """Часть номера без префикса менеджера: 039-2026."""
    return f"{seq:03d}-{year}"


def suggest_next_addendum_number(existing: list[int]) -> int:
    return (max(existing) if existing else 0) + 1
