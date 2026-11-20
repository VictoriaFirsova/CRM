from urllib.parse import quote

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.core.deps import CurrentUser, DbSession
from app.schemas.payroll import (
    PayrollExportRequest,
    PayrollLineResponse,
    PayrollLineUpdate,
    PayrollListResponse,
)
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


@router.post("/export")
async def export_payroll(
    data: PayrollExportRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    content = await PayrollService(db).export_xlsx(current_user, data.line_ids)
    filename = "raschet_zp.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}; filename*=UTF-8''{quote('расчёт_зп.xlsx')}"
        },
    )
