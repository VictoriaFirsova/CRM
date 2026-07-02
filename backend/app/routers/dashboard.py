from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.repositories.contract import ContractRepository
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(current_user: CurrentUser, db: DbSession):
    service = DashboardService(ContractRepository(db), db)
    return await service.get_dashboard()
