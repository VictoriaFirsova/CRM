from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    clients_count: int
    active_contracts: int
    unpaid_contracts: int


class RecentActivity(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: int
    user_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_activity: list[RecentActivity]
