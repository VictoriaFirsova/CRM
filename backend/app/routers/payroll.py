from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.schemas.payroll import PayrollLineResponse, PayrollLineUpdate, PayrollListResponse
from app.services.payroll import PayrollService

router = APIRouter(prefix="/payroll", tags=["payroll"])


@router.get("/lines", response_model=PayrollListResponse)
async def list_payroll_lines(
    current_user: CurrentUser,
    db: DbSession,
    year: int | None = Query(None, ge=2000, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    hide_paid: bool = Query(False),
):
    return await PayrollService(db).list_lines(
        current_user, year=year, month=month, hide_paid=hide_paid
    )


@router.patch("/lines/{line_id}", response_model=PayrollLineResponse)
async def update_payroll_line(
    line_id: int,
    data: PayrollLineUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    return await PayrollService(db).update_line(current_user, line_id, data)
