from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.permissions import can_edit_client
from app.services.dadata import normalize_inn
from app.models.client import Client, ClientHistory
from app.models.user import User
from app.repositories.client import ClientRepository
from app.schemas.client import ClientArchiveRequest, ClientCreate, ClientResponse, ClientUpdate
from app.services.audit import log_audit

TRACKED_FIELDS = [
    "company_name",
    "full_company_name",
    "inn",
    "kpp",
    "ogrn",
    "legal_address",
    "actual_address",
    "bank_name",
    "bik",
    "correspondent_account",
    "settlement_account",
    "director_name",
    "director_name_genitive",
    "signer_position",
    "signer_basis",
    "contact_person",
    "phone",
    "email",
    "notes",
]


class ClientService:
    def __init__(self, repo: ClientRepository):
        self.repo = repo

    async def _assert_inn_unique(self, inn: str | None, exclude_client_id: int | None = None) -> None:
        normalized = normalize_inn(inn)
        if not normalized:
            return
        existing = await self.repo.get_by_inn(normalized, exclude_id=exclude_client_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Клиент с ИНН {normalized} уже есть: «{existing.company_name}» "
                    f"(карточка №{existing.id})"
                ),
            )

    def _to_response(self, client: Client, user: User) -> ClientResponse:
        data = ClientResponse.model_validate(client)
        data.can_edit = can_edit_client(user, client.owner_id)
        return data

    async def list_clients(
        self, user: User, search: str | None = None, archived: bool = False
    ) -> list[ClientResponse]:
        clients = await self.repo.list_all(search=search, archived=archived)
        return [self._to_response(c, user) for c in clients]

    async def get_client(self, user: User, client_id: int) -> ClientResponse:
        client = await self.repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        return self._to_response(client, user)

    async def create_client(self, user: User, data: ClientCreate, db) -> ClientResponse:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewers cannot create clients")
        payload = data.model_dump()
        if payload.get("inn"):
            payload["inn"] = normalize_inn(payload["inn"]) or payload["inn"]
        await self._assert_inn_unique(payload.get("inn"))
        client = Client(owner_id=user.id, **payload)
        client = await self.repo.create(client)
        await log_audit(db, user.id, "CREATE", "client", client.id, new_data=data.model_dump())
        return self._to_response(client, user)

    async def update_client(self, user: User, client_id: int, data: ClientUpdate, db) -> ClientResponse:
        client = await self.repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if not can_edit_client(user, client.owner_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to edit")
        if client.is_archived:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Клиент в архиве. Сначала восстановите из архива.",
            )
        old_data = {f: getattr(client, f) for f in TRACKED_FIELDS}
        updates = data.model_dump(exclude_unset=True)
        if "inn" in updates and updates["inn"]:
            updates["inn"] = normalize_inn(updates["inn"]) or updates["inn"]
        if "inn" in updates:
            await self._assert_inn_unique(updates.get("inn"), exclude_client_id=client.id)
        for field, value in updates.items():
            old_val = getattr(client, field)
            if str(old_val) != str(value):
                await self.repo.add_history(
                    ClientHistory(
                        client_id=client.id,
                        changed_by=user.id,
                        field_name=field,
                        old_value=str(old_val) if old_val is not None else None,
                        new_value=str(value) if value is not None else None,
                    )
                )
            setattr(client, field, value)
        await log_audit(db, user.id, "UPDATE", "client", client.id, old_data=old_data, new_data=updates)
        await self.repo.flush_refresh(client)
        return self._to_response(client, user)

    async def delete_client(self, user: User, client_id: int, db) -> None:
        client = await self.repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if not can_edit_client(user, client.owner_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на удаление")
        contracts_count = await self.repo.count_contracts(client_id)
        if contracts_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Нельзя удалить: у клиента {contracts_count} договор(ов). Сначала удалите договоры.",
            )
        await log_audit(db, user.id, "DELETE", "client", client.id)
        await self.repo.delete(client)

    async def archive_client(
        self, user: User, client_id: int, data: ClientArchiveRequest, db
    ) -> ClientResponse:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
        client = await self.repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if not can_edit_client(user, client.owner_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
        if client.is_archived:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Клиент уже в архиве")

        comment = data.comment.strip()
        client.is_archived = True
        client.archive_comment = comment
        client.archived_at = datetime.now(timezone.utc)
        client.archived_by = user.id
        await self.repo.add_history(
            ClientHistory(
                client_id=client.id,
                changed_by=user.id,
                field_name="archived",
                old_value=None,
                new_value=comment,
            )
        )
        await log_audit(
            db,
            user.id,
            "ARCHIVE",
            "client",
            client.id,
            new_data={"archive_comment": comment},
        )
        await self.repo.flush_refresh(client)
        return self._to_response(client, user)

    async def unarchive_client(self, user: User, client_id: int, db) -> ClientResponse:
        if user.role.value == "VIEWER":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
        client = await self.repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if not can_edit_client(user, client.owner_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав")
        if not client.is_archived:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Клиент не в архиве")

        old_comment = client.archive_comment
        client.is_archived = False
        client.archive_comment = None
        client.archived_at = None
        client.archived_by = None
        await self.repo.add_history(
            ClientHistory(
                client_id=client.id,
                changed_by=user.id,
                field_name="archived",
                old_value=old_comment,
                new_value=None,
            )
        )
        await log_audit(db, user.id, "UNARCHIVE", "client", client.id)
        await self.repo.flush_refresh(client)
        return self._to_response(client, user)
