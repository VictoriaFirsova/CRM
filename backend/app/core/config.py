from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ — всегда ищем .env здесь, даже если PyCharm запускает из корня CRM
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


def normalize_database_url(url: str) -> str:
    """Railway/Heroku дают postgres://…; SQLAlchemy + asyncpg ждут postgresql+asyncpg://."""
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]
    url = url.replace("sslmode=require", "ssl=require")
    if "railway" in url and "ssl=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}ssl=require"
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://crm:crm@localhost:5432/crm"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    UPLOAD_DIR: str = "./uploads"
    # Пусто = backend/templates (шаблоны в репозитории, для сервера)
    TEMPLATES_DIR: str = ""
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    PORT: int = 8000
    DADATA_API_KEY: str = ""
    # Исполнитель (НСК) — один на все договоры; director = генеральный директор (одно лицо)
    EXECUTOR_SHORT_NAME: str = "ООО «НСК-Серт»"
    EXECUTOR_FULL_NAME: str = (
        "Общество с ограниченной ответственностью «Национальная Сертификационная Компания» "
        "(ООО «НСК-Серт»)"
    )
    EXECUTOR_DIRECTOR: str = "Дубинина Дениса Сергеевича"
    EXECUTOR_DIRECTOR_SIGN: str = "Дубинин Д.С."
    EXECUTOR_LEGAL_ADDRESS: str = (
        "124482, Москва, г. Зеленоград, проезд Савёлкинский, д. 4, пом. XXI, эт. 13, ком. 13-2"
    )
    EXECUTOR_OGRN: str = "1157746366293"
    EXECUTOR_INN: str = "7717286500"
    EXECUTOR_KPP: str = "773501001"
    EXECUTOR_BANK_NAME: str = "АО «Альфа-Банк» г. Москва"
    EXECUTOR_SETTLEMENT_ACCOUNT: str = "40702810802840001019"
    EXECUTOR_CORRESPONDENT_ACCOUNT: str = "30101810200000000593"
    EXECUTOR_BIK: str = "044525593"
    EXECUTOR_ACTS_ON_BASIS: str = "Устава"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _async_database_url(cls, value: str) -> str:
        return normalize_database_url(str(value)) if value else value


def get_templates_dir() -> Path:
    """Каталог шаблонов Word (всегда внутри backend/templates на сервере)."""
    if settings.TEMPLATES_DIR.strip():
        p = Path(settings.TEMPLATES_DIR)
        return p if p.is_absolute() else BACKEND_DIR / p
    return BACKEND_DIR / "templates"


settings = Settings()
