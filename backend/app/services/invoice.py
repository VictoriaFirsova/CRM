from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.permissions import can_edit_contract
from app.models.contract import Contract
from app.models.enums import ContractKind, InvoiceKind, PaymentRecordStatus, PaymentStatus
from app.models.invoice import Invoice
from app.models.user import User
from app.repositories.contract import ContractRepository
from app.repositories.invoice import InvoiceRepository
from app.schemas.invoice import InvoiceCreateRequest, InvoiceResponse, InvoiceUpdateRequest
from app.services.audit import log_audit
from app.services.invoice_xls import build_invoice_filename, save_invoice_xls


class InvoiceService:
    def __init__(self, repo: InvoiceRepository, contract_repo: ContractRepository):
        self.repo = repo
        self.contract_repo = contract_repo
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    def _can_edit(self, user: User, contract: Contract | None) -> bool:
        if not contract or not contract.client:
            return False
        return can_edit_contract(user, contract.client.owner_id, contract.responsible_manager_id)

    def _to_response(self, inv: Invoice, user: User | None = None) -> InvoiceResponse:
        data = InvoiceResponse.model_validate(inv)
        if inv.contract:
            data.contract_number = inv.contract.contract_number
            data.addendum_number = inv.contract.addendum_number
            if inv.contract.client:
                data.client_name = inv.contract.client.company_name
            if user:
                data.can_edit = self._can_edit(user, inv.contract)
        return data

    async def _sync_contract_payment_status(self, db: AsyncSession, contract_id: int) -> None:
        """Статус оплаты приложения по оплаченным счетам."""
        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract or contract.kind != ContractKind.ADDENDUM:
            return

        invoices = await self.repo.get_for_contract(contract_id)
        active = [i for i in invoices if i.status != PaymentRecordStatus.CANCELED]
        paid_sum = sum(
            (i.amount or Decimal("0")) for i in active if i.status == PaymentRecordStatus.PAID
        )
        total = contract.amount or Decimal("0")

        if paid_sum <= 0:
            contract.payment_status = PaymentStatus.NOT_PAID
        elif paid_sum >= total:
            contract.payment_status = PaymentStatus.PAID
        else:
            contract.payment_status = PaymentStatus.PARTIALLY_PAID

    def _resolve_kind_and_amount(self, contract: Contract, requested: InvoiceKind) -> tuple[InvoiceKind, float]:
        advance = contract.advance_percent if contract.advance_percent is not None else 100
        total = float(contract.amount or 0)
        if advance >= 100:
            if requested != InvoiceKind.FULL:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="При оплате 100% создаётся только один счёт (полная сумма).",
                )
            return InvoiceKind.FULL, total
        if requested == InvoiceKind.FULL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="При частичной оплате используйте счёт на аванс и на остаток.",
            )
        if requested == InvoiceKind.ADVANCE:
            return InvoiceKind.ADVANCE, total * advance / 100
        return InvoiceKind.BALANCE, total * (100 - advance) / 100

    async def _validate_create(self, contract: Contract, kind: InvoiceKind) -> None:
        existing = await self.repo.get_for_contract(contract.id)
        kinds = {i.kind for i in existing}
        if kind in kinds:
            labels = {
                InvoiceKind.ADVANCE: "на аванс",
                InvoiceKind.BALANCE: "на остаток",
                InvoiceKind.FULL: "на полную оплату",
            }
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Счёт {labels[kind]} для этого приложения уже создан.",
            )
        if kind == InvoiceKind.BALANCE and InvoiceKind.ADVANCE not in kinds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сначала создайте и сохраните счёт на аванс.",
            )

    async def list_invoices(self, user: User, contract_id: int | None = None) -> list[InvoiceResponse]:
        items = await self.repo.list_all(contract_id=contract_id)
        return [self._to_response(i, user) for i in items]

    async def get_invoice(self, invoice_id: int) -> Invoice:
        inv = await self.repo.get_by_id(invoice_id)
        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт не найден")
        return inv

    async def create_invoice(self, user: User, data: InvoiceCreateRequest, db) -> InvoiceResponse:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        contract = await self.contract_repo.get_by_id(data.contract_id)
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Договор не найден")
        if contract.kind != ContractKind.ADDENDUM:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Счета создаются только для приложений к договору.",
            )
        if not contract.client or not can_edit_contract(
            user, contract.client.owner_id, contract.responsible_manager_id
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        kind, amount = self._resolve_kind_and_amount(contract, data.kind)
        if amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сумма счёта должна быть больше 0")

        await self._validate_create(contract, kind)

        invoice_date = data.invoice_date or contract.start_date or date.today()
        invoice = Invoice(
            contract_id=contract.id,
            kind=kind,
            amount=amount,
            invoice_date=invoice_date,
            file_path="",
            created_by=user.id,
        )
        invoice = await self.repo.create(invoice)

        output_path = Path(settings.UPLOAD_DIR) / f"invoice_{invoice.id}_{kind.value}.xls"
        try:
            save_invoice_xls(
                contract,
                contract.client,
                kind,
                amount,
                output_path,
                invoice_number=invoice.id,
                invoice_date=invoice_date,
            )
        except FileNotFoundError as e:
            await db.delete(invoice)
            await db.flush()
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e

        invoice.file_path = str(output_path)
        await db.flush()
        await log_audit(db, user.id, "CREATE", "invoice", invoice.id, new_data={"kind": kind.value, "amount": amount})
        loaded = await self.repo.get_by_id(invoice.id)
        return self._to_response(loaded or invoice, user)

    async def update_invoice(
        self, user: User, invoice_id: int, data: InvoiceUpdateRequest, db: AsyncSession
    ) -> InvoiceResponse:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        inv = await self.repo.get_by_id(invoice_id)
        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт не найден")
        if not self._can_edit(user, inv.contract):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        if data.status is None and data.invoice_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Укажите статус или дату счёта",
            )

        audit_new: dict = {}
        if data.invoice_date is not None and data.invoice_date != inv.invoice_date:
            path = Path(inv.file_path) if inv.file_path else None
            if not path:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл счёта не найден")
            contract = inv.contract
            if not contract:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Договор не найден")
            try:
                save_invoice_xls(
                    contract,
                    contract.client,
                    inv.kind,
                    float(inv.amount or 0),
                    path,
                    invoice_number=inv.id,
                    invoice_date=data.invoice_date,
                )
            except FileNotFoundError as e:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
            inv.invoice_date = data.invoice_date
            audit_new["invoice_date"] = str(data.invoice_date)

        if data.status is not None:
            inv.status = data.status
            await self._sync_contract_payment_status(db, inv.contract_id)
            audit_new["status"] = data.status.value

        await log_audit(
            db,
            user.id,
            "UPDATE",
            "invoice",
            inv.id,
            new_data=audit_new or None,
        )
        loaded = await self.repo.get_by_id(inv.id)
        return self._to_response(loaded or inv, user)

    async def delete_invoice(self, user: User, invoice_id: int, db: AsyncSession) -> None:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        inv = await self.repo.get_by_id(invoice_id)
        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт не найден")
        if not self._can_edit(user, inv.contract):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        if inv.kind == InvoiceKind.ADVANCE:
            existing = await self.repo.get_for_contract(inv.contract_id)
            if any(i.kind == InvoiceKind.BALANCE and i.id != inv.id for i in existing):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Сначала удалите счёт на остаток.",
                )

        file_path = Path(inv.file_path) if inv.file_path else None
        contract_id = inv.contract_id
        kind = inv.kind.value
        amount = float(inv.amount or 0)

        await log_audit(db, user.id, "DELETE", "invoice", inv.id, old_data={"kind": kind, "amount": amount})
        await self.repo.delete(inv)

        if file_path and file_path.is_file():
            file_path.unlink(missing_ok=True)

        await self._sync_contract_payment_status(db, contract_id)

    def download_path(self, inv: Invoice) -> tuple[Path, str]:
        path = Path(inv.file_path)
        if not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл счёта не найден")
        contract = inv.contract
        client = contract.client if contract else None
        filename = (
            build_invoice_filename(contract, client, inv.kind, inv.invoice_date)
            if contract
            else f"invoice_{inv.id}.xls"
        )
        return path, filename
