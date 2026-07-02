"""Префикс номера договора: первая буква фамилии + первая буква имени (Фирсова В.В. → ФВ)."""


def _first_letter(token: str) -> str | None:
    for ch in token.strip():
        if ch.isalpha():
            return ch.upper()
    return None


def manager_prefix_from_name(full_name: str) -> str:
    """
    «Фирсова Виктория Владимировна» → ФВ
    «Фирсова В.В.» → ФВ
    """
    cleaned = " ".join(full_name.strip().split())
    if not cleaned:
        return "ХХ"

    parts = cleaned.split()
    surname = _first_letter(parts[0]) or "Х"
    if len(parts) >= 2:
        name = _first_letter(parts[1]) or surname
    else:
        name = surname

    return f"{surname}{name}"
