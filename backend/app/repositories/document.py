from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contract import Contract
from app.models.document import Document
from app.models.enums import DocumentType

_SINGLETON_TYPES = {DocumentType.CONTRACT, DocumentType.ACT}


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _with_contract(self, query):
        return query.options(
            selectinload(Document.contract).selectinload(Contract.client),
            selectinload(Document.contract).selectinload(Contract.parent),
        )

    async def get_by_id(self, doc_id: int) -> Document | None:
        q = self._with_contract(select(Document).where(Document.id == doc_id))
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def list_by_type(
        self, doc_type: DocumentType, contract_id: int | None = None
    ) -> list[Document]:
        q = self._with_contract(select(Document).where(Document.type == doc_type))
        if contract_id is not None:
            q = q.where(Document.contract_id == contract_id)
        q = q.order_by(Document.generated_at.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_latest(self, contract_id: int, doc_type: DocumentType) -> Document | None:
        q = (
            select(Document)
            .where(Document.contract_id == contract_id, Document.type == doc_type)
            .order_by(Document.generated_at.desc())
            .limit(1)
        )
        result = await self.db.execute(q)
        return result.scalar_one_or_none()

    async def list_all(self, contract_id: int | None = None) -> list[Document]:
        query = select(Document).order_by(Document.generated_at.desc())
        if contract_id:
            query = query.where(Document.contract_id == contract_id)
        result = await self.db.execute(query)
        docs = list(result.scalars().all())
        seen: set[tuple[int, DocumentType]] = set()
        filtered: list[Document] = []
        for doc in docs:
            key = (doc.contract_id, doc.type)
            if doc.type in _SINGLETON_TYPES:
                if key in seen:
                    continue
                seen.add(key)
            filtered.append(doc)
        return filtered

    async def create(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def delete(self, document: Document) -> None:
        await self.db.delete(document)
        await self.db.flush()

    async def has_required_for_close(self, contract_id: int) -> bool:
        result = await self.db.execute(
            select(Document.type).where(
                Document.contract_id == contract_id,
                Document.type.in_([DocumentType.CONTRACT, DocumentType.ACT]),
            )
        )
        types = {row[0] for row in result.all()}
        return DocumentType.CONTRACT in types and DocumentType.ACT in types
