from fastapi import APIRouter

from app.core.config import settings
from app.core.deps import CurrentUser
from app.schemas.settings import ExecutorSettingsResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/executor", response_model=ExecutorSettingsResponse)
async def get_executor_settings(current_user: CurrentUser):
    """Реквизиты исполнителя (НСК) — задаются в backend/.env, один на всю CRM."""
    _ = current_user
    configured = bool(settings.EXECUTOR_SHORT_NAME.strip() and settings.EXECUTOR_DIRECTOR.strip())
    return ExecutorSettingsResponse(
        short_name=settings.EXECUTOR_SHORT_NAME,
        full_name=settings.EXECUTOR_FULL_NAME,
        director=settings.EXECUTOR_DIRECTOR,
        director_sign=settings.EXECUTOR_DIRECTOR_SIGN or settings.EXECUTOR_DIRECTOR,
        legal_address=settings.EXECUTOR_LEGAL_ADDRESS,
        ogrn=settings.EXECUTOR_OGRN,
        inn=settings.EXECUTOR_INN,
        kpp=settings.EXECUTOR_KPP,
        bank_name=settings.EXECUTOR_BANK_NAME,
        settlement_account=settings.EXECUTOR_SETTLEMENT_ACCOUNT,
        correspondent_account=settings.EXECUTOR_CORRESPONDENT_ACCOUNT,
        bik=settings.EXECUTOR_BIK,
        acts_on_basis=settings.EXECUTOR_ACTS_ON_BASIS,
        configured=configured,
    )
