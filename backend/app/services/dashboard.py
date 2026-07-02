from sqlalchemy import func, select

from app.models.client import Client
from app.models.audit_log import AuditLog
from app.models.enums import ContractStatus
from app.repositories.contract import ContractRepository
from app.schemas.dashboard import DashboardResponse, DashboardStats, RecentActivity


class DashboardService:
    def __init__(self, contract_repo: ContractRepository, db):
        self.contract_repo = contract_repo
        self.db = db

    async def get_dashboard(self) -> DashboardResponse:
        clients_result = await self.db.execute(select(func.count()).select_from(Client))
        clients_count = clients_result.scalar() or 0
        active = await self.contract_repo.count_by_status(ContractStatus.OPEN)
        unpaid = await self.contract_repo.count_unpaid()

        activity_result = await self.db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
        )
        activities = [
            RecentActivity.model_validate(a) for a in activity_result.scalars().all()
        ]

        return DashboardResponse(
            stats=DashboardStats(
                clients_count=clients_count,
                active_contracts=active,
                unpaid_contracts=unpaid,
            ),
            recent_activity=activities,
        )
