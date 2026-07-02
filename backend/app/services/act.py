from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.permissions import can_edit_contract
from app.models.contract import Contract
from app.models.document import Document
from app.models.enums import ContractKind, DocumentType
from app.models.user import User
from app.repositories.contract import ContractRepository
from app.repositories.document import DocumentRepository
from app.schemas.act import ActCreateRequest, ActResponse, ActUpdateRequest
from app.services.act_xlsx import build_act_filename, save_act_xlsx
from app.services.audit import log_audit


class ActService:
    def __init__(self, doc_repo: DocumentRepository, contract_repo: ContractRepository):
        self.doc_repo = doc_repo
        self.contract_repo = contract_repo
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _act_date_from_doc(doc: Document) -> date:
        if doc.document_date:
            return doc.document_date
        if doc.generated_at:
            return doc.generated_at.date()
        return date.today()

    def _to_response(self, doc: Document, user: User | None = None) -> ActResponse:
        contract = doc.contract
        client = contract.client if contract else None
        can_edit = False
        if user and contract and client:
            can_edit = can_edit_contract(
                user, client.owner_id, contract.responsible_manager_id
            )
        return ActResponse(
            id=doc.id,
            contract_id=doc.contract_id,
            amount=(contract.amount if contract else None) or Decimal("0"),
            act_date=self._act_date_from_doc(doc),
            generated_at=doc.generated_at,
            contract_number=contract.contract_number if contract else None,
            client_name=client.company_name if client else None,
            addendum_number=contract.addendum_number if contract else None,
            production_status=contract.production_status if contract else None,
            can_edit=can_edit,
        )

    async def get_act_document(self, act_id: int) -> Document:
        doc = await self.doc_repo.get_by_id(act_id)
        if not doc or doc.type != DocumentType.ACT:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Акт не найден")
        return doc

    async def _has_act(self, contract_id: int) -> bool:
        acts = await self.doc_repo.list_by_type(DocumentType.ACT, contract_id=contract_id)
        return len(acts) > 0

    async def list_acts(self, user: User, contract_id: int | None = None) -> list[ActResponse]:
        acts = await self.doc_repo.list_by_type(DocumentType.ACT, contract_id=contract_id)
        return [self._to_response(d, user) for d in acts]

    async def generate_act(self, user: User, data: ActCreateRequest, db) -> ActResponse:
        act_date = data.act_date or date.today()
        return await self._generate_act(user, data.contract_id, act_date, db)

    async def _generate_act(
        self, user: User, contract_id: int, act_date: date, db
    ) -> ActResponse:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        contract = await self.contract_repo.get_by_id(contract_id)
        if not contract:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Договор не найден")
        if contract.kind != ContractKind.ADDENDUM:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Акт создаётся только для приложения к договору.",
            )
        if not contract.client or not can_edit_contract(
            user, contract.client.owner_id, contract.responsible_manager_id
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
        if await self._has_act(contract.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Акт для этого приложения уже создан.",
            )
        if not contract.amount or float(contract.amount) <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Укажите сумму приложения (таблица №1).",
            )

        output_path = Path(settings.UPLOAD_DIR) / f"act_{contract.id}_{uuid4().hex[:8]}.xlsx"
        try:
            save_act_xlsx(contract, contract.client, output_path, act_date)
        except FileNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e

        document = Document(
            contract_id=contract.id,
            client_id=contract.client_id,
            type=DocumentType.ACT,
            file_path=str(output_path),
            document_date=act_date,
            generated_by=user.id,
        )
        document = await self.doc_repo.create(document)
        await log_audit(db, user.id, "GENERATE", "document", document.id, new_data={"type": "ACT"})
        loaded = await self.doc_repo.get_by_id(document.id)
        return self._to_response(loaded or document, user)

    def download_path(self, doc: Document) -> tuple[Path, str]:
        path = Path(doc.file_path)
        if not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл акта не найден")
        contract = doc.contract if hasattr(doc, "contract") else None
        client = contract.client if contract else None
        act_date = self._act_date_from_doc(doc)
        filename = (
            build_act_filename(contract, client, act_date)
            if contract
            else f"act_{doc.id}.xlsx"
        )
        return path, filename

    async def update_act(
        self, user: User, act_id: int, data: ActUpdateRequest, db: AsyncSession
    ) -> ActResponse:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        doc = await self.get_act_document(act_id)
        contract = doc.contract
        if not contract or not contract.client or not can_edit_contract(
            user, contract.client.owner_id, contract.responsible_manager_id
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        path = Path(doc.file_path) if doc.file_path else None
        if not path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл акта не найден")

        try:
            save_act_xlsx(contract, contract.client, path, data.act_date)
        except FileNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e

        old_date = doc.document_date
        doc.document_date = data.act_date
        await db.flush()
        await log_audit(
            db,
            user.id,
            "UPDATE",
            "document",
            doc.id,
            old_data={"act_date": str(old_date) if old_date else None},
            new_data={"act_date": str(data.act_date)},
        )
        loaded = await self.doc_repo.get_by_id(doc.id)
        return self._to_response(loaded or doc, user)

    async def delete_act(self, user: User, act_id: int, db) -> None:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        doc = await self.get_act_document(act_id)
        contract = doc.contract
        if not contract or not contract.client or not can_edit_contract(
            user, contract.client.owner_id, contract.responsible_manager_id
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")

        file_path = Path(doc.file_path) if doc.file_path else None
        await log_audit(
            db,
            user.id,
            "DELETE",
            "document",
            doc.id,
            old_data={"type": "ACT", "contract_id": doc.contract_id},
        )
        await self.doc_repo.delete(doc)

        if file_path and file_path.is_file():
            file_path.unlink(missing_ok=True)
