from datetime import date
from decimal import Decimal

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.contract import Contract
from app.models.contract_line_item import ContractLineItem
from app.models.enums import ContractKind, ContractStatus, PaymentStatus, ProductionStatus
from app.services.contract_numbering import parse_framework_number


class ContractRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self):
        return select(Contract).options(
            selectinload(Contract.client),
            selectinload(Contract.responsible_manager),
            selectinload(Contract.parent),
            selectinload(Contract.line_items),
        )

    async def get_by_id(self, contract_id: int) -> Contract | None:
        result = await self.db.execute(self._base_query().where(Contract.id == contract_id))
        return result.scalar_one_or_none()

    async def get_framework_by_sequence_year(
        self, sequence: int, year: int, exclude_id: int | None = None
    ) -> Contract | None:
        query = self._base_query().where(
            Contract.kind == ContractKind.FRAMEWORK,
            Contract.number_sequence == sequence,
            Contract.number_year == year,
        )
        if exclude_id is not None:
            query = query.where(Contract.id != exclude_id)
        result = await self.db.execute(query.limit(1))
        found = result.scalar_one_or_none()
        if found:
            return found
        for num in await self.list_framework_numbers_for_year(year):
            parsed = parse_framework_number(num)
            if parsed and parsed[1] == sequence and parsed[2] == year:
                result = await self.db.execute(
                    self._base_query().where(Contract.contract_number == num).limit(1)
                )
                return result.scalar_one_or_none()
        return None

    async def list_framework_numbers_for_year(self, year: int) -> list[str]:
        """Все рамочные номера за год (любой префикс менеджера)."""
        suffix = f"-{year}"
        result = await self.db.execute(
            select(Contract.contract_number).where(
                Contract.kind == ContractKind.FRAMEWORK,
                Contract.contract_number.ilike(f"%{suffix}"),
            )
        )
        return [row[0] for row in result.all()]

    async def list_addendum_numbers(self, parent_contract_id: int, exclude_id: int | None = None) -> list[int]:
        query = select(Contract.addendum_number).where(
            Contract.kind == ContractKind.ADDENDUM,
            Contract.parent_contract_id == parent_contract_id,
            Contract.addendum_number.is_not(None),
        )
        if exclude_id is not None:
            query = query.where(Contract.id != exclude_id)
        result = await self.db.execute(query)
        return [row[0] for row in result.all() if row[0] is not None]

    async def get_addendum_by_number(
        self, parent_contract_id: int, addendum_number: int, exclude_id: int | None = None
    ) -> Contract | None:
        query = select(Contract).where(
            Contract.kind == ContractKind.ADDENDUM,
            Contract.parent_contract_id == parent_contract_id,
            Contract.addendum_number == addendum_number,
        )
        if exclude_id is not None:
            query = query.where(Contract.id != exclude_id)
        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def list_frameworks(self, client_id: int | None = None, open_only: bool = True) -> list[Contract]:
        query = self._base_query().where(Contract.kind == ContractKind.FRAMEWORK)
        if client_id is not None:
            query = query.where(Contract.client_id == client_id)
        if open_only:
            query = query.where(Contract.contract_status == ContractStatus.OPEN)
        query = query.order_by(Contract.contract_number.desc())
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def list_filtered(
        self,
        contract_status: ContractStatus | None = None,
        payment_status: PaymentStatus | None = None,
        production_status: ProductionStatus | None = None,
        responsible_manager_id: int | None = None,
        client_id: int | None = None,
        contract_number: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Contract], int]:
        query = self._base_query()
        count_query = select(func.count()).select_from(Contract)

        filters = []
        if contract_status:
            filters.append(Contract.contract_status == contract_status)
        if payment_status:
            filters.append(Contract.payment_status == payment_status)
        if production_status:
            filters.append(Contract.production_status == production_status)
        if responsible_manager_id:
            filters.append(Contract.responsible_manager_id == responsible_manager_id)
        if client_id:
            filters.append(Contract.client_id == client_id)
        if contract_number:
            filters.append(Contract.contract_number.ilike(f"%{contract_number}%"))
        if date_from:
            filters.append(Contract.start_date >= date_from)
        if date_to:
            filters.append(Contract.start_date <= date_to)
        if search:
            pattern = f"%{search}%"
            query = query.join(Client)
            count_query = count_query.join(Client)
            filters.append(
                or_(
                    Contract.contract_number.ilike(pattern),
                    Contract.title.ilike(pattern),
                    Contract.comment.ilike(pattern),
                    Client.company_name.ilike(pattern),
                    Client.inn.ilike(pattern),
                )
            )

        for f in filters:
            query = query.where(f)
            count_query = count_query.where(f)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Contract.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all()), total

    async def replace_line_items(
        self,
        contract_id: int,
        items: list[tuple[str, str, Decimal, bool]],
    ) -> None:
        await self.db.execute(
            delete(ContractLineItem).where(ContractLineItem.contract_id == contract_id)
        )
        for position, (document_name, product_name, price, vat_exempt) in enumerate(items):
            self.db.add(
                ContractLineItem(
                    contract_id=contract_id,
                    position=position,
                    document_name=document_name.strip(),
                    product_name=product_name.strip(),
                    price=price,
                    vat_exempt=vat_exempt,
                )
            )
        await self.db.flush()

    async def flush(self) -> None:
        await self.db.flush()

    async def create(self, contract: Contract) -> Contract:
        self.db.add(contract)
        await self.db.flush()
        await self.db.refresh(contract)
        return contract

    async def delete(self, contract: Contract) -> None:
        await self.db.delete(contract)

    async def count_by_status(self, status: ContractStatus) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Contract).where(Contract.contract_status == status)
        )
        return result.scalar() or 0

    async def count_unpaid(self) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Contract)
            .where(
                Contract.kind == ContractKind.ADDENDUM,
                Contract.contract_status == ContractStatus.OPEN,
                Contract.payment_status != PaymentStatus.PAID,
            )
        )
        return result.scalar() or 0
