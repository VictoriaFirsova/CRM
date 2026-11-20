from fastapi import HTTPException, status

from app.core.permissions import is_admin
from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.user_admin import UserCreateAdmin, UserUpdateAdmin
from app.services.audit import log_audit


class UserAdminService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def _require_admin(self, user: User) -> None:
        if not is_admin(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только администратор")

    async def list_users(self, actor: User) -> list[UserResponse]:
        self._require_admin(actor)
        users = await self.repo.list_all()
        return [UserResponse.model_validate(u) for u in users]

    async def create_user(self, actor: User, data: UserCreateAdmin, db) -> UserResponse:
        self._require_admin(actor)
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован")
        user = User(
            email=data.email.strip().lower(),
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name.strip(),
            role=data.role,
            is_active=True,
        )
        user = await self.repo.create(user)
        await log_audit(
            db,
            actor.id,
            "CREATE",
            "user",
            user.id,
            new_data={"email": user.email, "role": user.role.value},
        )
        return UserResponse.model_validate(user)

    async def update_user(
        self, actor: User, user_id: int, data: UserUpdateAdmin, db
    ) -> UserResponse:
        self._require_admin(actor)
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        updates = data.model_dump(exclude_unset=True)
        if "password" in updates:
            password = updates.pop("password")
            if password:
                user.hashed_password = get_password_hash(password)

        if "role" in updates and updates["role"] is not None:
            if user.id == actor.id and updates["role"] != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нельзя снять с себя роль администратора",
                )
            user.role = updates["role"]

        if "is_active" in updates and updates["is_active"] is not None:
            if user.id == actor.id and updates["is_active"] is False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нельзя деактивировать свой аккаунт",
                )
            user.is_active = updates["is_active"]

        if "full_name" in updates and updates["full_name"] is not None:
            user.full_name = updates["full_name"].strip()

        await self.repo.flush_refresh(user)
        await log_audit(
            db,
            actor.id,
            "UPDATE",
            "user",
            user.id,
            new_data={k: (v.value if hasattr(v, "value") else v) for k, v in updates.items()},
        )
        return UserResponse.model_validate(user)
