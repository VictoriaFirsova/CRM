from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client, ClientHistory
from app.models.contract import Contract


class ClientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, client_id: int) -> Client | None:
        result = await self.db.execute(
            select(Client).where(Client.id == client_id).options(selectinload(Client.owner))
        )
        return result.scalar_one_or_none()

    async def get_by_inn(self, inn: str, exclude_id: int | None = None) -> Client | None:
        query = select(Client).where(Client.inn == inn, Client.is_archived.is_(False))
        if exclude_id is not None:
            query = query.where(Client.id != exclude_id)
        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def count_contracts(self, client_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Contract).where(Contract.client_id == client_id)
        )
        return int(result.scalar_one())

    async def list_all(self, search: str | None = None, archived: bool = False) -> list[Client]:
        query = (
            select(Client)
            .where(Client.is_archived.is_(archived))
            .options(selectinload(Client.owner))
            .order_by(Client.company_name)
        )
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Client.company_name.ilike(pattern),
                    Client.full_company_name.ilike(pattern),
                    Client.inn.ilike(pattern),
                    Client.kpp.ilike(pattern),
                    Client.bank_name.ilike(pattern),
                    Client.settlement_account.ilike(pattern),
                    Client.contact_person.ilike(pattern),
                )
            )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, client: Client) -> Client:
        self.db.add(client)
        await self.db.flush()
        await self.db.refresh(client)
        return client

    async def flush_refresh(self, *instances: Client) -> None:
        """После flush async-сессия сбрасывает атрибуты — refresh до сериализации в Pydantic."""
        await self.db.flush()
        for instance in instances:
            await self.db.refresh(instance)

    async def delete(self, client: Client) -> None:
        await self.db.delete(client)

    async def add_history(self, entry: ClientHistory) -> ClientHistory:
        self.db.add(entry)
        return entry

    async def get_history(self, client_id: int) -> list[ClientHistory]:
        result = await self.db.execute(
            select(ClientHistory).where(ClientHistory.client_id == client_id).order_by(ClientHistory.changed_at.desc())
        )
        return list(result.scalars().all())
