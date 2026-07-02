from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select

from app.core.permissions import can_edit_contract
from app.models.contract import Contract
from app.models.document import Document
from app.models.enums import ContractKind, ContractStatus, PaymentStatus, ProductionStatus
from app.models.invoice import Invoice
from app.models.user import User
from app.repositories.client import ClientRepository
from app.repositories.contract import ContractRepository
from app.repositories.document import DocumentRepository
from app.schemas.contract import (
    AddendumNumberSuggestResponse,
    ContractCreate,
    ContractDuplicateCheckResponse,
    ContractLineItemInput,
    ContractNumberSuggestResponse,
    ContractResponse,
    ContractUpdate,
)
from app.services.audit import log_audit
from app.services.contract_numbering import (
    format_sequence_year,
    normalize_contract_number,
    parse_framework_number,
    suggest_next_addendum_number,
    suggest_next_framework_number,
)
from app.services.manager_prefix import manager_prefix_from_name


class ContractService:
    def __init__(
        self,
        repo: ContractRepository,
        client_repo: ClientRepository,
        doc_repo: DocumentRepository,
    ):
        self.repo = repo
        self.client_repo = client_repo
        self.doc_repo = doc_repo

    def _can_edit(self, user: User, contract: Contract) -> bool:
        client = contract.client
        owner_id = client.owner_id if client else 0
        return can_edit_contract(user, owner_id, contract.responsible_manager_id)

    def _ensure_framework_open_for_addendum(self, parent: Contract) -> None:
        if parent.contract_status != ContractStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Рамочный договор закрыт — новые приложения к нему создать нельзя",
            )

    _FRAMEWORK_UPDATE_FIELDS = frozenset({"contract_status", "comment"})

    @staticmethod
    def _lines_total(lines: list[ContractLineItemInput]) -> Decimal:
        return sum((line.price for line in lines), Decimal("0"))

    @staticmethod
    def _normalized_lines(
        lines: list[ContractLineItemInput],
    ) -> list[tuple[str, str, Decimal, bool]]:
        return [
            (line.document_name.strip(), line.product_name.strip(), line.price, line.vat_exempt)
            for line in lines
        ]

    async def _apply_line_items(
        self, contract_id: int, lines: list[ContractLineItemInput]
    ) -> Decimal:
        normalized = self._normalized_lines(lines)
        await self.repo.replace_line_items(contract_id, normalized)
        return self._lines_total(lines)

    def _display_label(self, contract: Contract) -> str:
        if contract.kind == ContractKind.ADDENDUM and contract.addendum_number is not None:
            parent_num = contract.parent.contract_number if contract.parent else contract.contract_number
            return f"{parent_num} · прил. №{contract.addendum_number}"
        return contract.contract_number

    def _to_response(self, contract: Contract, user: User) -> ContractResponse:
        data = ContractResponse.model_validate(contract)
        data.can_edit = self._can_edit(user, contract)
        if contract.client:
            data.client_name = contract.client.company_name
        if contract.responsible_manager:
            data.manager_name = contract.responsible_manager.full_name
        if contract.parent:
            data.parent_contract_number = contract.parent.contract_number
        data.display_label = self._display_label(contract)
        return data

    async def suggest_framework_number(
        self, user: User, year: int | None = None
    ) -> ContractNumberSuggestResponse:
        y = year or date.today().year
        prefix = manager_prefix_from_name(user.full_name)
        numbers = await self.repo.list_framework_numbers_for_year(y)
        suggested = suggest_next_framework_number(numbers, prefix, y)
        return ContractNumberSuggestResponse(
            suggested=suggested,
            year=y,
            prefix=prefix,
            manager_name=user.full_name,
        )

    async def suggest_addendum_number(self, parent_contract_id: int) -> AddendumNumberSuggestResponse:
        parent = await self.repo.get_by_id(parent_contract_id)
        if not parent or parent.kind != ContractKind.FRAMEWORK:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рамочный договор не найден",
            )
        self._ensure_framework_open_for_addendum(parent)
        existing = await self.repo.list_addendum_numbers(parent_contract_id)
        suggested = suggest_next_addendum_number(existing)
        return AddendumNumberSuggestResponse(
            suggested=suggested,
            parent_contract_id=parent.id,
            parent_contract_number=parent.contract_number,
        )

    async def check_framework_number(
        self, contract_number: str, exclude_id: int | None = None
    ) -> ContractDuplicateCheckResponse:
        normalized = normalize_contract_number(contract_number)
        if not parse_framework_number(normalized):
            return ContractDuplicateCheckResponse(
                exists=False,
                message="Номер должен быть в формате ФВ-000-2026 (инициалы менеджера, номер, год)",
            )
        _, seq, num_year = parse_framework_number(normalized)
        existing = await self.repo.get_framework_by_sequence_year(seq, num_year, exclude_id=exclude_id)
        if not existing:
            return ContractDuplicateCheckResponse(exists=False)
        core = format_sequence_year(seq, num_year)
        return ContractDuplicateCheckResponse(
            exists=True,
            message=(
                f"Номер {core} уже занят в системе "
                f"(договор {existing.contract_number}, «{existing.title}»)"
            ),
            existing_id=existing.id,
            existing_title=existing.title,
        )

    async def check_addendum_number(
        self, parent_contract_id: int, addendum_number: int, exclude_id: int | None = None
    ) -> ContractDuplicateCheckResponse:
        existing = await self.repo.get_addendum_by_number(
            parent_contract_id, addendum_number, exclude_id=exclude_id
        )
        if not existing:
            return ContractDuplicateCheckResponse(exists=False)
        return ContractDuplicateCheckResponse(
            exists=True,
            message=f"Приложение №{addendum_number} к этой рамке уже есть: «{existing.title}»",
            existing_id=existing.id,
            existing_title=existing.title,
        )

    async def list_frameworks(self, user: User, client_id: int | None = None) -> list[ContractResponse]:
        if client_id is None:
            return []
        contracts = await self.repo.list_frameworks(client_id=client_id, open_only=True)
        return [self._to_response(c, user) for c in contracts]

    async def list_contracts(
        self,
        user: User,
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
    ) -> tuple[list[ContractResponse], int]:
        contracts, total = await self.repo.list_filtered(
            contract_status=contract_status,
            payment_status=payment_status,
            production_status=production_status,
            responsible_manager_id=responsible_manager_id,
            client_id=client_id,
            contract_number=contract_number,
            date_from=date_from,
            date_to=date_to,
            search=search,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(c, user) for c in contracts], total

    async def get_contract(self, user: User, contract_id: int) -> ContractResponse:
        contract = await self.repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        return self._to_response(contract, user)

    async def _resolve_create_fields(
        self, user: User, data: ContractCreate
    ) -> tuple[str, str | None, int | None, int | None, int | None, int | None]:
        if data.kind == ContractKind.FRAMEWORK:
            if not data.contract_number or not data.contract_number.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Укажите номер рамочного договора",
                )
            number = normalize_contract_number(data.contract_number)
            parsed = parse_framework_number(number)
            if not parsed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Номер рамки: ФВ-000-2026 (инициалы менеджера, порядковый номер, год)",
                )
            expected_prefix = manager_prefix_from_name(user.full_name)
            if parsed[0] != expected_prefix:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Префикс номера должен быть {expected_prefix} "
                        f"(фамилия и имя менеджера «{user.full_name}»), указано: {parsed[0]}"
                    ),
                )
            dup = await self.check_framework_number(number)
            if dup.exists and not data.allow_duplicate:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dup.message)
            return number, expected_prefix, parsed[1], parsed[2], None, None

        parent = await self.repo.get_by_id(data.parent_contract_id)  # type: ignore[arg-type]
        if not parent or parent.kind != ContractKind.FRAMEWORK:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректная рамка")
        self._ensure_framework_open_for_addendum(parent)
        if parent.client_id != data.client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Клиент приложения должен совпадать с клиентом рамки",
            )

        addendum_num = data.addendum_number
        if addendum_num is None:
            existing = await self.repo.list_addendum_numbers(parent.id)
            addendum_num = suggest_next_addendum_number(existing)

        dup = await self.check_addendum_number(parent.id, addendum_num)
        if dup.exists and not data.allow_duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dup.message)

        return parent.contract_number, parent.number_prefix, None, None, parent.id, addendum_num

    async def create_contract(self, user: User, data: ContractCreate, db) -> ContractResponse:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewers cannot create contracts")
        client = await self.client_repo.get_by_id(data.client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        contract_number, number_prefix, number_sequence, number_year, parent_id, addendum_number = (
            await self._resolve_create_fields(user, data)
        )
        manager_id = data.responsible_manager_id or user.id

        if data.kind == ContractKind.FRAMEWORK:
            title = (data.title or "").strip() or f"Рамочный договор № {contract_number}"
            amount = Decimal("0")
            start_date = data.start_date or date.today()
        else:
            title = (data.title or "").strip()
            if data.line_items:
                amount = self._lines_total(data.line_items)
            else:
                amount = data.amount if data.amount is not None else Decimal("0")
            start_date = data.start_date

        if data.kind == ContractKind.FRAMEWORK:
            contract_status = ContractStatus.OPEN
            payment_status = PaymentStatus.NOT_PAID
            production_status = ProductionStatus.REQUEST
        else:
            contract_status = data.contract_status
            payment_status = data.payment_status
            production_status = data.production_status

        contract = Contract(
            kind=data.kind,
            client_id=data.client_id,
            parent_contract_id=parent_id,
            addendum_number=addendum_number,
            number_prefix=number_prefix,
            number_sequence=number_sequence,
            number_year=number_year,
            responsible_manager_id=manager_id,
            contract_number=contract_number,
            title=title,
            amount=amount,
            contract_status=contract_status,
            payment_status=payment_status,
            production_status=production_status,
            comment=data.comment,
            work_days=data.work_days if data.kind == ContractKind.ADDENDUM else None,
            advance_percent=data.advance_percent if data.kind == ContractKind.ADDENDUM else None,
            start_date=start_date,
            end_date=data.end_date if data.kind == ContractKind.ADDENDUM else None,
        )
        contract = await self.repo.create(contract)
        if data.kind == ContractKind.ADDENDUM and data.line_items:
            contract.amount = await self._apply_line_items(contract.id, data.line_items)
            await self.repo.flush()
        contract = await self.repo.get_by_id(contract.id)
        await log_audit(db, user.id, "CREATE", "contract", contract.id, new_data=data.model_dump(mode="json"))
        return self._to_response(contract, user)

    async def _validate_close(self, contract: Contract) -> None:
        if contract.kind == ContractKind.FRAMEWORK:
            return
        if contract.payment_status != PaymentStatus.PAID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot close: payment status must be PAID",
            )
        if contract.production_status != ProductionStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot close: production status must be READY",
            )
        has_docs = await self.doc_repo.has_required_for_close(contract.id)
        if not has_docs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot close: required documents (CONTRACT, ACT) are missing",
            )

    async def update_contract(
        self, user: User, contract_id: int, data: ContractUpdate, db
    ) -> ContractResponse:
        contract = await self.repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        if not self._can_edit(user, contract):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to edit")

        updates = data.model_dump(exclude_unset=True)
        allow_duplicate = updates.pop("allow_duplicate", False)
        line_items_raw = updates.pop("line_items", None)

        if contract.kind == ContractKind.FRAMEWORK:
            disallowed = set(updates) - self._FRAMEWORK_UPDATE_FIELDS
            if disallowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="У рамочного договора можно менять только статус (открыт/закрыт) и комментарий",
                )

        if contract.kind == ContractKind.ADDENDUM and updates.get("addendum_number") is not None:
            parent_id = contract.parent_contract_id
            if parent_id:
                dup = await self.check_addendum_number(
                    parent_id, updates["addendum_number"], exclude_id=contract.id
                )
                if dup.exists and not allow_duplicate:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=dup.message)

        if updates.get("contract_status") == ContractStatus.CLOSED:
            await self._validate_close(contract)

        if contract.kind == ContractKind.ADDENDUM and line_items_raw is not None:
            if not line_items_raw:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Таблица не может быть пустой",
                )
            parsed_lines = [ContractLineItemInput.model_validate(row) for row in line_items_raw]
            updates["amount"] = await self._apply_line_items(contract.id, parsed_lines)

        if "amount" in updates and line_items_raw is None and contract.kind == ContractKind.ADDENDUM:
            updates.pop("amount", None)

        old_data = {k: getattr(contract, k) for k in updates}
        for field, value in updates.items():
            setattr(contract, field, value)

        await log_audit(db, user.id, "UPDATE", "contract", contract.id, old_data=old_data, new_data=updates)
        contract = await self.repo.get_by_id(contract.id)
        return self._to_response(contract, user)

    async def delete_contract(self, user: User, contract_id: int, db) -> None:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        contract = await self.repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        if not self._can_edit(user, contract):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на удаление")

        if contract.kind == ContractKind.FRAMEWORK:
            addendums = await self.repo.list_addendum_numbers(contract.id)
            if addendums:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Сначала удалите приложения к этой рамке",
                )

        doc_paths = await db.execute(
            select(Document.file_path).where(Document.contract_id == contract_id)
        )
        inv_paths = await db.execute(
            select(Invoice.file_path).where(Invoice.contract_id == contract_id)
        )
        file_paths = [
            Path(p)
            for p in list(doc_paths.scalars().all()) + list(inv_paths.scalars().all())
            if p
        ]

        await log_audit(
            db,
            user.id,
            "DELETE",
            "contract",
            contract.id,
            old_data={"kind": contract.kind.value, "contract_number": contract.contract_number},
        )
        await self.repo.delete(contract)
        await db.flush()

        for path in file_paths:
            path.unlink(missing_ok=True)
