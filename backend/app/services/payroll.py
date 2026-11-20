from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import extract, select
from sqlalchemy.orm import selectinload

from app.models.contract import Contract
from app.models.contract_line_item import ContractLineItem
from app.models.enums import ContractKind, PaymentStatus
from app.models.user import User
from app.schemas.payroll import PayrollLineResponse, PayrollLineUpdate, PayrollListResponse
from app.services.payroll_xls import build_payroll_xlsx

TAX_KEEP = Decimal("0.94")
SHARE_COMPANY = Decimal("0.7")
TWO = Decimal("2")
ZERO = Decimal("0.00")


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_rewards(price: Decimal, cost_price: Decimal | None, share_half: bool) -> tuple[Decimal, Decimal]:
    cost = cost_price if cost_price is not None else ZERO
    full = _money(((price * TAX_KEEP) - cost) * SHARE_COMPANY)
    mine = _money(full / TWO) if share_half else full
    return full, mine


class PayrollService:
    def __init__(self, db):
        self.db = db

    def _contract_label(self, contract: Contract) -> str:
        if contract.kind == ContractKind.ADDENDUM and contract.addendum_number is not None:
            parent_num = contract.parent.contract_number if contract.parent else contract.contract_number
            return f"{parent_num} · прил. №{contract.addendum_number}"
        return contract.contract_number

    def _to_row(self, item: ContractLineItem) -> PayrollLineResponse:
        contract = item.contract
        full, mine = compute_rewards(item.price, item.cost_price, item.share_half)
        return PayrollLineResponse(
            id=item.id,
            contract_id=contract.id,
            contract_label=self._contract_label(contract),
            client_name=contract.client.company_name if contract.client else None,
            document_name=item.document_name,
            product_name=item.product_name,
            price=item.price,
            cost_price=item.cost_price,
            share_half=item.share_half,
            salary_paid=item.salary_paid,
            reward_full=full,
            reward_mine=mine,
            payment_status=contract.payment_status,
            start_date=contract.start_date,
            year=contract.start_date.year if contract.start_date else None,
        )

    async def list_lines(
        self,
        user: User,
        year: int | None = None,
        month: int | None = None,
        hide_paid: bool = False,
    ) -> PayrollListResponse:
        query = (
            select(ContractLineItem)
            .join(Contract, ContractLineItem.contract_id == Contract.id)
            .options(
                selectinload(ContractLineItem.contract).selectinload(Contract.client),
                selectinload(ContractLineItem.contract).selectinload(Contract.parent),
            )
            .where(
                Contract.responsible_manager_id == user.id,
                Contract.kind == ContractKind.ADDENDUM,
                Contract.payment_status.in_([PaymentStatus.PAID, PaymentStatus.PARTIALLY_PAID]),
            )
        )
        # Год/месяц — дата приложения (start_date у ADDENDUM)
        if year is not None:
            query = query.where(extract("year", Contract.start_date) == year)
        if month is not None:
            query = query.where(extract("month", Contract.start_date) == month)
        if hide_paid:
            query = query.where(ContractLineItem.salary_paid.is_(False))

        query = query.order_by(
            Contract.start_date.desc().nullslast(),
            Contract.addendum_number.desc().nullslast(),
            ContractLineItem.position,
        )
        result = await self.db.execute(query)
        items = list(result.scalars().unique().all())
        rows = [self._to_row(item) for item in items]

        total_to_pay = ZERO
        total_paid = ZERO
        total_all = ZERO
        for row in rows:
            total_all += row.reward_mine
            if row.salary_paid:
                total_paid += row.reward_mine
            else:
                total_to_pay += row.reward_mine

        return PayrollListResponse(
            items=rows,
            total_to_pay=_money(total_to_pay),
            total_paid=_money(total_paid),
            total_all=_money(total_all),
        )

    async def update_line(self, user: User, line_id: int, data: PayrollLineUpdate) -> PayrollLineResponse:
        result = await self.db.execute(
            select(ContractLineItem)
            .join(Contract, ContractLineItem.contract_id == Contract.id)
            .options(
                selectinload(ContractLineItem.contract).selectinload(Contract.client),
                selectinload(ContractLineItem.contract).selectinload(Contract.parent),
            )
            .where(ContractLineItem.id == line_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Строка не найдена")
        if item.contract.responsible_manager_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

        payload = data.model_dump(exclude_unset=True)
        for key, value in payload.items():
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        return self._to_row(item)

    async def export_xlsx(self, user: User, line_ids: list[int]) -> bytes:
        ids = list(dict.fromkeys(line_ids))
        result = await self.db.execute(
            select(ContractLineItem)
            .join(Contract, ContractLineItem.contract_id == Contract.id)
            .options(
                selectinload(ContractLineItem.contract).selectinload(Contract.client),
                selectinload(ContractLineItem.contract).selectinload(Contract.parent),
            )
            .where(
                ContractLineItem.id.in_(ids),
                Contract.responsible_manager_id == user.id,
                Contract.kind == ContractKind.ADDENDUM,
            )
            .order_by(
                Contract.start_date.desc().nullslast(),
                Contract.addendum_number.desc().nullslast(),
                ContractLineItem.position,
            )
        )
        items = list(result.scalars().unique().all())
        if not items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нет строк для выгрузки")
        rows = [self._to_row(item) for item in items]
        return build_payroll_xlsx(rows)
