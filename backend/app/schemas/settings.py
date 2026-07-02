from pydantic import BaseModel, Field


class ExecutorSettingsResponse(BaseModel):
    """Исполнитель — одна организация; генеральный директор = подписант."""

    short_name: str = Field(description="Краткое наименование, напр. ООО «НСК-Серт»")
    full_name: str
    director: str = Field(description="ФИО в род. падеже для «в лице Генерального директора …»")
    director_sign: str = Field(description="Подпись в таблице реквизитов, напр. Дубинин Д.С.")
    legal_address: str = ""
    ogrn: str = ""
    inn: str = ""
    kpp: str = ""
    bank_name: str = ""
    settlement_account: str = ""
    correspondent_account: str = ""
    bik: str = ""
    acts_on_basis: str = "Устава"
    configured: bool = True
