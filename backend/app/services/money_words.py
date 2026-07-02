"""Суммы в рублях: цифрами с копейками и прописью (рус.)."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

try:
    from num2words import num2words
except ImportError:  # pragma: no cover
    num2words = None


def _quantize_money(amount) -> Decimal:
    return Decimal(str(amount or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _plural(n: int, forms: tuple[str, str, str]) -> str:
    n = abs(n) % 100
    if 11 <= n <= 19:
        return forms[2]
    n = n % 10
    if n == 1:
        return forms[0]
    if 2 <= n <= 4:
        return forms[1]
    return forms[2]


def _int_to_words_ru(n: int) -> str:
    if num2words is None:
        return str(n)
    return num2words(n, lang="ru")


def rubles_kopecks_digits(amount) -> tuple[str, str]:
    """('56 250', '00')"""
    value = _quantize_money(amount)
    rub = int(value)
    kop = int((value - Decimal(rub)) * 100)
    rub_str = f"{rub:,}".replace(",", " ")
    return rub_str, f"{kop:02d}"


def format_rub_kopecks(amount) -> str:
    rub, kop = rubles_kopecks_digits(amount)
    return f"{rub} руб. {kop} коп."


def rubles_in_words(amount) -> str:
    value = _quantize_money(amount)
    rub = int(value)
    kop = int((value - Decimal(rub)) * 100)
    rub_words = _int_to_words_ru(rub)
    rub_unit = _plural(rub, ("рубль", "рубля", "рублей"))
    if kop == 0:
        return f"{rub_words} {rub_unit} 00 копеек"
    kop_words = _int_to_words_ru(kop)
    kop_unit = _plural(kop, ("копейка", "копейки", "копеек"))
    return f"{rub_words} {rub_unit} {kop_words} {kop_unit}"


def format_rub_kopecks_with_words(amount) -> str:
    return f"{format_rub_kopecks(amount)} ({rubles_in_words(amount)})"
